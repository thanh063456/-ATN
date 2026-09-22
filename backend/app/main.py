"""
backend/app/main.py — FastAPI application entry point
"""
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from loguru import logger

from app.core.config import settings
from app.core.elasticsearch import init_elasticsearch_index
from app.core.exceptions import AppException
from app.routers import auth, documents, health, search, stats, verify


# ── Lifespan ──────────────────────────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Startup và shutdown lifecycle hooks."""
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
        logger.exception(
            "Unhandled exception: path={path} error={error}",
            path=request.url.path,
            error=str(exc),
        )
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"detail": "Lỗi hệ thống: " + str(exc)},
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
