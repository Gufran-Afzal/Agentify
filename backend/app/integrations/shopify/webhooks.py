import json
import logging
import sqlite3
from typing import Any
from backend.app.utils.dates import utc_now_iso

logger = logging.getLogger(__name__)

def process_webhook_payload(
    conn: sqlite3.Connection,
    topic: str,
    shop_domain: str,
    payload: dict[str, Any],
) -> dict[str, Any]:
    """
    Process verified incoming Shopify webhook payload and update local catalog/articles.
    """
    now = utc_now_iso()
    logger.info("Processing webhook [%s] for shop: %s", topic, shop_domain)

    # Locate store_id by shop_domain
    store_conn = conn.execute(
        "SELECT store_id FROM store_connections WHERE shop_domain = ?",
        (shop_domain,)
    ).fetchone()
    store_id = store_conn["store_id"] if store_conn else "demo-store"

    if topic in ("products/create", "products/update"):
        shopify_id = str(payload.get("id", ""))
        title = payload.get("title", "")
        category = payload.get("product_type") or "General"
        description = payload.get("body_html") or ""
        handle = payload.get("handle") or ""
        tags = payload.get("tags") or ""
        status = payload.get("status") or "active"

        # Check existing
        existing = conn.execute(
            "SELECT id FROM products WHERE shopify_product_id = ? AND store_id = ?",
            (shopify_id, store_id)
        ).fetchone()

        if existing:
            conn.execute(
                """
                UPDATE products
                SET name = ?, category = ?, description = ?, handle = ?, tags = ?, status = ?, updated_at = ?
                WHERE id = ?
                """,
                (title, category, description, handle, tags, status, now, existing["id"])
            )
            action = "updated"
        else:
            conn.execute(
                """
                INSERT INTO products (name, category, description, store_id, shopify_product_id, handle, tags, status, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (title, category, description, store_id, shopify_id, handle, tags, status, now, now)
            )
            action = "created"
        conn.commit()
        return {"status": "ok", "action": action, "resource": "product", "id": shopify_id}

    elif topic == "products/delete":
        shopify_id = str(payload.get("id", ""))
        conn.execute(
            "DELETE FROM products WHERE shopify_product_id = ? AND store_id = ?",
            (shopify_id, store_id)
        )
        conn.commit()
        return {"status": "ok", "action": "deleted", "resource": "product", "id": shopify_id}

    elif topic in ("articles/create", "articles/update"):
        shopify_id = str(payload.get("id", ""))
        blog_id = str(payload.get("blog_id", ""))
        title = payload.get("title", "")
        handle = payload.get("handle", "")
        summary = payload.get("summary_html") or ""
        url = f"https://{shop_domain}/blogs/{blog_id}/{handle}" if handle else ""

        existing = conn.execute(
            "SELECT id FROM existing_content WHERE shopify_article_id = ? AND store_id = ?",
            (shopify_id, store_id)
        ).fetchone()

        if existing:
            conn.execute(
                """
                UPDATE existing_content
                SET title = ?, url = ?, handle = ?, summary = ?, shopify_blog_id = ?, updated_at = ?
                WHERE id = ?
                """,
                (title, url, handle, summary, blog_id, now, existing["id"])
            )
            action = "updated"
        else:
            conn.execute(
                """
                INSERT INTO existing_content (title, url, store_id, shopify_article_id, shopify_blog_id, handle, summary, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (title, url, store_id, shopify_id, blog_id, handle, summary, now, now)
            )
            action = "created"
        conn.commit()
        return {"status": "ok", "action": action, "resource": "article", "id": shopify_id}

    elif topic == "articles/delete":
        shopify_id = str(payload.get("id", ""))
        conn.execute(
            "DELETE FROM existing_content WHERE shopify_article_id = ? AND store_id = ?",
            (shopify_id, store_id)
        )
        conn.commit()
        return {"status": "ok", "action": "deleted", "resource": "article", "id": shopify_id}

    elif topic == "app/uninstalled":
        conn.execute(
            "UPDATE store_connections SET status = 'uninstalled', updated_at = ? WHERE shop_domain = ?",
            (now, shop_domain)
        )
        conn.commit()
        return {"status": "ok", "action": "uninstalled", "shop": shop_domain}

    return {"status": "ignored", "topic": topic}
