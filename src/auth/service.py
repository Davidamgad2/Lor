from typing import List, Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select
from .models import User


async def create_user(
    db: AsyncSession,
    username: str,
    email: str,
    password: str,
    is_active: bool = True,
    is_superuser: bool = False,
) -> User:
    user = User(
        username=username,
        email=email,
        password=password,
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
    query = select(User).where(User.id == user_id)
    result = await db.execute(query)
    user = result.scalars().first()
    if not user:
        return False
    await db.delete(user)
    await db.commit()
    return True
