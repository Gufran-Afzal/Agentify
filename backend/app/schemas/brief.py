from pydantic import BaseModel

class BriefResponse(BaseModel):
    id: int
    opportunity_id: int
    title: str
    objective: str
    primary_keyword: str | None
    search_volume: int
    search_intent: str = "informational"
    target_audience: str = "Skincare enthusiasts & shoppers"
    suggested_sections: list[str] = []
    suggested_angle: str = ""
    related_keywords: list[str] = []
    opportunity_evidence: list[str] = []
    status: str = "draft"
    created_at: str
    updated_at: str | None = None
