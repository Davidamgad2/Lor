from helpers.models import BaseModel
from characters.schemas import LorCharchter
from sqlmodel import String, Field, Relationship, UniqueConstraint
from typing import List, TYPE_CHECKING
from uuid import UUID

if TYPE_CHECKING:
    from auth.models import User


class UserFavoriteCharacter(BaseModel, table=True):
    __tablename__ = "user_favorite_characters"
    __table_args__ = (
        UniqueConstraint("user_id", "character_id"),
        {"extend_existing": True},
    )

    user_id: UUID = Field(foreign_key="users.id")
    character_id: UUID = Field(foreign_key="lor_characters.id")


class LorCharacter(BaseModel, LorCharchter, table=True):
    __tablename__ = "lor_characters"
    __table_args__ = {"extend_existing": True}

    external_id: str = Field(String, index=True, alias="_id")
    name: str = Field(String, index=True)
    favorited_by: List["User"] = Relationship(
        back_populates="favorite_characters",
        link_model=UserFavoriteCharacter,
        sa_relationship_kwargs={"lazy": "selectin"},
    )
