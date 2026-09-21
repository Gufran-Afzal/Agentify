def test_competitors_lifecycle(client):
    # 1. Create competitor
    res = client.post("/competitors", json={
        "domain": "glowskincare.com",
        "name": "Glow Skincare",
        "category": "content_competitor",
        "discovery_reason": "Ranks for Vitamin C terms",
    })
    assert res.status_code == 201
    comp = res.json()
    comp_id = comp["id"]
    assert comp["domain"] == "glowskincare.com"

    # 2. List competitors
    list_res = client.get("/competitors")
    assert list_res.status_code == 200
    assert any(c["id"] == comp_id for c in list_res.json())

    # 3. Add page
    page_res = client.post(f"/competitors/{comp_id}/pages", json={
        "url": "https://glowskincare.com/vitamin-c-benefits",
        "title": "Top 10 Vitamin C Benefits",
        "content_summary": "Guide to using vitamin C serum daily.",
        "page_type": "blog",
    })
    assert page_res.status_code == 201
    page = page_res.json()
    assert page["competitor_id"] == comp_id

    # 4. List pages
    pages_res = client.get(f"/competitors/{comp_id}/pages")
    assert pages_res.status_code == 200
    assert len(pages_res.json()) > 0

def test_stores_lifecycle(client):
    # 1. List stores (should contain seeded demo-store)
    stores_res = client.get("/stores")
    assert stores_res.status_code == 200
    stores = stores_res.json()
    assert any(s["id"] == "demo-store" for s in stores)

    # 2. Create store
    new_store_res = client.post("/stores", json={
        "id": "my-shopify-store",
        "name": "My Shopify Store",
        "domain": "myshopify.example.com",
        "platform": "shopify",
    })
    assert new_store_res.status_code == 201
    assert new_store_res.json()["id"] == "my-shopify-store"

    # 3. Add connection
    conn_res = client.post("/stores/my-shopify-store/connections", json={
        "provider": "shopify",
        "credentials_reference": "env:SHOPIFY_API_KEY",
    })
    assert conn_res.status_code == 201
    assert conn_res.json()["provider"] == "shopify"

    # 4. List connections
    list_conn = client.get("/stores/my-shopify-store/connections")
    assert list_conn.status_code == 200
    assert len(list_conn.json()) == 1
