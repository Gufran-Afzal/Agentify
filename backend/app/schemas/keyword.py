from pydantic import BaseModel, Field

class KeywordCreate(BaseModel):
    keyword: str = Field(..., min_length=1, max_length=200)
    search_volume: int = Field(..., ge=0)

class KeywordUpdate(BaseModel):
    keyword: str | None = Field(None, min_length=1, max_length=200)
    search_volume: int | None = Field(None, ge=0)

class KeywordResponse(BaseModel):
    id: int
    keyword: str
    search_volume: int
    created_at: str
    updated_at: str
    is_demo: bool = True
