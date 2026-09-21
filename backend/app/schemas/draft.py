from pydantic import BaseModel, Field

class DraftUpdate(BaseModel):
    title: str = Field(..., min_length=1)
    introduction: str = Field(..., min_length=1)
    body: str = Field(..., min_length=1)
    conclusion: str = Field(..., min_length=1)

class DraftResponse(BaseModel):
    id: int
    brief_id: int
    title: str
    primary_keyword: str | None
    introduction: str
    body: str
    conclusion: str
    status: str
    created_at: str
    updated_at: str | None = None

class DraftActionResponse(BaseModel):
    id: int
    status: str
