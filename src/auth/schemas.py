from pydantic import BaseModel
from typing import Optional


class UserCreate(BaseModel):
    username: str
    email: str
    password: str


class UserUpdate(BaseModel):
    username: Optional[str]
    email: Optional[str]
    password: Optional[str]
    is_active: Optional[bool]
    is_superuser: Optional[bool]


class UserInDB(UserCreate):
    id: int
    username: str
    is_active: bool
    is_superuser: bool


class UserLogin(BaseModel):
    username: str
    password: str


class RefreshToken(BaseModel):
    refresh_token: str

    class Config:
        json_schema_extra = {
            "example": {"token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."}
        }
