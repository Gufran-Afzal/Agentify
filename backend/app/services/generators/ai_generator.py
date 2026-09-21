import logging
from backend.app.config import settings
from backend.app.services.generators.base import ContentGenerator
from backend.app.services.generators.mock_generator import MockContentGenerator

logger = logging.getLogger(__name__)

class AIContentGenerator(ContentGenerator):
    """
    Extensible AI Content Generator designed for LLM APIs (OpenAI, Anthropic, Gemini, local models).
    Falls back gracefully to MockContentGenerator if no API key is configured.
    """
    def __init__(self, provider: str | None = None, api_key: str | None = None):
        self.provider = provider or settings.AI_PROVIDER
        self.api_key = api_key or settings.AI_API_KEY
        self.fallback = MockContentGenerator()

    def generate(self, brief: dict) -> dict[str, str]:
        if not self.api_key or self.provider.lower() == "mock":
            logger.info("Using deterministic generator (AI provider '%s' or no API key configured)", self.provider)
            return self.fallback.generate(brief)

        # Extensible provider hook:
        # if self.provider == "openai": ...
        # elif self.provider == "anthropic": ...
        # elif self.provider == "gemini": ...
        logger.warning("Provider '%s' configured but external network call not enabled; using mock fallback", self.provider)
        return self.fallback.generate(brief)

def get_content_generator() -> ContentGenerator:
    """Factory function returning the configured ContentGenerator instance."""
    if settings.AI_PROVIDER.lower() != "mock" and settings.AI_API_KEY:
        return AIContentGenerator(provider=settings.AI_PROVIDER, api_key=settings.AI_API_KEY)
    return MockContentGenerator()
