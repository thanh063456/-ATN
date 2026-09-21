"""backend/app/models/documents.py — Bảng `documents`"""
import uuid
from datetime import datetime

from sqlalchemy import BigInteger, Boolean, ForeignKey, Index, Integer, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.core.database import Base

# OCR status constants
OCR_STATUS_PENDING    = "PENDING"
OCR_STATUS_PROCESSING = "PROCESSING"
OCR_STATUS_DONE       = "DONE"
OCR_STATUS_FAILED     = "FAILED"
OCR_STATUS_SKIPPED    = "SKIPPED"


class Document(Base):
    __tablename__ = "documents"
    __table_args__ = (
        Index("idx_documents_uploaded_by",  "uploaded_by"),
        Index("idx_documents_category_id",  "category_id"),
        Index("idx_documents_ocr_status",   "ocr_status"),
        Index("idx_documents_created_at",   "created_at"),
        Index("idx_documents_is_deleted",   "is_deleted"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    original_filename: Mapped[str] = mapped_column(String(255), nullable=False)
    file_type: Mapped[str] = mapped_column(String(10), nullable=False)
    file_size_bytes: Mapped[int] = mapped_column(BigInteger, nullable=False)
    minio_object_key: Mapped[str] = mapped_column(String(1000), unique=True, nullable=False)
    page_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    category_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("document_categories.id", ondelete="SET NULL"),
        nullable=True,
    )
    uploaded_by: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
    )
    ocr_status: Mapped[str] = mapped_column(
        String(20), nullable=False, default=OCR_STATUS_PENDING
    )
    is_deleted: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    deleted_by: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    deleted_at: Mapped[datetime | None] = mapped_column(nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        server_default=func.now(), onupdate=func.now(), nullable=False
    )

    # Relationships
    category: Mapped["DocumentCategory | None"] = relationship(
        "DocumentCategory", back_populates="documents"
    )
    uploader: Mapped["User"] = relationship(
        "User", foreign_keys=[uploaded_by], back_populates="documents"
    )
    # 1:N — một document có NHIỀU ocr_results (is_latest flag)
    ocr_results: Mapped[list["OCRResult"]] = relationship(
        "OCRResult", back_populates="document", cascade="all, delete-orphan"
    )
    metadata_: Mapped["DocumentMetadata | None"] = relationship(
        "DocumentMetadata", back_populates="document",
        cascade="all, delete-orphan", uselist=False
    )
    processing_jobs: Mapped[list["ProcessingJob"]] = relationship(
        "ProcessingJob", back_populates="document", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Document id={self.id} title={self.title[:30]!r} status={self.ocr_status!r}>"
