from helpers.models import BaseModel
from sqlmodel import Field


class User(BaseModel, table=True):
    __tablename__ = "users"

    username: str = Field(unique=True, index=True)
    email: str = Field(unique=True, index=True)
    password: str
    is_active: bool = Field(default=True)
    is_superuser: bool = Field(default=False)


class BlacklistedToken(BaseModel, table=True):
    __tablename__ = "blacklisted_tokens"

    token: str = Field(sa_column_kwargs={"unique": True, "index": True})
