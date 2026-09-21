from typing import Optional
from pydantic import BaseModel

class CompetitorCreate(BaseModel):
    domain: str
    name: Optional[str] = ""
    category: Optional[str] = "content_competitor"
    discovery_reason: Optional[str] = ""

class CompetitorResponse(BaseModel):
    id: int
    store_id: str
    domain: str
    name: str
    category: str
    status: str
    discovery_reason: str
    created_at: str
    updated_at: str

class CompetitorPageCreate(BaseModel):
    url: str
    title: Optional[str] = ""
    content_summary: Optional[str] = ""
    page_type: Optional[str] = "blog"

class CompetitorPageResponse(BaseModel):
    id: int
    competitor_id: int
    url: str
    title: str
    content_summary: str
    page_type: str
    created_at: str
