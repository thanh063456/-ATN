"""
backend/tests/test_p1_database_reliability.py — Tests proving P1 Database Reliability fix (Item 13)

Verifies:
13. database.py:
    - Fallback SQLite only allowed when app_env == "development".
    - In staging/production, when PostgreSQL connection fails, app raises RuntimeError (fail-fast)
      and strictly refuses to fallback to SQLite.
    - In staging/production, configuring SQLite URL raises RuntimeError.
"""
import pytest
from unittest.mock import patch
from app.core.config import Settings
import app.core.database as db_module


@pytest.mark.asyncio
async def test_p1_13_production_fails_fast_on_postgres_failure():
    """13. Ở môi trường production/staging, nếu PostgreSQL lỗi thì raise exception ngay, không fallback SQLite."""
    prod_settings = Settings(
        app_env="production",
        database_url="postgresql+asyncpg://invalid_user:invalid_pass@127.0.0.1:59999/invalid_db",
        jwt_secret_key="a" * 32,
        app_secret_key="b" * 32,
        supabase_url="https://test.supabase.co",
        supabase_service_role_key="c" * 32,
    )

    with patch.object(db_module, "settings", prod_settings):
        with pytest.raises(RuntimeError) as exc_info:
            await db_module.init_db()

        assert "Không thể kết nối cơ sở dữ liệu PostgreSQL" in str(exc_info.value)
        assert "production" in str(exc_info.value)


@pytest.mark.asyncio
async def test_p1_13_production_rejects_sqlite_url():
    """13. Ở môi trường production/staging, cấu hình SQLite URL bị từ chối khởi động."""
    prod_settings = Settings(
        app_env="production",
        database_url="sqlite+aiosqlite:///local_data.db",
        jwt_secret_key="a" * 32,
        app_secret_key="b" * 32,
        supabase_url="https://test.supabase.co",
        supabase_service_role_key="c" * 32,
    )

    with patch.object(db_module, "settings", prod_settings):
        with pytest.raises(RuntimeError) as exc_info:
            await db_module.init_db()

        assert "Chỉ cho phép sử dụng SQLite ở môi trường development" in str(exc_info.value)
