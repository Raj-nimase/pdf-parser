from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

class PageChunk(BaseModel):
    page: int = Field(..., description="Zero-indexed page number")
    text: str = Field(..., description="Markdown text content of the page")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Metadata associated with the page")
    images: List[str] = Field(default_factory=list, description="Extracted image filenames or references")

class ParsePDFResponse(BaseModel):
    filename: str
    total_pages: int
    markdown: Optional[str] = Field(None, description="Full markdown content (when page_chunks is False)")
    chunks: Optional[List[PageChunk]] = Field(None, description="List of page chunks (when page_chunks is True)")

class HealthResponse(BaseModel):
    status: str = "ok"
    version: str
