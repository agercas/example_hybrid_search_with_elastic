from typing import List, Optional

from pydantic import BaseModel, Field


class DocumentID(BaseModel):
    id: str


class Document(BaseModel):
    content: str
    summary: Optional[str] = None
    name: Optional[str] = None
    url: Optional[str] = None
    created_on: Optional[str] = None
    updated_at: Optional[str] = None
    category: Optional[str] = None
    rolePermissions: Optional[List[str]] = Field(None, alias="role_permissions")


class SearchQuery(BaseModel):
    query: str
    top_k: Optional[int] = 10


class ChatQuestion(BaseModel):
    question: str
