import datetime
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select
from jose import JWTError, jwt
from auth.models import User, BlacklistedToken
from db import get_async_session
from settings import settings
from helpers.redis import RedisClient
from auth.utility import verify_password

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")


async def verify_refresh_token(token: str, db: AsyncSession) -> str:
    """
    Verify and decode a refresh token, ensuring it's valid and not blacklisted.

    Args:
        token (str): The refresh token to verify
        db (AsyncSession): Database session for blacklist checking

    Returns:
        str: The user ID extracted from the token payload

    Raises:
        HTTPException: If token is blacklisted or invalid with 401 Unauthorized
    """
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
    """Authenticate a user by verifying their username and password.

    This asynchronous function queries the database for a user with the given username
    and verifies their password. If authentication is successful, it returns the User object.

    Args:
        username (str): The username to authenticate.
        password (str): The password to verify.
        db (AsyncSession): The database session for executing queries.

    Returns:
        User: The authenticated user object if credentials are valid.
        None: If authentication fails (invalid username or password).

    Example:
        user = await authenticate_user("john_doe", "password123", db_session)
        if user:
            # User authenticated successfully
    """
    query = select(User).where(User.username == username)
    result = await db.execute(query)
    user = result.scalars().first()
    if user and verify_password(password, user.password):
        return user
    return None


async def blacklist_token(token: str, db: AsyncSession) -> None:
    redis_client = await RedisClient.get_instance()
    blacklisted = BlacklistedToken(token=token)
    db.add(blacklisted)
    await db.commit()
    await redis_client.set(
        f"bl:{token}", "true", ex=settings.refresh_token_expire_minutes * 60
    )


async def is_token_blacklisted(token: str, db: AsyncSession) -> bool:
    """Check if a token is blacklisted.

    This function checks both Redis cache and database to determine if a token has been blacklisted.
    First checks Redis for faster lookups, then falls back to database if not found in cache.

    Args:
        token (str): The JWT token to check
        db (AsyncSession): The database session for querying

    Returns:
        bool: True if token is blacklisted, False otherwise

    Example:
        >>> is_blacklisted = await is_token_blacklisted(jwt_token, db_session)
        >>> if is_blacklisted:
        >>>     raise HTTPException(status_code=401, detail="Token is blacklisted")
    """
    redis_client = await RedisClient.get_instance()
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
    """
    Validate JWT token and retrieve current user from database.

    This async function validates the provided JWT access token and returns the corresponding user.
    It checks if the token is valid, not a refresh token, and if the user exists in the database.

    Args:
        token (str): JWT access token obtained from oauth2_scheme dependency
        db (AsyncSession): Database session obtained from get_async_session dependency

    Returns:
        User: User object if authentication is successful

    Raises:
        HTTPException: 401 Unauthorized error if:
            - Token is invalid or expired
            - Token is a refresh token
            - User ID is missing from token
            - User does not exist in database
    """
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
    """
    Generate a JSON Web Token (JWT) access token for user authentication.

    Args:
        user_id (str): The unique identifier of the user.

    Returns:
        str: A JWT access token containing user ID, expiration time, and token type.

    Details:
        - Creates a token that expires based on settings.access_token_expire_minutes
        - Includes user ID in 'sub' claim, expiration in 'exp' claim, and token type
        - Signs token using settings.secret_key and settings.algorithm
    """
    expire = datetime.datetime.utcnow() + datetime.timedelta(
        minutes=settings.access_token_expire_minutes
    )
    payload = {"sub": str(user_id), "exp": expire, "type": "access"}
    token = jwt.encode(payload, settings.secret_key, algorithm=settings.algorithm)
    return token


def create_refresh_token(user_id: str) -> str:
    """
    Creates a JWT refresh token for a given user ID.

    Args:
        user_id (str): The unique identifier of the user.

    Returns:
        str: A JWT refresh token string.

    Details:
        - Generates a refresh token with expiration time based on settings
        - Includes user ID as subject ('sub'), expiration time ('exp'), and token type ('type')
        - Uses secret key and algorithm from settings to encode the token

    Example:
        refresh_token = create_refresh_token("user123")
    """
    refresh_expire = datetime.datetime.utcnow() + datetime.timedelta(
        minutes=settings.refresh_token_expire_minutes
    )
    payload = {"sub": str(user_id), "exp": refresh_expire, "type": "refresh"}
    token = jwt.encode(payload, settings.secret_key, algorithm=settings.algorithm)
    return token
