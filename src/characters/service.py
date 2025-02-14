from typing import List, Optional
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession
from fastapi import HTTPException
from characters.models import LorCharacter, UserFavoriteCharacter
from characters.schemas import LorCharchter
from sqlalchemy.exc import IntegrityError
import logging


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
    session: AsyncSession, offset: int = 0, limit: int = 100, name: str = None
) -> List[LorCharacter]:
    """
    List all LorCharacters within a pagination scope, and an optional name filter.
    """
    statement = select(LorCharacter).offset(offset).limit(limit)
    if name:
        statement = statement.where(LorCharacter.name.ilike(f"%{name}%"))
    results = await session.exec(statement)
    return results.all()


async def update_lor_character(
    session: AsyncSession, id: str, update_data: dict
) -> Optional[LorCharacter]:
    """
    Update an existing LorCharacter using id.
    """
    character = await get_lor_character(session, id)
    if not character:
        return None

    for key, value in update_data.items():
        if hasattr(character, key):
            setattr(character, key, value)
    session.add(character)
    await session.commit()
    await session.refresh(character)
    return character


async def delete_lor_character(session: AsyncSession, id: str) -> bool:
    """
    Delete a LorCharacter by its id.
    Returns True if deletion was successful.
    """
    statement = select(LorCharacter).where(LorCharacter.id == id)
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
    Bulk create or update LorCharacters using a single database operation.
    Returns list of created/updated characters.
    """
    if not characters_data:
        return []

    allowed_fields = {
        "external_id",
        "name",
        "wikiUrl",
        "race",
        "birth",
        "gender",
        "death",
        "hair",
        "height",
        "realm",
        "spouse",
    }
    values = []
    for data in characters_data:
        if "_id" in data:
            cleaned_data = {}
            cleaned_data["external_id"] = data["_id"]
            for field in allowed_fields - {"external_id"}:
                if field in data:
                    cleaned_data[field] = data[field]
            values.append(cleaned_data)

    if not values:
        return []

    try:
        stmt = pg_insert(LorCharacter.__table__).values(values)

        update_dict = {
            field: getattr(stmt.excluded, field)
            for field in allowed_fields
            if field != "external_id"
        }

        stmt = stmt.on_conflict_do_update(
            index_elements=["external_id"], set_=update_dict
        ).returning(*LorCharacter.__table__.columns)

        result = await session.execute(stmt)
        await session.commit()

        return [LorCharacter(**row._mapping) for row in result.fetchall()]

    except Exception as e:
        await session.rollback()
        raise e

    except Exception as e:
        await session.rollback()
        logging.error(f"Error in bulk operation: {str(e)}")
        raise


async def get_user_favorite_characters(
    db: AsyncSession, user_id: str
) -> List[LorCharacter]:
    """
    Retrieves a list of favorite LorCharacter objects for a specific user.

    Args:
        db (AsyncSession): The async database session to use for the query.
        user_id (str): The unique identifier of the user whose favorites to retrieve.

    Returns:
        List[LorCharacter]: A list of LorCharacter objects that the user has marked as favorites.

    Raises:
        SQLAlchemyError: If there's an error executing the database query.
    """
    query = (
        select(LorCharacter)
        .join(UserFavoriteCharacter)
        .where(UserFavoriteCharacter.user_id == user_id)
    )
    result = await db.exec(query)
    return result.all()


async def add_character_to_favorites(db: AsyncSession, user_id: str, character_id: str):
    """
    Add a character to user's favorites list.

    This function creates a new favorite character entry for a user in the database.

    Args:
        db (AsyncSession): The database session for executing the operation
        user_id (str): The ID of the user adding the favorite
        character_id (str): The ID of the character to be added to favorites

    Returns:
        dict: A message confirming the character was added to favorites

    Raises:
        HTTPException: If the character is already in user's favorites (400 Bad Request)

    Example:
        >>> await add_character_to_favorites(db, "user123", "char456")
        {"message": "Character added to favorites"}
    """
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
    """Removes a character from the user's favorites list.

    This asynchronous function queries the database for a specific favorite character entry
    and removes it if found. If the character is not in the user's favorites, it raises
    an HTTP 404 exception.

    Args:
        db (AsyncSession): The database session for executing queries
        user_id (str): The unique identifier of the user
        character_id (str): The unique identifier of the character to be removed

    Returns:
        dict: A message confirming the character was removed from favorites

    Raises:
        HTTPException: If the character is not found in the user's favorites (404)
    """
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
