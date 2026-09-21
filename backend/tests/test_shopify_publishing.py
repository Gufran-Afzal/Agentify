import sqlite3
import pytest
from unittest.mock import MagicMock, patch
from backend.app.database.schema import init_db
from backend.app.services.publishing_service import publishing_service
from backend.app.services.shopify_sync_service import shopify_sync_service
from backend.app.utils.security import encrypt_token

@pytest.fixture
def db_conn():
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    init_db(conn)

    # Seed brief & approved draft
    conn.execute(
        "INSERT INTO stores (id, name, domain, platform, created_at, updated_at) VALUES ('brand-1', 'Glow', 'glow.myshopify.com', 'shopify', '', '')"
    )
    enc_token = encrypt_token("shpat_valid_token")
    conn.execute(
        """
        INSERT INTO store_connections (
            store_id, provider, shop_domain, access_token_encrypted, status,
            api_version, installed_at, sync_status, created_at, updated_at
        )
        VALUES ('brand-1', 'shopify', 'glow.myshopify.com', ?, 'connected', '2024-04', '', 'idle', '', '')
        """,
        (enc_token,)
    )
    conn.execute(
        "INSERT INTO shopify_blogs (store_id, shopify_blog_id, title, handle, created_at, updated_at) VALUES ('brand-1', '777', 'Main Blog', 'news', '', '')"
    )

    # Seed research run & opportunity
    conn.execute("INSERT INTO research_runs (status, created_at) VALUES ('completed', '')")
    conn.execute(
        "INSERT INTO content_opportunities (id, research_run_id, title, reason, search_volume, confidence, status) VALUES (1, 1, 'Hydration Tips', 'Demand', 5000, 'high', 'approved')"
    )
    conn.execute(
        "INSERT INTO content_briefs (id, opportunity_id, title, objective, primary_keyword, search_volume, created_at) VALUES (1, 1, 'Hydration Tips', 'Guide', 'hydration tips', 5000, '')"
    )
    conn.execute(
        """
        INSERT INTO content_drafts (id, brief_id, title, primary_keyword, introduction, body, conclusion, status, created_at)
        VALUES (1, 1, 'Hydration Tips for Summer', 'hydration tips', 'Summer is hot.', '## Drink Water\n\nDrink lots of water daily.', 'Stay healthy.', 'approved', '')
        """
    )
    conn.commit()
    yield conn
    conn.close()

def test_publish_to_shopify_success(db_conn):
    mock_client = MagicMock()
    mock_client.shop_domain = "glow.myshopify.com"
    mock_client.create_article.return_value = {
        "id": 9991,
        "blog_id": 777,
        "title": "Hydration Tips for Summer",
        "handle": "hydration-tips-for-summer",
        "published": False,
    }

    with patch.object(shopify_sync_service, "get_client_for_store", return_value=mock_client):
        code, result = publishing_service.publish_to_shopify(
            db_conn,
            draft_id=1,
            store_id="brand-1",
            blog_id="777"
        )

    assert code == 201
    assert result["shopify_article_id"] == "9991"
    assert result["shopify_blog_id"] == "777"
    assert result["shopify_status"] == "draft"
    assert "admin/blogs/777/articles/9991" in result["admin_url"]

    # Verify call to Shopify client has published: False
    mock_client.create_article.assert_called_once()
    args, kwargs = mock_client.create_article.call_args
    assert args[0] == "777"
    assert args[1]["published"] is False
    assert "<div class=\"agentify-article\">" in args[1]["body_html"]

    # Verify recorded in published_content
    pub = db_conn.execute("SELECT * FROM published_content WHERE draft_id = 1").fetchone()
    assert pub is not None
    assert pub["shopify_article_id"] == "9991"
    assert pub["shopify_status"] == "draft"

def test_publish_unapproved_draft_fails(db_conn):
    # Set draft to 'draft' status
    db_conn.execute("UPDATE content_drafts SET status = 'draft' WHERE id = 1")
    db_conn.commit()

    code, result = publishing_service.publish_to_shopify(
        db_conn,
        draft_id=1,
        store_id="brand-1",
        blog_id="777"
    )
    assert code == 409
    assert "Only approved drafts can be published" in result["detail"]
