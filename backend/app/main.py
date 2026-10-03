"""
backend/app/main.py — FastAPI application entry point
"""
import logging
import re
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from loguru import logger

import uuid
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from app.core.config import settings
from app.core.elasticsearch import init_elasticsearch_index
from app.core.exceptions import AppException
from app.core.rate_limiter import limiter
from app.routers import auth, documents, health, search, stats, verify


# ── Access log token masking ──────────────────────────────────────────────────
class MaskTokenAccessLogFilter(logging.Filter):
    """
    logging.Filter cho logger 'uvicorn.access' để che giấu JWT token trong query parameter.

    Ví dụ:
        /api/v1/documents/41e6f99e/file?token=eyJhbGciOi... -> /api/v1/documents/41e6f99e/file?token=***
        /api/v1/documents/41e6f99e/file?download=1&token=eyJ...&page=1 -> /api/v1/documents/41e6f99e/file?download=1&token=***&page=1

    GHI CHÚ KIẾN TRÚC & BẢO MẬT DÀI HẠN:
    Việc truyền JWT token qua query string (?token=<JWT>) trên URL chỉ nên dùng tạm thời
    cho preview (iframe/img tags). Về lâu dài, dự án nên chuyển sang:
    1. Pre-signed URLs ngắn hạn (Supabase Storage createSignedUrl với TTL 60-300s).
    2. Hoặc Authorization header Bearer token qua fetch/Blob URL.
    """

    TOKEN_REGEX = re.compile(r'([?&]token=)[^&\s"\']+', re.IGNORECASE)

    def filter(self, record: logging.LogRecord) -> bool:
        if record.args:
            if isinstance(record.args, tuple):
                record.args = tuple(
                    self.TOKEN_REGEX.sub(r'\g<1>***', arg) if isinstance(arg, str) else arg
                    for arg in record.args
                )
            elif isinstance(record.args, dict):
                record.args = {
                    k: (self.TOKEN_REGEX.sub(r'\g<1>***', v) if isinstance(v, str) else v)
                    for k, v in record.args.items()
                }
        if isinstance(record.msg, str):
            record.msg = self.TOKEN_REGEX.sub(r'\g<1>***', record.msg)
        return True


def setup_access_log_filter() -> None:
    """Đăng ký MaskTokenAccessLogFilter cho logger uvicorn.access và các handlers của nó."""
    access_filter = MaskTokenAccessLogFilter()
    for logger_name in ("uvicorn.access", "uvicorn"):
        target_logger = logging.getLogger(logger_name)
        if not any(isinstance(f, MaskTokenAccessLogFilter) for f in target_logger.filters):
            target_logger.addFilter(access_filter)
        for handler in target_logger.handlers:
            if not any(isinstance(f, MaskTokenAccessLogFilter) for f in handler.filters):
                handler.addFilter(access_filter)


# Đăng ký filter ngay khi module được import
setup_access_log_filter()


# ── Lifespan ──────────────────────────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Startup và shutdown lifecycle hooks."""
    setup_access_log_filter()
    logger.info("Starting {name} [{env}]", name=settings.app_name, env=settings.app_env)
    # Khởi tạo Database schema và seed data
    from app.core.database import init_db
    try:
        await init_db()
    except Exception as exc:
        logger.warning("Could not initialize database on startup: {err}", err=str(exc))

    # Khởi tạo Elasticsearch index và mapping tiếng Việt nếu chưa tồn tại
    try:
        await init_elasticsearch_index()
    except Exception as exc:
        logger.warning("Could not initialize Elasticsearch on startup: {err}", err=str(exc))
    yield
    logger.info("Shutting down {name}", name=settings.app_name)
    # Dispose async engine để tránh ResourceWarning
    from app.core.database import engine
    await engine.dispose()


# ── App factory ───────────────────────────────────────────────────────────────
def create_app() -> FastAPI:
    app = FastAPI(
        title="Student Document OCR API",
        description=(
            "Hệ thống số hóa và quản lý tài liệu Công tác sinh viên "
            "ứng dụng OCR và Elasticsearch - Đại học Đà Lạt"
        ),
        version="0.1.0",
        docs_url="/docs" if not settings.is_production else None,
        redoc_url="/redoc" if not settings.is_production else None,
        openapi_url="/openapi.json" if not settings.is_production else None,
        lifespan=lifespan,
    )

    ALLOWED_ORIGINS = {
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:8000",
        "http://127.0.0.1:8000",
    }

    # ── CORS ──────────────────────────────────────────────────────────────────
    app.add_middleware(
        CORSMiddleware,
        allow_origins=list(ALLOWED_ORIGINS),
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["*"],
    )

    # ── Rate Limiter ───────────────────────────────────────────────────────────
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

    # ── Global exception handler ───────────────────────────────────────────────
    def _get_safe_cors_headers(request: Request) -> dict[str, str]:
        req_origin = request.headers.get("origin", "")
        origin = req_origin if req_origin in ALLOWED_ORIGINS else "http://localhost:3000"
        return {
            "Access-Control-Allow-Origin": origin,
            "Access-Control-Allow-Credentials": "true",
        }

    @app.exception_handler(AppException)
    async def app_exception_handler(request: Request, exc: AppException) -> JSONResponse:
        logger.warning(
            "AppException: status={status} message={msg} path={path}",
            status=exc.status_code,
            msg=exc.message,
            path=request.url.path,
        )
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": exc.message},
            headers=_get_safe_cors_headers(request),
        )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
        logger.exception(
            "Unhandled exception [request_id={req_id}]: path={path} error={error}",
            req_id=request_id,
            path=request.url.path,
            error=str(exc),
        )
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "detail": "Đã có lỗi hệ thống xảy ra. Vui lòng liên hệ quản trị viên.",
                "request_id": request_id,
            },
            headers=_get_safe_cors_headers(request),
        )

    # ── Routers ───────────────────────────────────────────────────────────────
    API_PREFIX = "/api/v1"

    app.include_router(health.router)                # /health, /health/ping (no prefix)
    app.include_router(auth.router, prefix=API_PREFIX)       # /api/v1/auth
    app.include_router(auth.router)                          # /auth (alias)
    app.include_router(documents.router, prefix=API_PREFIX)  # /api/v1/documents
    app.include_router(documents.router)                     # /documents (alias)
    app.include_router(search.router, prefix=API_PREFIX)     # /api/v1/search
    app.include_router(search.router)                        # /search (alias)
    app.include_router(stats.router, prefix=API_PREFIX)      # /api/v1/stats
    app.include_router(stats.router)                         # /stats (alias)
    app.include_router(verify.router, prefix=API_PREFIX)     # /api/v1/verify
    app.include_router(verify.router)                        # /verify (public alias)

    # ── Root ──────────────────────────────────────────────────────────────────
    @app.get("/", include_in_schema=False)
    async def root() -> dict:
        return {
            "service": settings.app_name,
            "env":     settings.app_env,
            "version": "0.1.0",
            "docs":    "/docs",
            "health":  "/health",
        }

    return app


app = create_app()
