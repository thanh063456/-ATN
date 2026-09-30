# -*- coding: utf-8 -*-
"""
backend/app/services/text_postprocessing/__init__.py

Package post-processing văn bản OCR tiếng Việt hành chính.

Kiến trúc 3 lớp:
1. ocr_char_fixes     — lỗi quang học tổng quát (l→1, O→0, rn→m...)
2. admin_dictionary   — từ điển domain hành chính (load từ JSON)
3. document_header_normalizer — rebuild khối Quốc hiệu/Số hiệu/Ngày tháng

Public API: post_process_vietnamese(text) → str
"""

import re
import unicodedata

from .ocr_char_fixes import apply_ocr_char_fixes
from .admin_dictionary import apply_admin_corrections
from .document_header_normalizer import normalize_document_header

__all__ = [
    "post_process_vietnamese",
    "apply_ocr_char_fixes",
    "apply_admin_corrections",
    "normalize_document_header",
]


def post_process_vietnamese(text: str) -> str:
    """
    Pipeline hậu xử lý văn bản OCR tiếng Việt hành chính.

    Thứ tự xử lý:
        1. Unicode NFC normalization
        2. OCR character fixes (lỗi quang học tổng quát)
        3. Admin dictionary corrections (domain hành chính)
        4. Document header normalization (Quốc hiệu/Số hiệu/Ngày tháng)
        5. Cleanup khoảng trắng thừa

    Args:
        text: Văn bản OCR thô

    Returns:
        Văn bản đã được chuẩn hóa
    """
    if not text:
        return ""

    # Bước 1: Unicode NFC
    text = unicodedata.normalize("NFC", text)

    # Bước 2: Sửa lỗi ký tự quang học tổng quát
    text = apply_ocr_char_fixes(text)

    # Bước 3: Sửa lỗi từ vựng hành chính (từ JSON dictionary)
    text = apply_admin_corrections(text)

    # Bước 4: Dọn dẹp khoảng trắng thừa trong phần nội dung
    text = re.sub(r'[ \t]+', ' ', text)
    text = re.sub(r'\n{3,}', '\n\n', text)

    # Bước 5: Chuẩn hóa và tái cấu trúc header văn bản hành chính (2 cột chuẩn)
    text = normalize_document_header(text)

    return text.strip()
