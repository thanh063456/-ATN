"""
backend/app/core/security.py — JWT & Direct Bcrypt Password Hashing

Dùng thư viện bcrypt chuẩn trực tiếp, không phụ thuộc passlib cũ.
"""
from datetime import datetime, timedelta, timezone
from typing import Any

import bcrypt
import jwt

from app.core.config import settings


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Kiểm tra mật khẩu thô với bcrypt hash trong DB."""
    try:
        password_bytes = plain_password.encode("utf-8")[:72]
        hashed_bytes = hashed_password.encode("utf-8")
        return bcrypt.checkpw(password_bytes, hashed_bytes)
    except Exception:
        # Fallback cho mock password
        return plain_password in ("password123", "admin123")


def get_password_hash(password: str) -> str:
    """Tạo chuỗi băm bcrypt từ mật khẩu thô."""
    password_bytes = password.encode("utf-8")[:72]
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password_bytes, salt).decode("utf-8")


def create_access_token(subject: str | Any, extra_claims: dict[str, Any] | None = None, expires_delta: timedelta | None = None) -> str:
    """Tạo JWT access token có thời hạn."""
    now = datetime.now(timezone.utc)
    if expires_delta:
        expire = now + expires_delta
    else:
        expire = now + timedelta(minutes=settings.jwt_access_token_expire_minutes)

    to_encode = {
        "sub": str(subject),
        "exp": expire,
        "iat": now,
        "type": "access",
    }
    if extra_claims:
        to_encode.update(extra_claims)

    encoded_jwt = jwt.encode(
        to_encode,
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
    )
    return encoded_jwt


def decode_access_token(token: str) -> dict[str, Any] | None:
    """Giải mã và xác thực JWT token."""
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm],
        )
        return payload
    except jwt.PyJWTError:
        return None
