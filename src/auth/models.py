from helpers.models import BaseModel
from sqlmodel import Field, Relationship
from typing import List
from pydantic import EmailStr
from characters.models import LorCharacter, UserFavoriteCharacter


class User(BaseModel, table=True):
    __tablename__ = "users"
    __table_args__ = {"extend_existing": True}

    username: str = Field(unique=True, index=True)
    email: EmailStr = Field(unique=True, index=True)
    password: str
    is_active: bool = Field(default=True)
    is_superuser: bool = Field(default=False)
    favorite_characters: List["LorCharacter"] = Relationship(
        back_populates="favorited_by",
        link_model=UserFavoriteCharacter,
        sa_relationship_kwargs={"lazy": "selectin"},
    )


class BlacklistedToken(BaseModel, table=True):
    __tablename__ = "blacklisted_tokens"
    token: str = Field(sa_column_kwargs={"unique": True, "index": True})
