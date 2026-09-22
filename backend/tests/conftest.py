"""
backend/tests/conftest.py — Pytest Fixtures & Test Setup
"""
import pytest
import pytest_asyncio
import httpx
from app.core.security import create_access_token


from httpx import ASGITransport
from app.main import create_app


@pytest_asyncio.fixture
async def async_client() -> httpx.AsyncClient:
    """Async test client kết nối trực tiếp app FastAPI in-memory."""
    from app.core.database import init_db
    await init_db()
    app = create_app()
    transport = ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
        yield client


@pytest_asyncio.fixture
def staff_token() -> str:
    """Token dành cho vai trò Cán bộ CTSV (STAFF)."""
    return create_access_token(
        subject="50fe2351-becd-4412-931e-44929ced9d63",
        extra_claims={"username": "canbo_ctsv", "role": "STAFF"},
    )


@pytest_asyncio.fixture
def admin_token() -> str:
    """Token dành cho vai trò Quản trị viên (ADMIN)."""
    return create_access_token(
        subject="c45bdb7f-2ffc-48b4-9705-9a7c1aebd9a0",
        extra_claims={"username": "admin_hethong", "role": "ADMIN"},
    )


@pytest_asyncio.fixture
def student_token() -> str:
    """Token dành cho vai trò Sinh viên (STUDENT)."""
    return create_access_token(
        subject="a62a05a2-20bc-4d24-ac25-762f08201006",
        extra_claims={"username": "20210678", "role": "STUDENT"},
    )
