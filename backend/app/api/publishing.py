import sqlite3
from fastapi import APIRouter, Depends, HTTPException, Query
from backend.app.database.connection import get_db
from backend.app.schemas.publishing import PublishedContentResponse, PublicArticleResponse
from backend.app.services.publishing_service import publishing_service

router = APIRouter(tags=["Publishing"])

@router.get("/published-content", response_model=list[PublishedContentResponse])
def get_published_content(
    status: str | None = Query(None, description="Filter by status: published, unpublished"),
    db: sqlite3.Connection = Depends(get_db)
):
    return publishing_service.list_published(db, status=status)

@router.get("/published-content/{published_id}", response_model=PublishedContentResponse)
def get_published_item(published_id: int, db: sqlite3.Connection = Depends(get_db)):
    item = publishing_service.get_published(db, published_id)
    if not item:
        raise HTTPException(status_code=404, detail="Published content record not found.")
    return item

@router.post("/published-content/{published_id}/unpublish", response_model=PublishedContentResponse)
def unpublish_content(published_id: int, db: sqlite3.Connection = Depends(get_db)):
    code, result = publishing_service.unpublish_content(db, published_id)
    if code != 200:
        raise HTTPException(status_code=code, detail=result.get("detail", "Error unpublishing content."))
    return result

@router.get("/blog/{slug}", response_model=PublicArticleResponse)
def get_public_blog_article(slug: str, db: sqlite3.Connection = Depends(get_db)):
    clean_slug = slug.strip().lower()
    article = publishing_service.get_public_article_by_slug(db, clean_slug)
    if not article:
        raise HTTPException(status_code=404, detail="Article not found or not published.")
    return article
