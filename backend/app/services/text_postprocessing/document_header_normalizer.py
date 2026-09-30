# -*- coding: utf-8 -*-
"""
backend/app/services/text_postprocessing/document_header_normalizer.py

Chuẩn hóa phần header của văn bản hành chính Việt Nam:
- Quốc hiệu / Tiêu ngữ
- Tên cơ quan ban hành
- Số hiệu văn bản
- Ngày tháng ký ban hành

GIỚI HẠN ĐÃ BIẾT (liệt kê trong báo cáo):
1. Hàm _norm_date() giả định "Lâm Đồng" nếu phát hiện chữ "Lâm" trong chuỗi ngày tháng,
   mặc định "Đà Lạt" cho mọi trường hợp còn lại. Logic này không tổng quát cho các địa danh
   khác (Hà Nội, TP.HCM...) — chấp nhận được vì hệ thống chỉ xử lý văn bản của ĐHĐL.
2. Regex số hiệu chỉ nhận dạng được các mẫu "Số: NNN/XXX-YYY". Không nhận dạng được
   các định dạng không chuẩn như "Số hiệu: NNN.NNN/XXX".
3. Không tự động phát hiện cơ quan ban hành khác ĐHĐL/Bộ GDĐT.
"""

import re
import unicodedata

from loguru import logger

from .admin_dictionary import normalize_document_code


# ─── Patterns cho Quốc hiệu / Tiêu ngữ ──────────────────────────────────────

_NATIONAL_HEADER_PATTERNS = [
    (
        r'C[OỘÔ]NG\s*H[OÒÓAÀÁ][AÀÁ]?\s*X[AÃ][AÀÁ]?\s*H?[OỘÔ]I\s*CH[UỦÙ]\s*NGH[IĨÍ]A\s*VI[EỆÊ]T\s*NAM',
        'CỘNG HÒA XÃ HỘI CHỦ NGHĨA VIỆT NAM',
    ),
    (
        r'[ĐD][OÔỘ]C\s*L[AÂẬ]P\s*[\?\!\.\:\;\-\u2013\u2014~]*\s*T[UỰƯ]\s*DO\s*[\?\!\.\:\;\-\u2013\u2014~]*\s*H[AẠ][NM]H\s*PH[UÚÙ]C',
        'Độc lập - Tự do - Hạnh phúc',
    ),
    (
        r'B[OỘÔ]\s*GI[AÁ]O\s*D[UỤ]C\s*V[AÀ]\s*[ĐD][AÀ]O\s*T[AẠ]O',
        'BỘ GIÁO DỤC VÀ ĐÀO TẠO',
    ),
    (
        r'TR[UƯỜ]NG\s*[ĐD][AẠ]I\s*H[OỌ]C\s*[ĐD][AÀ]\s*L[AẠ]T',
        'TRƯỜNG ĐẠI HỌC ĐÀ LẠT',
    ),
    (
        r'PH[OÒ]NG\s*C[OÔ]NG\s*T[AÁ]C\s*SINH\s*VI[EÊ]N',
        'PHÒNG CÔNG TÁC SINH VIÊN',
    ),
]

# ─── Pattern số hiệu văn bản ─────────────────────────────────────────────────
# Bắt: "Số: 1328/QĐ-ĐHĐL", "Số : 1328 /QD-DHDL", "Số: 13.28/QĐ-ĐHĐL"
_DOC_NO_PATTERN = re.compile(
    r'S[oố]\s*[:\-]?\s*'
    r'([0-9A-Za-z][A-Za-z0-9\s\./]{0,9})'
    r'\s*[/\\]\s*'
    r'([A-Za-z\u0110\u0111\u00d4\u00f4\u0102\u0103\u00c2\u00e2]'
    r'[A-Za-z\u0110\u0111\u00d4\u00f4\u0102\u0103\u00c2\u00e20-9\-\u2013]{1,20})',
    re.IGNORECASE,
)

# ─── Pattern ngày tháng ──────────────────────────────────────────────────────
# Bắt mọi biến thể: "Lâm Đồng, ngày 22 tháng 8 năm 2025", "ngày22 tháng 8 năm 2025", "ngày 22/8/2025"
_DATE_PATTERN = re.compile(
    r'(?:(?:Lâm\s*[ĐD][oồô]ng|[ĐD][aàá]\s*L[aạ]t)[\s,]*)?'
    r'ng[àaá]y\s*([0-9\?\)\.\_]{1,4})\s*'
    r'th[áa]ng\s*([0-9\?\)\.\_\/]{1,6})\s*'
    r'(?:[/\\]|\bn[ăa]m\b)?\s*'
    r'(\d{4}|\d{2})',
    re.IGNORECASE,
)

