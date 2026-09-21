from pydantic import BaseModel, Field

class ProductCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    category: str = Field(..., min_length=1, max_length=100)
    description: str = Field(..., min_length=1)

class ProductUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=200)
    category: str | None = Field(None, min_length=1, max_length=100)
    description: str | None = Field(None, min_length=1)

class ProductResponse(BaseModel):
    id: int
    name: str
    category: str
    description: str
    created_at: str
    updated_at: str
