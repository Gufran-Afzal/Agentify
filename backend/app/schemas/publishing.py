from pydantic import BaseModel

class PublishedContentResponse(BaseModel):
    id: int
    draft_id: int
    title: str
    slug: str
    url: str
    status: str
    published_at: str
    created_at: str
    updated_at: str

class PublicArticleResponse(BaseModel):
    title: str
    slug: str
    primary_keyword: str | None
    introduction: str
    body: str
    conclusion: str
    published_at: str
