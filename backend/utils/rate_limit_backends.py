import asyncio
import time
from typing import Protocol

from backend.configs.settings import Settings


class RateLimiterBackend(Protocol):
    async def is_allowed(self, identifier: str) -> bool: ...


class InMemoryRateLimiterBackend:
    """In-memory sliding window rate limiter."""

    def __init__(self, max_attempts: int, window_seconds: int) -> None:
        self.max_attempts = max_attempts
        self.window_seconds = window_seconds
        self.attempts: dict[str, list[float]] = {}
        self.lock = asyncio.Lock()

    async def is_allowed(self, identifier: str) -> bool:
        async with self.lock:
            now = time.time()
            window_start = now - self.window_seconds

            if identifier not in self.attempts:
                self.attempts[identifier] = []

            self.attempts[identifier] = [
                attempt
                for attempt in self.attempts[identifier]
                if attempt > window_start
            ]

            if len(self.attempts[identifier]) >= self.max_attempts:
                return False

            self.attempts[identifier].append(now)
            return True


class RedisRateLimiterBackend:
    """Redis-backed sliding window rate limiter."""

    def __init__(
        self,
        redis_url: str,
        prefix: str,
        max_attempts: int,
        window_seconds: int,
    ) -> None:
        from redis.asyncio import Redis  # noqa: PLC0415

        self.redis = Redis.from_url(redis_url, decode_responses=True)
        self.prefix = prefix
        self.max_attempts = max_attempts
        self.window_seconds = window_seconds

    async def is_allowed(self, identifier: str) -> bool:
        now = time.time()
        key = f'ratelimit:{self.prefix}:{identifier}'
        window_start = now - self.window_seconds

        pipe = self.redis.pipeline()
        pipe.zremrangebyscore(key, 0, window_start)
        pipe.zadd(key, {str(now): now})
        pipe.zcard(key)
        pipe.expire(key, self.window_seconds)
        results = await pipe.execute()
        count = int(results[2])
        return count <= self.max_attempts


def create_rate_limit_backend(
    prefix: str,
    max_attempts: int,
    window_seconds: int,
) -> RateLimiterBackend:
    settings = Settings()
    if settings.RATE_LIMIT_BACKEND == 'redis' and settings.REDIS_URL:
        return RedisRateLimiterBackend(
            redis_url=settings.REDIS_URL,
            prefix=prefix,
            max_attempts=max_attempts,
            window_seconds=window_seconds,
        )
    return InMemoryRateLimiterBackend(
        max_attempts=max_attempts,
        window_seconds=window_seconds,
    )
