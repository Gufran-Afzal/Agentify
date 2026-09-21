from typing import Any
from pydantic import BaseModel, Field

class ShopifyConnectTokenRequest(BaseModel):
    store_id: str = Field(..., description="Target store identifier (e.g. 'my-store' or 'demo-store')")
    shop_domain: str = Field(..., description="Shopify store domain (e.g. 'brand.myshopify.com')")
    access_token: str = Field(..., description="Admin API Access Token (shpat_...)")
    api_version: str = Field("2024-04", description="Shopify Admin API version")

class ShopifyConnectResponse(BaseModel):
    store_id: str
    shop_domain: str
    shop_name: str
    status: str
    installed_at: str
    message: str

class ShopifySyncResponse(BaseModel):
    store_id: str
    status: str
    blogs_synced: int
    collections_synced: int
    products_synced: int
    articles_synced: int
    total_items: int
    completed_at: str

class ShopifyBlogResponse(BaseModel):
    id: int
    store_id: str
    shopify_blog_id: str
    title: str
    handle: str
    commentable: str

class QualityAuditCheck(BaseModel):
    name: str
    category: str
    passed: bool
    value: str | None = None
    message: str

class QualityAuditResponse(BaseModel):
    draft_id: int | None
    score: int
    grade: str
    word_count: int
    sentence_count: int
    reading_ease: float
    grade_level: float
    checks: list[dict[str, Any]]
    warnings: list[str]
    matched_products: list[str]

class PublishToShopifyRequest(BaseModel):
    store_id: str = Field("demo-store", description="Store to publish with")
    blog_id: str | None = Field(None, description="Optional destination blog ID on Shopify")

class PublishToShopifyResponse(BaseModel):
    id: int
    draft_id: int
    title: str
    slug: str
    shopify_article_id: str
    shopify_blog_id: str
    shopify_status: str
    shopify_url: str
    admin_url: str
    published_at: str
    message: str
