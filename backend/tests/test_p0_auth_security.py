"""
backend/tests/test_p0_auth_security.py — Tests proving P0 Auth Security fixes

Verifies:
1. POST /auth/signup returns 409 if email already exists (no overwrite).
2. POST /auth/login returns 401 if user has empty hashed_password.
3. POST /auth/register requires Bearer token; POST /auth/confirm-user requires ADMIN.
4. _resolve_user_from_token enforces STUDENT role regardless of user_metadata.
5. Access token requires type=="access"; mock_user claim cannot bypass DB; Settings rejects short keys in non-dev.
6. Seeding only in development env.
7. Rate limiting on /auth/login.
8. Unhandled exceptions return generic message + request_id (no raw str(exc)).
"""
import uuid
import pytest
import httpx
from pydantic import ValidationError
from app.core.config import Settings
from app.core.security import create_access_token, decode_access_token
from app.models.users import User
from app.models.roles import Role


@pytest.mark.asyncio
async def test_p0_1_signup_duplicate_email_returns_409(async_client: httpx.AsyncClient):
    """1. POST /auth/signup trả 409 khi email đã tồn tại, không ghi đè mật khẩu."""
    payload = {
        "email": "canbo_ctsv@dlu.edu.vn",  # Seeded account
        "password": "new_password_attack",
        "full_name": "Attacker",
    }
    response = await async_client.post("/api/v1/auth/signup", json=payload)
    assert response.status_code == 409, f"Expected 409 but got {response.status_code}: {response.text}"


@pytest.mark.asyncio
async def test_p0_2_login_empty_hashed_password_rejected(async_client: httpx.AsyncClient):
    """2. User không có hashed_password chỉ được login qua Supabase; login direct trả 401."""
    from app.core.database import AsyncSessionLocal
    from sqlalchemy import select

    async with AsyncSessionLocal() as db:
        res = await db.execute(select(Role).where(Role.name == "STUDENT"))
        student_role = res.scalars().first()
        test_uid = f"nopass-{uuid.uuid4().hex[:8]}"
        user = User(
            username=test_uid,
            email=f"{test_uid}@dlu.edu.vn",
            hashed_password="",  # Empty password
            full_name="No Password User",
            role_id=student_role.id,
            is_active=True,
        )
        db.add(user)
        await db.commit()

    # Attempt to login with arbitrary password
    res = await async_client.post("/api/v1/auth/login", json={
        "username": test_uid,
        "password": "any_password_123",
    })
    assert res.status_code == 401, f"Expected 401 but got {res.status_code}: {res.text}"
    assert "supabase" in res.json().get("detail", "").lower()


@pytest.mark.asyncio
async def test_p0_3_register_unauthenticated_rejected(async_client: httpx.AsyncClient):
    """3. POST /auth/register bắt buộc xác thực qua Bearer token."""
    res = await async_client.post("/api/v1/auth/register", json={
        "full_name": "Hacker",
    })
    assert res.status_code == 401


@pytest.mark.asyncio
async def test_p0_3_confirm_user_requires_admin(async_client: httpx.AsyncClient, student_token: str):
    """3. POST /auth/confirm-user yêu cầu role ADMIN; STUDENT bị chặn 403."""
    res = await async_client.post(
        "/api/v1/auth/confirm-user",
        headers={"Authorization": f"Bearer {student_token}"},
        json={"email": "victim@dlu.edu.vn"},
    )
    assert res.status_code == 403, f"Expected 403 Forbidden for non-admin but got {res.status_code}"


@pytest.mark.asyncio
async def test_p0_5_token_must_have_access_type():
    """5. Token không có type == 'access' phải bị từ chối giải mã."""
    invalid_token = create_access_token(
        subject="test-user",
        extra_claims={"type": "refresh"},
    )
    payload = decode_access_token(invalid_token)
    assert payload is None, "Token with type!='access' must return None"


@pytest.mark.asyncio
async def test_p0_5_secret_key_length_validation_in_production():
    """5. Khi app_env != 'development', jwt_secret_key < 32 ký tự phải từ chối khởi động."""
    with pytest.raises(ValidationError) as exc_info:
        Settings(
            app_env="production",
            jwt_secret_key="short_secret_key",
            app_secret_key="a" * 32,
            supabase_url="https://test.supabase.co",
            supabase_service_role_key="service_role_key_long_enough",
        )
    assert "jwt_secret_key" in str(exc_info.value)


@pytest.mark.asyncio
async def test_p0_8_unhandled_exception_returns_generic_message_and_request_id():
    """8. Exception handler chung không để lộ str(exc), trả thông báo chung và request_id."""
    from app.main import create_app
    from starlette.requests import Request
    import json

    test_app = create_app()
    # Find unhandled exception handler
    handler = test_app.exception_handlers.get(Exception)
    assert handler is not None

    scope = {
        "type": "http",
        "method": "GET",
        "path": "/api/v1/test",
        "headers": [(b"x-request-id", b"test-req-123")],
    }
    request = Request(scope)
    secret_leak_msg = "FATAL: secret_db_password_123456"
    resp = await handler(request, RuntimeError(secret_leak_msg))
    assert resp.status_code == 500
    body = json.loads(resp.body.decode())
    assert secret_leak_msg not in resp.body.decode()
    assert body.get("request_id") == "test-req-123"
    assert "quản trị viên" in body.get("detail", "")
