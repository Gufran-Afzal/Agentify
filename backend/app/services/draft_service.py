import logging
import sqlite3
from typing import Any
from backend.app.services.brief_service import brief_service
from backend.app.services.generators.ai_generator import get_content_generator
from backend.app.utils.dates import utc_now_iso

logger = logging.getLogger(__name__)

class DraftService:
    def generate_draft(self, conn: sqlite3.Connection, brief_id: int) -> tuple[int, dict[str, Any]]:
        brief = brief_service.get_brief(conn, brief_id)
        if not brief:
            return 404, {"detail": "Content brief not found."}

        # Prevent duplicate drafts
        existing_draft = conn.execute(
            "SELECT id FROM content_drafts WHERE brief_id = ?",
            (brief_id,)
        ).fetchone()

        if existing_draft:
            return 409, {"detail": "A content draft already exists for this brief."}

        # Generate content using generator abstraction
        generator = get_content_generator()
        content = generator.generate(brief)

        title = content.get("title") or brief["title"]
        intro = content.get("introduction") or ""
        body = content.get("body") or ""
        conclusion = content.get("conclusion") or ""
        primary_kw = brief.get("primary_keyword")

        now = utc_now_iso()
        cursor = conn.execute(
            """
            INSERT INTO content_drafts (
                brief_id, title, primary_keyword, introduction, body,
                conclusion, status, created_at, updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, 'draft', ?, ?)
            """,
            (
                brief_id,
                title,
                primary_kw,
                intro,
                body,
                conclusion,
                now,
                now
            )
        )

        # Mark brief as completed
        conn.execute("UPDATE content_briefs SET status = 'completed', updated_at = ? WHERE id = ?", (now, brief_id))
        conn.commit()

        draft_id = cursor.lastrowid
        return 201, {
            "id": draft_id,
            "brief_id": brief_id,
            "title": title,
            "primary_keyword": primary_kw,
            "introduction": intro,
            "body": body,
            "conclusion": conclusion,
            "status": "draft",
            "created_at": now,
            "updated_at": now
        }

    def get_draft(self, conn: sqlite3.Connection, draft_id: int) -> dict[str, Any] | None:
        row = conn.execute(
            """
            SELECT id, brief_id, title, primary_keyword, introduction, body, conclusion,
                   status, created_at, updated_at
            FROM content_drafts
            WHERE id = ?
            """,
            (draft_id,)
        ).fetchone()
        return dict(row) if row else None

    def list_drafts(self, conn: sqlite3.Connection) -> list[dict[str, Any]]:
        rows = conn.execute(
            """
            SELECT id, brief_id, title, primary_keyword, introduction, body, conclusion,
                   status, created_at, updated_at
            FROM content_drafts
            ORDER BY id DESC
            """
        ).fetchall()
        return [dict(r) for r in rows]

    def update_draft(
        self,
        conn: sqlite3.Connection,
        draft_id: int,
        title: str,
        introduction: str,
        body: str,
        conclusion: str
    ) -> tuple[int, dict[str, Any]]:
        draft = self.get_draft(conn, draft_id)
        if not draft:
            return 404, {"detail": "Content draft not found."}

        if draft["status"] != "draft":
            return 409, {
                "detail": f"Only drafts with status 'draft' can be edited. Current status is '{draft['status']}'."
            }

        now = utc_now_iso()
        conn.execute(
            """
            UPDATE content_drafts
            SET title = ?, introduction = ?, body = ?, conclusion = ?, updated_at = ?
            WHERE id = ?
            """,
            (title, introduction, body, conclusion, now, draft_id)
        )
        conn.commit()

        updated = self.get_draft(conn, draft_id)
        return 200, updated or {}

    def approve_draft(self, conn: sqlite3.Connection, draft_id: int) -> tuple[int, dict[str, Any]]:
        draft = self.get_draft(conn, draft_id)
        if not draft:
            return 404, {"detail": "Content draft not found."}

        if draft["status"] != "draft":
            return 409, {
                "detail": f"Cannot approve draft. Current status is '{draft['status']}'. Only 'draft' status can be approved."
            }

        now = utc_now_iso()
        conn.execute("UPDATE content_drafts SET status = 'approved', updated_at = ? WHERE id = ?", (now, draft_id))
        conn.commit()
        return 200, {"id": draft_id, "status": "approved"}

    def reject_draft(self, conn: sqlite3.Connection, draft_id: int) -> tuple[int, dict[str, Any]]:
        draft = self.get_draft(conn, draft_id)
        if not draft:
            return 404, {"detail": "Content draft not found."}

        if draft["status"] != "draft":
            return 409, {
                "detail": f"Cannot reject draft. Current status is '{draft['status']}'. Only 'draft' status can be rejected."
            }

        now = utc_now_iso()
        conn.execute("UPDATE content_drafts SET status = 'rejected', updated_at = ? WHERE id = ?", (now, draft_id))
        conn.commit()
        return 200, {"id": draft_id, "status": "rejected"}

draft_service = DraftService()
