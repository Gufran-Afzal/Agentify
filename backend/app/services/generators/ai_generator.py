import logging
from typing import Any
from backend.app.config import settings
from backend.app.services.generators.base import ContentGenerator
from backend.app.services.generators.mock_generator import MockContentGenerator
from backend.app.providers.implementations.provider_factory import get_llm_provider

logger = logging.getLogger(__name__)

class AIContentGenerator(ContentGenerator):
    """
    AI Content Generator that routes to the configured LLM provider
    (Gemini or Mock) via the provider factory.
    """
    def __init__(self, provider: str | None = None, api_key: str | None = None):
        self.provider = provider or settings.AI_PROVIDER
        self.api_key = api_key or settings.GEMINI_API_KEY or settings.AI_API_KEY
        self.fallback = MockContentGenerator()

    def generate(self, brief: dict[str, Any]) -> dict[str, str]:
        try:
            llm = get_llm_provider()
            draft = llm.generate_draft(brief)
            if draft and draft.get("body"):
                return draft
        except Exception as e:
            logger.warning("LLM provider generate_draft failed: %s — falling back to mock", e)

        return self.fallback.generate(brief)

def get_content_generator() -> ContentGenerator:
    """Factory function returning the configured ContentGenerator instance."""
    if settings.AI_PROVIDER.lower() == "gemini":
        return AIContentGenerator(provider="gemini", api_key=settings.GEMINI_API_KEY)
    elif settings.AI_PROVIDER.lower() != "mock" and (settings.AI_API_KEY or settings.GEMINI_API_KEY):
        return AIContentGenerator(provider=settings.AI_PROVIDER, api_key=settings.AI_API_KEY or settings.GEMINI_API_KEY)
    return MockContentGenerator()
