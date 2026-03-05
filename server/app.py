from fastapi import FastAPI, HTTPException, Depends, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from vllm_engine import VLLMEngine
from scheduler import Scheduler
from limits import RateLimiter
from contextlib import asynccontextmanager
from typing import Optional
import secrets
from database import get_user_id, init_db, create_new_user 
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LORA_DIR = os.path.join(BASE_DIR, "loras")

@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    await scheduler.start()
    yield

security = HTTPBearer()

app = FastAPI(lifespan=lifespan)


# 1. Define the schema for registration
class RegisterRequest(BaseModel):
    user_id: str

@app.post("/register")
async def register_user(request: RegisterRequest):
    # Generate a random 16-character hex string for the API key
    new_api_key = f"vllm-{secrets.token_hex(8)}"
    
    # Assign a default LoRA ID (e.g., 1) and tier ("free")
    success = create_new_user(
        user_id=request.user_id, 
        api_key=new_api_key, 
        tier="free", 
        lora_id=1
    )
    
    if success:
        tenant_lora_mapping[request.user_id] = {
            "path": os.path.join(LORA_DIR, "function_adapter"), 
            "id": 1
        }
        return {"user_id": request.user_id, "api_key": new_api_key}
    else:
        raise HTTPException(status_code=400, detail="Could not create user.")

class GenerateRequest(BaseModel): 
    user_id: str
    prompt: str
    max_tokens: Optional[int] = 128
    stream: Optional[bool] = False
    ignore_eos: Optional[bool] = False

engine = VLLMEngine() 
limiter = RateLimiter()
scheduler = Scheduler(engine, limiter)

tenant_lora_mapping = {
   "admin1": {
        "path": os.path.join(LORA_DIR, "function_adapter"), 
        "id": 1 },
    "admin2": {
        "path": os.path.join(LORA_DIR, "general_adapter"), 
        "id": 2 },
    "admin3": {
        "path": os.path.join(LORA_DIR, "journal_adapter"),
        "id": 3},
    "admin4": {
        "path": os.path.join(LORA_DIR, "tool_adapter"),
        "id": 4},
    "admin5": {
        "path": os.path.join(LORA_DIR, "tool_adapter"),
        "id": 5
    }
}


@app.post("/generate")
async def generate(request: GenerateRequest, credentials : HTTPAuthorizationCredentials = Security(security) ):
    api_key = credentials.credentials
    server_validated_user_id = get_user_id(api_key)

    if not server_validated_user_id:
        raise HTTPException(status_code=401, detail="Invalid API key")
    
    lora_info = tenant_lora_mapping.get(server_validated_user_id)
    lora_path = lora_info["path"] if lora_info else None
    lora_id = lora_info["id"] if lora_info else None
    
    if request.stream:
        async def event_generator():
            generator = await scheduler.submit_stream(
                user_id = server_validated_user_id,
                api_key= api_key,
                prompt = request.prompt,
                max_tokens = request.max_tokens,
                ignore_eos = request.ignore_eos,
                lora_path=lora_path,
                lora_id=lora_id
            )

            async for chunk in generator:
                yield chunk
        
        return StreamingResponse(event_generator(), media_type="text/event-stream")
    
    else:
        output = await scheduler.submit(user_id = server_validated_user_id,
                                        api_key= api_key,
                                        prompt = request.prompt,
                                        max_tokens=request.max_tokens,   
                                        ignore_eos=request.ignore_eos,
                                        lora_path=lora_path,
                                        lora_id=lora_id
                                        )
        return {"response": output}

#  to build from scratch or after making changes to code
# sudo docker-compose up --build
