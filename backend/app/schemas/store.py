from typing import Optional
from pydantic import BaseModel

class StoreCreate(BaseModel):
    id: str
    name: str
    domain: Optional[str] = ""
    platform: Optional[str] = "demo"

class StoreResponse(BaseModel):
    id: str
    name: str
    domain: str
    platform: str
    created_at: str
    updated_at: str

class StoreConnectionCreate(BaseModel):
    provider: str
    credentials_reference: Optional[str] = ""

class StoreConnectionResponse(BaseModel):
    id: int
    store_id: str
    provider: str
    status: str
    credentials_reference: str
    created_at: str
    updated_at: str
