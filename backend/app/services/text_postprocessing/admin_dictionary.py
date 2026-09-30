# -*- coding: utf-8 -*-
"""
backend/app/services/text_postprocessing/admin_dictionary.py

Load và áp dụng từ điển sửa lỗi OCR chuyên biệt cho văn bản hành chính.
Từ điển được load từ file JSON bên ngoài để dễ cập nhật mà không cần
deploy lại code.

File JSON: data/admin_dictionary_vi.json (đường dẫn cấu hình qua settings)
"""

import json
import re
from functools import lru_cache
from pathlib import Path

from loguru import logger


@lru_cache(maxsize=4)
def _load_dictionary(dict_path: str) -> dict:
    """Load từ điển từ file JSON, cache kết quả."""
    path = Path(dict_path)
    if not path.exists() and not path.is_absolute():
        # Thử tìm relative to backend/ directory hoặc root
        for base in [Path("."), Path(__file__).parent.parent.parent.parent]:
            candidate = base / "data" / path.name
            if candidate.exists():
                path = candidate
                break
            candidate_full = base / path
            if candidate_full.exists():
                path = candidate_full
                break

    if not path.exists():
        logger.warning(
            "Admin dictionary not found at {p}. Skipping domain corrections.",
            p=dict_path,
        )
        return {}

    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        logger.info(
            "Loaded admin dictionary: {n} char corrections, {c} code map entries",
            n=len(data.get("char_corrections", [])),
            c=len(data.get("code_map", {})),
        )
        return data
    except (json.JSONDecodeError, OSError) as e:
        logger.error("Failed to load admin dictionary: {err}", err=str(e))
        return {}


def _build_correction_regex(entry: dict) -> tuple[re.Pattern, str] | None:
    """
    Xây dựng compiled regex pattern từ một entry trong từ điển.

    Args:
        entry: Dict với keys: wrong, correct, case_insensitive, boundary

    Returns:
        (compiled_pattern, replacement) hoặc None nếu invalid
    """
    wrong = entry.get("wrong", "")
    correct = entry.get("correct", "")
    if not wrong or not correct:
        return None

    case_insensitive = entry.get("case_insensitive", False)
    boundary = entry.get("boundary", "word")  # "word", "none"

    pattern_str = re.escape(wrong)
    if boundary == "word":
        pattern_str = r'\b' + pattern_str + r'\b'

    flags = re.IGNORECASE if case_insensitive else 0
    try:
        return re.compile(pattern_str, flags), correct
    except re.error:
        return None


def apply_admin_corrections(text: str, dict_path: str = "") -> str:
    """
    Áp dụng từ điển sửa lỗi OCR hành chính lên văn bản.

    Args:
        text: Văn bản sau khi đã qua ocr_char_fixes
        dict_path: Đường dẫn đến file JSON từ điển (nếu rỗng dùng default)

    Returns:
        Văn bản sau khi áp dụng các correction từ dictionary
    """
    if not text:
        return text

    if not dict_path:
        # Lấy từ settings nếu có, fallback sang default path
        try:
            from app.core.config import settings
            dict_path = settings.ocr_admin_dict_path
        except Exception:
            dict_path = "./data/admin_dictionary_vi.json"

    data = _load_dictionary(dict_path)
    if not data:
        return text

    # 1. Áp dụng char_corrections từ JSON
    for entry in data.get("char_corrections", []):
        result = _build_correction_regex(entry)
        if result is None:
            continue
        pattern, replacement = result
        try:
            text = pattern.sub(replacement, text)
        except re.error:
            pass

    return text


def normalize_document_code(code: str, dict_path: str = "") -> str:
    """
    Chuẩn hóa mã loại văn bản hành chính (vd: "QD-DHDL" → "QĐ-ĐHĐL").

    Args:
        code: Mã loại văn bản (UPPERCASE, có thể thiếu dấu)
        dict_path: Đường dẫn file từ điển

    Returns:
        Mã đã được chuẩn hóa, hoặc giữ nguyên nếu không tìm thấy
    """
    if not dict_path:
        try:
            from app.core.config import settings
            dict_path = settings.ocr_admin_dict_path
        except Exception:
            dict_path = "./data/admin_dictionary_vi.json"

    data = _load_dictionary(dict_path)
    code_map: dict[str, str] = data.get("code_map", {})
    return code_map.get(code.upper(), code)


def reload_dictionary(dict_path: str = "") -> None:
    """Xóa cache để reload từ điển (dùng khi file JSON thay đổi)."""
    _load_dictionary.cache_clear()
    logger.info("Admin dictionary cache cleared, will reload on next call.")
