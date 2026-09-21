def test_complete_end_to_end_user_workflow(client):
    """
    Simulates the full autonomous user journey:
    Store Catalog -> Research Run -> Execute Scan -> Opportunities ->
    Human Approval -> Content Brief -> Generate Draft -> Human Editing ->
    Draft Approval -> Publish Article -> Public Reader View -> Unpublish -> 404 Check
    """
    # 1. Check Store Profile and Catalog
    profile_res = client.get("/store-profile")
    assert profile_res.status_code == 200
    assert profile_res.json()["product_count"] >= 3

    # 2. Trigger Research Run
    run_create = client.post("/research-runs")
    assert run_create.status_code == 201
    run_id = run_create.json()["id"]

    # 3. Execute Research Run
    run_exec = client.post(f"/research-runs/{run_id}/execute")
    assert run_exec.status_code == 200
    exec_data = run_exec.json()
    assert exec_data["status"] == "completed"
    assert exec_data["opportunities_count"] >= 2

    # 4. Review Opportunities
    opps_res = client.get(f"/research-runs/{run_id}/opportunities")
    assert opps_res.status_code == 200
    opportunities = opps_res.json()
    target_opp = opportunities[0]
    target_opp_id = target_opp["id"]
    assert target_opp["status"] == "pending"

    # 5. Human Editorial Approval of Opportunity
    appr_opp_res = client.post(f"/opportunities/{target_opp_id}/approve")
    assert appr_opp_res.status_code == 200
    assert appr_opp_res.json()["status"] == "approved"

    # 6. Generate Structured Content Brief
    brief_res = client.post(f"/opportunities/{target_opp_id}/create-brief")
    assert brief_res.status_code == 201
    brief = brief_res.json()
    brief_id = brief["id"]
    assert brief["status"] == "draft"
    assert len(brief["suggested_sections"]) >= 4

    # 7. Generate Draft from Brief
    draft_res = client.post(f"/briefs/{brief_id}/generate-draft")
    assert draft_res.status_code == 201
    draft = draft_res.json()
    draft_id = draft["id"]
    assert draft["status"] == "draft"

    # 8. Human Editorial Polish / Editing
    edit_res = client.put(f"/content-drafts/{draft_id}", json={
        "title": f"{draft['title']} (Clinically Reviewed)",
        "introduction": "This enhanced introductory guide breaks down active ingredient synergy.",
        "body": draft["body"] + "\n\n## Additional Editorial Findings\nTailored for daily morning application.",
        "conclusion": draft["conclusion"]
    })
    assert edit_res.status_code == 200
    assert "Clinically Reviewed" in edit_res.json()["title"]

    # 9. Human Sign-off / Approve Draft
    appr_draft_res = client.post(f"/content-drafts/{draft_id}/approve")
    assert appr_draft_res.status_code == 200
    assert appr_draft_res.json()["status"] == "approved"

    # 10. Publish Approved Draft
    pub_res = client.post(f"/content-drafts/{draft_id}/publish")
    assert pub_res.status_code == 201
    published = pub_res.json()
    assert published["status"] == "published"
    slug = published["slug"]
    pub_id = published["id"]

    # 11. Customer Views Public Blog Article
    blog_res = client.get(f"/blog/{slug}")
    assert blog_res.status_code == 200
    article = blog_res.json()
    assert article["title"] == f"{draft['title']} (Clinically Reviewed)"
    assert article["slug"] == slug
    assert "active ingredient synergy" in article["introduction"]

    # 12. Editor Unpublishes Article
    unpub_res = client.post(f"/published-content/{pub_id}/unpublish")
    assert unpub_res.status_code == 200
    assert unpub_res.json()["status"] == "unpublished"

    # 13. Public Endpoint Now Returns 404 for Unpublished Content
    assert client.get(f"/blog/{slug}").status_code == 404
