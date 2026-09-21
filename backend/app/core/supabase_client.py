"""
backend/app/core/supabase_client.py — Supabase Python Client Singleton

Cung cấp:
- `supabase_admin`: Client dùng service_role key (full access, bypass RLS) — dùng ở backend
- `get_supabase_admin()`: Dependency cho FastAPI nếu cần inject

Ref: .ai/DECISIONS.md ADR-006 (Object Storage), .ai/CODING_RULES.md (singleton pattern)
"""
from functools import lru_cache

from loguru import logger
from supabase import Client, create_client

from app.core.config import settings


@lru_cache(maxsize=1)
def _create_admin_client() -> Client:
    """Tạo Supabase client với service_role key (singleton, thread-safe)."""
    try:
        client = create_client(
            supabase_url=settings.supabase_url,
            supabase_key=settings.supabase_service_key,
        )
        logger.info("Supabase admin client initialized: {url}", url=settings.supabase_url)
        return client
    except Exception as exc:
        logger.error("Failed to initialize Supabase client: {err}", err=str(exc))
        raise


def get_supabase_admin() -> Client:
    """
    Trả về Supabase admin client (service_role key).
    Dùng trực tiếp trong code hoặc qua FastAPI Depends.
    """
    return _create_admin_client()


# Convenience alias — import trực tiếp ở nơi cần
supabase_admin: Client = get_supabase_admin()
