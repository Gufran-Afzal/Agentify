import pytest
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)

def test_shopify_connect_token_api():
    mock_shop = {"name": "Radiant Beauty", "myshopify_domain": "radiant-beauty.myshopify.com"}
    with patch("backend.app.api.shopify.ShopifyClient.get_shop", return_value=mock_shop), \
         patch("backend.app.api.shopify.ShopifyClient.get_blogs", return_value=[{"id": 1, "title": "News", "handle": "news"}]):
        res = client.post(
            "/shopify/connect-token",
            json={
                "store_id": "radiant-store",
                "shop_domain": "radiant-beauty.myshopify.com",
                "access_token": "shpat_mock_secret_token_123"
            }
        )
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "connected"
    assert data["shop_name"] == "Radiant Beauty"
    assert data["shop_domain"] == "radiant-beauty.myshopify.com"

def test_shopify_store_status_api():
    res = client.get("/shopify/status/radiant-store")
    assert res.status_code == 200
    data = res.json()
    assert "connection" in data
    assert data["connection"]["status"] == "connected"
    assert "counts" in data
    assert "products" in data["counts"]

def test_draft_quality_check_api():
    # Fetch drafts
    drafts_res = client.get("/content-drafts")
    assert drafts_res.status_code == 200
    drafts = drafts_res.json()
    if drafts:
        draft_id = drafts[0]["id"]
        res = client.get(f"/content-drafts/{draft_id}/quality-check")
        assert res.status_code == 200
        data = res.json()
        assert "score" in data
        assert "checks" in data
        assert "reading_ease" in data

def test_publish_to_shopify_api():
    drafts_res = client.get("/content-drafts")
    drafts = drafts_res.json()
    if drafts:
        draft_id = drafts[0]["id"]
        # Ensure it's approved
        client.post(f"/content-drafts/{draft_id}/approve")

        mock_article = {
            "id": 8881,
            "blog_id": 1,
            "title": "Title",
            "handle": "title",
            "published": False,
        }

        with patch("backend.app.integrations.shopify.client.ShopifyClient.create_article", return_value=mock_article):
            res = client.post(
                f"/content-drafts/{draft_id}/publish-to-shopify",
                json={"store_id": "radiant-store"}
            )
            assert res.status_code in (200, 201)
            data = res.json()
            assert data["shopify_article_id"] == "8881"
            assert data["shopify_status"] == "draft"
