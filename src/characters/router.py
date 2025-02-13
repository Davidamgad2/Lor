from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from auth.dependencies import get_current_user
from characters.service import (
    get_lor_character,
    list_lor_characters,
    get_user_favorite_characters,
    add_character_to_favorites,
    remove_character_from_favorites,
)
from typing import List
from characters.models import LorCharacter
from sqlalchemy.ext.asyncio import AsyncSession
from db import get_async_session
from auth.models import User
from helpers.redis import (
    cache_user_favorites,
    get_cached_user_favorites,
    invalidate_user_favorites,
)

characters_router = APIRouter(prefix="/characters", tags=["characters"])


@characters_router.get("/", response_model=List[LorCharacter])
async def get_characters(
    _: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session),
    offset: int = 0,
    limit: int = 100,
):
    return await list_lor_characters(db, offset, limit)


@characters_router.get("/favorites", response_model=List[LorCharacter])
async def get_favorite_characters(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session),
):
    cached_favorites = await get_cached_user_favorites(current_user.id)
    if cached_favorites is not None:
        return cached_favorites

    favorites = await get_user_favorite_characters(db, current_user.id)
    await cache_user_favorites(current_user.id, favorites)
    return favorites


@characters_router.post("/{character_id}/favorites")
async def add_favorite_character(
    character_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session),
):
    result = await add_character_to_favorites(db, current_user.id, character_id)
    await invalidate_user_favorites(current_user.id)
    return result


@characters_router.delete("/{character_id}/favorites")
async def remove_favorite_character(
    character_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session),
):
    result = await remove_character_from_favorites(db, current_user.id, character_id)
    await invalidate_user_favorites(current_user.id)
    return result


@characters_router.get("/{id}", response_model=LorCharacter)
async def get_character(
    id: str,
    _: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session),
):
    character = await get_lor_character(db, id)
    if not character:
        return JSONResponse(status_code=404, content={"message": "Character not found"})
    return character
