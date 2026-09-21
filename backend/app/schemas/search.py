"""
backend/app/schemas/search.py — Pydantic Schemas for Search API

Định nghĩa cấu trúc response cho full-text search, highlights, và thống kê tìm kiếm.
"""
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class SearchHit(BaseModel):
    """Một kết quả tìm kiếm khớp."""
    model_config = ConfigDict(from_attributes=True)

    document_id: UUID
    title: str
    content_snippet: str | None = None
    category_code: str | None = None
    category_name: str | None = None
    student_id: str | None = None
    student_name: str | None = None
    document_date: str | None = None
    document_number: str | None = None
    ocr_status: str
    ocr_confidence: float | None = None
    score: float = Field(description="Điểm liên quan BM25 từ Elasticsearch")
    highlights: dict[str, list[str]] = Field(
        default_factory=dict,
        description="Các đoạn trích nổi bật khớp từ khóa (với thẻ <em>...</em>)",
    )
    created_at: datetime | None = None


class SearchResponse(BaseModel):
    """Response trả về cho GET /search."""
    model_config = ConfigDict(from_attributes=True)

    query: str
    total_hits: int
    page: int
    page_size: int
    total_pages: int
    took_ms: int
    results: list[SearchHit]
