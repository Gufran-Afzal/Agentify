import sqlite3
from fastapi import APIRouter, Depends, HTTPException, status
from backend.app.database.connection import get_db
from backend.app.schemas.content import (
    ExistingContentCreate,
    ExistingContentResponse,
    StoreProfileResponse
)
from backend.app.utils.dates import utc_now_iso

router = APIRouter(tags=["Store Content"])

@router.get("/content", response_model=list[ExistingContentResponse])
@router.get("/existing-content", response_model=list[ExistingContentResponse])
def get_existing_content(db: sqlite3.Connection = Depends(get_db)):
    rows = db.execute(
        "SELECT id, title, url, primary_keyword, created_at, updated_at FROM existing_content ORDER BY id ASC"
    ).fetchall()
    return [dict(r) for r in rows]

@router.post("/existing-content", response_model=ExistingContentResponse, status_code=status.HTTP_201_CREATED)
def create_existing_content(payload: ExistingContentCreate, db: sqlite3.Connection = Depends(get_db)):
    now = utc_now_iso()
    title = payload.title.strip()
    url = payload.url.strip()
    kw = payload.primary_keyword.strip() if payload.primary_keyword else None

    if not title or not url:
        raise HTTPException(status_code=400, detail="Title and URL cannot be empty.")

    cursor = db.execute(
        "INSERT INTO existing_content (title, url, primary_keyword, created_at, updated_at) VALUES (?, ?, ?, ?, ?)",
        (title, url, kw, now, now)
    )
    db.commit()
    return {
        "id": cursor.lastrowid,
        "title": title,
        "url": url,
        "primary_keyword": kw,
        "created_at": now,
        "updated_at": now
    }

@router.delete("/existing-content/{content_id}", status_code=status.HTTP_200_OK)
def delete_existing_content(content_id: int, db: sqlite3.Connection = Depends(get_db)):
    row = db.execute("SELECT id FROM existing_content WHERE id = ?", (content_id,)).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Content record not found.")
    db.execute("DELETE FROM existing_content WHERE id = ?", (content_id,))
    db.commit()
    return {"detail": "Existing content record deleted successfully."}

@router.get("/store-profile", response_model=StoreProfileResponse)
def get_store_profile(db: sqlite3.Connection = Depends(get_db)):
    rows = db.execute("SELECT name, category, description FROM products").fetchall()
    categories = sorted(list({r["category"] for r in rows}))
    names = [r["name"] for r in rows]
    descriptions = [r["description"] for r in rows]

    return {
        "categories": categories,
        "product_count": len(rows),
        "products": names,
        "descriptions": descriptions
    }
