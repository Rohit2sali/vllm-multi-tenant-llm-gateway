import uuid
from vllm import AsyncLLMEngine, AsyncEngineArgs
from vllm.sampling_params import SamplingParams
from vllm.lora.request import LoRARequest

import json
import asyncio

class VLLMEngine:
    def __init__(self):
        engine_args = AsyncEngineArgs(
            model="casperhansen/llama-3.2-1b-instruct-awq",
            quantization="awq",
            gpu_memory_utilization=0.6,
            max_model_len=2048, 
            enable_lora=True,
            max_loras=2, # max no of adapters active in GPU exactly at a same time
            max_lora_rank=64, # max dimension of the adapter 
            max_cpu_loras=16 # max adapters cached in standard CPU ram
        )
        self.engine = AsyncLLMEngine.from_engine_args(engine_args) 


    async def generate(self, prompt, max_tokens=128, ignore_eos=False, lora_path=None, lora_id=None):
        sampling_params = SamplingParams(
            temperature=0.7,
            max_tokens=max_tokens,
            ignore_eos=ignore_eos
        )

        # 1. Generate a mathematically unique ID for this specific API call
        request_id = str(uuid.uuid4())

        lora_request = None
        if lora_path and lora_id:
            lora_request = LoRARequest(
                lora_name=str(lora_id),
                lora_int_id=int(lora_id),
                lora_path=lora_path
            )

        # 2. Use keyword arguments to avoid vLLM versioning errors
        results_generator = self.engine.generate(
            prompt, # Pass prompt as the first positional argument
            sampling_params=sampling_params,
            request_id=request_id,
            lora_request=lora_request
        )

        final_output = None
        async for request_output in results_generator:
            final_output = request_output

        # outputs[0] gets the first sequence (since n=1 by default)
        return final_output.outputs[0].text


    async def generate_stream(self, prompt, max_tokens=128, ignore_eos=False, lora_path=None, lora_id=None):
        sampling_params = SamplingParams(
            temperature=0.7,
            max_tokens=max_tokens,
            ignore_eos=ignore_eos
        )

        # 1. Generate a mathematically unique ID for this specific API call
        request_id = str(uuid.uuid4())

        lora_request = None
        if lora_path and lora_id:
            lora_request = LoRARequest(
                lora_name=str(lora_id),
                lora_int_id=int(lora_id),
                lora_path=lora_path
            )

        # 2. Use keyword arguments to avoid vLLM versioning errors
        results_generator = self.engine.generate(
            prompt, # Pass prompt as the first positional argument
            sampling_params=sampling_params,
            request_id=request_id,
            lora_request=lora_request
        )

        previous_text = ""
        try:
            async for request_output in results_generator:
                text = request_output.outputs[0].text

                new_text = text[len(previous_text):]
                previous_text = text

                if new_text:
                    payload = json.dumps({"token" : new_text})
                    yield f"data: {payload}\n\n"

            yield f"data: [DONE]\n\n"

        except asyncio.CancelledError:
            await self.engine.abort(request_id)
            raise
