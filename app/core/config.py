"""Application settings loaded from environment variables."""
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Server
    port: int = 4000

    # Mongo
    mongo_uri: str

    # Auth
    secret_key: str
    jwt_expires_hours: int = 8
    jwt_algorithm: str = "HS256"

    # Redis
    redis_url: str = "redis://127.0.0.1:6379"

    # GCP / BigQuery
    google_application_credentials: str | None = None


@lru_cache
def get_settings() -> Settings:
    return Settings() # type: ignore


settings = get_settings()
