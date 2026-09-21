"""
backend/app/models/ocr_results.py — Bảng `ocr_results`

QUAN TRỌNG: Quan hệ 1 Document → NHIỀU OCRResult (KHÔNG phải 1:1).
  - document_id KHÔNG có UNIQUE constraint.
  - Dùng is_latest=True để lấy kết quả mới nhất.
  - Khi insert kết quả mới, phải reset is_latest=False cho tất cả bản ghi cũ.
  Ref: .ai/AGENTS.md §4, .ai/design/Database.md §2.5
"""
import uuid
from datetime import datetime

from sqlalchemy import Boolean, Float, ForeignKey, Index, Integer, JSON, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.core.database import Base


class OCRResult(Base):
    __tablename__ = "ocr_results"
    __table_args__ = (
        # Index thường — tra cứu tất cả results của một document
        Index("idx_ocr_results_document_id", "document_id"),
        # Partial index — chỉ index các bản ghi is_latest=True
        Index(
            "idx_ocr_results_latest",
            "document_id",
            "is_latest",
            postgresql_where="is_latest = true",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    # KHÔNG có unique=True — 1 document có thể có nhiều OCR runs
    document_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("documents.id", ondelete="CASCADE"),
        nullable=False,
    )
    is_latest: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True,
        comment="True = kết quả OCR mới nhất của document này.",
    )
    raw_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    corrected_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    confidence_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    ocr_engine: Mapped[str] = mapped_column(String(50), nullable=False, default="vietocr")
    ocr_engine_version: Mapped[str | None] = mapped_column(String(20), nullable=True)
    page_texts: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    processing_time_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    is_corrected: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    corrected_by: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    corrected_at: Mapped[datetime | None] = mapped_column(nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        server_default=func.now(), onupdate=func.now(), nullable=False
    )

    # Relationships
    document: Mapped["Document"] = relationship("Document", back_populates="ocr_results")
    corrector: Mapped["User | None"] = relationship(
        "User", foreign_keys=[corrected_by]
    )

    def __repr__(self) -> str:
        return (
            f"<OCRResult id={self.id} doc={self.document_id} "
            f"latest={self.is_latest} engine={self.ocr_engine!r}>"
        )
