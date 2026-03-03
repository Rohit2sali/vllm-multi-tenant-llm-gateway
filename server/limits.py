import time
from collections import defaultdict
import asyncio
from fastapi import HTTPException  # 👈 1. Add this import
from database import check_used_tokens


class RateLimiter:
    def __init__(self,
                 max_requests_per_minute=60,
                 max_concurrent_per_user=2,
                 max_global_concurrent=16,
                 max_tokens_free_user=10000, 
                 max_tokens_premium_tokens=15000):

        self.max_requests_per_minute = max_requests_per_minute
        self.max_concurrent_per_user = max_concurrent_per_user
        self.max_global_concurrent = max_global_concurrent
        self.max_tokens_free_user = max_tokens_free_user
        self.max_tokens_premium_user = max_tokens_premium_tokens

        self.user_timestamps = defaultdict(list)
        self.user_concurrent = defaultdict(int)
        self.global_concurrent = 0

        # self.check_used_tokens = check_used_tokens()

        self.lock = asyncio.Lock()

    async def check_and_acquire(self, user_id: str, api_key):
        async with self.lock:
            now = time.time()

            # 1️⃣ Clean old timestamps
            self.user_timestamps[user_id] = [
                ts for ts in self.user_timestamps[user_id]
                if now - ts < 60
            ]

            # 2️⃣ Requests per minute check
            if len(self.user_timestamps[user_id]) >= self.max_requests_per_minute:
                # 👈 2. Change to HTTPException
                raise HTTPException(status_code=429, detail="Rate limit exceeded (per minute)")

            # 3️⃣ Per-user concurrency check
            if self.user_concurrent[user_id] >= self.max_concurrent_per_user:
                # 👈 3. Change to HTTPException
                raise HTTPException(status_code=429, detail="Too many concurrent requests for this user")

            # 4️⃣ Global concurrency check
            if self.global_concurrent >= self.max_global_concurrent:
                # 👈 4. Change to HTTPException
                raise HTTPException(status_code=429, detail="Server overloaded")
            
            usage = check_used_tokens(api_key)
            if(((usage[1] == "free") and (usage[0] > self.max_tokens_free_user)) or ((usage[1] == "premium") and (usage[0] > self.max_tokens_premium_user))):
                raise HTTPException(status_code=429, detail=f"User has exceeded his limits of {usage[1]}")

            # ✅ Acquire
            self.user_timestamps[user_id].append(now)
            self.user_concurrent[user_id] += 1
            self.global_concurrent += 1

    async def release(self, user_id: str):
        async with self.lock:
            self.user_concurrent[user_id] -= 1
            self.global_concurrent -= 1