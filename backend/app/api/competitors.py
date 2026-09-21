import sqlite3
from fastapi import APIRouter, Depends, HTTPException, status
from backend.app.database.connection import get_db
from backend.app.schemas.competitor import (
    CompetitorCreate,
    CompetitorResponse,
    CompetitorPageCreate,
    CompetitorPageResponse,
)
from backend.app.utils.dates import utc_now_iso

router = APIRouter(prefix="/competitors", tags=["Competitors"])

@router.post("", response_model=CompetitorResponse, status_code=status.HTTP_201_CREATED)
def create_competitor(payload: CompetitorCreate, db: sqlite3.Connection = Depends(get_db)):
    now = utc_now_iso()
    cursor = db.execute(
        """
        INSERT INTO competitors (store_id, domain, name, category, status, discovery_reason, created_at, updated_at)
        VALUES ('demo-store', ?, ?, ?, 'discovered', ?, ?, ?)
        """,
        (
            payload.domain,
            payload.name or payload.domain,
            payload.category or "content_competitor",
            payload.discovery_reason or "",
            now,
            now,
        ),
    )
    db.commit()
    comp_id = cursor.lastrowid
    row = db.execute("SELECT * FROM competitors WHERE id = ?", (comp_id,)).fetchone()
    return dict(row)

@router.get("", response_model=list[CompetitorResponse])
def list_competitors(db: sqlite3.Connection = Depends(get_db)):
    rows = db.execute("SELECT * FROM competitors ORDER BY id DESC").fetchall()
    return [dict(r) for r in rows]

@router.get("/{competitor_id}", response_model=CompetitorResponse)
def get_competitor(competitor_id: int, db: sqlite3.Connection = Depends(get_db)):
    row = db.execute("SELECT * FROM competitors WHERE id = ?", (competitor_id,)).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Competitor not found.")
    return dict(row)

@router.post("/{competitor_id}/pages", response_model=CompetitorPageResponse, status_code=status.HTTP_201_CREATED)
def add_competitor_page(
    competitor_id: int,
    payload: CompetitorPageCreate,
    db: sqlite3.Connection = Depends(get_db),
):
    comp = db.execute("SELECT id FROM competitors WHERE id = ?", (competitor_id,)).fetchone()
    if not comp:
        raise HTTPException(status_code=404, detail="Competitor not found.")

    now = utc_now_iso()
    cursor = db.execute(
        """
        INSERT INTO competitor_pages (competitor_id, url, title, content_summary, page_type, created_at)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            competitor_id,
            payload.url,
            payload.title or "",
            payload.content_summary or "",
            payload.page_type or "blog",
            now,
        ),
    )
    db.commit()
    row = db.execute("SELECT * FROM competitor_pages WHERE id = ?", (cursor.lastrowid,)).fetchone()
    return dict(row)

@router.get("/{competitor_id}/pages", response_model=list[CompetitorPageResponse])
def list_competitor_pages(competitor_id: int, db: sqlite3.Connection = Depends(get_db)):
    comp = db.execute("SELECT id FROM competitors WHERE id = ?", (competitor_id,)).fetchone()
    if not comp:
        raise HTTPException(status_code=404, detail="Competitor not found.")

    rows = db.execute(
        "SELECT * FROM competitor_pages WHERE competitor_id = ? ORDER BY id DESC",
        (competitor_id,),
    ).fetchall()
    return [dict(r) for r in rows]
