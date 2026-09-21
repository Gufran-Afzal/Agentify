import logging
import sqlite3
import urllib.parse
from fastapi import APIRouter, Depends, Header, HTTPException, Query, Request, Response, status
from backend.app.config import settings
from backend.app.database.connection import get_db
from backend.app.integrations.shopify.client import ShopifyClient
from backend.app.integrations.shopify.exceptions import ShopifyAuthError, ShopifyError
from backend.app.integrations.shopify.webhooks import process_webhook_payload
from backend.app.schemas.shopify import (
    ShopifyConnectTokenRequest,
    ShopifyConnectResponse,
    ShopifySyncResponse,
    ShopifyBlogResponse,
)
from backend.app.services.shopify_sync_service import shopify_sync_service
from backend.app.utils.dates import utc_now_iso
from backend.app.utils.security import (
    clean_shop_domain,
    encrypt_token,
    verify_shopify_oauth_hmac,
    verify_shopify_webhook,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/shopify", tags=["Shopify Integration"])

@router.post("/connect-token", response_model=ShopifyConnectResponse)
def connect_custom_app_token(
    payload: ShopifyConnectTokenRequest,
    db: sqlite3.Connection = Depends(get_db),
):
    """
    Connect a Shopify store directly using a Custom App Admin API access token.
    Verifies the token against Shopify API, stores the encrypted secret, and links to the store.
    """
    cleaned_domain = clean_shop_domain(payload.shop_domain)
    client = ShopifyClient(
        shop_domain=cleaned_domain,
        access_token=payload.access_token,
        api_version=payload.api_version,
    )

    try:
        shop_info = client.get_shop()
    except ShopifyAuthError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Shopify authentication failed. Please verify the Admin API access token for {cleaned_domain}.",
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unable to connect to Shopify store {cleaned_domain}: {str(e)}",
        )

    shop_name = shop_info.get("name") or cleaned_domain
    now = utc_now_iso()

    # Ensure store record exists
    existing_store = db.execute("SELECT id FROM stores WHERE id = ?", (payload.store_id,)).fetchone()
    if existing_store:
        db.execute(
            """
            UPDATE stores
            SET name = ?, domain = ?, platform = 'shopify', updated_at = ?
            WHERE id = ?
            """,
            (shop_name, cleaned_domain, now, payload.store_id)
        )
    else:
        db.execute(
            """
            INSERT INTO stores (id, name, domain, platform, created_at, updated_at)
            VALUES (?, ?, ?, 'shopify', ?, ?)
            """,
            (payload.store_id, shop_name, cleaned_domain, now, now)
        )

    encrypted_token = encrypt_token(payload.access_token)

    # Upsert store_connection
    existing_conn = db.execute(
        "SELECT id FROM store_connections WHERE store_id = ? AND provider = 'shopify'",
        (payload.store_id,)
    ).fetchone()

    if existing_conn:
        db.execute(
            """
            UPDATE store_connections
            SET shop_domain = ?, access_token_encrypted = ?, api_version = ?, status = 'connected',
                installed_at = ?, sync_status = 'idle', error_message = '', updated_at = ?
            WHERE id = ?
            """,
            (cleaned_domain, encrypted_token, payload.api_version, now, now, existing_conn["id"])
        )
    else:
        db.execute(
            """
            INSERT INTO store_connections (
                store_id, provider, shop_domain, access_token_encrypted, api_version,
                status, installed_at, sync_status, created_at, updated_at
            )
            VALUES (?, 'shopify', ?, ?, ?, 'connected', ?, 'idle', ?, ?)
            """,
            (payload.store_id, cleaned_domain, encrypted_token, payload.api_version, now, now, now)
        )

    # Pre-cache blogs
    try:
        blogs = client.get_blogs()
        shopify_sync_service._sync_blogs(db, payload.store_id, blogs)
    except Exception as e:
        logger.warning("Could not pre-fetch blogs for %s: %s", payload.store_id, e)

    db.commit()

    return ShopifyConnectResponse(
        store_id=payload.store_id,
        shop_domain=cleaned_domain,
        shop_name=shop_name,
        status="connected",
        installed_at=now,
        message=f"Successfully connected to Shopify store '{shop_name}' ({cleaned_domain})."
    )

