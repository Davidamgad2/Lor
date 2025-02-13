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
        "token_type": "bearer",
    }


@auth_router.post("/refresh", response_model=Dict[str, str])
async def refresh(
    refresh_token: RefreshToken,
    db: AsyncSession = Depends(get_async_session),
):
    user_id = await verify_refresh_token(refresh_token, db)
    new_access_token = create_access_token(user_id)
    new_refresh_token = create_refresh_token(user_id)
    return {
        "access_token": new_access_token,
        "refresh_token": new_refresh_token,
        "token_type": "bearer",
    }


@auth_router.get("/me", response_model=Dict[str, str])
async def me(user: User = Depends(get_current_user)):
    return {"username": user.username, "email": user.email}


@auth_router.post("/signout", response_model=Dict[str, str])
async def signout(
    refresh_token: RefreshToken, db: AsyncSession = Depends(get_async_session)
):
    logging.info(f"Signing out user with token: {refresh_token}")
    await blacklist_token(refresh_token, db)
    return {"msg": "User signed out successfully"}
