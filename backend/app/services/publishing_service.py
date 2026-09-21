import logging
import sqlite3
from typing import Any
from backend.app.services.draft_service import draft_service
from backend.app.utils.dates import utc_now_iso
from backend.app.utils.slug import generate_unique_slug

logger = logging.getLogger(__name__)

class PublishingService:
    def publish_draft(self, conn: sqlite3.Connection, draft_id: int) -> tuple[int, dict[str, Any]]:
        """
        Publish an approved draft atomically.
        Creates or updates published_content record, assigns unique slug, and sets status = 'published'.
        """
        draft = draft_service.get_draft(conn, draft_id)
        if not draft:
            return 404, {"detail": "Content draft not found."}

        if draft["status"] != "approved":
            return 409, {
                "detail": f"Only approved drafts can be published. Current draft status is '{draft['status']}'."
            }

        # Check if already published
        existing_pub = conn.execute(
            "SELECT id, slug, status FROM published_content WHERE draft_id = ?",
            (draft_id,)
        ).fetchone()

        now = utc_now_iso()

        try:
            if existing_pub:
                pub_id = existing_pub["id"]
                slug = existing_pub["slug"]
                url = f"/blog/{slug}"
                conn.execute(
                    """
                    UPDATE published_content
                    SET title = ?, status = 'published', published_at = ?, updated_at = ?
                    WHERE id = ?
                    """,
                    (draft["title"], now, now, pub_id)
                )
            else:
                slug = generate_unique_slug(conn, draft["title"])
                url = f"/blog/{slug}"
                cursor = conn.execute(
                    """
                    INSERT INTO published_content (
                        draft_id, title, slug, url, published_at, status, created_at, updated_at
                    )
                    VALUES (?, ?, ?, ?, ?, 'published', ?, ?)
                    """,
                    (
                        draft_id,
                        draft["title"],
                        slug,
                        url,
                        now,
                        now,
                        now
                    )
                )
                pub_id = cursor.lastrowid

            conn.commit()

            return 201 if not existing_pub else 200, {
                "id": pub_id,
                "draft_id": draft_id,
                "title": draft["title"],
                "slug": slug,
                "url": url,
                "status": "published",
                "published_at": now,
                "created_at": now,
                "updated_at": now
            }
        except Exception as e:
            conn.rollback()
            logger.exception("Publishing failed: %s", e)
            return 500, {"detail": f"Publishing transaction failed: {str(e)}"}

    def unpublish_content(self, conn: sqlite3.Connection, published_id: int) -> tuple[int, dict[str, Any]]:
        row = conn.execute(
            "SELECT id, draft_id, title, slug, url, published_at, status, created_at, updated_at FROM published_content WHERE id = ?",
            (published_id,)
        ).fetchone()

        if not row:
            return 404, {"detail": "Published content record not found."}

        pub = dict(row)
        if pub["status"] == "unpublished":
            return 409, {"detail": "This content is already unpublished."}

        now = utc_now_iso()
        conn.execute(
            "UPDATE published_content SET status = 'unpublished', updated_at = ? WHERE id = ?",
            (now, published_id)
        )
        conn.commit()

        pub["status"] = "unpublished"
        pub["updated_at"] = now
        return 200, pub

    def get_published(self, conn: sqlite3.Connection, published_id: int) -> dict[str, Any] | None:
        row = conn.execute(
            "SELECT id, draft_id, title, slug, url, published_at, status, created_at, updated_at FROM published_content WHERE id = ?",
            (published_id,)
        ).fetchone()
        return dict(row) if row else None

    def list_published(self, conn: sqlite3.Connection, status: str | None = None) -> list[dict[str, Any]]:
        query = "SELECT id, draft_id, title, slug, url, published_at, status, created_at, updated_at FROM published_content"
        params: list[Any] = []
        if status:
            query += " WHERE status = ?"
            params.append(status)
        query += " ORDER BY id DESC"

        rows = conn.execute(query, params).fetchall()
        return [dict(r) for r in rows]

    def get_public_article_by_slug(self, conn: sqlite3.Connection, slug: str) -> dict[str, Any] | None:
        """
        Public endpoint retrieval. Returns article details only if status is 'published'.
        Unpublished or non-existent content returns None (which maps to 404).
        """
        row = conn.execute(
            """
            SELECT p.id, p.title, p.slug, p.published_at, p.status,
                   d.primary_keyword, d.introduction, d.body, d.conclusion
            FROM published_content p
            JOIN content_drafts d ON p.draft_id = d.id
            WHERE p.slug = ? AND p.status = 'published'
            """,
            (slug,)
        ).fetchone()

        if not row:
            return None

        return dict(row)

publishing_service = PublishingService()
