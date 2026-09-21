def test_opportunity_approval_and_rejection(client):
    # Setup research run and opportunities
    run_res = client.post("/research-runs")
    run_id = run_res.json()["id"]
    client.post(f"/research-runs/{run_id}/execute")

    opps_res = client.get(f"/research-runs/{run_id}/opportunities")
    opps = opps_res.json()
    assert len(opps) >= 2

    opp1_id = opps[0]["id"]
    opp2_id = opps[1]["id"]

    # 1. Nonexistent opportunity
    assert client.post("/opportunities/99999/approve").status_code == 404
    assert client.post("/opportunities/99999/reject").status_code == 404

    # 2. Approve pending opportunity
    approve_res = client.post(f"/opportunities/{opp1_id}/approve")
    assert approve_res.status_code == 200
    assert approve_res.json()["status"] == "approved"

    # Cannot approve approved opportunity
    dup_approve = client.post(f"/opportunities/{opp1_id}/approve")
    assert dup_approve.status_code == 409

    # Cannot reject approved opportunity
    bad_reject = client.post(f"/opportunities/{opp1_id}/reject")
    assert bad_reject.status_code == 409

    # 3. Reject pending opportunity
    reject_res = client.post(f"/opportunities/{opp2_id}/reject")
    assert reject_res.status_code == 200
    assert reject_res.json()["status"] == "rejected"

    # Cannot reject rejected opportunity
    dup_reject = client.post(f"/opportunities/{opp2_id}/reject")
    assert dup_reject.status_code == 409

    # Cannot approve rejected opportunity
    bad_approve = client.post(f"/opportunities/{opp2_id}/approve")
    assert bad_approve.status_code == 409

    # 4. Filter opportunities by status
    approved_list = client.get("/opportunities?status=approved").json()
    assert any(o["id"] == opp1_id for o in approved_list)

    rejected_list = client.get("/opportunities?status=rejected").json()
    assert any(o["id"] == opp2_id for o in rejected_list)
