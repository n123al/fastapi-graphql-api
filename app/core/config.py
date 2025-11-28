from typing import List, Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    APP_NAME: str = "FastAPI GraphQL API"
    DEBUG: bool = False
    HOST: str = "0.0.0.0"  # nosec B104
    PORT: int = 8000
    SECRET_KEY: str = "your-secret-key-change-this"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7
    MONGODB_URL: str = "mongodb://localhost:27017"
    DATABASE_NAME: str = "fastapi_graphql_db"
    ALLOWED_HOSTS: List[str] = ["*"]
    REQUIRE_AUTHENTICATION: bool = True
    ONBOARDING_EMAIL_ENABLED: bool = False
    SET_PASSWORD_TOKEN_EXPIRE_MINUTES: int = 60
    SET_PASSWORD_URL_BASE: Optional[str] = None
    SET_PASSWORD_URL_PARAM: str = "token"
    SMTP_HOST: Optional[str] = None
    SMTP_PORT: Optional[int] = None
    SMTP_USER: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    SMTP_FROM: Optional[str] = None
    SMTP_FROM_NAME: Optional[str] = None
    SMTP_USE_TLS: Optional[bool] = None
    SMTP_USE_SSL: Optional[bool] = None
    RATE_LIMIT_PER_MINUTE: int = 60
    LOG_LEVEL: str = "INFO"
    MAX_FILE_SIZE: int = 10485760
    UPLOAD_DIR: str = "uploads"

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", case_sensitive=True, extra="ignore"
    )


settings = Settings()
