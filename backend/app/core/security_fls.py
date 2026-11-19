"""
backend/app/core/security_fls.py — Field-Level Security (FLS) & Document-Level Security (DLS)
DocuCTSV — Hệ thống Số hóa & OCR Hồ sơ Sinh viên (Đại học Đà Lạt)

Chức năng:
1. Phân quyền hiển thị theo trường dữ liệu (Field-Level Security):
   - ADMIN & CTSV_STAFF: Hiển thị đầy đủ thông tin gốc (CCCD, SĐT, Số tài khoản, Mã hộ nghèo).
   - FACULTY_STAFF & ACADEMIC: Che mờ thông tin cá nhân PII (CCCD: 06820100****, SĐT: 0912***789).
   - STUDENT: Áp dụng Document-Level Security (DLS) — chỉ xem được hồ sơ có student_id của chính mình.
2. Giám sát tần suất truy xuất PII bất thường (Anomalous PII Harvesting Watcher).
"""

from collections import defaultdict
from datetime import datetime, timezone
import re
import time
from typing import Any

# Bộ nhớ đệm giám sát tần suất truy vấn PII (IP -> list timestamps)
_PII_ACCESS_TRACKER: dict[str, list[float]] = defaultdict(list)
_PII_RATE_LIMIT_WINDOW = 60.0  # 60 giây
_PII_RATE_LIMIT_MAX_REQUESTS = 15  # Tối đa 15 truy vấn PII/phút cho tài khoản không phải Admin


def mask_citizen_id(val: str | None) -> str | None:
    """Che mờ 4 số cuối của số Căn cước công dân (CCCD)."""
    if not val:
        return val
    s = str(val).strip()
    if len(s) >= 8:
        return f"{s[:len(s) - 4]}****"
    return "****"


def mask_phone_number(val: str | None) -> str | None:
    """Che mờ các số giữa của số điện thoại sinh viên."""
    if not val:
        return val
    s = str(val).strip()
    if len(s) >= 9:
        return f"{s[:3]}***{s[-3:]}"
    return "****"


def mask_bank_account(val: str | None) -> str | None:
    """Che mờ số tài khoản nhận học bổng / miễn giảm học phí."""
    if not val:
        return val
    s = str(val).strip()
    if len(s) >= 6:
        return f"{s[:4]}****{s[-2:]}"
    return "****"


def mask_ocr_pii_in_text(text: str) -> str:
    """Che mờ tự động các mẫu CCCD và Số điện thoại trong toàn văn OCR."""
    if not text:
        return text

    # Pattern CCCD 12 số
    text = re.sub(r"\b(\d{8})(\d{4})\b", r"\1****", text)
    # Pattern SĐT 10 số
    text = re.sub(r"\b(0\d{2})(\d{4})(\d{3})\b", r"\1****\3", text)
    # Pattern số tài khoản ngân hàng 10-14 số
    text = re.sub(r"\b(\d{4})(\d{4,8})(\d{2})\b", r"\1****\3", text)

    return text


def apply_fls_dls(
    results: list[dict[str, Any]],
    user_role: str | None = None,
    user_student_id: str | None = None,
) -> tuple[list[dict[str, Any]], int]:
    """
    Áp dụng chính sách FLS và DLS lên danh sách kết quả tìm kiếm:
    - Nếu vai trò là STUDENT: Lọc bỏ hồ sơ của sinh viên khác (DLS).
    - Nếu vai trò không phải ADMIN/CTSV: Che mờ các trường nhạy cảm trong metadata & toàn văn (FLS).
    """
    filtered_results: list[dict[str, Any]] = []
    masked_count = 0
    role_upper = (user_role or "GUEST").upper()
    is_privileged = role_upper in ("ADMIN", "CTSV", "CTSV_STAFF", "MANAGER")

    for item in results:
        doc_student_id = str(item.get("student_id") or "")

        # 1. Áp dụng Document-Level Security (DLS) cho Sinh viên
        if role_upper == "STUDENT":
            if user_student_id and doc_student_id and doc_student_id != str(user_student_id):
                continue  # Bỏ qua hồ sơ của sinh viên khác

        # 2. Áp dụng Field-Level Security (FLS) nếu không phải cán bộ đặc quyền
        if not is_privileged:
            item_copy = dict(item)

            # Che mờ trong metadata
            if "citizen_id" in item_copy:
                item_copy["citizen_id"] = mask_citizen_id(item_copy["citizen_id"])
            if "phone_number" in item_copy:
                item_copy["phone_number"] = mask_phone_number(item_copy["phone_number"])
            if "bank_account" in item_copy:
                item_copy["bank_account"] = mask_bank_account(item_copy["bank_account"])

            # Che mờ trong đoạn trích toàn văn (snippet / content)
            if "content" in item_copy and isinstance(item_copy["content"], str):
                item_copy["content"] = mask_ocr_pii_in_text(item_copy["content"])
            if "snippet" in item_copy and isinstance(item_copy["snippet"], str):
                item_copy["snippet"] = mask_ocr_pii_in_text(item_copy["snippet"])

            masked_count += 1
            filtered_results.append(item_copy)
        else:
            filtered_results.append(item)

    return filtered_results, masked_count


def check_pii_harvesting_watcher(identity: str, is_privileged: bool = False) -> tuple[bool, int]:
    """
    Watcher cảnh báo an toàn: Giám sát tần suất truy xuất PII liên tục.
    Trả về (is_anomaly_detected, current_rpm).
    """
    if is_privileged:
        return False, 0

    now = time.monotonic()
    history = _PII_ACCESS_TRACKER[identity]

    # Loại bỏ các mốc thời gian ngoài cửa sổ 60s
    history = [t for t in history if now - t <= _PII_RATE_LIMIT_WINDOW]
    history.append(now)
    _PII_ACCESS_TRACKER[identity] = history

    current_rpm = len(history)
    is_anomaly = current_rpm > _PII_RATE_LIMIT_MAX_REQUESTS

    return is_anomaly, current_rpm

