"""
backend/app/core/database.py — Async SQLAlchemy engine & session

Tự động kết nối PostgreSQL nếu có; nếu PostgreSQL offline/lỗi, tự động fallback SQLite (aiosqlite)
để hệ thống luôn chạy được ổn định ở môi trường phát triển local.
"""
import os
from collections.abc import AsyncGenerator
from pathlib import Path

from loguru import logger
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

from app.core.config import settings

# ── Base declarative ───────────────────────────────────────────────────────────
class Base(DeclarativeBase):
    """
    Base class cho tất cả SQLAlchemy models.
    Import từ đây: from app.core.database import Base
    """
    pass


# ── Engine & Session ───────────────────────────────────────────────────────────
SQLITE_DB_PATH = Path(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../data.db")))
SQLITE_URL = f"sqlite+aiosqlite:///{SQLITE_DB_PATH.as_posix()}"

engine = create_async_engine(SQLITE_URL, echo=False)
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


async def init_db() -> None:
    """Khởi tạo các bảng và dữ liệu ban đầu nếu chưa có."""
    global engine, AsyncSessionLocal
    
    # Thử kết nối PostgreSQL nếu được cấu hình
    if "postgresql" in settings.database_url:
        try:
            connect_args = {}
            if "asyncpg" in settings.database_url:
                connect_args = {
                    "statement_cache_size": 0,
                    "prepared_statement_cache_size": 0,
                }
            pg_engine = create_async_engine(
                settings.database_url,
                echo=False,
                pool_size=settings.db_pool_size,
                max_overflow=settings.db_max_overflow,
                pool_timeout=5,
                pool_pre_ping=True,
                connect_args=connect_args,
            )
            async with pg_engine.connect() as conn:
                await conn.execute(text("SELECT 1"))
            engine = pg_engine
            AsyncSessionLocal.configure(bind=engine)
            logger.info("Connected to PostgreSQL (Supabase) database successfully with PgBouncer compatibility.")
        except Exception as exc:
            logger.warning(
                "PostgreSQL connection failed ({err}). Using SQLite local DB: {path}",
                err=str(exc), path=str(SQLITE_DB_PATH)
            )
            engine = create_async_engine(SQLITE_URL, echo=False)
            AsyncSessionLocal.configure(bind=engine)
    else:
        engine = create_async_engine(SQLITE_URL, echo=False)
        AsyncSessionLocal.configure(bind=engine)

    # Tạo bảng tự động và cập nhật cột
    try:
        from app.models import (
            Role, User, DocumentCategory, Document, OCRResult,
            DocumentMetadata, ProcessingJob, SearchHistory, AuditLog
        )
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

        # Danh sách các cột cần migration bổ sung
        # Lưu ý: Mỗi câu lệnh ALTER chạy trong transaction/connection riêng
        # để tránh InFailedSQLTransactionError trên asyncpg khi một cột đã tồn tại hoặc gặp lỗi.
        #
        # KIẾN NGHỊ VỀ ALEMBIC:
        # Trong tương lai, nên chuyển cơ chế migration thủ công này sang Alembic
        # (alembic upgrade head) để quản lý phiên bản schema, hỗ trợ rollback
        # và đồng bộ CI/CD một cách chuyên nghiệp.
        columns_to_add = [
            {"table": "users", "column": "supabase_uid", "type": "VARCHAR(255)"},
            {"table": "users", "column": "mssv", "type": "VARCHAR(20)"},
            {"table": "documents", "column": "is_verified", "type": "BOOLEAN DEFAULT FALSE"},
            {"table": "documents", "column": "verification_code", "type": "VARCHAR(255)"},
            {"table": "documents", "column": "qr_code_url", "type": "TEXT"},
            {"table": "processing_jobs", "column": "ocr_progress", "type": "SMALLINT DEFAULT 0"},
        ]

        is_postgres = engine.dialect.name == "postgresql"
        for item in columns_to_add:
            tbl = item["table"]
            col = item["column"]
            col_type = item["type"]
            try:
                async with engine.begin() as conn:
                    if is_postgres:
                        stmt = f"ALTER TABLE {tbl} ADD COLUMN IF NOT EXISTS {col} {col_type};"
                    else:
                        stmt = f"ALTER TABLE {tbl} ADD COLUMN {col} {col_type};"
                    await conn.execute(text(stmt))
                logger.debug("Column {col} on table {tbl} checked/added successfully.", col=col, tbl=tbl)
            except Exception as col_exc:
                err_msg = str(col_exc).lower()
                if "already exists" in err_msg or "duplicate column" in err_msg:
                    logger.debug("Column {col} on table {tbl} đã tồn tại.", col=col, tbl=tbl)
                else:
                    logger.warning(
                        "Lỗi khi thêm cột {col} vào bảng {tbl}: {err}",
                        col=col,
                        tbl=tbl,
                        err=str(col_exc),
                    )

        logger.info("Database schema initialized successfully.")

        # Seed roles & default users
        async with AsyncSessionLocal() as session:
            try:
                from app.core.security import get_password_hash
                role_res = await session.execute(select(Role).limit(1))
                if not role_res.scalars().first():
                    admin_role = Role(name="ADMIN", description="Quản trị viên hệ thống")
                    staff_role = Role(name="STAFF", description="Cán bộ CTSV")
                    student_role = Role(name="STUDENT", description="Sinh viên")
                    session.add_all([admin_role, staff_role, student_role])
                    await session.flush()

                    admin_user = User(
                        username="admin_hethong",
                        email="admin@dlu.edu.vn",
                        hashed_password=get_password_hash("admin123"),
                        full_name="Quản trị viên Hệ thống (DLU)",
                        role_id=admin_role.id,
                        is_active=True,
                    )
                    staff_user = User(
                        username="canbo_ctsv",
                        email="canbo@dlu.edu.vn",
                        hashed_password=get_password_hash("password123"),
                        full_name="Cán bộ CTSV (STAFF)",
                        role_id=staff_role.id,
                        is_active=True,
                    )
                    student_demo = User(
                        username="sinhvien_demo",
                        email="sinhvien@dlu.edu.vn",
                        mssv="2210001",
                        hashed_password=get_password_hash("123456"),
                        full_name="Sinh Viên Mẫu (DLU)",
                        role_id=student_role.id,
                        is_active=True,
                    )
                    session.add_all([admin_user, staff_user, student_demo])
                    await session.commit()
                    logger.info("Database seeded with default roles and validly hashed users.")
            except Exception as seed_exc:
                await session.rollback()
                logger.warning("Seed initialization note: {err}", err=str(seed_exc))
    except Exception as exc:
        logger.error("Failed to initialize database tables: {err}", err=str(exc))


# ── Dependency ─────────────────────────────────────────────────────────────────
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency cung cấp DB session."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()

