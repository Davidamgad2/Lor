from typing import List, Optional
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession
from fastapi import HTTPException
from characters.models import LorCharacter, UserFavoriteCharacter
from characters.schemas import LorCharchter
from sqlalchemy.exc import IntegrityError


async def create_lor_character(
    session: AsyncSession, character_data: LorCharchter
) -> LorCharacter:
    """
    Create a new LorCharacter from a LorCharchter schema.
    """
    new_character = LorCharacter(**character_data.dict())
    session.add(new_character)
    await session.commit()
    await session.refresh(new_character)
    return new_character


async def get_lor_character(session: AsyncSession, id: str) -> Optional[LorCharacter]:
    """
    Retrieve a LorCharacter by its external ID.
    """
    statement = select(LorCharacter).where(LorCharacter.id == id)
    result = await session.exec(statement)
    return result.one_or_none()


async def list_lor_characters(
    session: AsyncSession, offset: int = 0, limit: int = 100
) -> List[LorCharacter]:
    """
    List all LorCharacters within a pagination scope.
    """
    statement = select(LorCharacter).offset(offset).limit(limit)
    results = await session.exec(statement)
    return results.all()


async def update_lor_character(
    session: AsyncSession, external_id: str, update_data: dict
) -> Optional[LorCharacter]:
    """
    Update an existing LorCharacter using external_id.
    """
    character = await get_lor_character(session, external_id)
    if not character:
        return None

    for key, value in update_data.items():
        if hasattr(character, key):
            setattr(character, key, value)
    session.add(character)
    await session.commit()
    await session.refresh(character)
    return character


async def delete_lor_character(session: AsyncSession, external_id: str) -> bool:
    """
    Delete a LorCharacter by its external_id.
    Returns True if deletion was successful.
    """
    statement = select(LorCharacter).where(LorCharacter.external_id == external_id)
    result = await session.exec(statement)
    character = result.one_or_none()
    if not character:
        return False
    await session.delete(character)
    await session.commit()
    return True


async def bulk_create_or_update_characters(
    session: AsyncSession, characters_data: List[dict]
) -> List[LorCharacter]:
    """
    Bulk create or update LorCharacters.
    Returns list of created/updated characters.
    """
    results = []
    for data in characters_data:
        external_id = data.get("_id")
        if not external_id:
            continue

        statement = select(LorCharacter).where(LorCharacter.external_id == external_id)
        result = await session.exec(statement)
        character = result.one_or_none()

        if character:
            for key, value in data.items():
                if hasattr(character, key):
                    setattr(character, key, value)
            results.append(character)
        else:
            new_character = LorCharacter(**data)
            session.add(new_character)
            results.append(new_character)

    await session.commit()
    return results


async def get_user_favorite_characters(
    db: AsyncSession, user_id: str
) -> List[LorCharacter]:
    query = (
        select(LorCharacter)
        .join(UserFavoriteCharacter)
        .where(UserFavoriteCharacter.user_id == user_id)
    )
    result = await db.exec(query)
    return result.all()


async def add_character_to_favorites(db: AsyncSession, user_id: str, character_id: str):
    favorite = UserFavoriteCharacter(user_id=user_id, character_id=character_id)
    db.add(favorite)
    try:
        await db.commit()
        return {"message": "Character added to favorites"}
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status_code=400, detail="Character already in favorites")


async def remove_character_from_favorites(
    db: AsyncSession, user_id: str, character_id: str
):
    query = select(UserFavoriteCharacter).where(
        UserFavoriteCharacter.user_id == user_id,
        UserFavoriteCharacter.character_id == character_id,
    )
    result = await db.exec(query)
    favorite = result.one_or_none()

    if not favorite:
        raise HTTPException(status_code=404, detail="Character not in favorites")

    await db.delete(favorite)
    await db.commit()
    return {"message": "Character removed from favorites"}
