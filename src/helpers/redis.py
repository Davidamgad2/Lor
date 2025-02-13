from redis.asyncio import Redis
from settings import settings
from typing import Optional
import json
from typing import List, Any
from characters.schemas import LorCharchter
from datetime import datetime
from uuid import UUID


def serialize_lor_character(obj: Any) -> Any:
    """Serialize objects for Redis storage"""
    if isinstance(obj, datetime):
        return obj.isoformat()
    if isinstance(obj, UUID):
        return str(obj)
    if isinstance(obj, LorCharchter):
        return serialize_lor_character(obj.dict())
    if hasattr(obj, "dict"):
        return {k: serialize_lor_character(v) for k, v in obj.dict().items()}
    if isinstance(obj, dict):
        return {k: serialize_lor_character(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [serialize_lor_character(item) for item in obj]
    return obj


def deserialize_lor_character(data: dict) -> dict:
    """Deserialize objects from Redis storage"""
    for key, value in data.items():
        if isinstance(value, str):
            try:
                data[key] = UUID(value)
                continue
            except ValueError:
                pass
            if value.endswith("Z"):
                try:
                    data[key] = datetime.fromisoformat(value.rstrip("Z"))
                except ValueError:
                    pass
    return data


class RedisClient:
    _instance: Optional[Redis] = None

    @classmethod
    async def get_instance(cls) -> Redis:
        if cls._instance is None:
            cls._instance = Redis(
                host=settings.REDIS_HOST,
                port=settings.REDIS_PORT,
                db=settings.REDIS_DB,
                decode_responses=True,
            )
        return cls._instance

    @classmethod
    async def close(cls) -> None:
        if cls._instance is not None:
            await cls._instance.close()
            cls._instance = None


async def cache_user_favorites(
    user_id: str, favorites: List[LorCharchter], expire_seconds: int = 3600
):
    redis = await RedisClient.get_instance()
    cache_key = f"user:{user_id}:favorites"
    serialized_favorites = [serialize_lor_character(f) for f in favorites]
    await redis.setex(cache_key, expire_seconds, json.dumps(serialized_favorites))


async def get_cached_user_favorites(user_id: str) -> List[LorCharchter] | None:
    redis = await RedisClient.get_instance()
    cache_key = f"user:{user_id}:favorites"
    cached = await redis.get(cache_key)
    if cached:
        from characters.models import LorCharacter

        data = json.loads(cached)
        return [LorCharacter(**deserialize_lor_character(item)) for item in data]
    return None


async def invalidate_user_favorites(user_id: str):
    redis = await RedisClient.get_instance()
    cache_key = f"user:{user_id}:favorites"
    await redis.delete(cache_key)
