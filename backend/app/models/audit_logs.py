"""backend/app/models/audit_logs.py — Bảng `audit_logs`"""
import uuid
from datetime import datetime

from sqlalchemy import ForeignKey, Index, JSON, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.core.database import Base

ACTION_LOGIN    = "LOGIN"
ACTION_LOGOUT   = "LOGOUT"
ACTION_UPLOAD   = "UPLOAD"
ACTION_DELETE   = "DELETE"
ACTION_DOWNLOAD = "DOWNLOAD"
ACTION_OCR      = "OCR_TRIGGER"
ACTION_SEARCH   = "SEARCH"
ACTION_EXPORT   = "EXPORT"


class AuditLog(Base):
    __tablename__ = "audit_logs"
    __table_args__ = (
        Index("idx_audit_logs_user_action", "user_id", "action"),
        Index("idx_audit_logs_created_at",  "created_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    action: Mapped[str] = mapped_column(String(50), nullable=False)
    resource_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    resource_id: Mapped[uuid.UUID | None] = mapped_column(Uuid(as_uuid=True), nullable=True)
    detail: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    ip_address: Mapped[str | None] = mapped_column(String(45), nullable=True)
    user_agent: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        server_default=func.now(), nullable=False
    )

    # Relationships
    user: Mapped["User | None"] = relationship("User", back_populates="audit_logs")

    def __repr__(self) -> str:
        return (
            f"<AuditLog id={self.id} action={self.action!r} "
            f"user={self.user_id} resource={self.resource_type}:{self.resource_id}>"
        )
