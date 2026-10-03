"""
backend/app/routers/auth.py — Authentication Router (JWT + Supabase Auth + RBAC)

Cung cấp các endpoints:
- POST /auth/signup: Đăng ký tài khoản (tạo user trên Supabase với auto email_confirm=True & lưu PostgreSQL)
- POST /auth/confirm-user: Tự động xác thực email cho user trên Supabase (giải quyết lỗi Email not confirmed)
- POST /auth/register: Đồng bộ hồ sơ người dùng từ Supabase Auth vào PostgreSQL (kèm MSSV)
- GET /auth/me: Lấy thông tin tài khoản hiện tại kèm vai trò và MSSV
- POST /auth/login: Đăng nhập trực tiếp (backward-compatible)
"""
import uuid
from datetime import datetime, timedelta, timezone
from uuid import UUID

from fastapi import APIRouter, Depends, Request, status
from fastapi.security import HTTPAuthorizationCredentials
from loguru import logger
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.config import settings
from app.core.database import get_db
from app.core.dependencies import get_current_user, require_roles, security_scheme
from app.core.exceptions import AppException
from app.core.rate_limiter import limiter
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
@limiter.limit("5/minute")
async def signup(request: Request, req: SignupRequest, db: AsyncSession = Depends(get_db)) -> UserResponse:
    """
    Tạo tài khoản sinh viên qua Supabase Admin API với `email_confirm: True`.
    Quy tắc bảo mật: Nếu email đã tồn tại thì KHÔNG được ghi đè, trả về 409 Conflict.
    """
    # 1. Kiểm tra đuôi email
    email_clean = req.email.strip().lower()
    if not email_clean.endswith("@dlu.edu.vn"):
        raise AppException(
            message="Chỉ email đuôi @dlu.edu.vn mới được phép tạo tài khoản",
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    # 2. Kiểm tra tài khoản đã tồn tại trong DB chưa -> Không ghi đè, trả 409 Conflict
    stmt = (
        select(User)
        .where(User.email == email_clean)
        .options(selectinload(User.role))
    )
    res = await db.execute(stmt)
    existing_user = res.scalars().first()
    if existing_user:
        raise AppException(
            message="Email này đã được đăng ký tài khoản. Vui lòng đăng nhập.",
            status_code=status.HTTP_409_CONFLICT,
        )

    # 3. Tạo user trên Supabase Auth
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
        logger.warning("Supabase create user notice: {err}", err=str(exc))

    # 4. Tạo mới trong PostgreSQL (luôn là role STUDENT)
    role_res = await db.execute(select(Role).where(Role.name == "STUDENT"))
    student_role = role_res.scalars().first()
    if not student_role:
        student_role = Role(name="STUDENT", description="Sinh viên")
        db.add(student_role)
        await db.flush()

    username = email_clean.split("@")[0]
    mssv = req.mssv or (username if username.isdigit() else None)

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


@router.post("/confirm-user", summary="Xác nhận email cho người dùng trên Supabase (Yêu cầu ADMIN)")
async def confirm_user(
    req: ConfirmEmailRequest,
    request: Request,
    current_user: User = Depends(require_roles("ADMIN")),
) -> dict:
    """
    Kích hoạt email_confirm cho tài khoản trên Supabase (yêu cầu quyền ADMIN).
    Không để lộ chi tiết ngoại lệ ra client.
    """
    email_clean = req.email.strip().lower()
    request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
    try:
        users_list = supabase_admin.auth.admin.list_users()
        target_user = next((u for u in users_list if u.email and u.email.lower() == email_clean), None)
        if target_user:
            supabase_admin.auth.admin.update_user_by_id(str(target_user.id), {"email_confirm": True})
            logger.info("Admin {admin} confirmed user email: {email} [req_id={req_id}]",
                        admin=current_user.username, email=email_clean, req_id=request_id)
            return {"success": True, "message": f"Tài khoản {email_clean} đã được kích hoạt email xác nhận."}
        else:
            return {"success": False, "message": "Không tìm thấy tài khoản với email này trên hệ thống Auth."}
    except Exception as exc:
        logger.error("Admin confirm user failed [req_id={req_id}]: {err}", req_id=request_id, err=str(exc))
        return {
            "success": False,
            "message": "Không thể xác nhận tài khoản do lỗi hệ thống.",
            "request_id": request_id,
        }


@router.post("/register", response_model=UserResponse, summary="Đồng bộ hồ sơ tài khoản sau khi đăng ký Supabase")
async def register(
    req: RegisterRequest,
    credentials: HTTPAuthorizationCredentials | None = Depends(security_scheme),
    db: AsyncSession = Depends(get_db),
) -> UserResponse:
    """
    Đồng bộ thông tin profile vào PostgreSQL.
    Bắt buộc xác thực: Lấy supabase_uid và email trực tiếp từ Supabase JWT đã xác thực,
    không tin cậy dữ liệu truyền lên từ body.
    """
    if not credentials or not credentials.credentials:
        raise AppException(
            message="Yêu cầu Bearer token xác thực để đồng bộ tài khoản",
            status_code=status.HTTP_401_UNAUTHORIZED,
        )

    try:
        supa_res = supabase_admin.auth.get_user(credentials.credentials)
    except Exception as exc:
        logger.warning("Supabase token verification failed in /register: {err}", err=str(exc))
        raise AppException(
            message="Token xác thực không hợp lệ hoặc đã hết hạn",
            status_code=status.HTTP_401_UNAUTHORIZED,
        )

    if not supa_res or not supa_res.user:
        raise AppException(
            message="Token không hợp lệ hoặc không tìm thấy user trên Supabase",
            status_code=status.HTTP_401_UNAUTHORIZED,
        )

    supa_user = supa_res.user
    token_uid = str(supa_user.id)
    token_email = (supa_user.email or "").strip().lower()

    if not token_email.endswith("@dlu.edu.vn"):
        raise AppException(
            message="Chỉ email đuôi @dlu.edu.vn mới được phép đồng bộ tài khoản",
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    email_confirmed = bool(
        getattr(supa_user, "email_confirmed_at", None)
        or getattr(supa_user, "confirmed_at", None)
    )

    # Tìm user trong DB theo token_uid; chỉ match theo email nếu email đã được Supabase xác nhận
    if email_confirmed:
        condition = (User.supabase_uid == token_uid) | (User.email == token_email)
    else:
        condition = (User.supabase_uid == token_uid)

    stmt = select(User).where(condition).options(selectinload(User.role))
    res = await db.execute(stmt)
    user = res.scalars().first()

    if user:
        user.supabase_uid = token_uid
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

        username = token_email.split("@")[0]
        u_check = await db.execute(select(User).where(User.username == username))
        if u_check.scalars().first():
            username = f"{username}_{token_uid[:6]}"

        user = User(
            supabase_uid=token_uid,
            username=username,
            email=token_email,
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
@limiter.limit("5/minute")
async def login(request: Request, req: LoginRequest, db: AsyncSession = Depends(get_db)) -> TokenResponse:
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

    # Yêu cầu bảo mật: User không có hashed_password chỉ được đăng nhập qua Supabase Auth; trả 401.
    if not user or not user.hashed_password:
        raise AppException(
            message="Tài khoản chưa thiết lập mật khẩu trực tiếp hoặc không tồn tại. Vui lòng đăng nhập qua Supabase Auth.",
            status_code=status.HTTP_401_UNAUTHORIZED,
        )

    if not verify_password(req.password, user.hashed_password):
        raise AppException(
            message="Tên đăng nhập / email hoặc mật khẩu không chính xác",
            status_code=status.HTTP_401_UNAUTHORIZED,
        )

    if not user.is_active:
        raise AppException(
            message="Tài khoản này đã bị khóa, vui lòng liên hệ quản trị viên",
            status_code=status.HTTP_403_FORBIDDEN,
        )

    user.last_login_at = datetime.now()
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
