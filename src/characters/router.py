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
    _: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session),
    offset: int = 0,
    limit: int = 100,
    name: str = None,
):
    """
    Retrieves a list of LorCharacter objects from the database with pagination.

    Args:
        _: Authentication token obtained from get_current_user dependency
        db (AsyncSession): Database session dependency
        offset (int, optional): Number of records to skip. Defaults to 0.
        limit (int, optional): Maximum number of records to return. Defaults to 100.
        name (str, optional): Filter characters by name. Defaults to None.
    Returns:
        List[LorCharacter]: A list of LorCharacter objects

    Raises:
        HTTPException: If authentication fails or database error occurs
    """
    return await list_lor_characters(db, offset, limit, name)


@characters_router.get("/favorites", response_model=List[LorCharacter])
async def get_favorite_characters(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session),
):
    """
    Get a list of favorite characters for the current user.

    This endpoint retrieves the user's favorite characters, first checking the cache
    and falling back to the database if necessary. The results are cached for future requests.

    Args:
        current_user (User): The authenticated user making the request.
        db (AsyncSession): The database session for queries.

    Returns:
        List[LorCharacter]: A list of favorite character objects associated with the user.

    Cache behavior:
        - First attempts to fetch favorites from cache
        - If cache miss, queries database and updates cache
        - Returns cached results if available

    Dependencies:
        - Requires authentication (get_current_user)
        - Requires database session (get_async_session)
    """
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
    """
    Add a character to user's favorites.

    This endpoint allows a user to mark a character as favorite.

    Args:
        character_id (str): The unique identifier of the character to favorite.
        current_user (User): The currently authenticated user (injected by FastAPI).
        db (AsyncSession): Database session dependency (injected by FastAPI).

    Returns:
        The result of adding the character to favorites.

    Raises:
        HTTPException: If character doesn't exist or user is not authorized.

    Notes:
        - Requires authentication
        - Invalidates user favorites cache after successful operation
    """
    result = await add_character_to_favorites(db, current_user.id, character_id)
    await invalidate_user_favorites(current_user.id)
    return result


@characters_router.delete("/{character_id}/favorites")
async def remove_favorite_character(
    character_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session),
):
    """
    Removes a character from user's favorites.

    This endpoint allows authenticated users to remove a character from their favorites list.

    Args:
        character_id (str): The ID of the character to be removed from favorites
        current_user (User): The currently authenticated user (injected by dependency)
        db (AsyncSession): Database session dependency

    Returns:
        dict: Result of the removal operation

    Raises:
        HTTPException: If character is not found or user is not authorized

    Side Effects:
        - Removes character-user favorite relationship from database
        - Invalidates user's favorites cache
    """
    result = await remove_character_from_favorites(db, current_user.id, character_id)
    await invalidate_user_favorites(current_user.id)
    return result


@characters_router.get("/{id}", response_model=LorCharacter)
async def get_character(
    id: str,
    _: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session),
):
    """Retrieve a single LoR character by ID.

    This endpoint fetches a character from the database using the provided ID. It requires user
    authentication and returns a LorCharacter model if found.

    Args:
        id (str): The unique identifier of the character to retrieve
        _ (str): Current authenticated user (via dependency injection)
        db (AsyncSession): Database session (via dependency injection)

    Returns:
        LorCharacter: The requested character details
        JSONResponse: 404 error if character is not found

    Raises:
        HTTPException: If authentication fails
    """
    character = await get_lor_character(db, id)
    if not character:
        return JSONResponse(status_code=404, content={"message": "Character not found"})
    return character
