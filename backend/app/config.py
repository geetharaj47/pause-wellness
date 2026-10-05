import os
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent.parent

class Settings(BaseSettings):
    ENVIRONMENT: str = "development"
    PORT: int = 8000
    HOST: str = "0.0.0.0"
    DATABASE_URL: str = "postgresql+asyncpg://postgres@localhost:5434/pause_wellness"
    DATABASE_URL_FALLBACK: str = "sqlite+aiosqlite:///./pause.db"
    
    JWT_SECRET_KEY: str = "pause_wellness_secret_jwt_key_2026_capstone_secure_local"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440
    
    PAUSE_JOURNAL_ENCRYPTION_KEY: str = "Q4sSoV0CV1htMwJdS_jTxPU-FnuKF-Pwso9V-47TvkU="
    ENABLE_EXTERNAL_MODEL_PROVIDER: bool = False

    CORS_ORIGINS: str = "*"
    ENABLE_DEMO_ACCOUNT: bool = True
    PREFER_LIGHTWEIGHT_MODELS: bool = False

    model_config = SettingsConfigDict(
        env_file=(
            os.path.join(os.getcwd(), ".env"),
            os.path.join(BASE_DIR, ".env")
        ),
        env_file_encoding="utf-8",
        extra="ignore"
    )

settings = Settings()
