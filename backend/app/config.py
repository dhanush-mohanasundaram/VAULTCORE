from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    # Required security
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # Database
    DATABASE_URL: str = "postgresql+psycopg2://postgres@localhost:5432/vaultcore"

    # CORS (comma-separated)
    CORS_ORIGINS: str = "http://localhost:5173"

    # Low-stock alert threshold
    LOW_STOCK_THRESHOLD: int = 5

    # Rate limiting
    LOGIN_LIMIT: int = 5
    LOGIN_WINDOW_SECONDS: int = 300


settings = Settings()
