from typing import Any, Optional
from pydantic import BaseModel

class EvidenceResponse(BaseModel):
    id: int
    research_run_id: Optional[int] = None
    store_id: str = "demo-store"
    source_type: str
    source_reference: str = ""
    evidence_type: str
    data: dict[str, Any] = {}
    reliability: float = 1.0
    created_at: str
    notes: Optional[str] = ""
