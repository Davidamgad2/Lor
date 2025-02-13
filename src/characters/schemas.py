from pydantic import BaseModel


class LorCharchter(BaseModel):
    _id: str
    name: str
    wikiUrl: str | None
    race: str | None
    birth: str | None
    gender: str | None
    death: str | None
    hair: str | None
    height: str | None
    realm: str | None
    spouse: str | None