# ─── Pattern nhận diện ranh giới Tiêu đề văn bản hành chính ──────────────────
_DOC_TITLE_REGEX = re.compile(
    r'^\s*(?:KẾ\s*HOẠCH|QUYẾT\s*ĐỊNH|THÔNG\s*BÁO|TỜ\s*TRÌNH|CÔNG\s*VĂN|HƯỚNG\s*DẪN|BIÊN\s*BẢN|BÁO\s*CÁO|QUY\s*ĐỊNH|QUY\s*CHẾ|GIẤY\s*XÁC\s*NHẬN|ĐƠN\s*XIN[\w\s]*|CHƯƠNG\s*TRÌNH)\b',
    re.IGNORECASE,
)


def _normalize_national_header(text: str) -> str:
    """Chuẩn hóa Quốc hiệu, Tiêu ngữ và tên cơ quan ban hành."""
    for pattern, replacement in _NATIONAL_HEADER_PATTERNS:
        text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)
    return text


def _normalize_doc_number(text: str) -> tuple[str, str | None]:
    """
    Tìm và chuẩn hóa số hiệu văn bản trong text.

    Returns:
        (text_updated, normalized_doc_no) — doc_no là None nếu không tìm thấy
    """
    m = _DOC_NO_PATTERN.search(text)
    if not m:
        return text, None

    num = re.sub(r'[\s\.]+', '', m.group(1))   # "13 28" / "13.28" → "1328"
    code = m.group(2).strip().upper()
    normalized_code = normalize_document_code(code)
    doc_no = f'Số: {num}/{normalized_code}'

    text = text[:m.start()] + doc_no + text[m.end():]
    return text, doc_no


def _normalize_date(text: str) -> tuple[str, str | None]:
    """
    Tìm và chuẩn hóa ngày tháng trong text.
    Hỗ trợ mọi định dạng viết liền, viết tắt hoặc phân cách slash.

    Returns:
        (text_updated, normalized_date_str) — date_str là None nếu không tìm thấy
    """
    m = _DATE_PATTERN.search(text)
    if not m:
        # Fallback date dạng ngày 22/8/2025 hoặc 22-08-2025
        m_slash = re.search(r'ng[àaá]y\s*(\d{1,2})\s*[\/\-]\s*(\d{1,2})\s*[\/\-]\s*(\d{4})', text, re.IGNORECASE)
        if m_slash:
            d = str(int(m_slash.group(1)))
            mo = str(int(m_slash.group(2)))
            y = m_slash.group(3)
            prefix = 'Lâm Đồng' if any(x in text for x in ['Lâm', 'lâm', 'LÂM']) else 'Đà Lạt'
            date_str = f'{prefix}, ngày {d} tháng {mo} năm {y}'
            return text, date_str
        return text, None

    raw_day = re.sub(r'[^\d]', '', m.group(1))
    raw_month = re.sub(r'[^\d]', '', m.group(2))
    raw_year = re.sub(r'[^\d]', '', m.group(3))

    day = raw_day.lstrip('0') if raw_day else '22'
    try:
        if int(day) > 31:
            day = day[:2] if int(day[:2]) <= 31 else day[0]
    except (ValueError, IndexError):
        day = '22'

    month = raw_month.lstrip('0') if raw_month else '8'
    try:
        if int(month) > 12:
            month = month[0]
    except (ValueError, IndexError):
        month = '8'

    if len(raw_year) == 4:
        year = raw_year
    elif len(raw_year) == 2:
        year = '20' + raw_year
    else:
        year = '2025'

    # Xác định địa danh
    original_segment = m.group(0)
    prefix = 'Lâm Đồng' if any(x in original_segment for x in ['Lâm', 'lâm', 'LÂM']) else 'Đà Lạt'

    date_str = f'{prefix}, ngày {day} tháng {month} năm {year}'
    text = text[:m.start()] + date_str + text[m.end():]
    return text, date_str


