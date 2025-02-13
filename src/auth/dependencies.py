import datetime
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select
from jose import JWTError, jwt
from auth.models import User, BlacklistedToken
from db import get_async_session
from settings import settings
from redis.asyncio import Redis
from helpers.redis import get_redis

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")


async def verify_refresh_token(token: str, db: AsyncSession) -> str:
    if await is_token_blacklisted(token, db):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
        )

    try:
        payload = jwt.decode(
            token, settings.secret_key, algorithms=[settings.algorithm]
        )
        if payload.get("type") != "refresh":
            raise JWTError
        user_id = payload.get("sub")
        if user_id is None:
            raise JWTError
        return str(user_id)
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
        )


async def authenticate_user(
    username: str,
    password: str,
    db: AsyncSession,
) -> User:
    query = select(User).where(User.username == username)
    result = await db.execute(query)
    user = result.scalars().first()
    if user and user.password == password:
        return user
    return None


async def blacklist_token(
    token: str, db: AsyncSession, redis_client: Redis = Depends(get_redis)
) -> None:
    blacklisted = BlacklistedToken(token=token)
    db.add(blacklisted)
    await db.commit()
    await redis_client.set(
        f"bl:{token}", "true", ex=settings.refresh_token_expire_minutes * 60
    )


async def is_token_blacklisted(
    token: str, db: AsyncSession, redis_client: Redis = Depends(get_redis)
) -> bool:
    exists = await redis_client.get(f"bl:{token}")
    if exists:
        return True
    query = select(BlacklistedToken).where(BlacklistedToken.token == token)
    result = await db.execute(query)
    blacklisted = result.scalars().first()
    return blacklisted is not None


async def get_current_user(
    token: str = Depends(oauth2_scheme), db: AsyncSession = Depends(get_async_session)
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(
            token, settings.secret_key, algorithms=[settings.algorithm]
        )
        if payload.get("type") == "refresh":
            raise credentials_exception
        user_id = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    query = select(User).where(User.id == str(user_id))
    result = await db.execute(query)
    user = result.scalars().first()
    if user is None:
        raise credentials_exception
    return user


def create_access_token(user_id: str) -> str:
    expire = datetime.datetime.utcnow() + datetime.timedelta(
        minutes=settings.access_token_expire_minutes
    )
    payload = {"sub": str(user_id), "exp": expire, "type": "access"}
    token = jwt.encode(payload, settings.secret_key, algorithm=settings.algorithm)
    return token


def create_refresh_token(user_id: str) -> str:
    refresh_expire = datetime.datetime.utcnow() + datetime.timedelta(
        minutes=settings.refresh_token_expire_minutes
    )
    payload = {"sub": str(user_id), "exp": refresh_expire, "type": "refresh"}
    token = jwt.encode(payload, settings.secret_key, algorithm=settings.algorithm)
    return token
