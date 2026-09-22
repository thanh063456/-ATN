"""
backend/app/routers/auth.py — Authentication Router (JWT + Supabase Auth + RBAC)

Cung cấp các endpoints:
- POST /auth/signup: Đăng ký tài khoản (tạo user trên Supabase với auto email_confirm=True & lưu PostgreSQL)
- POST /auth/confirm-user: Tự động xác thực email cho user trên Supabase (giải quyết lỗi Email not confirmed)
- POST /auth/register: Đồng bộ hồ sơ người dùng từ Supabase Auth vào PostgreSQL (kèm MSSV)
- GET /auth/me: Lấy thông tin tài khoản hiện tại kèm vai trò và MSSV
- POST /auth/login: Đăng nhập trực tiếp (backward-compatible)
"""
from datetime import datetime, timedelta, timezone
from uuid import UUID

from fastapi import APIRouter, Depends, status
from loguru import logger
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.config import settings
from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.core.exceptions import AppException
from app.core.security import create_access_token, get_password_hash, verify_password
from app.core.supabase_client import supabase_admin
from app.models.roles import Role
from app.models.users import User
from app.schemas.auth import (
    ConfirmEmailRequest,
    LoginRequest,
    RegisterRequest,
    SignupRequest,
    TokenResponse,
    UserResponse,
)

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/signup", response_model=UserResponse, summary="Đăng ký tài khoản với Supabase Auto-confirm")
async def signup(req: SignupRequest, db: AsyncSession = Depends(get_db)) -> UserResponse:
    """
    Tạo tài khoản sinh viên qua Supabase Admin API với `email_confirm: True`.
    Người dùng có thể đăng nhập ngay mà không bị chặn bởi lỗi 'Email not confirmed'.
    """
    # 1. Kiểm tra đuôi email
    email_clean = req.email.strip().lower()
    if not email_clean.endswith("@dlu.edu.vn"):
        raise AppException(
            message="Chỉ email đuôi @dlu.edu.vn mới được phép tạo tài khoản",
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    # 2. Tạo hoặc cập nhật user trên Supabase Auth
    supabase_uid: str | None = None
    try:
        supa_user_res = supabase_admin.auth.admin.create_user({
            "email": email_clean,
            "password": req.password,
            "email_confirm": True,
            "user_metadata": {
                "full_name": req.full_name,
                "mssv": req.mssv or (email_clean.split("@")[0] if email_clean.split("@")[0].isdigit() else None),
                "role": "STUDENT",
            },
        })
        if supa_user_res and supa_user_res.user:
            supabase_uid = str(supa_user_res.user.id)
    except Exception as exc:
        logger.warning("Supabase create user error (might already exist): {err}", err=str(exc))

    # 3. Lưu vào Database
    stmt = (
        select(User)
        .where(User.email == email_clean)
        .options(selectinload(User.role))
    )
    res = await db.execute(stmt)
    user = res.scalars().first()

    mssv = req.mssv or (email_clean.split("@")[0] if email_clean.split("@")[0].isdigit() else None)

    if user:
        user.full_name = req.full_name
        user.hashed_password = get_password_hash(req.password)
        if mssv:
            user.mssv = mssv
        if supabase_uid:
            user.supabase_uid = supabase_uid
        await db.commit()
        await db.refresh(user)
    else:
        role_res = await db.execute(select(Role).where(Role.name == "STUDENT"))
        student_role = role_res.scalars().first()
        if not student_role:
            student_role = Role(name="STUDENT", description="Sinh viên")
            db.add(student_role)
            await db.flush()

        username = email_clean.split("@")[0]
        user = User(
            supabase_uid=supabase_uid,
            username=username,
            email=email_clean,
            full_name=req.full_name,
            mssv=mssv,
            hashed_password=get_password_hash(req.password),
            role_id=student_role.id,
            is_active=True,
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)

    stmt = select(User).where(User.id == user.id).options(selectinload(User.role))
    res = await db.execute(stmt)
    user = res.scalars().first()
    role_name = user.role.name if user.role else "STUDENT"

    return UserResponse(
        id=user.id,
        supabase_uid=user.supabase_uid,
        username=user.username,
        email=user.email,
        full_name=user.full_name,
        mssv=user.mssv,
        role_name=role_name,
        is_active=user.is_active,
        created_at=user.created_at,
    )


@router.post("/confirm-user", summary="Tự động xác nhận email cho người dùng trên Supabase")
async def confirm_user(req: ConfirmEmailRequest) -> dict:
    """
    Tự động kích hoạt email_confirm cho tài khoản trên Supabase nếu bị kẹt trạng thái 'Email not confirmed'.
    """
    email_clean = req.email.strip().lower()
    try:
        users_list = supabase_admin.auth.admin.list_users()
        target_user = next((u for u in users_list if u.email and u.email.lower() == email_clean), None)
        if target_user:
            supabase_admin.auth.admin.update_user_by_id(str(target_user.id), {"email_confirm": True})
            logger.info("Auto-confirmed user email in Supabase: {email}", email=email_clean)
            return {"success": True, "message": f"Tài khoản {email_clean} đã được kích hoạt email xác nhận."}
        else:
            return {"success": False, "message": "Không tìm thấy tài khoản với email này trên hệ thống Auth."}
    except Exception as exc:
        logger.error("Auto confirm failed: {err}", err=str(exc))
        return {"success": False, "message": str(exc)}


@router.post("/register", response_model=UserResponse, summary="Đồng bộ hồ sơ tài khoản sau khi đăng ký Supabase")
async def register(req: RegisterRequest, db: AsyncSession = Depends(get_db)) -> UserResponse:
    """
    Đồng bộ thông tin profile (MSSV, tên, email) vào PostgreSQL.
    """
    if not req.email.lower().endswith("@dlu.edu.vn"):
        raise AppException(
            message="Chỉ email đuôi @dlu.edu.vn mới được phép tạo tài khoản",
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    stmt = (
        select(User)
        .where((User.supabase_uid == req.supabase_uid) | (User.email == req.email))
        .options(selectinload(User.role))
    )
    res = await db.execute(stmt)
    user = res.scalars().first()

    if user:
        user.supabase_uid = req.supabase_uid
        user.full_name = req.full_name
        if req.mssv:
            user.mssv = req.mssv
        await db.commit()
        await db.refresh(user)
    else:
        role_res = await db.execute(select(Role).where(Role.name == "STUDENT"))
        student_role = role_res.scalars().first()
        if not student_role:
            student_role = Role(name="STUDENT", description="Sinh viên")
            db.add(student_role)
            await db.flush()

        username = req.email.split("@")[0]
        u_check = await db.execute(select(User).where(User.username == username))
        if u_check.scalars().first():
            username = f"{username}_{req.supabase_uid[:6]}"

        user = User(
            supabase_uid=req.supabase_uid,
            username=username,
            email=req.email,
            full_name=req.full_name,
            mssv=req.mssv,
            hashed_password="",
            role_id=student_role.id,
            is_active=True,
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)

        stmt = select(User).where(User.id == user.id).options(selectinload(User.role))
        res = await db.execute(stmt)
        user = res.scalars().first()

    role_name = user.role.name if user.role else "STUDENT"
    return UserResponse(
        id=user.id,
        supabase_uid=user.supabase_uid,
        username=user.username,
        email=user.email,
        full_name=user.full_name,
        mssv=user.mssv,
        role_name=role_name,
        is_active=user.is_active,
        created_at=user.created_at,
    )


@router.post("/login", response_model=TokenResponse, summary="Đăng nhập nhận JWT access token (Direct)")
async def login(req: LoginRequest, db: AsyncSession = Depends(get_db)) -> TokenResponse:
    """Xác thực người dùng (bằng username hoặc email) và cấp phát JWT token."""
    login_identifier = req.username.strip().lower()
    prefix = login_identifier.split("@")[0]

    # Hỗ trợ tìm kiếm linh hoạt theo email, username, mssv và bí danh
    match_targets = {login_identifier, prefix}
    if login_identifier in ("canbo@dlu.edu.vn", "canbo_ctsv@dlu.edu.vn", "canbo", "canbo_ctsv"):
        match_targets.update({"canbo@dlu.edu.vn", "canbo_ctsv@dlu.edu.vn", "canbo", "canbo_ctsv"})
    if login_identifier in ("admin@dlu.edu.vn", "admin_hethong@dlu.edu.vn", "admin", "admin_hethong"):
        match_targets.update({"admin@dlu.edu.vn", "admin_hethong@dlu.edu.vn", "admin", "admin_hethong"})

    stmt = (
        select(User)
        .where(
            (User.username.in_(match_targets))
            | (User.email.in_(match_targets))
            | (User.mssv.in_(match_targets))
        )
        .options(selectinload(User.role))
    )
    res = await db.execute(stmt)
    user = res.scalars().first()

    # Nếu chưa có password hash (user tạo từ Supabase Auth), hỗ trợ cập nhật hoặc kiểm tra
    if user and not user.hashed_password and req.password:
        user.hashed_password = get_password_hash(req.password)
        await db.commit()

    if not user or not verify_password(req.password, user.hashed_password):
        raise AppException(
            message="Tên đăng nhập / email hoặc mật khẩu không chính xác",
            status_code=status.HTTP_401_UNAUTHORIZED,
        )

    if not user.is_active:
        raise AppException(
            message="Tài khoản này đã bị khóa, vui lòng liên hệ quản trị viên",
            status_code=status.HTTP_403_FORBIDDEN,
        )

    user.last_login_at = datetime.now(timezone.utc)
    await db.commit()

    role_name = user.role.name if user.role else "STUDENT"
    access_token = create_access_token(
        subject=str(user.id),
        extra_claims={"username": user.username, "role": role_name, "mssv": user.mssv},
        expires_delta=timedelta(minutes=settings.jwt_access_token_expire_minutes),
    )

    user_resp = UserResponse(
        id=user.id,
        supabase_uid=user.supabase_uid,
        username=user.username,
        email=user.email,
        full_name=user.full_name,
        mssv=user.mssv,
        role_name=role_name,
        is_active=user.is_active,
        created_at=user.created_at,
    )

    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        expires_in=settings.jwt_access_token_expire_minutes * 60,
        user=user_resp,
    )


@router.get("/me", response_model=UserResponse, summary="Lấy thông tin người dùng đang đăng nhập")
async def get_me(current_user: User = Depends(get_current_user)) -> UserResponse:
    """Trả về thông tin chi tiết của user từ JWT Bearer token."""
    role_name = current_user.role.name if current_user.role else "STUDENT"
    return UserResponse(
        id=current_user.id,
        supabase_uid=current_user.supabase_uid,
        username=current_user.username,
        email=current_user.email,
        full_name=current_user.full_name,
        mssv=current_user.mssv,
        role_name=role_name,
        is_active=current_user.is_active,
        created_at=current_user.created_at,
    )
