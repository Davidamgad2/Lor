from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlmodel.ext.asyncio.session import AsyncSession
from typing import AsyncGenerator

from settings import settings

async_engine = create_async_engine(
    settings.db_url, echo=False, future=True, pool_size=20, max_overflow=5
)


async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Asynchronous generator function that yields a database session.

    This function creates and provides an asynchronous database session using SQLAlchemy's
    AsyncSession. The session is configured with expire_on_commit=False to prevent
    automatic expiration of objects after transaction commits.

    Yields:
        AsyncSession: An asynchronous SQLAlchemy session object for database operations.

    Example:
        async for session in get_async_session():
            result = await session.execute(query)
            await session.commit()
    """
    async_session = sessionmaker(
        bind=async_engine, class_=AsyncSession, expire_on_commit=False
    )
    async with async_session() as session:
        yield session
