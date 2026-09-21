def test_evidence_and_actions_endpoints(client):
    run_res = client.post("/research-runs")
    run_id = run_res.json()["id"]

    exec_res = client.post(f"/research-runs/{run_id}/execute")
    assert exec_res.status_code == 200

    # Test actions endpoint
    actions_res = client.get(f"/research-runs/{run_id}/actions")
    assert actions_res.status_code == 200
    actions = actions_res.json()
    assert len(actions) > 0
    assert any(a["action_type"] == "ANALYZE_STORE" for a in actions)

    # Test evidence endpoint
    evidence_res = client.get(f"/research-runs/{run_id}/evidence")
    assert evidence_res.status_code == 200
    evidence = evidence_res.json()
    assert len(evidence) > 0
    assert any(e["evidence_type"] == "store_product" for e in evidence)
    assert any(e["evidence_type"] == "keyword" for e in evidence)
