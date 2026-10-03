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
            if settings.app_env != "development":
                logger.critical(
                    "PostgreSQL connection failed in environment '{env}': {err}. Refusing SQLite fallback in non-development.",
                    env=settings.app_env,
                    err=str(exc),
                )
                raise RuntimeError(
                    f"Không thể kết nối cơ sở dữ liệu PostgreSQL trong môi trường '{settings.app_env}': {str(exc)}"
                ) from exc

            logger.warning(
                "PostgreSQL connection failed ({err}). Using SQLite local DB: {path}",
                err=str(exc), path=str(SQLITE_DB_PATH)
            )
            engine = create_async_engine(SQLITE_URL, echo=False)
            AsyncSessionLocal.configure(bind=engine)
    else:
        if settings.app_env != "development":
            logger.critical("SQLite database is not allowed in environment '{env}'.", env=settings.app_env)
            raise RuntimeError(
                f"Chỉ cho phép sử dụng SQLite ở môi trường development. Môi trường hiện tại: {settings.app_env}"
            )
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
            {"table": "documents", "column": "is_public", "type": "BOOLEAN DEFAULT FALSE"},
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
                # Ensure roles exist
                role_map = {}
                for r_name, r_desc in [("ADMIN", "Quản trị viên hệ thống"), ("STAFF", "Cán bộ CTSV"), ("STUDENT", "Sinh viên")]:
                    r_check = await session.execute(select(Role).where(Role.name == r_name))
                    role_obj = r_check.scalars().first()
                    if not role_obj:
                        role_obj = Role(name=r_name, description=r_desc)
                        session.add(role_obj)
                        await session.flush()
                    role_map[r_name] = role_obj

                # Yêu cầu bảo mật: User mặc định chỉ được seed ở môi trường development.
                # Mật khẩu được đọc từ cấu hình (seed_admin_password, seed_staff_password...), không hardcode.
                if settings.app_env == "development":
                    user_configs = [
                        ("admin_hethong", "admin@dlu.edu.vn", settings.seed_admin_password, "Quản trị viên Hệ thống (DLU)", "ADMIN", None),
                        ("canbo_ctsv", "canbo@dlu.edu.vn", settings.seed_staff_password, "Cán bộ CTSV (STAFF)", "STAFF", None),
                        ("sinhvien_demo", "sinhvien@dlu.edu.vn", settings.seed_student_password, "Sinh Viên Mẫu (DLU)", "STUDENT", "2210001"),
                    ]
                    for uname, email, pwd, fname, rname, mssv in user_configs:
                        u_check = await session.execute(select(User).where((User.username == uname) | (User.email == email)))
                        if not u_check.scalars().first():
                            u_obj = User(
                                username=uname,
                                email=email,
                                hashed_password=get_password_hash(pwd),
                                full_name=fname,
                                role_id=role_map[rname].id,
                                mssv=mssv,
                                is_active=True,
                            )
                            session.add(u_obj)
                    await session.commit()
                    logger.info("Database ensured default roles and development demo users.")
                else:
                    await session.commit()
                    logger.info("Database initialized default roles for production/staging (no demo users seeded).")
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

