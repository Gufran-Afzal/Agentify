def test_research_run_lifecycle(client):
    # 1. Create run
    create_res = client.post("/research-runs")
    assert create_res.status_code == 201
    run = create_res.json()
    run_id = run["id"]
    assert run["status"] == "created"

    # 2. Get run details
    get_res = client.get(f"/research-runs/{run_id}")
    assert get_res.status_code == 200
    assert get_res.json()["status"] == "created"

    # 3. Nonexistent run check
    assert client.get("/research-runs/9999").status_code == 404
    assert client.post("/research-runs/9999/execute").status_code == 404

    # 4. Execute run
    exec_res = client.post(f"/research-runs/{run_id}/execute")
    assert exec_res.status_code == 200
    exec_data = exec_res.json()
    assert exec_data["status"] == "completed"
    assert exec_data["opportunities_count"] > 0
    assert len(exec_data["opportunities"]) > 0

    # Verify opportunities are saved in DB
    opps_res = client.get(f"/research-runs/{run_id}/opportunities")
    assert opps_res.status_code == 200
    opps = opps_res.json()
    assert len(opps) == exec_data["opportunities_count"]
    for opp in opps:
        assert opp["status"] == "pending"
        assert len(opp["evidence"]) > 0
        assert opp["confidence"] in ["high", "medium", "low"]

    # 5. Cannot execute completed run twice
    second_exec = client.post(f"/research-runs/{run_id}/execute")
    assert second_exec.status_code == 409
    assert "already been completed" in second_exec.json()["detail"]
