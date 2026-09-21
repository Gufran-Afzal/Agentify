import pytest
from backend.app.utils.security import (
    encrypt_token,
    decrypt_token,
    clean_shop_domain,
    verify_shopify_webhook,
    verify_shopify_oauth_hmac,
)

def test_fernet_token_encryption_decryption():
    raw_token = "shpat_1234567890abcdef"
    encrypted = encrypt_token(raw_token)
    assert encrypted != raw_token
    decrypted = decrypt_token(encrypted)
    assert decrypted == raw_token

def test_empty_token_encryption():
    assert encrypt_token("") == ""
    assert decrypt_token("") == ""

def test_clean_shop_domain():
    assert clean_shop_domain("my-store.myshopify.com") == "my-store.myshopify.com"
    assert clean_shop_domain("https://my-store.myshopify.com/") == "my-store.myshopify.com"
    assert clean_shop_domain("http://my-store.myshopify.com/admin") == "my-store.myshopify.com"
    assert clean_shop_domain("my-store") == "my-store.myshopify.com"

def test_verify_shopify_webhook():
    import base64
    import hashlib
    import hmac

    secret = "secret_key_123"
    body = b'{"id": 999, "title": "Test Product"}'

    # Compute valid HMAC
    digest = hmac.new(secret.encode("utf-8"), body, hashlib.sha256).digest()
    valid_hmac = base64.b64encode(digest).decode("utf-8")

    assert verify_shopify_webhook(body, valid_hmac, secret=secret) is True
    assert verify_shopify_webhook(body, "invalid_hmac_string", secret=secret) is False
    assert verify_shopify_webhook(b'altered body', valid_hmac, secret=secret) is False

def test_verify_shopify_oauth_hmac():
    import hashlib
    import hmac

    secret = "oauth_secret"
    params = {
        "code": "auth_code_xyz",
        "shop": "test.myshopify.com",
        "state": "demo-store",
        "timestamp": "1234567890",
    }
    # Calculate HMAC over sorted params
    message = "code=auth_code_xyz&shop=test.myshopify.com&state=demo-store&timestamp=1234567890"
    computed = hmac.new(secret.encode("utf-8"), message.encode("utf-8"), hashlib.sha256).hexdigest()

    params_with_hmac = dict(params)
    params_with_hmac["hmac"] = computed

    assert verify_shopify_oauth_hmac(params_with_hmac, secret=secret) is True
    params_with_hmac["hmac"] = "corrupted_hmac"
    assert verify_shopify_oauth_hmac(params_with_hmac, secret=secret) is False
