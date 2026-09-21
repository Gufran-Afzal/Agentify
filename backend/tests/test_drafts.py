def test_draft_lifecycle_and_editing(client):
    # Setup approved opportunity and brief
    run_res = client.post("/research-runs")
    run_id = run_res.json()["id"]
    client.post(f"/research-runs/{run_id}/execute")
    opps = client.get(f"/research-runs/{run_id}/opportunities").json()

    opp_id = opps[0]["id"]
    client.post(f"/opportunities/{opp_id}/approve")
    brief_res = client.post(f"/opportunities/{opp_id}/create-brief")
    brief_id = brief_res.json()["id"]

    # 1. Nonexistent brief returns 404
    assert client.post("/briefs/99999/generate-draft").status_code == 404

    # 2. Generate draft from valid brief
    gen_res = client.post(f"/briefs/{brief_id}/generate-draft")
    assert gen_res.status_code == 201
    draft = gen_res.json()
    draft_id = draft["id"]
    assert draft["status"] == "draft"
    assert len(draft["introduction"]) > 0
    assert len(draft["body"]) > 0
    assert len(draft["conclusion"]) > 0

    # 3. Duplicate draft prevented
    dup_res = client.post(f"/briefs/{brief_id}/generate-draft")
    assert dup_res.status_code == 409
    assert "already exists" in dup_res.json()["detail"]

    # 4. Draft editing
    edit_res = client.put(f"/content-drafts/{draft_id}", json={
        "title": "Updated Title for Draft",
        "introduction": "Updated custom introduction text.",
        "body": "## Updated Heading\n\nUpdated custom body content.",
        "conclusion": "Updated conclusion text."
    })
    assert edit_res.status_code == 200
    updated_draft = edit_res.json()
    assert updated_draft["title"] == "Updated Title for Draft"

    # 5. Approve draft
    appr_res = client.post(f"/content-drafts/{draft_id}/approve")
    assert appr_res.status_code == 200
    assert appr_res.json()["status"] == "approved"

    # 6. Approved draft cannot be edited
    bad_edit = client.put(f"/content-drafts/{draft_id}", json={
        "title": "Cannot Change Title",
        "introduction": "Intro",
        "body": "Body",
        "conclusion": "Conclusion"
    })
    assert bad_edit.status_code == 409

    # Setup another brief & draft to test rejection
    opp2_id = opps[1]["id"]
    client.post(f"/opportunities/{opp2_id}/approve")
    brief2_id = client.post(f"/opportunities/{opp2_id}/create-brief").json()["id"]
    draft2_id = client.post(f"/briefs/{brief2_id}/generate-draft").json()["id"]

    # Reject draft
    rej_res = client.post(f"/content-drafts/{draft2_id}/reject")
    assert rej_res.status_code == 200
    assert rej_res.json()["status"] == "rejected"

    # Rejected draft cannot be edited
    bad_edit2 = client.put(f"/content-drafts/{draft2_id}", json={
        "title": "Cannot Edit Rejected",
        "introduction": "Intro",
        "body": "Body",
        "conclusion": "Conclusion"
    })
    assert bad_edit2.status_code == 409
