from pydantic import BaseModel, EmailStr
from typing import Optional
from uuid import UUID


class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str


class UserUpdate(BaseModel):
    username: Optional[str]
    email: Optional[EmailStr]
    password: Optional[str]
    is_active: Optional[bool]
    is_superuser: Optional[bool]


class UserInDB(UserCreate):
    id: UUID
    username: str
    is_active: bool
    is_superuser: bool


class UserLogin(BaseModel):
    username: str
    password: str


class RefreshToken(BaseModel):
    refresh_token: str
