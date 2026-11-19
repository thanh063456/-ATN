"""backend/app/models/users.py — Bảng `users`

Thêm:
- supabase_uid: UUID từ Supabase Auth (auth.users.id) — dùng để map JWT → profile
- mssv: Mã số sinh viên (optional, dành cho STUDENT)
"""
import uuid
from datetime import datetime

from sqlalchemy import Boolean, ForeignKey, Index, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.core.database import Base


class User(Base):
    __tablename__ = "users"
    __table_args__ = (
        Index("idx_users_username", "username"),
        Index("idx_users_email", "email"),
        Index("idx_users_supabase_uid", "supabase_uid"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    # Supabase Auth UUID — dùng để verify JWT và lookup profile
    supabase_uid: Mapped[str | None] = mapped_column(
        String(36), unique=True, nullable=True, index=True
    )
    username: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False, default="")
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    # Mã số sinh viên (chỉ dành cho STUDENT)
    mssv: Mapped[str | None] = mapped_column(String(20), unique=True, nullable=True)
    role_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("roles.id", ondelete="RESTRICT"), nullable=False
    )
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    last_login_at: Mapped[datetime | None] = mapped_column(nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        server_default=func.now(), onupdate=func.now(), nullable=False
    )

    # Relationships
    role: Mapped["Role"] = relationship("Role", back_populates="users")
    documents: Mapped[list["Document"]] = relationship(
        "Document", foreign_keys="Document.uploaded_by", back_populates="uploader"
    )
    audit_logs: Mapped[list["AuditLog"]] = relationship("AuditLog", back_populates="user")
    search_history: Mapped[list["SearchHistory"]] = relationship(
        "SearchHistory", back_populates="user"
    )

    def __repr__(self) -> str:
        return f"<User id={self.id} username={self.username!r} mssv={self.mssv!r}>"
