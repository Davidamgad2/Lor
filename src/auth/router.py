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
    oauth2_scheme,
    create_refresh_token,
    verify_refresh_token,
)
from .models import User
import logging

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/signup", response_model=Dict[str, str])
async def signup(user_data: UserCreate, db: AsyncSession = Depends(get_async_session)):
    await create_user(
        db=db,
        username=user_data.username,
        email=user_data.email,
        password=user_data.password,
    )
    return {"msg": "User created successfully"}


@router.post("/login", response_model=Dict[str, str])
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


@router.post("/refresh", response_model=Dict[str, str])
async def refresh(
    refresh_token: str,
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


@router.get("/me", response_model=Dict[str, str])
async def me(user: User = Depends(get_current_user)):
    return {"username": user.username, "email": user.email}


@router.post("/signout", response_model=Dict[str, str])
async def signout(refresh_token: str, db: AsyncSession = Depends(get_async_session)):
    logging.info(f"Signing out user with token: {refresh_token}")
    await blacklist_token(refresh_token, db)
    return {"msg": "User signed out successfully"}
