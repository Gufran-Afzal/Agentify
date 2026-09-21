import json
import sqlite3
from fastapi import APIRouter, Depends, HTTPException, status
from backend.app.database.connection import get_db
from backend.app.schemas.research import ResearchRunResponse, ResearchRunExecuteResponse
from backend.app.schemas.opportunity import OpportunityResponse
from backend.app.schemas.research_action import ResearchActionResponse
from backend.app.schemas.evidence import EvidenceResponse
from backend.app.services.research_service import research_service

router = APIRouter(tags=["Research Runs"])

@router.post("/research-runs", response_model=ResearchRunResponse, status_code=status.HTTP_201_CREATED)
def create_research_run(db: sqlite3.Connection = Depends(get_db)):
    return research_service.create_run(db)

@router.get("/research-runs", response_model=list[ResearchRunResponse])
def get_research_runs(db: sqlite3.Connection = Depends(get_db)):
    return research_service.list_runs(db)

@router.get("/research-runs/{run_id}", response_model=ResearchRunResponse)
def get_research_run(run_id: int, db: sqlite3.Connection = Depends(get_db)):
    run = research_service.get_run(db, run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Research run not found.")
    return run

@router.post("/research-runs/{run_id}/execute", response_model=ResearchRunExecuteResponse)
def execute_research_run(run_id: int, db: sqlite3.Connection = Depends(get_db)):
    status_code, result = research_service.execute_run(db, run_id)
    if status_code != 200:
        raise HTTPException(status_code=status_code, detail=result.get("detail", "Error executing research run."))
    return result

@router.get("/research-runs/{run_id}/opportunities", response_model=list[OpportunityResponse])
def get_run_opportunities(run_id: int, db: sqlite3.Connection = Depends(get_db)):
    status_code, result = research_service.get_run_opportunities(db, run_id)
    if status_code != 200:
        raise HTTPException(status_code=status_code, detail=result.get("detail", "Error retrieving opportunities."))
    return result

@router.get("/research-runs/{run_id}/actions", response_model=list[ResearchActionResponse])
def get_run_actions(run_id: int, db: sqlite3.Connection = Depends(get_db)):
    run = research_service.get_run(db, run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Research run not found.")
    rows = db.execute(
        """
        SELECT id, research_run_id, action_type, arguments, result, status, created_at, completed_at
        FROM research_actions
        WHERE research_run_id = ?
        ORDER BY id ASC
        """,
        (run_id,)
    ).fetchall()
    actions = []
    for r in rows:
        d = dict(r)
        try:
            d["arguments"] = json.loads(d["arguments"]) if d.get("arguments") else {}
        except Exception:
            d["arguments"] = {}
        try:
            d["result"] = json.loads(d["result"]) if d.get("result") else {}
        except Exception:
            d["result"] = {}
        actions.append(d)
    return actions

@router.get("/research-runs/{run_id}/evidence", response_model=list[EvidenceResponse])
def get_run_evidence(run_id: int, db: sqlite3.Connection = Depends(get_db)):
    run = research_service.get_run(db, run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Research run not found.")
    rows = db.execute(
        """
        SELECT id, research_run_id, store_id, source_type, source_reference, evidence_type, data, reliability, created_at
        FROM research_evidence
        WHERE research_run_id = ?
        ORDER BY id ASC
        """,
        (run_id,)
    ).fetchall()
    items = []
    for r in rows:
        d = dict(r)
        try:
            d["data"] = json.loads(d["data"]) if d.get("data") else {}
        except Exception:
            d["data"] = {}
        items.append(d)
    return items
