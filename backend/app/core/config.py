import os
from typing import List
from pydantic import AnyHttpUrl, BeforeValidator
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing_extensions import Annotated


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_ignore_empty=True, extra="ignore"
    )

    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "DevLab SaaS Platform"

    # JWT Settings
    # In production, these must be overridden via environment variables
    JWT_SECRET: str = "your_jwt_secret_key_here"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # Database Settings
    # Defaults to a local SQLite db if postgres isn't configured, but Neon is expected
    DATABASE_URL: str = "postgresql://your_user:your_password@your_host:5432/your_db?sslmode=require"

    # Upstash Redis Settings
    UPSTASH_REDIS_REST_URL: str = ""
    UPSTASH_REDIS_REST_TOKEN: str = ""

    # CORS Settings
    BACKEND_CORS_ORIGINS: List[str] = [
        "http://localhost:3000",  # Frontend Next.js default dev port
        "http://localhost:8000",  # Backend FastAPI default dev port
        "http://127.0.0.1:3000",
        "http://127.0.0.1:8000",
    ]


settings = Settings()
