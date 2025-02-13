from helpers.models import BaseModel
from characters.schemas import LorCharchter
from sqlmodel import String, Field


class LorCharacter(BaseModel, LorCharchter, table=True):
    __tablename__ = "lor_characters"

    external_id: str = Field(String, index=True, alias="_id")
    name: str = Field(String, index=True)
