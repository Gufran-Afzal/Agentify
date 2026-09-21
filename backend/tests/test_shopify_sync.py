import sqlite3
import pytest
from unittest.mock import MagicMock, patch
from backend.app.database.connection import get_connection
from backend.app.database.schema import init_db
from backend.app.services.shopify_sync_service import shopify_sync_service
from backend.app.utils.security import encrypt_token

@pytest.fixture
def db_conn():
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    init_db(conn)
    yield conn
    conn.close()

def test_shopify_sync_all_flow(db_conn):
    store_id = "test-store"
    # Seed store and store_connection
    encrypted = encrypt_token("shpat_test_secret_123")
    db_conn.execute(
        "INSERT INTO stores (id, name, domain, platform, created_at, updated_at) VALUES (?, ?, ?, 'shopify', '', '')",
        (store_id, "Test Brand", "test-brand.myshopify.com")
    )
    db_conn.execute(
        """
        INSERT INTO store_connections (
            store_id, provider, shop_domain, access_token_encrypted, status,
            api_version, installed_at, sync_status, created_at, updated_at
        )
        VALUES (?, 'shopify', 'test-brand.myshopify.com', ?, 'connected', '2024-04', '', 'idle', '', '')
        """,
        (store_id, encrypted)
    )
    db_conn.commit()

    # Mock ShopifyClient
    mock_client = MagicMock()
    mock_client.shop_domain = "test-brand.myshopify.com"
    mock_client.get_shop.return_value = {"name": "Test Brand", "myshopify_domain": "test-brand.myshopify.com"}
    mock_client.get_blogs.return_value = [
        {"id": 101, "title": "Skincare Tips", "handle": "skincare-tips", "commentable": "no"}
    ]
    mock_client.get_all_collections.return_value = [
        {"id": 201, "title": "Serums", "handle": "serums", "body_html": "Best facial serums", "products_count": 5}
    ]
    mock_client.get_products.return_value = [
        {
            "id": 301,
            "title": "Hyaluronic Acid 2%",
            "product_type": "Serum",
            "body_html": "<p>Deep hydration serum.</p>",
            "handle": "hyaluronic-acid-2",
            "tags": "serum, hydration, skincare",
            "status": "active",
            "images": [{"src": "https://cdn.shopify.com/serum.jpg"}],
            "variants": [{"price": "24.00"}]
        }
    ]
    mock_client.get_articles.return_value = [
        {
            "id": 401,
            "title": "Why Hydration Matters",
            "handle": "why-hydration-matters",
            "summary_html": "<p>Learn why skin hydration is key.</p>",
            "tags": "hydration benefits, skincare"
        }
    ]

    with patch.object(shopify_sync_service, "get_client_for_store", return_value=mock_client):
        result = shopify_sync_service.sync_all(db_conn, store_id)

    assert result["status"] == "completed"
    assert result["blogs_synced"] == 1
    assert result["collections_synced"] == 1
    assert result["products_synced"] == 1
    assert result["articles_synced"] == 1

    # Verify database persistence
    prod = db_conn.execute("SELECT * FROM products WHERE shopify_product_id = '301'").fetchone()
    assert prod is not None
    assert prod["name"] == "Hyaluronic Acid 2%"
    assert prod["store_id"] == store_id
    assert prod["category"] == "Serum"

    coll = db_conn.execute("SELECT * FROM collections WHERE shopify_collection_id = '201'").fetchone()
    assert coll is not None
    assert coll["title"] == "Serums"

    art = db_conn.execute("SELECT * FROM existing_content WHERE shopify_article_id = '401'").fetchone()
    assert art is not None
    assert art["title"] == "Why Hydration Matters"

    blog = db_conn.execute("SELECT * FROM shopify_blogs WHERE shopify_blog_id = '101'").fetchone()
    assert blog is not None
    assert blog["title"] == "Skincare Tips"

    conn_status = db_conn.execute("SELECT sync_status, last_synced_at FROM store_connections WHERE store_id = ?", (store_id,)).fetchone()
    assert conn_status["sync_status"] == "success"
    assert conn_status["last_synced_at"] != ""
