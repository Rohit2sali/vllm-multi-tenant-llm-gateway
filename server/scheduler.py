import asyncio
import uuid
from transformers import AutoTokenizer
from database import update_user_tokens

class Scheduler:
    def __init__(self, engine, limiter):
        self.engine = engine
        self.limiter = limiter
        # DO NOT initialize asyncio objects here. Set them to None.
        self.queue_short = None
        self.queue_medium = None 
        self.queue_long = None
        self.tokenizer = None
        self.dispatch_task = None

    async def start(self):
        """Called by FastAPI when the server boots up."""
        # Now we are safely inside the Uvicorn event loop
        self.queue_short = asyncio.Queue()
        self.queue_medium = asyncio.Queue()
        self.queue_long = asyncio.Queue()
        
        # Load the tokenizer once during startup
        self.tokenizer = AutoTokenizer.from_pretrained("EleutherAI/pythia-70m")
        
        # Start the background loop safely
        self.background_task = asyncio.create_task(self.dispatch_loop())
        print("Scheduler started successfully.")

    async def dispatch_loop(self):
        weights = {"short": 5, "medium": 3, "long": 1}

        while True:
            requests_to_send = []

            for _ in range(weights["short"]):
                if not self.queue_short.empty():
                    requests_to_send.append(self.queue_short.get_nowait())

            for _ in range(weights["medium"]):
                if not self.queue_medium.empty():
                    requests_to_send.append(self.queue_medium.get_nowait())

            for _ in range(weights["long"]):
                if not self.queue_long.empty():
                    requests_to_send.append(self.queue_long.get_nowait()) 

            if requests_to_send:
                for req in requests_to_send:
                    if "response_queue" in req:
                        asyncio.create_task(self.process_stream_request(req))
                    else:
                        asyncio.create_task(self.process_standard_request(req))
            else:
                await asyncio.sleep(0.05)

    async def process_standard_request(self, request):
        user_id = request["user_id"]
        prompt = request["prompt"]
        max_tokens = request.get("max_tokens", 128) 
        ignore_eos = request.get("ignore_eos", False)
        future = request["future"]
        prompt_tokens = request.get("prompt_tokens", 0)
        lora_path = request.get("lora_path")
        lora_id = request.get("lora_id")

        try:
            result = await self.engine.generate(prompt,
                                                max_tokens=max_tokens, 
                                                ignore_eos=ignore_eos,
                                                lora_path=lora_path,
                                                lora_id=lora_id)
            
            # 2. Set the final text string to the future
            future.set_result(result)

            output_tokens = int(len(self.tokenizer(result)["input_ids"]))
            total_used = prompt_tokens + output_tokens
         

            asyncio.create_task(asyncio.to_thread(update_user_tokens, user_id, total_used))
            
        except Exception as e:
            future.set_exception(e)
        finally:
            await self.limiter.release(user_id)

    async def process_stream_request(self, request):
        user_id = request["user_id"]
        prompt = request["prompt"]
        max_tokens = request.get("max_tokens", 128)
        ignore_eos = request.get("ignore_eos", False)
        prompt_tokens = request.get("prompt_tokens", 0)
        response_queue = request["response_queue"]
        lora_path = request.get("lora_path")
        lora_id = request.get("lora_id")

        output_tokens = 0

        try:
            stream_gen = self.engine.generate_stream(
                                                prompt=prompt,
                                                max_tokens=max_tokens, 
                                                ignore_eos=ignore_eos,
                                                lora_path=lora_path,
                                                lora_id=lora_id)
            
            async for chunk in stream_gen:
                await response_queue.put(chunk)

                output_tokens += 1

            total_used = prompt_tokens + output_tokens
            asyncio.create_task(asyncio.to_thread(update_user_tokens, user_id, total_used))

        except Exception as e:
            print(f"Geneation Error in stream {e}")
            error_payload = f'data : {{"error" : "generation_failed : {str(e)}"}}\n\n'
            await response_queue.put(error_payload)

        finally:

            await response_queue.put(None)
            await self.limiter.release(user_id)

    async def submit_stream(self, user_id, api_key, prompt, max_tokens=128, ignore_eos=False, lora_path=None, lora_id=None):
        await self.limiter.check_and_acquire(user_id, api_key)
        
        encoded_input = self.tokenizer(prompt)
        prompt_tokens = int(len(encoded_input["input_ids"]))

        response_queue = asyncio.Queue()
        

        request_data = {
            "user_id": user_id,
            "prompt": prompt,
            "max_tokens": max_tokens, 
            "ignore_eos": ignore_eos,
            "response_queue": response_queue,
            "prompt_tokens" : prompt_tokens,
            "lora_path": lora_path,
            "lora_id": lora_id
        }

        if prompt_tokens <= 10:
            await self.queue_short.put(request_data)
        elif prompt_tokens <= 50:
            await self.queue_medium.put(request_data)
        else:
            await self.queue_long.put(request_data)

        async def stream_generator():
            while True:
                chunk = await response_queue.get()

                if chunk is None:
                    break

                yield chunk

        return stream_generator()
    

    async def submit(self, user_id, api_key, prompt, max_tokens=128, ignore_eos=False, lora_path=None, lora_id=None):
        await self.limiter.check_and_acquire(user_id, api_key)

        # Use get_running_loop() instead of get_event_loop()
        loop = asyncio.get_running_loop()
        future = loop.create_future()
        
        encoded_input = self.tokenizer(prompt)
        prompt_tokens = int(len(encoded_input["input_ids"]))
        

        request_data = {
            "user_id": user_id,
            "prompt": prompt,
            "max_tokens": max_tokens, 
            "ignore_eos": ignore_eos,
            "future": future,
            "prompt_tokens" : prompt_tokens,
            "lora_path": lora_path,
            "lora_id": lora_id
        }

        if prompt_tokens <= 10:
            await self.queue_short.put(request_data)
        elif prompt_tokens <= 50:
            await self.queue_medium.put(request_data)
        else:
            await self.queue_long.put(request_data)

        return await future
      