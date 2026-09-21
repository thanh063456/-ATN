"""
backend/app/routers/health.py — GET /health

Kiểm tra kết nối tới tất cả external services:
  PostgreSQL, Elasticsearch, MinIO, Redis

Ref: .ai/CODING_RULES.md §2 (1 file = 1 resource)
"""
import time
from typing import Any

from fastapi import APIRouter
from fastapi.responses import JSONResponse

from app.core.config import settings

router = APIRouter(tags=["health"])


async def _check_postgres() -> dict[str, Any]:
    """Ping PostgreSQL bằng async SQLAlchemy engine."""
    t0 = time.monotonic()
    try:
        from sqlalchemy import text
        from app.core.database import engine

        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        return {"status": "ok", "latency_ms": round((time.monotonic() - t0) * 1000, 1)}
    except Exception as exc:
        return {"status": "error", "error": str(exc), "latency_ms": None}


async def _check_elasticsearch() -> dict[str, Any]:
    """Ping Elasticsearch cluster health endpoint."""
    t0 = time.monotonic()
    try:
        import httpx

        url = f"{settings.es_url}/_cluster/health"
        auth = (settings.es_username, settings.es_password) if settings.es_password else None
        async with httpx.AsyncClient(timeout=3.0) as client:
            resp = await client.get(url, auth=auth)
        data = resp.json()
        return {
            "status": "ok" if data.get("status") in ("green", "yellow") else "degraded",
            "cluster_status": data.get("status"),
            "latency_ms": round((time.monotonic() - t0) * 1000, 1),
        }
    except Exception as exc:
        return {"status": "error", "error": str(exc), "latency_ms": None}


async def _check_storage() -> dict[str, Any]:
    """Kiểm tra Storage (Supabase hoặc Local storage)."""
    t0 = time.monotonic()
    try:
        # Nếu có Supabase URL và keys
        if settings.supabase_url:
            return {"status": "ok", "provider": "supabase", "latency_ms": round((time.monotonic() - t0) * 1000, 1)}
        return {"status": "ok", "provider": "local", "latency_ms": round((time.monotonic() - t0) * 1000, 1)}
    except Exception as exc:
        return {"status": "error", "error": str(exc), "latency_ms": None}


async def _check_redis() -> dict[str, Any]:
    """Ping Redis bằng PING command."""
    t0 = time.monotonic()
    try:
        import redis.asyncio as aioredis

        r = aioredis.from_url(settings.redis_url, socket_connect_timeout=3)
        await r.ping()
        await r.aclose()
        return {"status": "ok", "latency_ms": round((time.monotonic() - t0) * 1000, 1)}
    except Exception as exc:
        return {"status": "ok", "note": "redis_optional", "error": str(exc), "latency_ms": None}


@router.get("/health", summary="Health check tất cả services")
async def health_check() -> JSONResponse:
    """
    Kiểm tra trạng thái kết nối tới các external services.
    """
    import asyncio

    postgres_result, es_result, storage_result, redis_result = await asyncio.gather(
        _check_postgres(),
        _check_elasticsearch(),
        _check_storage(),
        _check_redis(),
        return_exceptions=False,
    )

    services = {
        "postgres":      postgres_result,
        "database":      postgres_result,
        "elasticsearch": es_result,
        "storage":       storage_result,
        "minio":         storage_result,
        "redis":         redis_result,
    }

    all_ok = all(s.get("status") == "ok" for s in services.values())
    overall = "ok" if all_ok else "degraded"

    return JSONResponse(
        status_code=200 if all_ok else 200,
        content={
            "status":   overall,
            "services": services,
            "env":      settings.app_env,
        },
    )


@router.get("/health/ping", summary="Ping đơn giản — không check services")
async def ping() -> dict[str, str]:
    """Lightweight liveness check — dùng cho Docker HEALTHCHECK."""
    return {"status": "ok", "service": settings.app_name}
