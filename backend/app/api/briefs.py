import sqlite3
from fastapi import APIRouter, Depends, HTTPException, status
from backend.app.database.connection import get_db
from backend.app.schemas.brief import BriefResponse
from backend.app.schemas.draft import DraftResponse
from backend.app.services.brief_service import brief_service
from backend.app.services.draft_service import draft_service

router = APIRouter(tags=["Content Briefs"])

@router.get("/content-briefs", response_model=list[BriefResponse])
def get_content_briefs(db: sqlite3.Connection = Depends(get_db)):
    return brief_service.list_briefs(db)

@router.get("/content-briefs/{brief_id}", response_model=BriefResponse)
def get_content_brief(brief_id: int, db: sqlite3.Connection = Depends(get_db)):
    brief = brief_service.get_brief(db, brief_id)
    if not brief:
        raise HTTPException(status_code=404, detail="Content brief not found.")
    return brief

@router.post("/briefs/{brief_id}/generate-draft", response_model=DraftResponse, status_code=status.HTTP_201_CREATED)
@router.post("/content-briefs/{brief_id}/generate-draft", response_model=DraftResponse, status_code=status.HTTP_201_CREATED)
def generate_content_draft(brief_id: int, db: sqlite3.Connection = Depends(get_db)):
    code, result = draft_service.generate_draft(db, brief_id)
    if code != 201:
        raise HTTPException(status_code=code, detail=result.get("detail", "Error generating draft."))
    return result
