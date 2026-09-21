import sqlite3
from fastapi import APIRouter, Depends, HTTPException, Query, status
from backend.app.database.connection import get_db
from backend.app.schemas.opportunity import OpportunityResponse, OpportunityActionResponse
from backend.app.schemas.brief import BriefResponse
from backend.app.services.opportunity_service import opportunity_service
from backend.app.services.brief_service import brief_service

router = APIRouter(tags=["Content Opportunities"])

@router.get("/content-opportunities", response_model=list[dict])
def get_discovered_opportunities(db: sqlite3.Connection = Depends(get_db)):
    """Backwards-compatible endpoint returning dynamically calculated opportunities."""
    return opportunity_service.discover_opportunities(db)

@router.get("/opportunities", response_model=list[OpportunityResponse])
def list_opportunities(
    status: str | None = Query(None, description="Filter opportunities by status: pending, approved, rejected"),
    db: sqlite3.Connection = Depends(get_db)
):
    return opportunity_service.list_opportunities(db, status=status)

@router.get("/opportunities/{opportunity_id}", response_model=OpportunityResponse)
def get_opportunity(opportunity_id: int, db: sqlite3.Connection = Depends(get_db)):
    opp = opportunity_service.get_opportunity(db, opportunity_id)
    if not opp:
        raise HTTPException(status_code=404, detail="Opportunity not found.")
    return opp

@router.post("/opportunities/{opportunity_id}/approve", response_model=OpportunityActionResponse)
def approve_opportunity(opportunity_id: int, db: sqlite3.Connection = Depends(get_db)):
    code, msg = opportunity_service.approve_opportunity(db, opportunity_id)
    if code != 200:
        raise HTTPException(status_code=code, detail=msg)
    return {"id": opportunity_id, "status": "approved", "message": "Opportunity approved successfully."}

@router.post("/opportunities/{opportunity_id}/reject", response_model=OpportunityActionResponse)
def reject_opportunity(opportunity_id: int, db: sqlite3.Connection = Depends(get_db)):
    code, msg = opportunity_service.reject_opportunity(db, opportunity_id)
    if code != 200:
        raise HTTPException(status_code=code, detail=msg)
    return {"id": opportunity_id, "status": "rejected", "message": "Opportunity rejected successfully."}

@router.post("/opportunities/{opportunity_id}/create-brief", response_model=BriefResponse, status_code=status.HTTP_201_CREATED)
def create_brief_from_opportunity(opportunity_id: int, db: sqlite3.Connection = Depends(get_db)):
    code, result = brief_service.create_brief_from_opportunity(db, opportunity_id)
    if code != 201:
        raise HTTPException(status_code=code, detail=result.get("detail", "Error creating content brief."))
    return result
