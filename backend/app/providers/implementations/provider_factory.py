"""
Provider Factory — creates the appropriate provider implementations based on config.

Usage:
  from backend.app.providers.implementations.provider_factory import get_llm_provider

  llm = get_llm_provider()
  if llm.is_available():
      brief = llm.generate_content_brief(opportunity, evidence)
  else:
      # falls back automatically inside the provider
      brief = llm.generate_content_brief(opportunity, evidence)

The factory reads AI_PROVIDER from environment:
  AI_PROVIDER=mock    → MockLLMProvider (default, no API key needed)
  AI_PROVIDER=gemini  → GeminiLLMProvider (requires GEMINI_API_KEY)

The factory returns a singleton-per-call (not a module-level singleton)
to allow easy testing with dependency injection.
"""

from __future__ import annotations

import logging
from functools import lru_cache

from backend.app.config import settings
from backend.app.providers.interfaces.llm import LLMProvider

logger = logging.getLogger(__name__)

# Module-level cached provider instance (reset between tests via clear_cache())
_provider_cache: LLMProvider | None = None


def get_llm_provider(force_refresh: bool = False) -> LLMProvider:
    """
    Return the configured LLM provider.

    The provider is cached after first creation. Use force_refresh=True
    in tests to get a fresh instance.
    """
    global _provider_cache

    if _provider_cache is not None and not force_refresh:
        return _provider_cache

    provider_name = settings.AI_PROVIDER.lower()

    if provider_name == "gemini":
        try:
            from backend.app.providers.implementations.gemini_llm import GeminiLLMProvider
            provider = GeminiLLMProvider()
            if not provider.is_available():
                logger.warning(
                    "GeminiLLMProvider not available (missing API key or SDK). "
                    "Falling back to MockLLMProvider."
                )
                from backend.app.providers.mocks.mock_llm import MockLLMProvider
                provider = MockLLMProvider()
        except Exception as e:
            logger.error("Failed to initialize GeminiLLMProvider: %s — using mock", e)
            from backend.app.providers.mocks.mock_llm import MockLLMProvider
            provider = MockLLMProvider()
    else:
        # Default: mock provider
        if provider_name != "mock":
            logger.info(
                "Unknown AI_PROVIDER '%s' — using mock provider. "
                "Supported: mock, gemini",
                provider_name,
            )
        from backend.app.providers.mocks.mock_llm import MockLLMProvider
        provider = MockLLMProvider()

    logger.info(
        "LLM provider: %s (available=%s)",
        type(provider).__name__,
        provider.is_available(),
    )
    _provider_cache = provider
    return provider


def clear_provider_cache() -> None:
    """Clear the cached provider — used in tests to get fresh instances."""
    global _provider_cache
    _provider_cache = None
