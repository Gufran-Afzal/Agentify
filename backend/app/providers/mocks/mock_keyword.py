"""
Mock Keyword Provider — reads from the local database.

In Phase 1, keywords come from the local database (seeded data).
In Phase 6, this is replaced by a real keyword API implementation.
"""

from __future__ import annotations

import sqlite3
import logging
from typing import Any, Optional

from backend.app.providers.interfaces.keyword import KeywordProvider

logger = logging.getLogger(__name__)


class MockKeywordProvider(KeywordProvider):
    """
    Returns keyword data from the local SQLite database.
    No external API calls required.
    """

    def __init__(self, conn: Optional[sqlite3.Connection] = None):
        self._conn = conn

    def is_available(self) -> bool:
        return True  # Always available — just reads from local DB

    def get_keywords_for_topic(
        self,
        topic: str,
        limit: int = 50,
    ) -> list[dict[str, Any]]:
        """
        Return keywords from the database that relate to the topic.
        Uses simple string matching — no embeddings needed for Phase 1.
        """
        if self._conn is None:
            logger.warning("MockKeywordProvider: no database connection provided")
            return []

        topic_lower = topic.lower()
        rows = self._conn.execute(
            "SELECT id, keyword, search_volume FROM keywords LIMIT ?",
            (limit,),
        ).fetchall()

        results = []
        for row in rows:
            kw = dict(row)
            # Simple relevance filter
            if any(word in kw["keyword"].lower() for word in topic_lower.split()):
                results.append({
                    "keyword": kw["keyword"],
                    "search_volume": kw["search_volume"],
                    "source": "local_database",
                    "id": kw["id"],
                })

        return results

    def get_search_volume(self, keywords: list[str]) -> dict[str, int]:
        """Return search volumes from the local database."""
        if self._conn is None:
            return {}

        result: dict[str, int] = {}
        for kw in keywords:
            row = self._conn.execute(
                "SELECT search_volume FROM keywords WHERE keyword = ?",
                (kw,),
            ).fetchone()
            if row:
                result[kw] = row[0]

        return result
