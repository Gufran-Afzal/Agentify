class ShopifyError(Exception):
    """Base exception for Shopify API errors."""
    def __init__(self, message: str, status_code: int | None = None, response_body: dict | str | None = None):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.response_body = response_body

class ShopifyAuthError(ShopifyError):
    """Raised when authentication fails (401 Unauthorized, invalid token)."""
    pass

class ShopifyPermissionError(ShopifyError):
    """Raised when the access token lacks required scopes (403 Forbidden)."""
    pass

class ShopifyNotFoundError(ShopifyError):
    """Raised when a requested resource is not found (404 Not Found)."""
    pass

class ShopifyRateLimitError(ShopifyError):
    """Raised when Shopify rate limits requests (429 Too Many Requests)."""
    def __init__(self, message: str, retry_after: float = 2.0, response_body: dict | str | None = None):
        super().__init__(message, status_code=429, response_body=response_body)
        self.retry_after = retry_after

class ShopifyAPIError(ShopifyError):
    """Raised on Shopify 5xx errors or unexpected API response payloads."""
    pass
