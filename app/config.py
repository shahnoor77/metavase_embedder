from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # ===============================
    # Application Database
    # ===============================
    APP_DB_HOST: str
    APP_DB_PORT: int
    APP_DB_NAME: str
    APP_DB_USER: str
    APP_DB_PASSWORD: str

    # ===============================
    # JWT
    # ===============================
    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRATION_HOURS: int = 24

    # ===============================
    # Metabase (API / Embedding)
    # ===============================
    METABASE_URL: str
    METABASE_EMAIL: str
    METABASE_PASSWORD: str
    METABASE_EMBEDDING_SECRET: str

    # ===============================
    # Metabase Metadata DB (Postgres)
    # (Not used by app, but injected by Docker)
    # ===============================
    METABASE_DB_HOST: Optional[str] = None
    METABASE_DB_PORT: Optional[int] = None
    METABASE_DB_NAME: Optional[str] = None
    METABASE_DB_USER: Optional[str] = None
    METABASE_DB_PASSWORD: Optional[str] = None

    # ===============================
    # Analytics DB (external)
    # ===============================
    ANALYTICS_DB_HOST: Optional[str] = None
    ANALYTICS_DB_PORT: Optional[int] = None
    ANALYTICS_DB_NAME: Optional[str] = None
    ANALYTICS_DB_USER: Optional[str] = None
    ANALYTICS_DB_PASSWORD: Optional[str] = None

    class Config:
        env_file = ".env"


settings = Settings()
