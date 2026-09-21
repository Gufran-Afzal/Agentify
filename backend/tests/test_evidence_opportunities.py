def test_evidence_fields_in_opportunities(client):
    run_res = client.post("/research-runs")
    run_id = run_res.json()["id"]

    exec_res = client.post(f"/research-runs/{run_id}/execute")
    assert exec_res.status_code == 200

    opps_res = client.get(f"/research-runs/{run_id}/opportunities")
    assert opps_res.status_code == 200
    opps = opps_res.json()
    assert len(opps) > 0

    first = opps[0]
    assert "why_it_matters" in first
    assert "supporting_evidence" in first
    assert "search_intent" in first
    assert "confidence_level" in first
    assert len(first["supporting_evidence"]) > 0

    # Test individual get opportunity
    opp_id = first["id"]
    single_res = client.get(f"/opportunities/{opp_id}")
    assert single_res.status_code == 200
    single = single_res.json()
    assert single["id"] == opp_id
    assert single["why_it_matters"] == first["why_it_matters"]
