from pydantic import BaseModel

class OpportunityResponse(BaseModel):
    id: int
    research_run_id: int
    title: str
    reason: str
    primary_keyword: str | None
    search_volume: int
    confidence: str
    status: str
    evidence: list[str] = []
    created_at: str | None = None

class OpportunityActionResponse(BaseModel):
    id: int
    status: str
    message: str | None = None
