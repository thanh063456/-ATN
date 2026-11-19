"""
backend/app/models/search_history.py — Bảng `search_history`
Append-only — không có UPDATE, không có soft-delete.
"""
import uuid
from datetime import datetime

from sqlalchemy import ForeignKey, Index, Integer, JSON, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.core.database import Base


class SearchHistory(Base):
    __tablename__ = "search_history"
    __table_args__ = (
        Index("idx_search_history_user_id",    "user_id"),
        Index("idx_search_history_created_at", "created_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        comment="NULL nếu tìm kiếm anonymous",
    )
    keyword: Mapped[str] = mapped_column(Text, nullable=False)
    filter: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    result_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        server_default=func.now(), nullable=False
    )

    # Relationships
    user: Mapped["User | None"] = relationship("User", back_populates="search_history")

    def __repr__(self) -> str:
        return f"<SearchHistory id={self.id} keyword={self.keyword[:30]!r}>"
