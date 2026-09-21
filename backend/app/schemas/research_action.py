from typing import Any, Optional
from pydantic import BaseModel

class ResearchActionResponse(BaseModel):
    id: int
    research_run_id: int
    action_type: str
    arguments: dict[str, Any] = {}
    result: dict[str, Any] = {}
    status: str
    created_at: str
    completed_at: Optional[str] = None
