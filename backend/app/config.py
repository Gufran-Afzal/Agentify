import os
from pydantic import BaseModel

class Settings(BaseModel):
    DATABASE_PATH: str = os.getenv("DATABASE_URL", "adaptive_content.db")
    AI_PROVIDER: str = os.getenv("AI_PROVIDER", "mock")
    AI_API_KEY: str = os.getenv("AI_API_KEY", "")
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    CORS_ORIGINS: list[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:8000",
        "http://127.0.0.1:8000",
    ]

settings = Settings()
