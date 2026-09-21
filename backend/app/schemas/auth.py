"""
backend/app/schemas/auth.py — Pydantic Schemas for Authentication & User Roles
"""
from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field


class SignupRequest(BaseModel):
    """Payload đăng ký tài khoản mới (tạo trực tiếp có auto-confirm email)."""
    email: str
    password: str
    full_name: str
    mssv: str | None = Field(None, description="Mã số sinh viên (STUDENT only)")


class ConfirmEmailRequest(BaseModel):
    """Yêu cầu xác nhận email thủ công hoặc tự động."""
    email: str


class RegisterRequest(BaseModel):
    """Payload từ frontend sau khi Supabase Auth signup thành công."""
    supabase_uid: str = Field(..., description="Supabase auth.users.id")
    email: str
    full_name: str
    mssv: str | None = Field(None, description="Mã số sinh viên (STUDENT only)")
    access_token: str = Field(..., description="Supabase JWT để xác minh")


class LoginRequest(BaseModel):
    """Kept for backward compat — dùng khi test với username/password trực tiếp."""
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user: "UserResponse"


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    supabase_uid: str | None = None
    username: str
    email: str
    full_name: str
    mssv: str | None = None
    role_name: str
    is_active: bool
    created_at: datetime
