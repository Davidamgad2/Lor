from pydantic import BaseModel
from abc import ABC
from typing import Literal, List
from characters.schemas import LorCharchter


class FetcherOptions(BaseModel, ABC):
    resourse: str


class ResourceFilterOptions(BaseModel):
    key: str
    value: str
    equality: Literal["=", "!="]


class LorFetcherOptions(FetcherOptions):
    filters: list[ResourceFilterOptions] | None = None
    id: str | None = None


class LorResponse(BaseModel):
    docs: List[LorCharchter] | list = []
    total: int = 0
    limit: int = 0
    offset: int = 0
    page: int = 0
    pages: int = 0
