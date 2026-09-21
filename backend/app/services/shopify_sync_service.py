import json
import logging
import sqlite3
from typing import Any
from backend.app.integrations.shopify.client import ShopifyClient
from backend.app.integrations.shopify.exceptions import ShopifyError
from backend.app.utils.dates import utc_now_iso
from backend.app.utils.security import decrypt_token

logger = logging.getLogger(__name__)

class ShopifySyncService:
    """
    Manages synchronization of store catalog, collections, blogs, and articles
    from Shopify into Agentify's database.
    """

    def get_client_for_store(self, conn: sqlite3.Connection, store_id: str) -> ShopifyClient:
        """Helper to instantiate an authenticated ShopifyClient for a store."""
        row = conn.execute(
            """
            SELECT shop_domain, access_token_encrypted, api_version
            FROM store_connections
            WHERE store_id = ? AND status = 'connected'
            ORDER BY id DESC LIMIT 1
            """,
            (store_id,)
        ).fetchone()

        if not row:
            raise ValueError(f"No active connected Shopify connection found for store '{store_id}'.")

        token = decrypt_token(row["access_token_encrypted"])
        if not token:
            raise ValueError(f"Access token decryption failed for store '{store_id}'.")

        return ShopifyClient(
            shop_domain=row["shop_domain"],
            access_token=token,
            api_version=row["api_version"] or "2024-04",
        )

    def sync_all(self, conn: sqlite3.Connection, store_id: str) -> dict[str, Any]:
        """
        Execute a full synchronization cycle:
        1. Shop Profile
        2. Blogs
        3. Collections
        4. Products
        5. Existing Articles
        """
        now = utc_now_iso()
        logger.info("Starting Shopify sync for store: %s", store_id)

        # Log start in shopify_sync_logs
        cursor = conn.execute(
            """
            INSERT INTO shopify_sync_logs (store_id, resource_type, items_synced, status, started_at)
            VALUES (?, 'all', 0, 'running', ?)
            """,
            (store_id, now)
        )
        sync_log_id = cursor.lastrowid
        conn.commit()

        # Update connection status
        conn.execute(
            "UPDATE store_connections SET sync_status = 'syncing', updated_at = ? WHERE store_id = ?",
            (now, store_id)
        )
        conn.commit()

        try:
            client = self.get_client_for_store(conn, store_id)

            # 1. Shop profile
            shop_data = client.get_shop()
            if shop_data.get("name"):
                conn.execute(
                    "UPDATE stores SET name = ?, domain = ?, updated_at = ? WHERE id = ?",
                    (shop_data["name"], shop_data.get("myshopify_domain", ""), now, store_id)
                )

            # 2. Blogs
            blogs = client.get_blogs()
            blogs_synced = self._sync_blogs(conn, store_id, blogs)

            # 3. Collections
            collections = client.get_all_collections()
            collections_synced = self._sync_collections(conn, store_id, collections)

            # 4. Products
            products = client.get_products(limit=250)
            products_synced = self._sync_products(conn, store_id, products)

            # 5. Articles across all blogs
            articles_synced = 0
            for blog in blogs:
                b_id = blog["id"]
                articles = client.get_articles(b_id, limit=250)
                articles_synced += self._sync_articles(conn, store_id, b_id, articles)

            total_items = blogs_synced + collections_synced + products_synced + articles_synced

            completed_now = utc_now_iso()
            conn.execute(
                """
                UPDATE shopify_sync_logs
                SET status = 'completed', items_synced = ?, completed_at = ?
                WHERE id = ?
                """,
                (total_items, completed_now, sync_log_id)
            )
            conn.execute(
                """
                UPDATE store_connections
                SET sync_status = 'success', last_synced_at = ?, updated_at = ?
                WHERE store_id = ?
                """,
                (completed_now, completed_now, store_id)
            )
            conn.commit()

            result = {
                "store_id": store_id,
                "status": "completed",
                "blogs_synced": blogs_synced,
                "collections_synced": collections_synced,
                "products_synced": products_synced,
                "articles_synced": articles_synced,
                "total_items": total_items,
                "completed_at": completed_now,
            }
            logger.info("Shopify sync completed successfully for %s: %s", store_id, result)
            return result

        except Exception as e:
            conn.rollback()
            err_msg = str(e)
            logger.exception("Shopify sync failed for store %s: %s", store_id, err_msg)
            completed_now = utc_now_iso()
            conn.execute(
                """
                UPDATE shopify_sync_logs
                SET status = 'failed', error_message = ?, completed_at = ?
                WHERE id = ?
                """,
                (err_msg, completed_now, sync_log_id)
            )
            conn.execute(
                """
                UPDATE store_connections
                SET sync_status = 'failed', error_message = ?, updated_at = ?
                WHERE store_id = ?
                """,
                (err_msg, completed_now, store_id)
            )
            conn.commit()
            raise

    def _sync_blogs(self, conn: sqlite3.Connection, store_id: str, blogs: list[dict[str, Any]]) -> int:
        count = 0
        now = utc_now_iso()
        for b in blogs:
            b_id = str(b["id"])
            title = b.get("title", "")
            handle = b.get("handle", "")
            commentable = b.get("commentable", "no")

            existing = conn.execute(
                "SELECT id FROM shopify_blogs WHERE store_id = ? AND shopify_blog_id = ?",
                (store_id, b_id)
            ).fetchone()

            if existing:
                conn.execute(
                    """
                    UPDATE shopify_blogs
                    SET title = ?, handle = ?, commentable = ?, updated_at = ?
                    WHERE id = ?
                    """,
                    (title, handle, commentable, now, existing["id"])
                )
            else:
                conn.execute(
                    """
                    INSERT INTO shopify_blogs (store_id, shopify_blog_id, title, handle, commentable, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (store_id, b_id, title, handle, commentable, now, now)
                )
            count += 1
        return count

    def _sync_collections(self, conn: sqlite3.Connection, store_id: str, collections: list[dict[str, Any]]) -> int:
        count = 0
        now = utc_now_iso()
        for c in collections:
            c_id = str(c["id"])
            title = c.get("title", "")
            handle = c.get("handle", "")
            description = c.get("body_html") or ""
            products_count = c.get("products_count", 0)

            existing = conn.execute(
                "SELECT id FROM collections WHERE store_id = ? AND shopify_collection_id = ?",
                (store_id, c_id)
            ).fetchone()

            if existing:
                conn.execute(
                    """
                    UPDATE collections
                    SET title = ?, handle = ?, description = ?, products_count = ?, updated_at = ?
                    WHERE id = ?
                    """,
                    (title, handle, description, products_count, now, existing["id"])
                )
            else:
                conn.execute(
                    """
                    INSERT INTO collections (store_id, shopify_collection_id, title, handle, description, products_count, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (store_id, c_id, title, handle, description, products_count, now, now)
                )
            count += 1
        return count

    def _sync_products(self, conn: sqlite3.Connection, store_id: str, products: list[dict[str, Any]]) -> int:
        count = 0
        now = utc_now_iso()
        for p in products:
            p_id = str(p["id"])
            title = p.get("title", "")
            category = p.get("product_type") or "General"
            description = p.get("body_html") or ""
            handle = p.get("handle") or ""
            tags = p.get("tags") or ""
            status = p.get("status") or "active"

            # Image
            images = p.get("images", [])
            image_url = images[0].get("src", "") if images else ""

            # Price
            variants = p.get("variants", [])
            price = f"${variants[0].get('price', '')}" if variants else ""

            existing = conn.execute(
                "SELECT id FROM products WHERE store_id = ? AND shopify_product_id = ?",
                (store_id, p_id)
            ).fetchone()

            if existing:
                conn.execute(
                    """
                    UPDATE products
                    SET name = ?, category = ?, description = ?, handle = ?, tags = ?, status = ?,
                        image_url = ?, price_range = ?, updated_at = ?
                    WHERE id = ?
                    """,
                    (title, category, description, handle, tags, status, image_url, price, now, existing["id"])
                )
            else:
                conn.execute(
                    """
                    INSERT INTO products (
                        name, category, description, store_id, shopify_product_id,
                        handle, tags, status, image_url, price_range, created_at, updated_at
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (title, category, description, store_id, p_id, handle, tags, status, image_url, price, now, now)
                )
            count += 1
        return count

    def _sync_articles(self, conn: sqlite3.Connection, store_id: str, blog_id: int | str, articles: list[dict[str, Any]]) -> int:
        count = 0
        now = utc_now_iso()
        for a in articles:
            a_id = str(a["id"])
            title = a.get("title", "")
            handle = a.get("handle", "")
            summary = a.get("summary_html") or ""
            tags = a.get("tags") or ""

            # Extract primary keyword from tags or title
            primary_kw = tags.split(",")[0].strip() if tags else ""

            existing = conn.execute(
                "SELECT id FROM existing_content WHERE store_id = ? AND shopify_article_id = ?",
                (store_id, a_id)
            ).fetchone()

            if existing:
                conn.execute(
                    """
                    UPDATE existing_content
                    SET title = ?, handle = ?, summary = ?, shopify_blog_id = ?, primary_keyword = ?, updated_at = ?
                    WHERE id = ?
                    """,
                    (title, handle, summary, str(blog_id), primary_kw, now, existing["id"])
                )
            else:
                conn.execute(
                    """
                    INSERT INTO existing_content (
                        title, url, store_id, shopify_article_id, shopify_blog_id, handle, summary, primary_keyword, created_at, updated_at
                    )
                    VALUES (?, '', ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (title, store_id, a_id, str(blog_id), handle, summary, primary_kw, now, now)
                )
            count += 1
        return count

shopify_sync_service = ShopifySyncService()
