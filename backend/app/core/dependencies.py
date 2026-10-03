"""
backend/app/core/dependencies.py — FastAPI Dependencies for Auth & RBAC

Cung cấp:
- get_current_user: Xác thực token (hỗ trợ cả Supabase Auth JWT lẫn local JWT)
- get_current_user_optional: Xác thực nếu có token, không bắt buộc
- require_roles: RBAC Guard chặn theo vai trò (ADMIN, STAFF, STUDENT)
"""
from typing import Sequence
from uuid import UUID

from fastapi import Depends, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from loguru import logger
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.core.exceptions import AppException
from app.core.security import decode_access_token
from app.core.supabase_client import supabase_admin
from app.models.roles import Role
from app.models.users import User

security_scheme = HTTPBearer(auto_error=False)


async def _resolve_user_from_token(
    token: str, db: AsyncSession
) -> User | None:
    """
    Xác thực token theo 2 cơ chế:
    1. Local JWT token (được tạo bởi FastAPI backend)
    2. Supabase JWT token (được cấp bởi Supabase Auth)
    """
    # 1. Thử giải mã bằng local JWT
    payload = decode_access_token(token)
    if payload and payload.get("sub"):
        try:
            user_id = UUID(payload["sub"])
            stmt = (
                select(User)
                .where(User.id == user_id, User.is_active == True)
                .options(selectinload(User.role))
            )
            res = await db.execute(stmt)
            user = res.scalars().first()
            if user:
                return user
        except ValueError:
            user_id = None

        # Yêu cầu bảo mật: User bắt buộc phải tồn tại trong Database, không tạo mock user từ JWT claim.
        return None

    # 2. Thử xác thực với Supabase Auth
    try:
        supa_res = supabase_admin.auth.get_user(token)
        if supa_res and supa_res.user:
            supa_user = supa_res.user
            supa_uid = str(supa_user.id)
            email = (supa_user.email or "").strip().lower()
            metadata = supa_user.user_metadata or {}

            # Kiểm tra trạng thái xác minh email của Supabase
            email_confirmed = bool(
                getattr(supa_user, "email_confirmed_at", None)
                or getattr(supa_user, "confirmed_at", None)
            )

            # Tìm trong DB: Luôn ưu tiên supabase_uid. Chỉ cho phép match theo email nếu email đã được xác nhận.
            if email_confirmed and email:
                condition = (User.supabase_uid == supa_uid) | (User.email == email)
            else:
                condition = (User.supabase_uid == supa_uid)

            stmt = (
                select(User)
                .where(
                    condition,
                    User.is_active == True,
                )
                .options(selectinload(User.role))
            )
            res = await db.execute(stmt)
            user = res.scalars().first()

            if user:
                # Cập nhật supabase_uid hoặc mssv nếu chưa có
                updated = False
                if not user.supabase_uid and email_confirmed:
                    user.supabase_uid = supa_uid
                    updated = True
                if metadata.get("mssv") and not user.mssv:
                    user.mssv = metadata.get("mssv")
                    updated = True
                if updated:
                    await db.commit()
                return user

            # Nếu user chưa có trong DB (tài khoản vừa tạo qua Supabase), auto-sync vào PostgreSQL
            # Quy tắc bảo mật: User mới đồng bộ từ Supabase LUÔN có role STUDENT.
            # Chỉ ADMIN mới có quyền nâng role qua API quản trị (role lưu trong DB, không tin user_metadata).
            role_res = await db.execute(select(Role).where(Role.name == "STUDENT"))
            student_role = role_res.scalars().first()
            if not student_role:
                student_role = Role(name="STUDENT", description="Sinh viên")
                db.add(student_role)
                await db.flush()

            username = metadata.get("username") or (email.split("@")[0] if email else supa_uid[:8])
            full_name = metadata.get("full_name") or metadata.get("name") or username

            new_user = User(
                supabase_uid=supa_uid,
                username=username,
                email=email,
                full_name=full_name,
                mssv=metadata.get("mssv"),
                hashed_password="",
                role_id=student_role.id,
                is_active=True,
            )
            db.add(new_user)
            await db.commit()

            stmt = (
                select(User)
                .where(User.id == new_user.id)
                .options(selectinload(User.role))
            )
            res = await db.execute(stmt)
            return res.scalars().first()

    except Exception as exc:
        logger.debug("Supabase token verification failed: {err}", err=str(exc))

    return None


async def get_current_user_optional(
    auth: HTTPAuthorizationCredentials | None = Depends(security_scheme),
    db: AsyncSession = Depends(get_db),
) -> User | None:
    """Lấy user hiện tại nếu có header Authorization Bearer."""
    if not auth or not auth.credentials:
        return None
    return await _resolve_user_from_token(auth.credentials, db)


async def get_current_user(
    auth: HTTPAuthorizationCredentials | None = Depends(security_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    """Yêu cầu bắt buộc đăng nhập hợp lệ (hỗ trợ cả Supabase JWT và Backend JWT)."""
    if not auth or not auth.credentials:
        raise AppException(
            message="Vui lòng đăng nhập để thực hiện thao tác này",
            status_code=status.HTTP_401_UNAUTHORIZED,
        )

    user = await _resolve_user_from_token(auth.credentials, db)
    if not user:
        raise AppException(
            message="Phiên đăng nhập không hợp lệ hoặc tài khoản đã bị khóa",
            status_code=status.HTTP_401_UNAUTHORIZED,
        )

    return user


def require_roles(allowed_roles: Sequence[str]):
    """RBAC Guard: Chỉ cho phép các vai trò trong allowed_roles (ADMIN, STAFF, STUDENT)."""
    async def role_checker(current_user: User = Depends(get_current_user)) -> User:
        role_name = current_user.role.name if current_user.role else "STUDENT"
        if role_name not in allowed_roles:
            raise AppException(
                message=f"Bạn không có quyền thực hiện thao tác này (yêu cầu vai trò: {', '.join(allowed_roles)})",
                status_code=status.HTTP_403_FORBIDDEN,
            )
        return current_user

    return role_checker
