import sqlite3
from fastapi import APIRouter, Depends, HTTPException, status
from backend.app.database.connection import get_db
from backend.app.schemas.keyword import KeywordCreate, KeywordUpdate, KeywordResponse
from backend.app.utils.dates import utc_now_iso

router = APIRouter(tags=["Keywords"])

@router.get("/keywords", response_model=list[KeywordResponse])
def get_keywords(db: sqlite3.Connection = Depends(get_db)):
    rows = db.execute("SELECT id, keyword, search_volume, created_at, updated_at FROM keywords ORDER BY search_volume DESC").fetchall()
    return [dict(r) for r in rows]

@router.post("/keywords", response_model=KeywordResponse, status_code=status.HTTP_201_CREATED)
def create_keyword(payload: KeywordCreate, db: sqlite3.Connection = Depends(get_db)):
    now = utc_now_iso()
    kw_text = payload.keyword.strip().lower()
    if not kw_text:
        raise HTTPException(status_code=400, detail="Keyword cannot be empty.")

    # Check duplicate keyword
    existing = db.execute("SELECT id FROM keywords WHERE keyword = ?", (kw_text,)).fetchone()
    if existing:
        raise HTTPException(status_code=409, detail=f"Keyword '{kw_text}' already exists.")

    cursor = db.execute(
        "INSERT INTO keywords (keyword, search_volume, created_at, updated_at) VALUES (?, ?, ?, ?)",
        (kw_text, payload.search_volume, now, now)
    )
    db.commit()
    return {
        "id": cursor.lastrowid,
        "keyword": kw_text,
        "search_volume": payload.search_volume,
        "created_at": now,
        "updated_at": now,
        "is_demo": True
    }

@router.put("/keywords/{keyword_id}", response_model=KeywordResponse)
def update_keyword(keyword_id: int, payload: KeywordUpdate, db: sqlite3.Connection = Depends(get_db)):
    row = db.execute("SELECT id, keyword, search_volume, created_at, updated_at FROM keywords WHERE id = ?", (keyword_id,)).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Keyword not found.")

    current = dict(row)
    now = utc_now_iso()
    new_kw = payload.keyword.strip().lower() if payload.keyword is not None else current["keyword"]
    new_vol = payload.search_volume if payload.search_volume is not None else current["search_volume"]

    if not new_kw:
        raise HTTPException(status_code=400, detail="Keyword cannot be empty.")

    # Check collision if keyword string changed
    if new_kw != current["keyword"]:
        collision = db.execute("SELECT id FROM keywords WHERE keyword = ? AND id != ?", (new_kw, keyword_id)).fetchone()
        if collision:
            raise HTTPException(status_code=409, detail=f"Keyword '{new_kw}' already exists.")

    db.execute(
        "UPDATE keywords SET keyword = ?, search_volume = ?, updated_at = ? WHERE id = ?",
        (new_kw, new_vol, now, keyword_id)
    )
    db.commit()

    return {
        "id": keyword_id,
        "keyword": new_kw,
        "search_volume": new_vol,
        "created_at": current["created_at"],
        "updated_at": now,
        "is_demo": True
    }

@router.delete("/keywords/{keyword_id}", status_code=status.HTTP_200_OK)
def delete_keyword(keyword_id: int, db: sqlite3.Connection = Depends(get_db)):
    row = db.execute("SELECT id FROM keywords WHERE id = ?", (keyword_id,)).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Keyword not found.")
    db.execute("DELETE FROM keywords WHERE id = ?", (keyword_id,))
    db.commit()
    return {"detail": "Keyword deleted successfully."}
