import base64
import hashlib
import hmac
import logging
import re
from urllib.parse import parse_qsl, urlencode
from cryptography.fernet import Fernet
from backend.app.config import settings

logger = logging.getLogger(__name__)

# Fallback deterministic key for local development if ENCRYPTION_KEY is not set
# In production, ENCRYPTION_KEY must be a 32-byte base64 string
_DEV_KEY = b"agentify_dev_fernet_secret_key_32b="

def _get_fernet() -> Fernet:
    key = settings.ENCRYPTION_KEY.strip()
    if key:
        try:
            return Fernet(key.encode("utf-8") if isinstance(key, str) else key)
        except Exception as e:
            logger.warning("Invalid ENCRYPTION_KEY, deriving 32-byte Fernet key: %s", e)
            derived = base64.urlsafe_b64encode(hashlib.sha256(key.encode("utf-8")).digest())
            return Fernet(derived)
    # Safe dev fallback derived from fixed seed
    derived = base64.urlsafe_b64encode(hashlib.sha256(_DEV_KEY).digest())
    return Fernet(derived)

def encrypt_token(raw_token: str) -> str:
    """Encrypt a sensitive token (such as a Shopify Admin API access token)."""
    if not raw_token:
        return ""
    f = _get_fernet()
    encrypted_bytes = f.encrypt(raw_token.encode("utf-8"))
    return encrypted_bytes.decode("utf-8")

def decrypt_token(encrypted_token: str) -> str:
    """Decrypt an encrypted token."""
    if not encrypted_token:
        return ""
    f = _get_fernet()
    decrypted_bytes = f.decrypt(encrypted_token.encode("utf-8"))
    return decrypted_bytes.decode("utf-8")

def clean_shop_domain(shop: str) -> str:
    """
    Normalize and validate shop domain.
    Strips protocol, paths, and ensures '.myshopify.com' suffix.
    E.g., 'https://my-store.myshopify.com/' -> 'my-store.myshopify.com'
          'my-store' -> 'my-store.myshopify.com'
    """
    cleaned = shop.strip().lower()
    cleaned = re.sub(r"^https?://", "", cleaned)
    cleaned = cleaned.split("/")[0]
    if not cleaned.endswith(".myshopify.com"):
        # Strip any invalid chars
        cleaned = re.sub(r"[^a-z0-9\-]", "", cleaned)
        cleaned = f"{cleaned}.myshopify.com"
    return cleaned

def verify_shopify_webhook(body_bytes: bytes, hmac_header: str, secret: str | None = None) -> bool:
    """
    Verify the HMAC-SHA256 signature of an incoming Shopify webhook payload.
    """
    signing_secret = secret or settings.SHOPIFY_API_SECRET
    if not signing_secret or not hmac_header:
        return False

    digest = hmac.new(
        signing_secret.encode("utf-8"),
        body_bytes,
        hashlib.sha256
    ).digest()
    computed_hmac = base64.b64encode(digest).decode("utf-8")
    return hmac.compare_digest(computed_hmac, hmac_header)

def verify_shopify_oauth_hmac(query_params: dict[str, str], secret: str | None = None) -> bool:
    """
    Verify the HMAC signature of OAuth callback query parameters from Shopify.
    Shopify signs all query params except 'hmac' and 'signature'.
    """
    signing_secret = secret or settings.SHOPIFY_API_SECRET
    if not signing_secret:
        return False

    received_hmac = query_params.get("hmac", "")
    if not received_hmac:
        return False

    # Filter out hmac and signature
    filtered_params = {
        k: v for k, v in query_params.items() if k not in ("hmac", "signature")
    }
    # Sort lexicographically by key and format as query string
    sorted_params = sorted(filtered_params.items())
    message = "&".join(f"{k}={v}" for k, v in sorted_params)

    computed_hmac = hmac.new(
        signing_secret.encode("utf-8"),
        message.encode("utf-8"),
        hashlib.sha256
    ).hexdigest()

    return hmac.compare_digest(computed_hmac, received_hmac)
