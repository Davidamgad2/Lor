import uvicorn
from fastapi import FastAPI
from settings import settings, custom_openapi
from auth.router import router as auth_router


API_V1_PREFIX = "/api/v1"

app = FastAPI(
    title=settings.APP_NAME,
)
app.openapi = custom_openapi

app.include_router(
    auth_router,
    prefix=API_V1_PREFIX,
)
if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        port=settings.APP_PORT,
        host=settings.APP_HOST,
        reload=settings.DEBUG,
    )
