import sqlite3
from typing import Any
from backend.app.utils.text import tokenize, normalize_text

class ContentAnalysisService:
    """
    Analyzes content to detect duplicate or closely overlapping topics
    between proposed product opportunities and existing published content.
    Designed to easily plug in vector/semantic similarity models in the future.
    """

    def check_existing_content(
        self,
        query_text: str,
        existing_articles: list[dict[str, Any]] | None = None,
        conn: sqlite3.Connection | None = None
    ) -> dict[str, Any]:
        """
        Check if an article covering the query_text already exists.
        Returns:
            {
                "exists": bool,
                "matched_content_id": int | None,
                "matched_title": str | None,
                "similarity_score": float,
                "similarity_reason": str
            }
        """
        if existing_articles is None:
            if conn is None:
                raise ValueError("Either existing_articles or conn must be provided")
            rows = conn.execute("SELECT id, title, url, primary_keyword FROM existing_content").fetchall()
            existing_articles = [dict(row) for row in rows]

        query_tokens = tokenize(query_text, remove_stopwords=True)
        if not query_tokens:
            return {
                "exists": False,
                "matched_content_id": None,
                "matched_title": None,
                "similarity_score": 0.0,
                "similarity_reason": "Query text has no significant descriptive keywords."
            }

        best_match = None
        highest_overlap_ratio = 0.0

        for article in existing_articles:
            # Combine title and primary keyword for analysis
            article_text = f"{article.get('title', '')} {article.get('primary_keyword') or ''}"
            article_tokens = tokenize(article_text, remove_stopwords=True)

            if not article_tokens:
                continue

            intersection = query_tokens.intersection(article_tokens)
            overlap_count = len(intersection)

            # Jaccard-like ratio against query tokens
            overlap_ratio = overlap_count / len(query_tokens)

            if overlap_ratio > highest_overlap_ratio:
                highest_overlap_ratio = overlap_ratio
                best_match = {
                    "article": article,
                    "overlap_ratio": overlap_ratio,
                    "matched_tokens": list(intersection)
                }

        # Threshold: if at least 60% of significant query tokens overlap, or >= 2 core tokens match
        if best_match and (highest_overlap_ratio >= 0.60 or len(best_match["matched_tokens"]) >= 2):
            article = best_match["article"]
            matched_words = ", ".join(best_match["matched_tokens"])
            return {
                "exists": True,
                "matched_content_id": article.get("id"),
                "matched_title": article.get("title"),
                "similarity_score": round(highest_overlap_ratio, 2),
                "similarity_reason": (
                    f"Existing article '{article.get('title')}' covers matching topics ({matched_words})."
                )
            }

        return {
            "exists": False,
            "matched_content_id": None,
            "matched_title": None,
            "similarity_score": round(highest_overlap_ratio, 2),
            "similarity_reason": "No equivalent existing article detected."
        }

content_analysis_service = ContentAnalysisService()
