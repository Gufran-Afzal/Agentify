from pydantic import BaseModel, Field

class ExistingContentCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=300)
    url: str = Field(..., min_length=1, max_length=500)
    primary_keyword: str | None = None

class ExistingContentResponse(BaseModel):
    id: int
    title: str
    url: str
    primary_keyword: str | None = None
    created_at: str
    updated_at: str

class StoreProfileResponse(BaseModel):
    categories: list[str]
    product_count: int
    products: list[str]
    descriptions: list[str]