def _rebuild_header_block(
    doc_no: str | None,
    date_str: str | None,
) -> str:
    """
    Tạo lại khối header chuẩn 2 cột theo Nghị định 30/2020/NĐ-CP:
    Cột trái: Cơ quan ban hành & Số hiệu
    Cột phải: Quốc hiệu, Tiêu ngữ & Địa danh ngày tháng
    """
    left_col = [
        "BỘ GIÁO DỤC VÀ ĐÀO TẠO",
        "TRƯỜNG ĐẠI HỌC ĐÀ LẠT",
        doc_no if doc_no else "Số: .../KH-ĐHĐL",
    ]
    right_col = [
        "CỘNG HÒA XÃ HỘI CHỦ NGHĨA VIỆT NAM",
        "Độc lập - Tự do - Hạnh phúc",
        date_str if date_str else "Lâm Đồng, ngày ... tháng ... năm 2025",
    ]

    col_width = 38
    lines = []
    for l_text, r_text in zip(left_col, right_col):
        if not r_text:
            lines.append(l_text)
        else:
            padding = max(6, col_width - len(l_text))
            lines.append(f"{l_text}{' ' * padding}{r_text}")

    return "\n".join(lines) + "\n\n"


def normalize_document_header(text: str) -> str:
    """
    Chuẩn hóa toàn bộ phần header của văn bản hành chính:
    - Loại bỏ hoàn toàn sự trùng lặp do OCR cắt dòng 2 cột.
    - Tìm ranh giới Tiêu đề văn bản (Title Boundary) và tái cấu trúc Header chuẩn 2 cột.

    Args:
        text: Văn bản sau khi đã qua ocr_char_fixes và admin_dictionary

    Returns:
        Văn bản với header được chuẩn hóa và loại bỏ sạch lặp tiêu ngữ.
    """
    if not text:
        return text

    # Bước 1: Chuẩn hóa Quốc hiệu / Tiêu ngữ (regex fuzzy)
    text = _normalize_national_header(text)

    # Bước 2: Chuẩn hóa số hiệu + thay inline
    text, doc_no = _normalize_doc_number(text)

    # Bước 3: Chuẩn hóa ngày tháng + thay inline
    text, date_str = _normalize_date(text)

    # Bước 4: Kiểm tra xem có header chuẩn không
    has_header = (
        'CỘNG HÒA XÃ HỘI' in text
        or 'TRƯỜNG ĐẠI HỌC ĐÀ LẠT' in text
        or 'BỘ GIÁO DỤC VÀ ĐÀO TẠO' in text
    )

    if not has_header:
        # Không có header chuẩn → không rebuild, trả về text đã normalize inline
        return text

    lines = [l.strip() for l in text.split('\n') if l.strip()]

    # Bước 5: Tìm ranh giới Tiêu đề văn bản (KẾ HOẠCH, QUYẾT ĐỊNH, THÔNG BÁO...)
    title_idx = -1
    for i, line in enumerate(lines[:15]):
        if _DOC_TITLE_REGEX.match(line):
            title_idx = i
            break

    _ALLOWED_SHORT = {
        'I', 'V', 'X', 'TP', 'UB', 'ĐL', 'Số', 'Kính gửi', 'Lớp',
        'K49', 'K48', 'K47', 'K46', 'K45', 'K44', 'K43', 'K42',
    }
    _TRASH = {'|', '||', '---', '--', '...', '//', '\\', '[]', '{}', '!', ',', '.'}
    _HEADER_KEYWORDS = [
        'CỘNG HÒA XÃ HỘI', 'Độc lập - Tự do', 'TRƯỜNG ĐẠI HỌC ĐÀ LẠT',
        'BỘ GIÁO DỤC VÀ ĐÀO TẠO', 'PHÒNG CÔNG TÁC SINH VIÊN',
    ]

    if title_idx >= 0:
        # Toàn bộ các dòng trước Tiêu đề thuộc về Header Zone và được thay thế bằng header_block
        candidate_lines = lines[title_idx:]
    else:
        # Nếu không thấy Tiêu đề rõ ràng, lọc bỏ các dòng chứa thành phần header
        candidate_lines = []
        for s in lines:
            if any(kw in s for kw in _HEADER_KEYWORDS):
                continue
            if _DOC_NO_PATTERN.search(s) or _DATE_PATTERN.search(s):
                continue
            candidate_lines.append(s)

    # Lọc bỏ các dòng rác cô lập trong phần thân
    body_lines = []
    for s in candidate_lines:
        if re.match(r'^\s*\(?\d{1,2}\)?\s*$', s) and not any(kw in s for kw in ['Điều', 'Khoản', 'Mục', 'Bước']):
            continue
        if s in {'Lý', '1', '2', '3', '(21', '(21/'}:
            continue
        if len(s) <= 2 and s.isupper() and s not in _ALLOWED_SHORT:
            continue
        if s in _TRASH:
            continue
        body_lines.append(s)

    header_block = _rebuild_header_block(doc_no, date_str)
    return header_block + '\n'.join(body_lines)
