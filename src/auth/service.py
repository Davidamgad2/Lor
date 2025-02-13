from typing import List, Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select
from .models import User
from .utility import get_password_hash


async def create_user(
    db: AsyncSession,
    username: str,
    email: str,
    password: str,
    is_active: bool = True,
    is_superuser: bool = False,
) -> User:
    """Create a new user in the database.

    This function creates a new user with the provided credentials and saves it to the database.

    Args:
        db (AsyncSession): The database session.
        username (str): The username for the new user.
        email (str): The email address for the new user.
        password (str): The password for the new user.
        is_active (bool, optional): Whether the user account is active. Defaults to True.
        is_superuser (bool, optional): Whether the user has superuser privileges. Defaults to False.

    Returns:
        User: The newly created user object.

    Raises:
        SQLAlchemyError: If there's an error during database operations.
    """
    user = User(
        username=username,
        email=email,
        password=get_password_hash(password),
        is_active=is_active,
        is_superuser=is_superuser,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


async def get_users(
    db: AsyncSession, filters: Optional[Dict[str, Any]] = None
) -> List[User]:
    """
    Retrieve users from the database based on optional filters.

    This asynchronous function fetches User records from the database and allows filtering
    based on User model attributes.

    Args:
        db (AsyncSession): The database session for executing queries.
        filters (Optional[Dict[str, Any]], optional): Dictionary of field-value pairs to filter users.
            Keys must correspond to User model attributes. Defaults to None.

    Returns:
        List[User]: A list of User objects matching the specified filters.
    """
    query = select(User)
    if filters:
        for field, value in filters.items():
            if hasattr(User, field):
                query = query.where(getattr(User, field) == value)
    result = await db.execute(query)
    return result.scalars().all()


async def update_user(
    db: AsyncSession, user_id: Any, update_data: Dict[str, Any]
) -> Optional[User]:
    """
    Asynchronously updates a user's information in the database.

    Args:
        db (AsyncSession): The database session.
        user_id (Any): The ID of the user to update.
        update_data (Dict[str, Any]): Dictionary containing the fields to update and their new values.

    Returns:
        Optional[User]: The updated user object if found, None if user doesn't exist.
    """
    query = select(User).where(User.id == user_id)
    result = await db.execute(query)
    user = result.scalars().first()
    if not user:
        return None
    for field, value in update_data.items():
        if hasattr(user, field):
            setattr(user, field, value)
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


async def delete_user(db: AsyncSession, user_id: Any) -> bool:
    """Delete a user from the database by their ID.

    Args:
        db (AsyncSession): The database session for executing the query.
        user_id (Any): The ID of the user to be deleted.

    Returns:
        bool: True if the user was successfully deleted, False if the user was not found.
    """
    query = select(User).where(User.id == user_id)
    result = await db.execute(query)
    user = result.scalars().first()
    if not user:
        return False
    await db.delete(user)
    await db.commit()
    return True
