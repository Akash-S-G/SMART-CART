from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application Settings
    Automatically loaded from .env
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    # =====================
    # App
    # =====================

    APP_NAME: str = "SmartCart AI"

    APP_VERSION: str = "1.0.0"

    ENVIRONMENT: str = "development"

    DEBUG: bool = True

    # =====================
    # Database
    # =====================

    DATABASE_URL: str

    # Auto-create DB schema in app startup (unsafe unless DB user has CREATE privileges)
    # Enabled by default for local development to prevent "relation users does not exist" errors.
    DB_AUTO_CREATE: bool = True

    # =====================
    # JWT
    # =====================

    SECRET_KEY: str

    ALGORITHM: str = "HS256"

    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # =====================
    # Password
    # =====================

    PASSWORD_MIN_LENGTH: int = 8

    # =====================
    # CORS
    # =====================

    BACKEND_CORS_ORIGINS: list[str] = Field(default_factory=list)

    # =====================
    # Cloudinary
    # =====================
    CLOUDINARY_CLOUD_NAME: str | None = None
    CLOUDINARY_API_KEY: str | None = None
    CLOUDINARY_API_SECRET: str | None = None

    # =====================
    # Google OAuth
    # =====================
    GOOGLE_CLIENT_ID: str | None = None
    GOOGLE_CLIENT_SECRET: str | None = None
    GOOGLE_REDIRECT_URI: str | None = None


    def validate_secrets(self) -> None:
        if not self.SECRET_KEY or self.SECRET_KEY in ["secret", "change-me", "your_secret_key"]:
            if self.ENVIRONMENT == "production":
                raise RuntimeError("CRITICAL: Insecure or missing SECRET_KEY in production environment!")
        if not self.DATABASE_URL:
            raise RuntimeError("CRITICAL: Missing DATABASE_URL environment variable!")


@lru_cache
def get_settings() -> Settings:
    st = Settings()
    st.validate_secrets()
    return st


settings = get_settings()