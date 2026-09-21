def test_brief_lifecycle_and_constraints(client):
    run_res = client.post("/research-runs")
    run_id = run_res.json()["id"]
    client.post(f"/research-runs/{run_id}/execute")

    opps = client.get(f"/research-runs/{run_id}/opportunities").json()
    pending_opp = opps[0]
    opp_id = pending_opp["id"]

    # 1. Pending opportunity cannot create brief
    pending_brief_res = client.post(f"/opportunities/{opp_id}/create-brief")
    assert pending_brief_res.status_code == 409
    assert "Only approved opportunities" in pending_brief_res.json()["detail"]

    # 2. Reject opportunity and verify rejected opportunity cannot create brief
    client.post(f"/opportunities/{opp_id}/reject")
    rej_brief_res = client.post(f"/opportunities/{opp_id}/create-brief")
    assert rej_brief_res.status_code == 409

    # Use second opportunity and approve it
    opp2_id = opps[1]["id"]
    client.post(f"/opportunities/{opp2_id}/approve")

    # 3. Approved opportunity creates brief
    create_res = client.post(f"/opportunities/{opp2_id}/create-brief")
    assert create_res.status_code == 201
    brief = create_res.json()
    brief_id = brief["id"]
    assert brief["opportunity_id"] == opp2_id
    assert brief["status"] == "draft"
    assert len(brief["suggested_sections"]) > 0
    assert brief["search_intent"] is not None
    assert brief["target_audience"] is not None

    # 4. Duplicate brief prevented
    dup_res = client.post(f"/opportunities/{opp2_id}/create-brief")
    assert dup_res.status_code == 409
    assert "already exists" in dup_res.json()["detail"]

    # 5. Get brief
    get_res = client.get(f"/content-briefs/{brief_id}")
    assert get_res.status_code == 200
    assert get_res.json()["id"] == brief_id

    # 6. List briefs
    list_res = client.get("/content-briefs")
    assert list_res.status_code == 200
    assert any(b["id"] == brief_id for b in list_res.json())
