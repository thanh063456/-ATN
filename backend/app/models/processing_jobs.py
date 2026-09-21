"""backend/app/models/processing_jobs.py — Bảng `processing_jobs`"""
import uuid
from datetime import datetime

from sqlalchemy import ForeignKey, Integer, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.core.database import Base

JOB_STATUS_PENDING  = "PENDING"
JOB_STATUS_RUNNING  = "RUNNING"
JOB_STATUS_SUCCESS  = "SUCCESS"
JOB_STATUS_FAILED   = "FAILED"
JOB_STATUS_RETRYING = "RETRYING"


class ProcessingJob(Base):
    __tablename__ = "processing_jobs"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    document_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("documents.id", ondelete="CASCADE"),
        nullable=False,
    )
    celery_task_id: Mapped[str | None] = mapped_column(
        String(255), unique=True, nullable=True
    )
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default=JOB_STATUS_PENDING
    )
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    retry_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    started_at: Mapped[datetime | None] = mapped_column(nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        server_default=func.now(), nullable=False
    )

    # Relationships
    document: Mapped["Document"] = relationship(
        "Document", back_populates="processing_jobs"
    )

    def __repr__(self) -> str:
        return (
            f"<ProcessingJob id={self.id} doc={self.document_id} "
            f"status={self.status!r} celery={self.celery_task_id!r}>"
        )
