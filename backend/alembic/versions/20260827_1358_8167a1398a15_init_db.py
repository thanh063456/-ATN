"""init_db

Revision ID: 8167a1398a15
Revises:
Create Date: 2026-08-27

Tạo 9 bảng ban đầu cho hệ thống Student-Document-OCR:
  roles, users, document_categories, documents, ocr_results,
  document_metadata, processing_jobs, search_history, audit_logs

Ref: .ai/design/Database.md
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "8167a1398a15"
down_revision: str | None = None
branch_labels: str | tuple[str, ...] | None = None
depends_on: str | tuple[str, ...] | None = None


def upgrade() -> None:
    # ── Kích hoạt uuid-ossp extension ────────────────────────────────────────
    op.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"')

    # ── 1. roles ──────────────────────────────────────────────────────────────
    op.create_table(
        "roles",
        sa.Column("id", postgresql.UUID(as_uuid=True),
                  server_default=sa.text("uuid_generate_v4()"), nullable=False),
        sa.Column("name", sa.String(50), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True),
                  server_default=sa.text("NOW()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
    )

    # ── 2. users ──────────────────────────────────────────────────────────────
    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True),
                  server_default=sa.text("uuid_generate_v4()"), nullable=False),
        sa.Column("username", sa.String(50), nullable=False),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("hashed_password", sa.String(255), nullable=False),
        sa.Column("full_name", sa.String(255), nullable=False),
        sa.Column("role_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("last_login_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True),
                  server_default=sa.text("NOW()"), nullable=False),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True),
                  server_default=sa.text("NOW()"), nullable=False),
        sa.ForeignKeyConstraint(["role_id"], ["roles.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("username"),
        sa.UniqueConstraint("email"),
    )
    op.create_index("idx_users_username", "users", ["username"])
    op.create_index("idx_users_email",    "users", ["email"])

    # ── 3. document_categories ────────────────────────────────────────────────
    op.create_table(
        "document_categories",
        sa.Column("id", postgresql.UUID(as_uuid=True),
                  server_default=sa.text("uuid_generate_v4()"), nullable=False),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("code", sa.String(50), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True),
                  server_default=sa.text("NOW()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
        sa.UniqueConstraint("code"),
    )

    # ── 4. documents ──────────────────────────────────────────────────────────
    op.create_table(
        "documents",
        sa.Column("id", postgresql.UUID(as_uuid=True),
                  server_default=sa.text("uuid_generate_v4()"), nullable=False),
        sa.Column("title", sa.String(500), nullable=False),
        sa.Column("original_filename", sa.String(255), nullable=False),
        sa.Column("file_type", sa.String(10), nullable=False),
        sa.Column("file_size_bytes", sa.BigInteger(), nullable=False),
        sa.Column("minio_object_key", sa.String(1000), nullable=False),
        sa.Column("page_count", sa.Integer(), nullable=True),
        sa.Column("category_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("uploaded_by", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("ocr_status", sa.String(20), nullable=False,
                  server_default=sa.text("'PENDING'")),
        sa.Column("is_deleted", sa.Boolean(), nullable=False,
                  server_default=sa.text("false")),
        sa.Column("deleted_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("deleted_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True),
                  server_default=sa.text("NOW()"), nullable=False),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True),
                  server_default=sa.text("NOW()"), nullable=False),
        sa.ForeignKeyConstraint(["category_id"], ["document_categories.id"],
                                ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["uploaded_by"], ["users.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["deleted_by"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("minio_object_key"),
    )
    op.create_index("idx_documents_uploaded_by", "documents", ["uploaded_by"])
    op.create_index("idx_documents_category_id", "documents", ["category_id"])
    op.create_index("idx_documents_ocr_status",  "documents", ["ocr_status"])
    op.create_index("idx_documents_created_at",  "documents", ["created_at"])
    op.create_index("idx_documents_is_deleted",  "documents", ["is_deleted"])

    # ── 5. ocr_results ────────────────────────────────────────────────────────
    # document_id KHÔNG UNIQUE — 1 Document có NHIỀU OCRResult (quan hệ 1:N)
    op.create_table(
        "ocr_results",
        sa.Column("id", postgresql.UUID(as_uuid=True),
                  server_default=sa.text("uuid_generate_v4()"), nullable=False),
        sa.Column("document_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("is_latest", sa.Boolean(), nullable=False,
                  server_default=sa.text("true"),
                  comment="True = kết quả OCR mới nhất của document này"),
        sa.Column("raw_text", sa.Text(), nullable=True),
        sa.Column("corrected_text", sa.Text(), nullable=True),
        sa.Column("confidence_score", sa.Float(), nullable=True),
        sa.Column("ocr_engine", sa.String(50), nullable=False,
                  server_default=sa.text("'vietocr'")),
        sa.Column("ocr_engine_version", sa.String(20), nullable=True),
        sa.Column("page_texts", postgresql.JSONB(), nullable=True),
        sa.Column("processing_time_ms", sa.Integer(), nullable=True),
        sa.Column("is_corrected", sa.Boolean(), nullable=False,
                  server_default=sa.text("false")),
        sa.Column("corrected_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("corrected_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True),
                  server_default=sa.text("NOW()"), nullable=False),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True),
                  server_default=sa.text("NOW()"), nullable=False),
        sa.ForeignKeyConstraint(["document_id"], ["documents.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["corrected_by"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        # KHÔNG có UniqueConstraint("document_id") — thiết kế đúng theo Database.md
    )
    op.create_index("idx_ocr_results_document_id", "ocr_results", ["document_id"])
    # Partial index: chỉ index các bản ghi is_latest=True
    op.create_index(
        "idx_ocr_results_latest",
        "ocr_results",
        ["document_id", "is_latest"],
        postgresql_where=sa.text("is_latest = true"),
    )

    # ── 6. document_metadata ──────────────────────────────────────────────────
    # document_id UNIQUE — 1:1 với documents
    op.create_table(
        "document_metadata",
        sa.Column("id", postgresql.UUID(as_uuid=True),
                  server_default=sa.text("uuid_generate_v4()"), nullable=False),
        sa.Column("document_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("student_id", sa.String(20), nullable=True),
        sa.Column("student_name", sa.String(255), nullable=True),
        sa.Column("document_date", sa.Date(), nullable=True),
        sa.Column("document_number", sa.String(100), nullable=True),
        sa.Column("extra", postgresql.JSONB(), nullable=True),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True),
                  server_default=sa.text("NOW()"), nullable=False),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True),
                  server_default=sa.text("NOW()"), nullable=False),
        sa.ForeignKeyConstraint(["document_id"], ["documents.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("document_id"),   # 1:1
    )
    op.create_index("idx_document_metadata_student_id", "document_metadata", ["student_id"])

    # ── 7. processing_jobs ────────────────────────────────────────────────────
    op.create_table(
        "processing_jobs",
        sa.Column("id", postgresql.UUID(as_uuid=True),
                  server_default=sa.text("uuid_generate_v4()"), nullable=False),
        sa.Column("document_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("celery_task_id", sa.String(255), nullable=True),
        sa.Column("status", sa.String(20), nullable=False,
                  server_default=sa.text("'PENDING'")),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("retry_count", sa.Integer(), nullable=False,
                  server_default=sa.text("0")),
        sa.Column("started_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("completed_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True),
                  server_default=sa.text("NOW()"), nullable=False),
        sa.ForeignKeyConstraint(["document_id"], ["documents.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("celery_task_id"),
    )

    # ── 8. search_history ─────────────────────────────────────────────────────
    op.create_table(
        "search_history",
        sa.Column("id", postgresql.UUID(as_uuid=True),
                  server_default=sa.text("uuid_generate_v4()"), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("keyword", sa.Text(), nullable=False),
        sa.Column("filter", postgresql.JSONB(), nullable=True),
        sa.Column("result_count", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True),
                  server_default=sa.text("NOW()"), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_search_history_user_id",    "search_history", ["user_id"])
    op.create_index("idx_search_history_created_at", "search_history", ["created_at"])

    # ── 9. audit_logs ─────────────────────────────────────────────────────────
    op.create_table(
        "audit_logs",
        sa.Column("id", postgresql.UUID(as_uuid=True),
                  server_default=sa.text("uuid_generate_v4()"), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("action", sa.String(50), nullable=False),
        sa.Column("resource_type", sa.String(50), nullable=True),
        sa.Column("resource_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("detail", postgresql.JSONB(), nullable=True),
        sa.Column("ip_address", sa.String(45), nullable=True),
        sa.Column("user_agent", sa.Text(), nullable=True),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True),
                  server_default=sa.text("NOW()"), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_audit_logs_user_action", "audit_logs", ["user_id", "action"])
    op.create_index("idx_audit_logs_created_at",  "audit_logs", ["created_at"])


def downgrade() -> None:
    # Drop theo thứ tự ngược lại (FK dependencies)
    op.drop_table("audit_logs")
    op.drop_table("search_history")
    op.drop_table("processing_jobs")
    op.drop_table("document_metadata")
    op.drop_table("ocr_results")
    op.drop_table("documents")
    op.drop_table("document_categories")
    op.drop_table("users")
    op.drop_table("roles")
    op.execute('DROP EXTENSION IF EXISTS "uuid-ossp"')
