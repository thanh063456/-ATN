"""
backend/tests/test_auth.py — Authentication & RBAC Unit / Integration Tests

Tuân thủ AAA Pattern (Arrange - Act - Assert) theo .ai/CODING_RULES.md.
"""
import pytest
import httpx


@pytest.mark.asyncio
async def test_login_success(async_client: httpx.AsyncClient):
    """Kiểm tra đăng nhập thành công với tài khoản STAFF hợp lệ."""
    # ── Arrange ───────────────────────────────────────────────────────────
    payload = {
        "username": "canbo_ctsv",
        "password": "password123",
    }

    # ── Act ───────────────────────────────────────────────────────────────
    response = await async_client.post("/api/v1/auth/login", json=payload)

    # ── Assert ────────────────────────────────────────────────────────────
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["user"]["username"] == "canbo_ctsv"
    assert data["user"]["role_name"] == "STAFF"


@pytest.mark.asyncio
async def test_login_wrong_password(async_client: httpx.AsyncClient):
    """Kiểm tra đăng nhập thất bại khi sai mật khẩu -> 401 Unauthorized."""
    # ── Arrange ───────────────────────────────────────────────────────────
    payload = {
        "username": "canbo_ctsv",
        "password": "incorrect_password_xyz",
    }

    # ── Act ───────────────────────────────────────────────────────────────
    response = await async_client.post("/api/v1/auth/login", json=payload)

    # ── Assert ────────────────────────────────────────────────────────────
    assert response.status_code == 401
    assert "detail" in response.json()


@pytest.mark.asyncio
async def test_get_me_authenticated(async_client: httpx.AsyncClient):
    """Kiểm tra lấy profile người dùng hiện tại khi đã đính kèm Bearer token."""
    # ── Arrange ───────────────────────────────────────────────────────────
    login_res = await async_client.post("/api/v1/auth/login", json={
        "username": "canbo_ctsv",
        "password": "password123",
    })
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # ── Act ───────────────────────────────────────────────────────────────
    response = await async_client.get("/api/v1/auth/me", headers=headers)

    # ── Assert ────────────────────────────────────────────────────────────
    assert response.status_code == 200
    data = response.json()
    assert data["username"] == "canbo_ctsv"
    assert data["role_name"] == "STAFF"


@pytest.mark.asyncio
async def test_get_me_unauthorized(async_client: httpx.AsyncClient):
    """Kiểm tra lấy profile khi không có token -> 401 Unauthorized."""
    # ── Arrange ───────────────────────────────────────────────────────────
    headers = {}

    # ── Act ───────────────────────────────────────────────────────────────
    response = await async_client.get("/api/v1/auth/me", headers=headers)

    # ── Assert ────────────────────────────────────────────────────────────
    assert response.status_code == 401
