import uvicorn
from fastapi import FastAPI
from settings import settings

API_V1_PREFIX = "/api/v1"

app = FastAPI(
    title=settings.APP_NAME,
)

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        port=settings.APP_PORT,
        host=settings.APP_HOST,
        reload=settings.DEBUG,
    )
