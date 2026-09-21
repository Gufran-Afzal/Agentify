import sqlite3
from fastapi import APIRouter, Depends, HTTPException, status
from backend.app.database.connection import get_db
from backend.app.schemas.product import ProductCreate, ProductUpdate, ProductResponse
from backend.app.utils.dates import utc_now_iso

router = APIRouter(tags=["Products"])

@router.get("/products", response_model=list[ProductResponse])
def get_products(db: sqlite3.Connection = Depends(get_db)):
    rows = db.execute("SELECT id, name, category, description, created_at, updated_at FROM products ORDER BY id ASC").fetchall()
    return [dict(r) for r in rows]

@router.post("/products", response_model=ProductResponse, status_code=status.HTTP_201_CREATED)
def create_product(payload: ProductCreate, db: sqlite3.Connection = Depends(get_db)):
    now = utc_now_iso()
    name = payload.name.strip()
    category = payload.category.strip()
    description = payload.description.strip()

    if not name or not category or not description:
        raise HTTPException(status_code=400, detail="Product fields cannot be empty.")

    cursor = db.execute(
        "INSERT INTO products (name, category, description, created_at, updated_at) VALUES (?, ?, ?, ?, ?)",
        (name, category, description, now, now)
    )
    db.commit()
    return {
        "id": cursor.lastrowid,
        "name": name,
        "category": category,
        "description": description,
        "created_at": now,
        "updated_at": now
    }

@router.get("/products/{product_id}", response_model=ProductResponse)
def get_product(product_id: int, db: sqlite3.Connection = Depends(get_db)):
    row = db.execute(
        "SELECT id, name, category, description, created_at, updated_at FROM products WHERE id = ?",
        (product_id,)
    ).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Product not found.")
    return dict(row)

@router.put("/products/{product_id}", response_model=ProductResponse)
def update_product(product_id: int, payload: ProductUpdate, db: sqlite3.Connection = Depends(get_db)):
    row = db.execute("SELECT id, name, category, description, created_at, updated_at FROM products WHERE id = ?", (product_id,)).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Product not found.")

    current = dict(row)
    now = utc_now_iso()
    new_name = payload.name.strip() if payload.name is not None else current["name"]
    new_cat = payload.category.strip() if payload.category is not None else current["category"]
    new_desc = payload.description.strip() if payload.description is not None else current["description"]

    if not new_name or not new_cat or not new_desc:
        raise HTTPException(status_code=400, detail="Product fields cannot be empty.")

    db.execute(
        "UPDATE products SET name = ?, category = ?, description = ?, updated_at = ? WHERE id = ?",
        (new_name, new_cat, new_desc, now, product_id)
    )
    db.commit()

    return {
        "id": product_id,
        "name": new_name,
        "category": new_cat,
        "description": new_desc,
        "created_at": current["created_at"],
        "updated_at": now
    }

@router.delete("/products/{product_id}", status_code=status.HTTP_200_OK)
def delete_product(product_id: int, db: sqlite3.Connection = Depends(get_db)):
    row = db.execute("SELECT id FROM products WHERE id = ?", (product_id,)).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Product not found.")
    db.execute("DELETE FROM products WHERE id = ?", (product_id,))
    db.commit()
    return {"detail": "Product deleted successfully."}
