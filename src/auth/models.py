from helpers.models import BaseModel
from sqlmodel import Column, String, Boolean, Field


class User(BaseModel):
    __tablename__ = "users"

    username = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True)
    password = Column(String)
    is_active = Column(Boolean, default=True)
    is_superuser = Column(Boolean, default=False)


class BlacklistedToken(BaseModel):
    __tablename__ = "blacklisted_tokens"
    token: str = Field(sa_column_kwargs={"unique": True, "index": True})
