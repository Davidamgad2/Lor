from redis.asyncio import Redis
from typing import AsyncGenerator
from settings import settings

redis_client = Redis(
    host=settings.REDIS_HOST, port=settings.REDIS_PORT, decode_responses=True
)


async def get_redis() -> AsyncGenerator[Redis, None]:
    yield redis_client
