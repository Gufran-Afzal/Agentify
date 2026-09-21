def test_slug_collision_resolution(client):
    run_res = client.post("/research-runs")
    run_id = run_res.json()["id"]
    client.post(f"/research-runs/{run_id}/execute")
    opps = client.get(f"/research-runs/{run_id}/opportunities").json()

    # Create brief 1 & draft 1
    client.post(f"/opportunities/{opps[0]['id']}/approve")
    b1_id = client.post(f"/opportunities/{opps[0]['id']}/create-brief").json()["id"]
    d1_id = client.post(f"/briefs/{b1_id}/generate-draft").json()["id"]

    # Create brief 2 & draft 2
    client.post(f"/opportunities/{opps[1]['id']}/approve")
    b2_id = client.post(f"/opportunities/{opps[1]['id']}/create-brief").json()["id"]
    d2_id = client.post(f"/briefs/{b2_id}/generate-draft").json()["id"]

    # Edit draft 2 to have identical title as draft 1
    d1 = client.get(f"/content-drafts/{d1_id}").json()
    client.put(f"/content-drafts/{d2_id}", json={
        "title": d1["title"],
        "introduction": "Second article intro",
        "body": "Second article body",
        "conclusion": "Second article conclusion"
    })

    # Approve both drafts
    client.post(f"/content-drafts/{d1_id}/approve")
    client.post(f"/content-drafts/{d2_id}/approve")

    # Publish draft 1
    pub1 = client.post(f"/content-drafts/{d1_id}/publish").json()
    slug1 = pub1["slug"]

    # Publish draft 2 with identical title -> should get -2
    pub2 = client.post(f"/content-drafts/{d2_id}/publish").json()
    slug2 = pub2["slug"]

    assert slug1 != slug2
    assert slug2 == f"{slug1}-2"

    # Both articles must be accessible
    assert client.get(f"/blog/{slug1}").status_code == 200
    assert client.get(f"/blog/{slug2}").status_code == 200

def test_publishing_lifecycle(client):
    run_res = client.post("/research-runs")
    run_id = run_res.json()["id"]
    client.post(f"/research-runs/{run_id}/execute")
    opps = client.get(f"/research-runs/{run_id}/opportunities").json()

    opp1_id = opps[0]["id"]
    client.post(f"/opportunities/{opp1_id}/approve")
    brief1_id = client.post(f"/opportunities/{opp1_id}/create-brief").json()["id"]
    draft1_id = client.post(f"/briefs/{brief1_id}/generate-draft").json()["id"]

    # 1. Unapproved draft ('draft' status) cannot publish
    fail_pub = client.post(f"/content-drafts/{draft1_id}/publish")
    assert fail_pub.status_code == 409
    assert "Only approved drafts" in fail_pub.json()["detail"]

    # 2. Reject draft and verify rejected draft cannot publish
    client.post(f"/content-drafts/{draft1_id}/reject")
    rej_pub = client.post(f"/content-drafts/{draft1_id}/publish")
    assert rej_pub.status_code == 409

    # Setup draft 2 and approve it
    opp2_id = opps[1]["id"]
    client.post(f"/opportunities/{opp2_id}/approve")
    brief2_id = client.post(f"/opportunities/{opp2_id}/create-brief").json()["id"]
    draft2_id = client.post(f"/briefs/{brief2_id}/generate-draft").json()["id"]
    client.post(f"/content-drafts/{draft2_id}/approve")

    # 3. Publish approved draft
    pub_res = client.post(f"/content-drafts/{draft2_id}/publish")
    assert pub_res.status_code == 201
    pub_item = pub_res.json()
    assert pub_item["status"] == "published"
    assert pub_item["slug"] is not None
    slug = pub_item["slug"]
    pub_id = pub_item["id"]
    assert pub_item["url"] == f"/blog/{slug}"

    # 4. Public published article works
    public_res = client.get(f"/blog/{slug}")
    assert public_res.status_code == 200
    article = public_res.json()
    assert article["slug"] == slug
    assert len(article["body"]) > 0

    # 5. Unpublish works
    unpub_res = client.post(f"/published-content/{pub_id}/unpublish")
    assert unpub_res.status_code == 200
    assert unpub_res.json()["status"] == "unpublished"

    # 6. Unpublished article returns 404 from public endpoint
    assert client.get(f"/blog/{slug}").status_code == 404

    # 7. Unpublish already unpublished returns 409
    dup_unpub = client.post(f"/published-content/{pub_id}/unpublish")
    assert dup_unpub.status_code == 409
