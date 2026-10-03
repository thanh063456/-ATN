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


from app.core.database import AsyncSessionLocal
from app.models.users import User
from sqlalchemy import select


@pytest_asyncio.fixture
async def staff_token() -> str:
    """Token dành cho vai trò Cán bộ CTSV (STAFF)."""
    async with AsyncSessionLocal() as session:
        res = await session.execute(select(User).where(User.username == "canbo_ctsv"))
        user = res.scalars().first()
        uid = str(user.id) if user else "50fe2351-becd-4412-931e-44929ced9d63"
    return create_access_token(
        subject=uid,
        extra_claims={"username": "canbo_ctsv", "role": "STAFF", "type": "access"},
    )


@pytest_asyncio.fixture
async def admin_token() -> str:
    """Token dành cho vai trò Quản trị viên (ADMIN)."""
    async with AsyncSessionLocal() as session:
        res = await session.execute(select(User).where(User.username == "admin_hethong"))
        user = res.scalars().first()
        uid = str(user.id) if user else "c45bdb7f-2ffc-48b4-9705-9a7c1aebd9a0"
    return create_access_token(
        subject=uid,
        extra_claims={"username": "admin_hethong", "role": "ADMIN", "type": "access"},
    )


@pytest_asyncio.fixture
async def student_token() -> str:
    """Token dành cho vai trò Sinh viên (STUDENT)."""
    async with AsyncSessionLocal() as session:
        res = await session.execute(select(User).where(User.username == "sinhvien_demo"))
        user = res.scalars().first()
        uid = str(user.id) if user else "a62a05a2-20bc-4d24-ac25-762f08201006"
    return create_access_token(
        subject=uid,
        extra_claims={"username": "sinhvien_demo", "role": "STUDENT", "type": "access"},
    )
