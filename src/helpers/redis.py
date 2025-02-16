from redis.asyncio import Redis
from settings import settings
import json
from typing import Optional, Any, List, Dict
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


def deserialize_lor_character(data: Dict[str, Any]) -> Dict[str, Any]:
    """Deserialize objects from Redis storage"""
    result = {}
    for key, value in data.items():
        if isinstance(value, str):
            try:
                result[key] = UUID(value)
                continue
            except ValueError:
                pass

            try:
                result[key] = datetime.fromisoformat(value)
                continue
            except ValueError:
                pass

        elif isinstance(value, dict):
            result[key] = deserialize_lor_character(value)
            continue
        elif isinstance(value, list):
            result[key] = [
                deserialize_lor_character(item) if isinstance(item, dict) else item
                for item in value
            ]
            continue

        result[key] = value
    return result


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
    """
    Cache user's favorite LoR characters in Redis.

    This function stores a list of favorite characters for a specific user in Redis cache
    with an expiration time.

    Args:
        user_id (str): The unique identifier of the user
        favorites (List[LorCharchter]): List of LoR character objects to cache
        expire_seconds (int, optional): Cache expiration time in seconds. Defaults to 3600.

    Returns:
        None

    Examples:
        >>> await cache_user_favorites("user123", [char1, char2], 7200)
    """
    redis = await RedisClient.get_instance()
    cache_key = f"user:{user_id}:favorites"
    serialized_favorites = [serialize_lor_character(f) for f in favorites]
    await redis.setex(cache_key, expire_seconds, json.dumps(serialized_favorites))


async def get_cached_user_favorites(user_id: str) -> List[LorCharchter] | None:
    """
    Retrieves a user's cached favorite characters from Redis.

    Args:
        user_id (str): The unique identifier of the user whose favorites are being retrieved.

    Returns:
        List[LorCharacter] | None: A list of LorCharacter objects if cached data exists,
        or None if no cached data is found.

    Example:
        favorites = await get_cached_user_favorites("user123")
        if favorites:
            for character in favorites:
                print(character.name)
    """
    redis = await RedisClient.get_instance()
    cache_key = f"user:{user_id}:favorites"
    cached = await redis.get(cache_key)
    if cached:
        from characters.models import LorCharacter

        data = json.loads(cached)
        return [LorCharacter(**deserialize_lor_character(item)) for item in data]
    return None


async def invalidate_user_favorites(user_id: str):
    """
    Invalidates the cached favorites for a specific user by removing the corresponding Redis key.

    Args:
        user_id (str): The unique identifier of the user whose favorites cache needs to be invalidated.

    Returns:
        None

    Raises:
        RedisError: If there's an error connecting to or interacting with Redis.
    """
    redis = await RedisClient.get_instance()
    cache_key = f"user:{user_id}:favorites"
    await redis.delete(cache_key)


async def cache_lor_character(
    character: Dict[str, Any], expire_seconds: int = 3600
) -> None:
    """
    Cache a single LorCharacter object.
    """
    redis = await RedisClient.get_instance()
    key = f"character:{character['id']}"
    await redis.setex(
        key, expire_seconds, json.dumps(character, default=serialize_lor_character)
    )


async def get_cached_lor_character(character_id: str) -> Optional[Dict[str, Any]]:
    """
    Get a cached LorCharacter object.
    """
    redis = await RedisClient.get_instance()
    key = f"character:{character_id}"
    cached = await redis.get(key)
    if cached:
        return json.loads(cached)
    return None


async def invalidate_characters_cache() -> None:
    """
    Invalidate all character caches.
    This example assumes all cached character keys begin with 'character:'.
    """
    redis = await RedisClient.get_instance()
    charchters_keys = await redis.keys("character:*")
    charchters_list_keys = await redis.keys("characters:list:*")
    keys = charchters_keys + charchters_list_keys
    if keys:
        await redis.delete(*keys)


async def invalidate_users_cache() -> None:
    """
    Invalidate all user caches.
    This example assumes all cached user keys begin with 'user:'.
    """
    redis = await RedisClient.get_instance()
    keys = await redis.keys("user:*:favorites")
    if keys:
        await redis.delete(*keys)
