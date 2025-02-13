from pydantic_settings import BaseSettings
from functools import cached_property
import logging.config
from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi
from typing import Dict


def custom_openapi(app: FastAPI) -> Dict:
    """
    Customizes the OpenAPI schema for the FastAPI application to include JWT Bearer authentication.
    This function modifies the OpenAPI documentation to add security schemes and requirements
    for JWT Bearer token authentication on all endpoints.
    Args:
        app (FastAPI): The FastAPI application instance to customize OpenAPI for.
    Returns:
        Dict: The modified OpenAPI schema with JWT Bearer authentication configured.
    Note:
        - If the OpenAPI schema already exists for the app, returns it without modifications
        - Adds 'BearerAuth' security scheme with JWT bearer format
        - Applies the security requirement to all endpoints in the API
    """

    if app.openapi_schema:
        return app.openapi_schema
    openapi_schema = get_openapi(
        title=app.title,
        version="1.0.0",
        routes=app.routes,
    )
    openapi_schema["components"]["securitySchemes"] = {
        "BearerAuth": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
        }
    }
    for path in openapi_schema["paths"]:
        for method in openapi_schema["paths"][path]:
            openapi_schema["paths"][path][method]["security"] = [{"BearerAuth": []}]
    app.openapi_schema = openapi_schema
    return app.openapi_schema


class Settings(BaseSettings):
    # APP CONFIG
    APP_NAME: str
    APP_HOST: str
    APP_PORT: int
    NUMBER_OF_WORKERS: int
    DEBUG: bool

    # DATABASE
    DB_USER: str
    DB_PASSWORD: str
    DB_HOST: str
    DB_NAME: str
    DB_PORT: str

    # EXTERNAL API CONFIG
    LOR_API_KEY: str
    LOR_API_BASE_URL: str

    # JWT
    secret_key: str = "your-secret-key"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_minutes: int = 1

    # REDIS
    REDIS_HOST: str
    REDIS_PORT: int
    REDIS_DB: int = 0

    @cached_property
    def db_url(self):
        return f"postgresql+asyncpg://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings: Settings = Settings()

LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "standard": {"format": "%(asctime)s [%(levelname)s] %(name)s: %(message)s"},
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "standard",
            "level": "DEBUG" if settings.DEBUG else "INFO",
        },
        "file": {
            "class": "logging.FileHandler",
            "formatter": "standard",
            "filename": "application.log",
            "mode": "a",
            "level": "DEBUG" if settings.DEBUG else "INFO",
        },
    },
    "root": {
        "handlers": ["console", "file"],
        "level": "DEBUG" if settings.DEBUG else "INFO",
    },
}
logging.config.dictConfig(LOGGING_CONFIG)
