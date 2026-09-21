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
    topic: str = ""
    search_intent: str = "informational"
    why_it_matters: str = ""
    evidence_ids: list[str] = []
    supporting_evidence: list[str] = []
    missing_evidence: list[str] = []
    confidence_level: str = "exploratory"
    created_at: str | None = None

class OpportunityActionResponse(BaseModel):
    id: int
    status: str
    message: str | None = None
