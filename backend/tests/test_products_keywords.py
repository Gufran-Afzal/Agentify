def test_list_products(client):
    response = client.get("/products")
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 3
    assert any(p["name"] == "Vitamin C Serum" for p in data)

def test_create_and_delete_product(client):
    create_res = client.post("/products", json={
        "name": "Retinol Cream",
        "category": "Anti-Aging",
        "description": "0.5% pure retinol nighttime treatment"
    })
    assert create_res.status_code == 201
    prod = create_res.json()
    prod_id = prod["id"]
    assert prod["name"] == "Retinol Cream"

    # Get single
    get_res = client.get(f"/products/{prod_id}")
    assert get_res.status_code == 200
    assert get_res.json()["category"] == "Anti-Aging"

    # Update
    update_res = client.put(f"/products/{prod_id}", json={
        "name": "Retinol Night Cream",
        "category": "Anti-Aging Skincare",
        "description": "Enhanced 0.5% pure retinol treatment"
    })
    assert update_res.status_code == 200
    assert update_res.json()["name"] == "Retinol Night Cream"

    # Delete
    del_res = client.delete(f"/products/{prod_id}")
    assert del_res.status_code == 200
    assert client.get(f"/products/{prod_id}").status_code == 404

def test_list_and_create_keywords(client):
    response = client.get("/keywords")
    assert response.status_code == 200
    kws = response.json()
    assert len(kws) >= 5

    # Create keyword
    create_res = client.post("/keywords", json={
        "keyword": "best retinol for beginners",
        "search_volume": 4500
    })
    assert create_res.status_code == 201
    kw_id = create_res.json()["id"]

    # Duplicate keyword returns 409
    dup_res = client.post("/keywords", json={
        "keyword": "best retinol for beginners",
        "search_volume": 5000
    })
    assert dup_res.status_code == 409

    # Delete
    del_res = client.delete(f"/keywords/{kw_id}")
    assert del_res.status_code == 200
