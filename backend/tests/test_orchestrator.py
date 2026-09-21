from backend.app.agents.orchestrator import ResearchOrchestrator
from backend.app.agents.state import ResearchStatus, ResearchBudget
from backend.app.database.connection import get_connection
from backend.app.database.schema import init_db
from backend.app.database.seed import seed_db

def test_orchestrator_run():
    conn = get_connection()
    init_db(conn)
    seed_db(conn, force_reset=True)

    # Insert a dummy research run
    cursor = conn.execute("INSERT INTO research_runs (status, created_at) VALUES ('created', '2026-01-01T00:00:00')")
    conn.commit()
    run_id = cursor.lastrowid

    orchestrator = ResearchOrchestrator()
    state = orchestrator.run(conn, run_id=run_id, store_id="demo-store")

    assert state.status == ResearchStatus.COMPLETED
    assert len(state.evidence) > 0
    assert len(state.opportunities) > 0
    assert len(state.actions_taken) > 0

    # Verify actions and evidence are written to DB
    action_rows = conn.execute(
        "SELECT id, action_type FROM research_actions WHERE research_run_id = ?",
        (run_id,),
    ).fetchall()
    assert len(action_rows) >= 3

    evidence_rows = conn.execute(
        "SELECT id, evidence_type FROM research_evidence WHERE research_run_id = ?",
        (run_id,),
    ).fetchall()
    assert len(evidence_rows) > 0

    conn.close()