@router.get("/auth")
def shopify_oauth_init(
    shop: str = Query(..., description="Shopify store domain"),
    store_id: str = Query("demo-store", description="Store ID in Agentify"),
):
    """
    Initiate public Shopify OAuth authorization handshake.
    """
    if not settings.SHOPIFY_API_KEY:
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="SHOPIFY_API_KEY is not configured on the server for OAuth.",
        )

    cleaned_domain = clean_shop_domain(shop)
    redirect_uri = f"{settings.APP_URL}/api/shopify/callback"
    scopes = settings.SHOPIFY_SCOPES

    auth_url = (
        f"https://{cleaned_domain}/admin/oauth/authorize?"
        f"client_id={settings.SHOPIFY_API_KEY}&"
        f"scope={scopes}&"
        f"redirect_uri={urllib.parse.quote(redirect_uri, safe='')}&"
        f"state={store_id}"
    )

    from fastapi.responses import RedirectResponse
    return RedirectResponse(url=auth_url)

@router.get("/callback")
def shopify_oauth_callback(
    request: Request,
    db: sqlite3.Connection = Depends(get_db),
):
    """
    Handle OAuth callback redirect from Shopify, exchange code for access token.
    """
    query_params = dict(request.query_params)
    shop = query_params.get("shop", "")
    code = query_params.get("code", "")
    store_id = query_params.get("state", "demo-store")

    if not shop or not code:
        raise HTTPException(status_code=400, detail="Missing shop or code in OAuth callback.")

    if settings.SHOPIFY_API_SECRET:
        if not verify_shopify_oauth_hmac(query_params):
            raise HTTPException(status_code=403, detail="Invalid Shopify OAuth HMAC signature.")

    cleaned_domain = clean_shop_domain(shop)

    # Exchange code for access token
    import httpx
    token_url = f"https://{cleaned_domain}/admin/oauth/access_token"
    payload = {
        "client_id": settings.SHOPIFY_API_KEY,
        "client_secret": settings.SHOPIFY_API_SECRET,
        "code": code,
    }

    try:
        with httpx.Client(timeout=20.0) as client:
            resp = client.post(token_url, json=payload)
            if resp.status_code != 200:
                raise HTTPException(status_code=400, detail=f"Failed to exchange token with Shopify: {resp.text}")
            token_data = resp.json()
            access_token = token_data["access_token"]
            scope = token_data.get("scope", "")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Shopify OAuth exchange error: {str(e)}")

    # Store credentials
    connect_payload = ShopifyConnectTokenRequest(
        store_id=store_id,
        shop_domain=cleaned_domain,
        access_token=access_token,
    )
    result = connect_custom_app_token(connect_payload, db)

    from fastapi.responses import RedirectResponse
    return RedirectResponse(url=f"{settings.CORS_ORIGINS[0]}/settings?connected=true&store={store_id}")

@router.post("/sync/{store_id}", response_model=ShopifySyncResponse)
def trigger_sync(
    store_id: str,
    db: sqlite3.Connection = Depends(get_db),
):
    """
    Trigger immediate synchronization of products, collections, blogs, and articles from Shopify.
    """
    try:
        res = shopify_sync_service.sync_all(db, store_id)
        return ShopifySyncResponse(**res)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Synchronization failed: {str(e)}")

