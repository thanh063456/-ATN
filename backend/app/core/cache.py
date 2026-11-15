"""
backend/app/core/cache.py — In-Memory TTL Cache

Cung cấp cơ chế bộ nhớ đệm (In-memory TTL Cache) siêu tốc (0.1ms) cho các query nặng:
- Thống kê thẻ nhãn: /documents/tags/summary
- Thống kê Dashboard: /stats/dashboard
- Danh mục và cấu hình tham chiếu

Hỗ trợ:
- get(key)
- set(key, value, ttl=60)
- invalidate(prefix)
- clear()
"""

import time
from typing import Any
from loguru import logger


class SimpleMemoryCache:
    def __init__(self, default_ttl: int = 60) -> None:
        self._store: dict[str, tuple[float, Any]] = {}
        self._default_ttl = default_ttl

    def get(self, key: str) -> Any | None:
        """Lấy giá trị từ cache nếu chưa hết hạn TTL."""
        if key in self._store:
            expire_at, value = self._store[key]
            if time.monotonic() < expire_at:
                return value
            # Hết hạn -> xóa
            del self._store[key]
        return None

    def set(self, key: str, value: Any, ttl: int | None = None) -> None:
        """Lưu giá trị vào cache với thời hạn sống TTL (giây)."""
        ttl_val = ttl if ttl is not None else self._default_ttl
        self._store[key] = (time.monotonic() + ttl_val, value)

    def invalidate(self, prefix: str = "") -> None:
        """Xóa các key khớp với tiền tố prefix (hoặc xóa toàn bộ nếu prefix='')."""
        if not prefix:
            self._store.clear()
            logger.debug("[Cache] Toàn bộ cache đã được làm mới.")
            return
        keys_to_del = [k for k in self._store if k.startswith(prefix)]
        for k in keys_to_del:
            self._store.pop(k, None)
        if keys_to_del:
            logger.debug(f"[Cache] Đã xóa {len(keys_to_del)} key khớp với tiền tố '{prefix}'.")

    def clear(self) -> None:
        """Xóa sạch cache."""
        self._store.clear()


# Singleton cache instance dùng chung toàn ứng dụng
app_cache = SimpleMemoryCache(default_ttl=60)
