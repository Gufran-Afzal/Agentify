import sqlite3
from fastapi import APIRouter, Depends, HTTPException, status
from backend.app.database.connection import get_db
from backend.app.schemas.draft import DraftUpdate, DraftResponse, DraftActionResponse
from backend.app.schemas.publishing import PublishedContentResponse
from backend.app.schemas.shopify import (
    QualityAuditResponse,
    PublishToShopifyRequest,
    PublishToShopifyResponse,
)
from backend.app.services.draft_service import draft_service
from backend.app.services.publishing_service import publishing_service
from backend.app.services.quality_check_service import quality_check_service

router = APIRouter(tags=["Content Drafts"])

@router.get("/content-drafts", response_model=list[DraftResponse])
def get_content_drafts(db: sqlite3.Connection = Depends(get_db)):
    return draft_service.list_drafts(db)

@router.get("/content-drafts/{draft_id}", response_model=DraftResponse)
def get_content_draft(draft_id: int, db: sqlite3.Connection = Depends(get_db)):
    draft = draft_service.get_draft(db, draft_id)
    if not draft:
        raise HTTPException(status_code=404, detail="Content draft not found.")
    return draft

@router.put("/content-drafts/{draft_id}", response_model=DraftResponse)
def update_content_draft(
    draft_id: int,
    payload: DraftUpdate,
    db: sqlite3.Connection = Depends(get_db)
):
    title = payload.title.strip()
    intro = payload.introduction.strip()
    body = payload.body.strip()
    conclusion = payload.conclusion.strip()

    if not title or not intro or not body or not conclusion:
        raise HTTPException(status_code=400, detail="Draft fields cannot be empty.")

    code, result = draft_service.update_draft(db, draft_id, title, intro, body, conclusion)
    if code != 200:
        raise HTTPException(status_code=code, detail=result.get("detail", "Error updating draft."))
    return result

@router.post("/content-drafts/{draft_id}/approve", response_model=DraftActionResponse)
def approve_content_draft(draft_id: int, db: sqlite3.Connection = Depends(get_db)):
    code, result = draft_service.approve_draft(db, draft_id)
    if code != 200:
        raise HTTPException(status_code=code, detail=result.get("detail", "Error approving draft."))
    return result

@router.post("/content-drafts/{draft_id}/reject", response_model=DraftActionResponse)
def reject_content_draft(draft_id: int, db: sqlite3.Connection = Depends(get_db)):
    code, result = draft_service.reject_draft(db, draft_id)
    if code != 200:
        raise HTTPException(status_code=code, detail=result.get("detail", "Error rejecting draft."))
    return result

@router.post("/content-drafts/{draft_id}/publish", response_model=PublishedContentResponse, status_code=status.HTTP_201_CREATED)
def publish_content_draft(draft_id: int, db: sqlite3.Connection = Depends(get_db)):
    code, result = publishing_service.publish_draft(db, draft_id)
    if code not in (200, 201):
        raise HTTPException(status_code=code, detail=result.get("detail", "Error publishing draft."))
    return result

@router.get("/content-drafts/{draft_id}/quality-check", response_model=QualityAuditResponse)
def get_draft_quality_audit(
    draft_id: int,
    store_id: str = "demo-store",
    db: sqlite3.Connection = Depends(get_db),
):
    draft = draft_service.get_draft(db, draft_id)
    if not draft:
        raise HTTPException(status_code=404, detail="Content draft not found.")
    audit = quality_check_service.audit_draft(db, draft, store_id=store_id)
    return audit

@router.post("/content-drafts/{draft_id}/publish-to-shopify", response_model=PublishToShopifyResponse, status_code=status.HTTP_201_CREATED)
def publish_draft_to_shopify(
    draft_id: int,
    payload: PublishToShopifyRequest,
    db: sqlite3.Connection = Depends(get_db),
):
    code, result = publishing_service.publish_to_shopify(
        db,
        draft_id=draft_id,
        store_id=payload.store_id,
        blog_id=payload.blog_id,
    )
    if code not in (200, 201):
        raise HTTPException(status_code=code, detail=result.get("detail", "Failed to publish to Shopify."))
    return result

