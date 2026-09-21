"""
backend/alembic/env.py — Alembic migration environment

Dùng ALEMBIC_DATABASE_URL (psycopg2, sync) — KHÔNG dùng asyncpg.
Ref: .ai/AGENTS.md §5, .ai/design/Database.md §4
"""
import os
import sys
from logging.config import fileConfig
from pathlib import Path

from alembic import context
from sqlalchemy import engine_from_config, pool

# Thêm backend/ vào sys.path để import app.*
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# Import settings và tất cả models để autogenerate hoạt động
from app.core.config import settings
from app.core.database import Base
import app.models  # noqa: F401 — import để Alembic thấy tất cả models

# ── Alembic config ────────────────────────────────────────────────────────────
config = context.config

# Logging từ alembic.ini
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Target metadata cho autogenerate
target_metadata = Base.metadata

# ── URL: dùng ALEMBIC_DATABASE_URL (psycopg2, sync) ──────────────────────────
# Ref: .ai/AGENTS.md §5 — Alembic chạy sync, cần driver psycopg2
alembic_url = os.getenv("ALEMBIC_DATABASE_URL") or settings.alembic_database_url
config.set_main_option("sqlalchemy.url", alembic_url)


def run_migrations_offline() -> None:
    """
    Chạy migration ở chế độ 'offline' (không cần kết nối DB thật).
    Xuất ra SQL script thay vì thực thi.
    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """
    Chạy migration ở chế độ 'online' — kết nối thật vào DB và thực thi.
    """
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,              # phát hiện thay đổi kiểu dữ liệu
            compare_server_default=True,    # phát hiện thay đổi server default
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
