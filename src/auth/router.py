from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict
from db import get_async_session
from .schemas import UserCreate, UserLogin
from .service import create_user
from .dependencies import (
    authenticate_user,
    create_access_token,
    get_current_user,
    blacklist_token,
    create_refresh_token,
    verify_refresh_token,
)
from .models import User
import logging
from sqlalchemy.exc import IntegrityError
from auth.schemas import RefreshToken

logger = logging.getLogger(__name__)
auth_router = APIRouter(prefix="/auth", tags=["auth"])


@auth_router.post("/signup", response_model=Dict[str, str])
async def signup(user_data: UserCreate, db: AsyncSession = Depends(get_async_session)):
    """Handle user registration endpoint.

    This endpoint processes user signup requests by creating new user accounts in the database.

    Args:
        user_data (UserCreate): User registration data containing username, email and password
        db (AsyncSession): Async database session dependency

    Returns:
        Dict[str, str]: Success message indicating user creation

    Raises:
        HTTPException 400: If email or username already exists in database
        HTTPException 400: For other database integrity errors
        HTTPException 500: For unexpected server errors during user creation

    Examples:
        POST /signup
        {
            "username": "john_doe",
            "email": "john@example.com",
            "password": "securepassword123"
        }
    """
    try:
        await create_user(
            db=db,
            username=user_data.username,
            email=user_data.email,
            password=user_data.password,
        )
    except IntegrityError as e:
        error_detail = str(e.orig)
        if "ix_users_email" in error_detail:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User with this email already exists",
            )
        elif "ix_users_username" in error_detail:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User with this username already exists",
            )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Database integrity error",
        )
    except Exception as e:
        logger.error(f"Error creating user: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while creating user",
        )
    return {"msg": "User created successfully"}


@auth_router.post("/login", response_model=Dict[str, str])
async def login(
    user_data: UserLogin,
    db: AsyncSession = Depends(get_async_session),
):
    """Login endpoint for user authentication.

    This endpoint handles user authentication by validating credentials and generating access
    and refresh tokens upon successful authentication.

    Args:
        user_data (UserLogin): The user login data containing username and password.
        db (AsyncSession): The database session dependency.

    Returns:
        Dict[str, str]: A dictionary containing:
            - access_token: JWT access token
            - refresh_token: JWT refresh token
            - token_type: Token type (bearer)

    Raises:
        HTTPException: 401 UNAUTHORIZED if credentials are invalid.
    """
    user = await authenticate_user(user_data.username, user_data.password, db)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
        )
    access_token = create_access_token(user.id)
    refresh_token = create_refresh_token(user.id)
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "Bearer",
    }


@auth_router.post("/refresh", response_model=Dict[str, str])
async def refresh(
    refresh_token: RefreshToken,
    db: AsyncSession = Depends(get_async_session),
):
    """
    Refreshes the access token using a valid refresh token.

    This endpoint generates new access and refresh tokens for a user when provided with a valid refresh token.
    The existing refresh token is verified against the database before generating new tokens.

    Args:
        refresh_token (RefreshToken): The refresh token object containing the token to verify
        db (AsyncSession): Database session dependency

    Returns:
        Dict[str, str]: A dictionary containing:
            - access_token: New JWT access token
            - refresh_token: New JWT refresh token
            - token_type: Token type (always "Bearer")

    Raises:
        HTTPException: If the refresh token is invalid or expired

    Notes:
        The endpoint requires a valid refresh token to be provided in the request body.
        Both the access token and refresh token are renewed in this operation.
    """
    user_id = await verify_refresh_token(refresh_token, db)
    new_access_token = create_access_token(user_id)
    new_refresh_token = create_refresh_token(user_id)
    return {
        "access_token": new_access_token,
        "refresh_token": new_refresh_token,
        "token_type": "Bearer",
    }


@auth_router.get("/me", response_model=Dict[str, str])
async def me(user: User = Depends(get_current_user)):
    """
    Retrieves information about the currently authenticated user.

    This endpoint requires authentication and returns basic user information including
    username, email, active status, and superuser status.

    Args:
        user (User): The currently authenticated user object, obtained via dependency injection.

    Returns:
        Dict[str, str]: A dictionary containing:
            - username: The user's username
            - email: The user's email address
            - is_active: Whether the user account is active
            - is_superuser: Whether the user has superuser privileges

    Dependencies:
        - get_current_user: Validates the authentication token and returns the User object

    Requires:
        - Authentication: Valid JWT token must be provided in request headers
    """
    return {
        "username": user.username,
        "email": user.email,
        "is_active": user.is_active,
        "is_superuser": user.is_superuser,
    }


@auth_router.post("/signout", response_model=Dict[str, str])
async def signout(
    refresh_token: RefreshToken, db: AsyncSession = Depends(get_async_session)
):
    """
    Sign out a user by blacklisting their refresh token.

    This endpoint handles user sign-out by adding the provided refresh token
    to a blacklist, preventing its future use for authentication.

    Args:
        refresh_token (RefreshToken): The refresh token to be blacklisted
        db (AsyncSession): Database session dependency

    Returns:
        Dict[str, str]: A dictionary containing a success message
            - msg: Confirmation message that user was signed out

    Raises:
        HTTPException: If token blacklisting fails

    Example:
        {
            "msg": "User signed out successfully"
        }
    """
    logging.info(f"Signing out user with token: {refresh_token}")
    await blacklist_token(refresh_token, db)
    return {"msg": "User signed out successfully"}
