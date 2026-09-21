import httpx
import pytest
from unittest.mock import MagicMock, patch
from backend.app.integrations.shopify.client import ShopifyClient
from backend.app.integrations.shopify.exceptions import (
    ShopifyAuthError,
    ShopifyPermissionError,
    ShopifyNotFoundError,
    ShopifyRateLimitError,
    ShopifyAPIError,
)

def test_client_init_and_headers():
    client = ShopifyClient("my-store.myshopify.com", "shpat_12345", api_version="2024-04")
    assert client.shop_domain == "my-store.myshopify.com"
    assert client.base_url == "https://my-store.myshopify.com/admin/api/2024-04"
    assert client._headers["X-Shopify-Access-Token"] == "shpat_12345"
    assert client._headers["Content-Type"] == "application/json"

def test_client_auth_error_401():
    client = ShopifyClient("my-store.myshopify.com", "invalid_token")
    mock_resp = httpx.Response(status_code=401, text="Invalid API key or access token", request=httpx.Request("GET", "http://test"))
    
    with pytest.raises(ShopifyAuthError) as exc_info:
        client._handle_response(mock_resp)
    assert exc_info.value.status_code == 401

def test_client_permission_error_403():
    client = ShopifyClient("my-store.myshopify.com", "shpat_limited")
    mock_resp = httpx.Response(status_code=403, text="Forbidden", request=httpx.Request("GET", "http://test"))
    
    with pytest.raises(ShopifyPermissionError) as exc_info:
        client._handle_response(mock_resp)
    assert exc_info.value.status_code == 403

def test_client_not_found_404():
    client = ShopifyClient("my-store.myshopify.com", "shpat_12345")
    mock_resp = httpx.Response(status_code=404, text="Not Found", request=httpx.Request("GET", "http://test"))
    
    with pytest.raises(ShopifyNotFoundError) as exc_info:
        client._handle_response(mock_resp)
    assert exc_info.value.status_code == 404

def test_client_rate_limit_429():
    client = ShopifyClient("my-store.myshopify.com", "shpat_12345")
    mock_resp = httpx.Response(
        status_code=429,
        headers={"Retry-After": "3.5"},
        text="Exceeded 2.0 calls/second",
        request=httpx.Request("GET", "http://test")
    )
    
    with pytest.raises(ShopifyRateLimitError) as exc_info:
        client._handle_response(mock_resp)
    assert exc_info.value.retry_after == 3.5

def test_client_successful_calls():
    client = ShopifyClient("my-store.myshopify.com", "shpat_12345")

    with patch.object(client, "request") as mock_req:
        mock_req.return_value = {"shop": {"id": 100, "name": "Glow Naturals"}}
        shop = client.get_shop()
        assert shop["name"] == "Glow Naturals"
        mock_req.assert_called_with("GET", "shop.json")

    with patch.object(client, "request") as mock_req:
        mock_req.return_value = {"blogs": [{"id": 10, "title": "News"}]}
        blogs = client.get_blogs()
        assert len(blogs) == 1
        assert blogs[0]["title"] == "News"

    with patch.object(client, "request") as mock_req:
        mock_req.return_value = {"article": {"id": 501, "title": "Hydration Guide", "handle": "hydration-guide"}}
        article = client.create_article(10, {"title": "Hydration Guide", "published": False})
        assert article["id"] == 501
        mock_req.assert_called_with(
            "POST",
            "blogs/10/articles.json",
            json_data={"article": {"title": "Hydration Guide", "published": False}}
        )
