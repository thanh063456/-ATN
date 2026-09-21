"""backend/app/models/document_categories.py — Bảng `document_categories`"""
import uuid
from datetime import datetime

from sqlalchemy import Boolean, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.core.database import Base


class DocumentCategory(Base):
    __tablename__ = "document_categories"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(
        server_default=func.now(), nullable=False
    )

    # Relationships
    documents: Mapped[list["Document"]] = relationship(
        "Document", back_populates="category"
    )

    def __repr__(self) -> str:
        return f"<DocumentCategory code={self.code!r} name={self.name!r}>"
