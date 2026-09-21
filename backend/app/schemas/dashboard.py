from pydantic import BaseModel

class DashboardStatsResponse(BaseModel):
    total_products: int
    total_keywords: int
    total_existing_content: int
    research_runs: int
    pending_opportunities: int
    approved_opportunities: int
    content_briefs: int
    drafts: int
    published_content: int