@router.get("/blogs/{store_id}", response_model=list[ShopifyBlogResponse])
def get_store_blogs(
    store_id: str,
    db: sqlite3.Connection = Depends(get_db),
):
    """
    Get cached Shopify blogs for the store.
    """
    rows = db.execute(
        "SELECT id, store_id, shopify_blog_id, title, handle, commentable FROM shopify_blogs WHERE store_id = ? ORDER BY id ASC",
        (store_id,)
    ).fetchall()

    if not rows:
        # Try fetching live
        try:
            client = shopify_sync_service.get_client_for_store(db, store_id)
            blogs = client.get_blogs()
            shopify_sync_service._sync_blogs(db, store_id, blogs)
            db.commit()
            rows = db.execute(
                "SELECT id, store_id, shopify_blog_id, title, handle, commentable FROM shopify_blogs WHERE store_id = ? ORDER BY id ASC",
                (store_id,)
            ).fetchall()
        except Exception:
            pass

    return [dict(r) for r in rows]

@router.get("/status/{store_id}")
def get_store_status(
    store_id: str,
    db: sqlite3.Connection = Depends(get_db),
):
    """
    Get connection details and sync summary for a store.
    """
    store = db.execute("SELECT * FROM stores WHERE id = ?", (store_id,)).fetchone()
    if not store:
        raise HTTPException(status_code=404, detail="Store not found.")

    conn_row = db.execute(
        "SELECT * FROM store_connections WHERE store_id = ? AND provider = 'shopify' ORDER BY id DESC LIMIT 1",
        (store_id,)
    ).fetchone()

    # Get count stats
    products_count = db.execute("SELECT COUNT(*) as c FROM products WHERE store_id = ?", (store_id,)).fetchone()["c"]
    collections_count = db.execute("SELECT COUNT(*) as c FROM collections WHERE store_id = ?", (store_id,)).fetchone()["c"]
    existing_articles = db.execute("SELECT COUNT(*) as c FROM existing_content WHERE store_id = ?", (store_id,)).fetchone()["c"]
    blogs_count = db.execute("SELECT COUNT(*) as c FROM shopify_blogs WHERE store_id = ?", (store_id,)).fetchone()["c"]

    return {
        "store": dict(store),
        "connection": {
            "status": conn_row["status"] if conn_row else "disconnected",
            "shop_domain": conn_row["shop_domain"] if conn_row else "",
            "last_synced_at": conn_row["last_synced_at"] if conn_row else None,
            "sync_status": conn_row["sync_status"] if conn_row else "idle",
            "error_message": conn_row["error_message"] if conn_row else "",
        } if conn_row else None,
        "counts": {
            "products": products_count,
            "collections": collections_count,
            "existing_articles": existing_articles,
            "blogs": blogs_count,
        }
    }

@router.post("/webhooks")
async def handle_shopify_webhook(
    request: Request,
    x_shopify_topic: str | None = Header(None, alias="X-Shopify-Topic"),
    x_shopify_shop_domain: str | None = Header(None, alias="X-Shopify-Shop-Domain"),
    x_shopify_hmac_sha256: str | None = Header(None, alias="X-Shopify-Hmac-Sha256"),
    db: sqlite3.Connection = Depends(get_db),
):
    """
    Handle verified incoming webhooks from Shopify.
    """
    body_bytes = await request.body()

    if settings.SHOPIFY_API_SECRET:
        if not x_shopify_hmac_sha256 or not verify_shopify_webhook(body_bytes, x_shopify_hmac_sha256):
            logger.warning("Rejected webhook with invalid HMAC from %s", x_shopify_shop_domain)
            raise HTTPException(status_code=401, detail="Invalid Shopify webhook HMAC signature.")

    if not x_shopify_topic or not x_shopify_shop_domain:
        raise HTTPException(status_code=400, detail="Missing X-Shopify-Topic or X-Shopify-Shop-Domain headers.")

    try:
        import json
        payload = json.loads(body_bytes.decode("utf-8")) if body_bytes else {}
    except Exception:
        payload = {}

    result = process_webhook_payload(db, x_shopify_topic, x_shopify_shop_domain, payload)
    return result
