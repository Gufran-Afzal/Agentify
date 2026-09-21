import os
from pydantic import BaseModel

class Settings(BaseModel):
    DATABASE_PATH: str = os.getenv("DATABASE_URL", "adaptive_content.db")

    # AI provider: "mock" (default, no API key needed) or "gemini"
    AI_PROVIDER: str = os.getenv("AI_PROVIDER", "mock")

    # Legacy API key field (kept for backward compat)
    AI_API_KEY: str = os.getenv("AI_API_KEY", "")

    # Gemini-specific settings
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    # gemini-2.5-flash-lite: use for classification, extraction, planning
    # gemini-2.5-flash: use for complex reasoning, briefs, article drafts
    GEMINI_MODEL: str = os.getenv("GEMINI_MODEL", "gemini-2.5-flash-lite")

    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    APP_URL: str = os.getenv("APP_URL", "http://localhost:8000")

    # Shopify settings
    SHOPIFY_API_KEY: str = os.getenv("SHOPIFY_API_KEY", "")
    SHOPIFY_API_SECRET: str = os.getenv("SHOPIFY_API_SECRET", "")
    SHOPIFY_SCOPES: str = os.getenv("SHOPIFY_SCOPES", "read_products,write_products,read_content,write_content")
    SHOPIFY_API_VERSION: str = os.getenv("SHOPIFY_API_VERSION", "2024-04")

    # Security & Encryption (Fernet 32 url-safe base64 key)
    # If empty, security module provides a deterministic dev fallback
    ENCRYPTION_KEY: str = os.getenv("ENCRYPTION_KEY", "")

    CORS_ORIGINS: list[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:8000",
        "http://127.0.0.1:8000",
    ]

settings = Settings()
