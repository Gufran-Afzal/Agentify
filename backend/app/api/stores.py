import sqlite3
from fastapi import APIRouter, Depends, HTTPException, status
from backend.app.database.connection import get_db
from backend.app.schemas.store import (
    StoreCreate,
    StoreResponse,
    StoreConnectionCreate,
    StoreConnectionResponse,
)
from backend.app.utils.dates import utc_now_iso

router = APIRouter(prefix="/stores", tags=["Stores"])

@router.post("", response_model=StoreResponse, status_code=status.HTTP_201_CREATED)
def create_store(payload: StoreCreate, db: sqlite3.Connection = Depends(get_db)):
    existing = db.execute("SELECT id FROM stores WHERE id = ?", (payload.id,)).fetchone()
    if existing:
        raise HTTPException(status_code=409, detail=f"Store with id '{payload.id}' already exists.")

    now = utc_now_iso()
    db.execute(
        """
        INSERT INTO stores (id, name, domain, platform, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (payload.id, payload.name, payload.domain or "", payload.platform or "demo", now, now),
    )
    db.commit()
    row = db.execute("SELECT * FROM stores WHERE id = ?", (payload.id,)).fetchone()
    return dict(row)

@router.get("", response_model=list[StoreResponse])
def list_stores(db: sqlite3.Connection = Depends(get_db)):
    rows = db.execute("SELECT * FROM stores ORDER BY created_at DESC").fetchall()
    return [dict(r) for r in rows]

@router.get("/{store_id}", response_model=StoreResponse)
def get_store(store_id: str, db: sqlite3.Connection = Depends(get_db)):
    row = db.execute("SELECT * FROM stores WHERE id = ?", (store_id,)).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Store not found.")
    return dict(row)

@router.post("/{store_id}/connections", response_model=StoreConnectionResponse, status_code=status.HTTP_201_CREATED)
def add_store_connection(
    store_id: str,
    payload: StoreConnectionCreate,
    db: sqlite3.Connection = Depends(get_db),
):
    store = db.execute("SELECT id FROM stores WHERE id = ?", (store_id,)).fetchone()
    if not store:
        raise HTTPException(status_code=404, detail="Store not found.")

    now = utc_now_iso()
    cursor = db.execute(
        """
        INSERT INTO store_connections (store_id, provider, status, credentials_reference, created_at, updated_at)
        VALUES (?, ?, 'pending', ?, ?, ?)
        """,
        (store_id, payload.provider, payload.credentials_reference or "", now, now),
    )
    db.commit()
    row = db.execute("SELECT * FROM store_connections WHERE id = ?", (cursor.lastrowid,)).fetchone()
    return dict(row)

@router.get("/{store_id}/connections", response_model=list[StoreConnectionResponse])
def list_store_connections(store_id: str, db: sqlite3.Connection = Depends(get_db)):
    store = db.execute("SELECT id FROM stores WHERE id = ?", (store_id,)).fetchone()
    if not store:
        raise HTTPException(status_code=404, detail="Store not found.")

    rows = db.execute(
        "SELECT * FROM store_connections WHERE store_id = ? ORDER BY id DESC",
        (store_id,),
    ).fetchall()
    return [dict(r) for r in rows]
