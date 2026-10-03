"""
backend/app/core/tickets.py — Single-use, short-lived file ticket manager
"""
import secrets
import time
from typing import Any

# In-memory ticket storage: {ticket_str: {"document_id": str, "user_id": str, "expires_at": float}}
_tickets: dict[str, dict[str, Any]] = {}


def create_file_ticket(document_id: str, user_id: str | None = None, ttl_seconds: int = 180) -> str:
    """Tạo single-use file ticket có TTL (mặc định 180 giây: 60-300s)."""
    now = time.time()
    # Dọn dẹp ticket đã hết hạn
    expired_keys = [k for k, v in _tickets.items() if v["expires_at"] < now]
    for k in expired_keys:
        _tickets.pop(k, None)

    ticket = secrets.token_urlsafe(32)
    _tickets[ticket] = {
        "document_id": str(document_id),
        "user_id": str(user_id) if user_id else None,
        "expires_at": now + ttl_seconds,
    }
    return ticket


def validate_and_consume_file_ticket(ticket: str, document_id: str) -> bool:
    """
    Xác minh và tiêu thụ vé xem file (chỉ được dùng duy nhất 1 lần).
    Trả về True nếu vé hợp lệ và chưa hết hạn, ngược lại False.
    """
    if not ticket:
        return False

    now = time.time()
    data = _tickets.pop(ticket, None)
    if not data:
        return False

    if data["expires_at"] < now:
        return False

    return data["document_id"] == str(document_id)
