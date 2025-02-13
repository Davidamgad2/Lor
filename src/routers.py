from fastapi import APIRouter

from auth.router import auth_router
from characters.router import characters_router

V1_PREFIX = "/v1"
api_router = APIRouter(prefix=V1_PREFIX)

api_router.include_router(auth_router)
api_router.include_router(characters_router)
