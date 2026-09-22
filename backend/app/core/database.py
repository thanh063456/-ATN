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
            columns_to_add = [
                ("users", "supabase_uid", "VARCHAR(255)"),
                ("users", "mssv", "VARCHAR(20)"),
                ("documents", "is_verified", "BOOLEAN DEFAULT FALSE"),
                ("documents", "verification_code", "VARCHAR(255)"),
                ("documents", "qr_code_url", "TEXT"),
            ]
            for tbl, col, col_type in columns_to_add:
                try:
                    await conn.execute(text(f"ALTER TABLE {tbl} ADD COLUMN {col} {col_type};"))
                except Exception as col_exc:
                    logger.debug("Column {col} on {tbl} already exists or error: {err}", col=col, tbl=tbl, err=str(col_exc))

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

