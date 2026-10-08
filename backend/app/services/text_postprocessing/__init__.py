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


def rejoin_paragraphs(text: str) -> str:
    """Rejoin soft-wrapped lines into paragraphs without breaking document structure."""
    lines = text.split('\n')
    if len(lines) < 2:
        return text

    result = [lines[0]]
    for i in range(1, len(lines)):
        prev = result[-1].strip()
        curr = lines[i].strip()

        if not prev or not curr:
            result.append(lines[i])
            continue
            
        # Không nối các dòng Header 2 cột (có khoảng cách lớn giữa 2 cột)
        if "      " in result[-1]:
            result.append(lines[i])
            continue

        # Không nối nếu dòng trước là tiêu đề / đề mục viết hoa (vd: "KẾ HOẠCH", "QUYẾT ĐỊNH", "I. MỤC ĐÍCH")
        if prev.isupper() and len(prev) >= 3:
            result.append(lines[i])
            continue

        # Giữ nguyên dấu xuống dòng nếu dòng hiện tại là đề mục, số thứ tự (vd: 1., 1.1., 1.1.1., I., II., -, +)
        if re.match(r'^([\+\-\–\—]|\d+(\.\d+)*\.?|[IVXLCDM]+\.)\s+', curr):
            result.append(lines[i])
            continue

        # Giữ nguyên nếu dòng hiện tại bắt đầu bằng từ khóa phân đoạn hành chính
        if re.match(r'^(Căn cứ|Điều \d+|Chương [IVXLCDM\d]+|Kính gửi|Nơi nhận|Thời gian|Địa điểm|Thành phần)', curr, re.IGNORECASE):
            result.append(lines[i])
            continue

        # Giữ nguyên nếu dòng trước kết thúc bằng dấu câu ngắt đoạn
        if prev[-1] in ['.', ':', ';', '!', '?', '…']:
            result.append(lines[i])
            continue

        # CHỈ NỐI DÒNG nếu dòng hiện tại rõ ràng là phần tiếp nối của câu (bắt đầu bằng chữ thường)
        # hoặc dòng trước kết thúc bằng dấu gạch nối ngắt từ
        if prev.endswith('-') or prev.endswith('–'):
            result[-1] = result[-1].rstrip('-–') + curr
        elif re.match(r'^[a-zà-ỹ]', curr):
            result[-1] = result[-1] + " " + curr
        else:
            result.append(lines[i])

    return '\n'.join(result)

def post_process_vietnamese(text: str) -> str:
    """
    Pipeline hậu xử lý văn bản OCR tiếng Việt hành chính.

    Thứ tự xử lý:
        1. Unicode NFC normalization
        2. OCR character fixes (lỗi quang học tổng quát)
        3. Admin dictionary corrections (domain hành chính)
        4. Document header normalization (Quốc hiệu/Số hiệu/Ngày tháng)
        5. Rejoin paragraphs
        6. Cleanup khoảng trắng thừa

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
    
    # Bước 6: Nối dòng
    text = rejoin_paragraphs(text)

    return text.strip()
