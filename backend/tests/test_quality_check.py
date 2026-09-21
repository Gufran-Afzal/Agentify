import sqlite3
import pytest
from backend.app.database.schema import init_db
from backend.app.services.quality_check_service import quality_check_service

@pytest.fixture
def db_conn():
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    init_db(conn)
    # Seed a product
    conn.execute(
        "INSERT INTO products (name, category, description, store_id, created_at, updated_at) VALUES ('Niacinamide Serum', 'Skincare', 'Daily face serum', 'demo-store', '', '')"
    )
    conn.commit()
    yield conn
    conn.close()

def test_quality_check_high_quality_draft(db_conn):
    draft = {
        "id": 1,
        "title": "Niacinamide Serum Benefits for Radiant Skin",
        "primary_keyword": "niacinamide serum benefits",
        "introduction": "Looking for the top niacinamide serum benefits? This powerful skincare ingredient has gained massive popularity for evening skin tone and clearing pores.",
        "body": """## Understanding Niacinamide Serum Benefits

Niacinamide, also known as vitamin B3, is a water-soluble vitamin that works with the natural substances in your skin to help visibly minimize enlarged pores, tighten lax pores, improve uneven skin tone, and soften fine lines and wrinkles.

### How To Apply Your Niacinamide Serum

Applying a few drops of Niacinamide Serum after cleansing and toning delivers optimum absorption. Pair it with a gentle moisturizer for best results. Many dermatologists suggest daily application for consistent improvement in skin texture.

- Cleanse thoroughly with a gentle foaming wash.
- Apply 3-4 drops of Niacinamide Serum across cheeks and forehead.
- Follow up with sunscreen during morning hours.
""",
        "conclusion": "In summary, embracing niacinamide serum benefits in your daily routine can transform skin texture. Always consult with a licensed dermatologist before starting new active treatments. Results may vary."
    }

    result = quality_check_service.audit_draft(db_conn, draft, store_id="demo-store")

    assert result["score"] >= 80
    assert result["grade"] in ("Excellent", "Good")
    assert result["word_count"] > 100
    assert result["reading_ease"] > 20
    assert "Niacinamide Serum" in result["matched_products"]

    check_names = {c["name"]: c["passed"] for c in result["checks"]}
    assert check_names["Keyword in Title"] is True
    assert check_names["Keyword in Introduction"] is True
    assert check_names["Keyword in Headings"] is True
    assert check_names["Brand Safety & Disclaimers"] is True
    assert check_names["Catalog Product Integration"] is True

def test_quality_check_poor_draft_penalties(db_conn):
    draft = {
        "id": 2,
        "title": "Random Title Without Topic",
        "primary_keyword": "vitamin c booster",
        "introduction": "Hello world.",
        "body": "Just a very short sentence.",
        "conclusion": "The end."
    }

    result = quality_check_service.audit_draft(db_conn, draft, store_id="demo-store")
    assert result["score"] < 60
    assert len(result["warnings"]) > 0
    check_names = {c["name"]: c["passed"] for c in result["checks"]}
    assert check_names["Keyword in Title"] is False
    assert check_names["Keyword in Introduction"] is False
