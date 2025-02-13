from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from auth.dependencies import get_current_user
from characters.service import get_lor_character
from typing import List
from characters.models import LorCharacter

characters_router = APIRouter(prefix="/characters", tags=["characters"])


@characters_router.get("/characters", response_model=List[LorCharacter])
async def get_characters(_: str = Depends(get_current_user)):
    characters = await get_lor_character()
    return characters


@characters_router.get("/characters/{id}", response_model=LorCharacter)
async def get_character(id: str, _: str = Depends(get_current_user)):
    character = await get_lor_character(id)
    if not character:
        return JSONResponse(status_code=404, content={"message": "Character not found"})
    return character
