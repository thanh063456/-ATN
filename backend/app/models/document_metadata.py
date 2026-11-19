"""backend/app/models/document_metadata.py — Bảng `document_metadata` (1:1 với documents)"""
import uuid
from datetime import date, datetime

from sqlalchemy import Date, ForeignKey, Index, JSON, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.core.database import Base


class DocumentMetadata(Base):
    __tablename__ = "document_metadata"
    __table_args__ = (
        Index("idx_document_metadata_student_id", "student_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    # 1:1 — document_id UNIQUE
    document_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("documents.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
    )
    student_id: Mapped[str | None] = mapped_column(String(20), nullable=True)
    student_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    document_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    document_number: Mapped[str | None] = mapped_column(String(100), nullable=True)
    extra: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        server_default=func.now(), onupdate=func.now(), nullable=False
    )

    # Relationships
    document: Mapped["Document"] = relationship("Document", back_populates="metadata_")

    def __repr__(self) -> str:
        return f"<DocumentMetadata doc={self.document_id} student={self.student_id!r}>"
