"""
Search Provider Interface.

In Phase 1: Not used (no web search in mock mode).
In Phase 6: implemented using Gemini Search Grounding or similar.

Keeps web search optional and replaceable without touching business logic.
"""

from abc import ABC, abstractmethod
from typing import Any


class SearchProvider(ABC):
    """Abstract base class for web search providers."""

    @abstractmethod
    def is_available(self) -> bool:
        """Return True if this provider is configured and available."""
        ...

    @abstractmethod
    def search(self, query: str, num_results: int = 10) -> list[dict[str, Any]]:
        """
        Perform a web search and return structured results.

        Each result contains at minimum:
          - url: str
          - title: str
          - snippet: str
          - domain: str

        Returns an empty list if unavailable.
        """
        ...

    @abstractmethod
    def discover_competitor_domains(
        self,
        product_names: list[str],
        store_domain: Optional[str] = None,
    ) -> list[dict[str, Any]]:
        """
        Search for domains that appear for product-related queries.

        Returns list of candidate domains with discovery context.
        """
        ...


# Fix missing import
from typing import Optional  # noqa: E402
