from pydantic_settings import BaseSettings
from functools import cached_property
import logging.config


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
