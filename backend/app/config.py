import os
from pathlib import Path
from pydantic_settings import BaseSettings

# Locate parent directories for .env discovery
BASE_DIR = Path(__file__).resolve().parent.parent.parent

class Settings(BaseSettings):
    ENVIRONMENT: str = "development"
    PORT: int = 8000
    HOST: str = "0.0.0.0"
    DATABASE_URL: str = "sqlite+aiosqlite:///./mindtrace.db"
    
    JWT_SECRET_KEY: str = "devsecretjwtkeymindtrace2026forlocaltestingonly"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440

    class Config:
        # Check both the current directory and project root for a .env file
        env_file = (
            os.path.join(os.getcwd(), ".env"),
            os.path.join(BASE_DIR, ".env")
        )
        env_file_encoding = "utf-8"
        extra = "ignore"

settings = Settings()
