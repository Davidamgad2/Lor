import uvicorn
from fastapi import FastAPI
from settings import settings, custom_openapi
from routers import api_router
from characters.tasks import start_scheduler
from contextlib import asynccontextmanager

API_V1_PREFIX = "/api"


@asynccontextmanager
async def setup(app: FastAPI):
    start_scheduler()
    yield


app = FastAPI(
    title=settings.APP_NAME,
    description="Lord of the Rings API Service",
    version="1.0.0",
    lifespan=setup,
)

app.include_router(api_router, prefix=API_V1_PREFIX)

app.openapi = lambda: custom_openapi(app)


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        port=settings.APP_PORT,
        host=settings.APP_HOST,
        reload=settings.DEBUG,
    )
