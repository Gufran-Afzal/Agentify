import sqlite3
from backend.app.utils.dates import utc_now_iso

DEFAULT_PRODUCTS = [
    {
        "name": "Vitamin C Serum",
        "category": "Skincare",
        "description": "Brightening facial serum with vitamin C"
    },
    {
        "name": "Hyaluronic Acid Serum",
        "category": "Skincare",
        "description": "Hydrating serum for dry and dehydrated skin"
    },
    {
        "name": "Niacinamide Serum",
        "category": "Skincare",
        "description": "Oil-control and pore-refining facial serum"
    }
]

DEFAULT_KEYWORDS = [
    {
        "keyword": "vitamin c serum benefits",
        "search_volume": 12000
    },
    {
        "keyword": "hyaluronic acid serum benefits",
        "search_volume": 9000
    },
    {
        "keyword": "niacinamide serum benefits",
        "search_volume": 8000
    },
    {
        "keyword": "vitamin c vs hyaluronic acid",
        "search_volume": 3500
    },
    {
        "keyword": "best serum for dry skin",
        "search_volume": 7000
    }
]

DEFAULT_EXISTING_CONTENT = [
    {
        "title": "How to Build a Simple Skincare Routine",
        "url": "/blog/simple-skincare-routine",
        "primary_keyword": "simple skincare routine"
    },
    {
        "title": "Vitamin C Serum Benefits and How to Use It",
        "url": "/blog/vitamin-c-serum-benefits",
        "primary_keyword": "vitamin c serum benefits"
    }
]

def seed_db(conn: sqlite3.Connection, force_reset: bool = False) -> None:
    """Populate database with default seed records if empty, or reset if requested."""
    now = utc_now_iso()

    if force_reset:
        conn.execute("DELETE FROM published_content")
        conn.execute("DELETE FROM content_drafts")
        conn.execute("DELETE FROM content_briefs")
        conn.execute("DELETE FROM content_opportunities")
        conn.execute("DELETE FROM research_runs")
        conn.execute("DELETE FROM existing_content")
        conn.execute("DELETE FROM keywords")
        conn.execute("DELETE FROM products")
        conn.commit()

    # Seed products
    product_count = conn.execute("SELECT COUNT(*) FROM products").fetchone()[0]
    if product_count == 0:
        for p in DEFAULT_PRODUCTS:
            conn.execute(
                """
                INSERT INTO products (name, category, description, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (p["name"], p["category"], p["description"], now, now)
            )

    # Seed keywords
    keyword_count = conn.execute("SELECT COUNT(*) FROM keywords").fetchone()[0]
    if keyword_count == 0:
        for k in DEFAULT_KEYWORDS:
            conn.execute(
                """
                INSERT INTO keywords (keyword, search_volume, created_at, updated_at)
                VALUES (?, ?, ?, ?)
                """,
                (k["keyword"], k["search_volume"], now, now)
            )

    # Seed existing content
    content_count = conn.execute("SELECT COUNT(*) FROM existing_content").fetchone()[0]
    if content_count == 0:
        for c in DEFAULT_EXISTING_CONTENT:
            conn.execute(
                """
                INSERT INTO existing_content (title, url, primary_keyword, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (c["title"], c["url"], c["primary_keyword"], now, now)
            )

    conn.commit()
