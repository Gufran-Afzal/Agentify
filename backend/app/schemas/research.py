from pydantic import BaseModel

class ResearchRunResponse(BaseModel):
    id: int
    status: str
    created_at: str
    completed_at: str | None = None

class ResearchRunExecuteResponse(BaseModel):
    id: int
    status: str
    completed_at: str | None = None
    opportunities_count: int
    opportunities: list[dict]
