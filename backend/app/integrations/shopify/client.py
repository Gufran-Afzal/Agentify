import logging
import time
from typing import Any
import httpx
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
)
from backend.app.config import settings
from backend.app.integrations.shopify.exceptions import (
    ShopifyError,
    ShopifyAuthError,
    ShopifyPermissionError,
    ShopifyNotFoundError,
    ShopifyRateLimitError,
    ShopifyAPIError,
)
from backend.app.utils.security import clean_shop_domain

logger = logging.getLogger(__name__)

class ShopifyClient:
    """
    Production-grade HTTP client for Shopify Admin REST API.
    Handles rate-limits (HTTP 429), token authentication, and automatic retries.
    """
    def __init__(
        self,
        shop_domain: str,
        access_token: str,
        api_version: str | None = None,
        timeout: float = 30.0,
    ):
        self.shop_domain = clean_shop_domain(shop_domain)
        self.access_token = access_token.strip()
        self.api_version = api_version or settings.SHOPIFY_API_VERSION
        self.base_url = f"https://{self.shop_domain}/admin/api/{self.api_version}"
        self.timeout = timeout
        self._masked_token = f"{self.access_token[:6]}...{self.access_token[-4:]}" if len(self.access_token) > 10 else "***"

    @property
    def _headers(self) -> dict[str, str]:
        return {
            "X-Shopify-Access-Token": self.access_token,
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": "Agentify-Content-Intelligence/1.0",
        }

    def _handle_response(self, response: httpx.Response) -> dict[str, Any]:
        call_limit = response.headers.get("X-Shopify-Shop-Api-Call-Limit", "")
        if call_limit:
            logger.debug("Shopify [%s] Call limit: %s", self.shop_domain, call_limit)

        if response.status_code in (200, 201):
            try:
                return response.json()
            except Exception:
                return {}

        if response.status_code == 401:
            raise ShopifyAuthError(
                f"Unauthorized for shop {self.shop_domain}. Check Admin API access token.",
                status_code=401,
                response_body=response.text,
            )
        elif response.status_code == 403:
            raise ShopifyPermissionError(
                f"Forbidden for shop {self.shop_domain}. Required API scopes missing.",
                status_code=403,
                response_body=response.text,
            )
        elif response.status_code == 404:
            raise ShopifyNotFoundError(
                f"Resource not found on shop {self.shop_domain}.",
                status_code=404,
                response_body=response.text,
            )
        elif response.status_code == 429:
            retry_after = float(response.headers.get("Retry-After", 2.0))
            logger.warning("Shopify rate limit hit for %s. Retry-After: %.1fs", self.shop_domain, retry_after)
            raise ShopifyRateLimitError(
                f"Rate limit exceeded for shop {self.shop_domain}.",
                retry_after=retry_after,
                response_body=response.text,
            )
        else:
            raise ShopifyAPIError(
                f"Shopify API error ({response.status_code}): {response.text[:200]}",
                status_code=response.status_code,
                response_body=response.text,
            )

    def request(
        self,
        method: str,
        path: str,
        params: dict[str, Any] | None = None,
        json_data: dict[str, Any] | None = None,
        max_retries: int = 3,
    ) -> dict[str, Any]:
        """Execute request with automatic 429 rate-limit backoff and retry."""
        url = f"{self.base_url}/{path.lstrip('/')}"
        attempts = 0

        while attempts < max_retries:
            attempts += 1
            try:
                with httpx.Client(timeout=self.timeout) as client:
                    response = client.request(
                        method=method.upper(),
                        url=url,
                        headers=self._headers,
                        params=params,
                        json=json_data,
                    )
                    return self._handle_response(response)
            except ShopifyRateLimitError as e:
                if attempts >= max_retries:
                    raise
                time.sleep(e.retry_after)
            except (httpx.NetworkError, httpx.TimeoutException) as e:
                if attempts >= max_retries:
                    raise ShopifyAPIError(f"Network error communicating with Shopify: {e}")
                time.sleep(1.0 * attempts)

        raise ShopifyAPIError(f"Request to Shopify failed after {max_retries} attempts.")

    # -------------------------------------------------------------------------
    # Shop & Health
    # -------------------------------------------------------------------------
    def get_shop(self) -> dict[str, Any]:
        """Fetch shop details to verify credentials and store info."""
        data = self.request("GET", "shop.json")
        return data.get("shop", {})

    # -------------------------------------------------------------------------
    # Blogs
    # -------------------------------------------------------------------------
    def get_blogs(self) -> list[dict[str, Any]]:
        """Fetch all blogs configured in the store."""
        data = self.request("GET", "blogs.json")
        return data.get("blogs", [])

    def get_blog(self, blog_id: int | str) -> dict[str, Any]:
        """Fetch a specific blog by ID."""
        data = self.request("GET", f"blogs/{blog_id}.json")
        return data.get("blog", {})

    # -------------------------------------------------------------------------
    # Articles
    # -------------------------------------------------------------------------
    def get_articles(self, blog_id: int | str, limit: int = 50) -> list[dict[str, Any]]:
        """Fetch articles for a specific blog."""
        data = self.request("GET", f"blogs/{blog_id}/articles.json", params={"limit": limit})
        return data.get("articles", [])

    def get_article(self, blog_id: int | str, article_id: int | str) -> dict[str, Any]:
        """Fetch single article by ID."""
        data = self.request("GET", f"blogs/{blog_id}/articles/{article_id}.json")
        return data.get("article", {})

    def create_article(self, blog_id: int | str, article_data: dict[str, Any]) -> dict[str, Any]:
        """
        Create an article on a Shopify blog.
        article_data should include: title, body_html, tags, summary_html, published (bool).
        """
        payload = {"article": article_data}
        data = self.request("POST", f"blogs/{blog_id}/articles.json", json_data=payload)
        return data.get("article", {})

    def update_article(
        self,
        blog_id: int | str,
        article_id: int | str,
        article_data: dict[str, Any],
    ) -> dict[str, Any]:
        """Update existing article on Shopify."""
        payload = {"article": article_data}
        data = self.request("PUT", f"blogs/{blog_id}/articles/{article_id}.json", json_data=payload)
        return data.get("article", {})

    def delete_article(self, blog_id: int | str, article_id: int | str) -> bool:
        """Delete an article from Shopify."""
        self.request("DELETE", f"blogs/{blog_id}/articles/{article_id}.json")
        return True

    # -------------------------------------------------------------------------
    # Products & Collections
    # -------------------------------------------------------------------------
    def get_products(self, limit: int = 50, since_id: int | None = None) -> list[dict[str, Any]]:
        """Fetch store products with pagination support."""
        params: dict[str, Any] = {"limit": limit}
        if since_id:
            params["since_id"] = since_id
        data = self.request("GET", "products.json", params=params)
        return data.get("products", [])

    def get_custom_collections(self) -> list[dict[str, Any]]:
        """Fetch custom collections."""
        data = self.request("GET", "custom_collections.json")
        return data.get("custom_collections", [])

    def get_smart_collections(self) -> list[dict[str, Any]]:
        """Fetch automated smart collections."""
        data = self.request("GET", "smart_collections.json")
        return data.get("smart_collections", [])

    def get_all_collections(self) -> list[dict[str, Any]]:
        """Fetch both custom and smart collections unified."""
        custom = self.get_custom_collections()
        smart = self.get_smart_collections()
        return custom + smart

    # -------------------------------------------------------------------------
    # Webhooks
    # -------------------------------------------------------------------------
    def register_webhook(self, topic: str, address: str) -> dict[str, Any]:
        """Register a webhook topic (e.g., 'products/create') to an address."""
        payload = {
            "webhook": {
                "topic": topic,
                "address": address,
                "format": "json",
            }
        }
        data = self.request("POST", "webhooks.json", json_data=payload)
        return data.get("webhook", {})

    def list_webhooks(self) -> list[dict[str, Any]]:
        """List registered webhooks."""
        data = self.request("GET", "webhooks.json")
        return data.get("webhooks", [])
