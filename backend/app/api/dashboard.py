import sqlite3
from fastapi import APIRouter, Depends
from backend.app.database.connection import get_db
from backend.app.schemas.dashboard import DashboardStatsResponse

router = APIRouter(tags=["Dashboard"])

@router.get("/dashboard/stats", response_model=DashboardStatsResponse)
def get_dashboard_stats(db: sqlite3.Connection = Depends(get_db)):
    products_count = db.execute("SELECT COUNT(*) FROM products").fetchone()[0]
    keywords_count = db.execute("SELECT COUNT(*) FROM keywords").fetchone()[0]
    content_count = db.execute("SELECT COUNT(*) FROM existing_content").fetchone()[0]
    research_runs_count = db.execute("SELECT COUNT(*) FROM research_runs").fetchone()[0]

    pending_opps = db.execute("SELECT COUNT(*) FROM content_opportunities WHERE status = 'pending'").fetchone()[0]
    approved_opps = db.execute("SELECT COUNT(*) FROM content_opportunities WHERE status = 'approved'").fetchone()[0]
    briefs_count = db.execute("SELECT COUNT(*) FROM content_briefs").fetchone()[0]
    drafts_count = db.execute("SELECT COUNT(*) FROM content_drafts").fetchone()[0]
    published_count = db.execute("SELECT COUNT(*) FROM published_content WHERE status = 'published'").fetchone()[0]

    return {
        "total_products": products_count,
        "total_keywords": keywords_count,
        "total_existing_content": content_count,
        "research_runs": research_runs_count,
        "pending_opportunities": pending_opps,
        "approved_opportunities": approved_opps,
        "content_briefs": briefs_count,
        "drafts": drafts_count,
        "published_content": published_count
    }
