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

    def _format_article_html(self, draft: dict[str, Any]) -> str:
        """Convert draft sections into Shopify-ready HTML."""
        import re

        intro = draft.get("introduction", "")
        body_md = draft.get("body", "")
        conclusion = draft.get("conclusion", "")

        lines = body_md.split("\n")
        html_lines: list[str] = []
        in_ul = False
        in_ol = False

        for line in lines:
            trimmed = line.strip()
            if not trimmed:
                if in_ul:
                    html_lines.append("</ul>")
                    in_ul = False
                if in_ol:
                    html_lines.append("</ol>")
                    in_ol = False
                continue

            if trimmed.startswith("### "):
                if in_ul: html_lines.append("</ul>"); in_ul = False
                if in_ol: html_lines.append("</ol>"); in_ol = False
                html_lines.append(f"<h3>{trimmed[4:]}</h3>")
            elif trimmed.startswith("## "):
                if in_ul: html_lines.append("</ul>"); in_ul = False
                if in_ol: html_lines.append("</ol>"); in_ol = False
                html_lines.append(f"<h2>{trimmed[3:]}</h2>")
            elif trimmed.startswith("# "):
                if in_ul: html_lines.append("</ul>"); in_ul = False
                if in_ol: html_lines.append("</ol>"); in_ol = False
                html_lines.append(f"<h2>{trimmed[2:]}</h2>")
            elif trimmed.startswith("- ") or trimmed.startswith("* "):
                if not in_ul:
                    html_lines.append("<ul>")
                    in_ul = True
                item_text = trimmed[2:]
                item_text = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", item_text)
                html_lines.append(f"<li>{item_text}</li>")
            elif re.match(r"^\d+\.\s+", trimmed):
                if not in_ol:
                    html_lines.append("<ol>")
                    in_ol = True
                item_text = re.sub(r"^\d+\.\s+", "", trimmed)
                item_text = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", item_text)
                html_lines.append(f"<li>{item_text}</li>")
            else:
                if in_ul: html_lines.append("</ul>"); in_ul = False
                if in_ol: html_lines.append("</ol>"); in_ol = False
                p_text = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", trimmed)
                p_text = re.sub(r"\*(.+?)\*", r"<em>\1</em>", p_text)
                html_lines.append(f"<p>{p_text}</p>")

        if in_ul: html_lines.append("</ul>")
        if in_ol: html_lines.append("</ol>")

        body_html = "\n".join(html_lines)

        return f"""<div class="agentify-article">
  <div class="article-intro" style="font-size: 1.1em; line-height: 1.6; margin-bottom: 1.5em; border-left: 3px solid #6366f1; padding-left: 1rem; color: #4b5563;">
    <p>{intro}</p>
  </div>
  <div class="article-body">
    {body_html}
  </div>
  <div class="article-conclusion" style="margin-top: 2em; padding: 1.25em; background-color: #f8fafc; border-radius: 8px;">
    <h3 style="margin-top: 0;">Key Takeaways</h3>
    <p>{conclusion}</p>
  </div>
</div>"""

    def publish_to_shopify(
        self,
        conn: sqlite3.Connection,
        draft_id: int,
        store_id: str,
        blog_id: str | None = None,
    ) -> tuple[int, dict[str, Any]]:
        """Publish an approved draft to a connected Shopify store as a DRAFT article."""
        from backend.app.services.shopify_sync_service import shopify_sync_service

        draft = draft_service.get_draft(conn, draft_id)
        if not draft:
            return 404, {"detail": "Content draft not found."}

        if draft["status"] != "approved":
            return 409, {
                "detail": f"Only approved drafts can be published to Shopify. Current draft status is '{draft['status']}'."
            }

        try:
            client = shopify_sync_service.get_client_for_store(conn, store_id)
        except Exception as e:
            return 400, {"detail": f"Shopify connection error for store '{store_id}': {str(e)}"}

        target_blog_id = blog_id
        if not target_blog_id:
            row = conn.execute(
                "SELECT shopify_blog_id FROM shopify_blogs WHERE store_id = ? ORDER BY id ASC LIMIT 1",
                (store_id,)
            ).fetchone()
            if row:
                target_blog_id = row["shopify_blog_id"]
            else:
                blogs = client.get_blogs()
                if not blogs:
                    return 400, {"detail": "No blogs found on the connected Shopify store to publish to."}
                target_blog_id = str(blogs[0]["id"])

        body_html = self._format_article_html(draft)
        primary_kw = draft.get("primary_keyword") or ""
        tags = f"{primary_kw}, Agentify" if primary_kw else "Agentify"

        article_payload = {
            "title": draft["title"],
            "body_html": body_html,
            "tags": tags,
            "summary_html": f"<p>{draft.get('introduction', '')}</p>",
            "published": False,
        }

        try:
            shopify_article = client.create_article(target_blog_id, article_payload)
            article_id = str(shopify_article["id"])
            handle = shopify_article.get("handle", "")
            shopify_blog_id = str(shopify_article.get("blog_id", target_blog_id))

            shopify_url = f"https://{client.shop_domain}/blogs/{shopify_blog_id}/{handle}" if handle else ""
            admin_url = f"https://{client.shop_domain}/admin/blogs/{shopify_blog_id}/articles/{article_id}"

            now = utc_now_iso()

            existing_pub = conn.execute(
                "SELECT id, slug FROM published_content WHERE draft_id = ?",
                (draft_id,)
            ).fetchone()

            if existing_pub:
                pub_id = existing_pub["id"]
                slug = existing_pub["slug"]
                conn.execute(
                    """
                    UPDATE published_content
                    SET title = ?, status = 'published', shopify_article_id = ?, shopify_blog_id = ?,
                        shopify_status = 'draft', shopify_url = ?, published_at = ?, updated_at = ?
                    WHERE id = ?
                    """,
                    (draft["title"], article_id, shopify_blog_id, shopify_url, now, now, pub_id)
                )
            else:
                slug = generate_unique_slug(conn, draft["title"])
                url = f"/blog/{slug}"
                cursor = conn.execute(
                    """
                    INSERT INTO published_content (
                        draft_id, title, slug, url, published_at, status, shopify_article_id,
                        shopify_blog_id, shopify_status, shopify_url, created_at, updated_at
                    )
                    VALUES (?, ?, ?, ?, ?, 'published', ?, ?, 'draft', ?, ?, ?)
                    """,
                    (
                        draft_id,
                        draft["title"],
                        slug,
                        url,
                        now,
                        article_id,
                        shopify_blog_id,
                        shopify_url,
                        now,
                        now
                    )
                )
                pub_id = cursor.lastrowid

            conn.commit()

            return 201, {
                "id": pub_id,
                "draft_id": draft_id,
                "title": draft["title"],
                "slug": slug,
                "shopify_article_id": article_id,
                "shopify_blog_id": shopify_blog_id,
                "shopify_status": "draft",
                "shopify_url": shopify_url,
                "admin_url": admin_url,
                "published_at": now,
                "message": f"Draft article successfully created in Shopify Blog #{shopify_blog_id}."
            }
        except Exception as e:
            conn.rollback()
            logger.exception("Shopify publishing failed: %s", e)
            return 500, {"detail": f"Failed to publish article to Shopify: {str(e)}"}

publishing_service = PublishingService()
