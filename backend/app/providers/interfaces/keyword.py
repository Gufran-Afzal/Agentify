"""
Keyword Provider Interface.

In Phase 1: implemented by MockKeywordProvider (reads from DB).
In Phase 6: implemented by a real keyword API (DataForSEO, Semrush, etc.).
"""

from abc import ABC, abstractmethod
from typing import Any


class KeywordProvider(ABC):
    """Abstract base class for all keyword data providers."""

    @abstractmethod
    def is_available(self) -> bool:
        """Return True if this provider is configured and available."""
        ...

    @abstractmethod
    def get_keywords_for_topic(
        self,
        topic: str,
        limit: int = 50,
    ) -> list[dict[str, Any]]:
        """
        Return keyword suggestions for a topic.

        Each dict contains at minimum:
          - keyword: str
          - search_volume: int (estimated monthly searches)
          - source: str (where the data came from)

        Returns an empty list if unavailable.
        """
        ...

    @abstractmethod
    def get_search_volume(self, keywords: list[str]) -> dict[str, int]:
        """
        Return estimated search volumes for a list of keywords.

        Returns {keyword: volume} dict.
        Returns empty dict if unavailable.
        """
        ...
