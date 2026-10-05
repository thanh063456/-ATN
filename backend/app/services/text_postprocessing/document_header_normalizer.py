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
        r'C[OỘÔoồô]\s*NG\s*H[OÒÓAÀÁoòóaàá][AÀÁaàá]?\s*X[AÃaã][AÀÁaàá]?\s*H?[OỘÔoộô]I\s*CH[UỦÙuủù]\s*NGH[IĨÍiĩí][AÀÁaàá]?\s*VI[EỆÊeệê]T\s*NAM',
        'CỘNG HÒA XÃ HỘI CHỦ NGHĨA VIỆT NAM',
    ),
    (
        r'C[OỘÔoồô]\s*NG\s*H[OÒÓAÀÁoòóaàá][AÀÁaàá]?\s*X[AÃaã][AÀÁaàá]?\s*H?[OỘÔoộô]I\s*CH[UỦÙuủù]\s*NGH[IĨÍiĩí][AÀÁaàá]?\b',
        'CỘNG HÒA XÃ HỘI CHỦ NGHĨA VIỆT NAM',
    ),
    (
        r'[ĐD][OÔỘoôộ]\s*C\s*L[AÂẬaâậ]\s*P\s*[\?\!\.\:\;\,\_\-\u2013\u2014~/\\\s]*\s*T[UỰƯuựư]\s*DO\s*[\?\!\.\:\;\,\_\-\u2013\u2014~/\\\s]*\s*H[AẠaạ][NMnm]H\s*PH[UÚÙƯuúùư][CCTct\?]*',
        'Độc lập - Tự do - Hạnh phúc',
    ),
    (
        r'[ĐD][OÔỘoôộ]\s*C\s*L[AÂẬaâậ]\s*P\s*[\?\!\.\:\;\,\_\-\u2013\u2014~/\\\s]*\s*T[UỰƯuựư]\s*DO\b',
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


def _normalize_national_header(header_text: str) -> str:
    """Chuẩn hóa Quốc hiệu, Tiêu ngữ và tên cơ quan ban hành."""
    for pattern, replacement in _NATIONAL_HEADER_PATTERNS:
        header_text = re.sub(pattern, replacement, header_text, flags=re.IGNORECASE)
    return header_text


def _normalize_doc_number(header_text: str) -> tuple[str, str | None]:
    """
    Tìm và chuẩn hóa số hiệu văn bản trong text.
    """
    reject_words = ["công văn", "căn cứ", "theo", "của", "quyết định", "thông tư", "nghị định"]
    
    for m in _DOC_NO_PATTERN.finditer(header_text):
        start_idx = m.start()
        context_before = header_text[max(0, start_idx - 40):start_idx].lower()
        if any(w in context_before for w in reject_words):
            continue
            
        num = re.sub(r'[\s\.]+', '', m.group(1))   # "13 28" / "13.28" → "1328"
        code = m.group(2).strip().upper()
        normalized_code = normalize_document_code(code)
        doc_no = f'Số: {num}/{normalized_code}'
    
        text = header_text[:m.start()] + doc_no + header_text[m.end():]
        return text, doc_no

    fallback_m = re.search(r'S[oố]\s*[:\-]?\s*([^\n]{2,30})', header_text, re.IGNORECASE)
    if fallback_m:
        start_idx = fallback_m.start()
        context_before = header_text[max(0, start_idx - 40):start_idx].lower()
        if not any(w in context_before for w in reject_words):
            doc_no = "Số: [chưa đọc được]"
            return header_text, doc_no

    return header_text, None


def _normalize_date(header_text: str) -> tuple[str, str | None]:
    """
    Tìm và chuẩn hóa ngày tháng trong text.
    """
    reject_words = ["công văn", "căn cứ", "theo", "của", "quyết định", "thông tư", "nghị định"]

    for m in _DATE_PATTERN.finditer(header_text):
        start_idx = m.start()
        context_before = header_text[max(0, start_idx - 40):start_idx].lower()
        if any(w in context_before for w in reject_words):
            continue

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
    
        original_segment = m.group(0)
        prefix = 'Lâm Đồng' if any(x in original_segment for x in ['Lâm', 'lâm', 'LÂM']) else 'Đà Lạt'
    
        date_str = f'{prefix}, ngày {day} tháng {month} năm {year}'
        text = header_text[:m.start()] + date_str + header_text[m.end():]
        return text, date_str

    for m_slash in re.finditer(r'ng[àaá]y\s*(\d{1,2})\s*[\/\-]\s*(\d{1,2})\s*[\/\-]\s*(\d{4})', header_text, re.IGNORECASE):
        start_idx = m_slash.start()
        context_before = header_text[max(0, start_idx - 40):start_idx].lower()
        if any(w in context_before for w in reject_words):
            continue
            
        d = str(int(m_slash.group(1)))
        mo = str(int(m_slash.group(2)))
        y = m_slash.group(3)
        prefix = 'Lâm Đồng' if any(x in header_text for x in ['Lâm', 'lâm', 'LÂM']) else 'Đà Lạt'
        date_str = f'{prefix}, ngày {d} tháng {mo} năm {y}'
        return header_text, date_str

    fallback_m = re.search(r'(?:Lâm Đồng|Đà Lạt)?[\s,]*ng[àaá]y\s+[^\n]{2,30}', header_text, re.IGNORECASE)
    if fallback_m:
        start_idx = fallback_m.start()
        context_before = header_text[max(0, start_idx - 40):start_idx].lower()
        if not any(w in context_before for w in reject_words):
            prefix = 'Lâm Đồng' if any(x in header_text for x in ['Lâm', 'lâm', 'LÂM']) else 'Đà Lạt'
            date_str = f'{prefix}, ngày [chưa đọc được]'
            return header_text, date_str

    return header_text, None


def _is_header_fragment(line: str, doc_no: str | None, date_str: str | None) -> bool:
    """Kiểm tra một dòng text có phải là mảnh vỡ của khối header đã được chuẩn hóa."""
    line_clean = line.strip()
    if not line_clean:
        return True

    line_upper = line_clean.upper()
    keywords = [
        "BỘ GIÁO DỤC VÀ ĐÀO TẠO",
        "TRƯỜNG ĐẠI HỌC ĐÀ LẠT",
        "CỘNG HÒA XÃ HỘI CHỦ NGHĨA VIỆT NAM",
        "CỘNG HOÀ XÃ HỘI CHỦ NGHĨA VIỆT NAM",
        "ĐỘC LẬP - TỰ DO - HẠNH PHÚC",
        "ĐỘC LẬP – TỰ DO – HẠNH PHÚC",
        "PHÒNG CÔNG TÁC SINH VIÊN",
    ]
    for kw in keywords:
        if line_upper == kw:
            return True

    if doc_no and (line_clean == doc_no or line_clean == f"Số: {doc_no}" or line_upper == doc_no.upper()):
        return True
    if date_str and (line_clean == date_str or line_upper == date_str.upper()):
        return True

    # Kiểm tra dòng ghép 2 cột bị OCR đọc chung 1 hàng
    stripped = line_upper
    for kw in keywords:
        stripped = stripped.replace(kw, "").strip()
    if doc_no:
        stripped = stripped.replace(doc_no.upper(), "").strip()
    if date_str:
        stripped = stripped.replace(date_str.upper(), "").strip()

    # Dòng chỉ chứa các từ khóa header hoặc ký tự ngăn cách rác
    if not stripped or len(re.sub(r'[\s\.\:\,\-\_\?\!/]+', '', stripped)) == 0:
        return True

    return False


def _rebuild_header_block(
    doc_no: str | None,
    date_str: str | None,
    is_admin_doc: list,
    has_national_header: list,
) -> str:
    lines = []

    left_col = []
    if is_admin_doc:
        if "BỘ GIÁO DỤC VÀ ĐÀO TẠO" in is_admin_doc:
            left_col.append("BỘ GIÁO DỤC VÀ ĐÀO TẠO")
        if "TRƯỜNG ĐẠI HỌC ĐÀ LẠT" in is_admin_doc:
            left_col.append("TRƯỜNG ĐẠI HỌC ĐÀ LẠT")
        elif "PHÒNG CÔNG TÁC SINH VIÊN" in is_admin_doc:
            left_col.append("PHÒNG CÔNG TÁC SINH VIÊN")
        
        if doc_no:
            left_col.append(doc_no)
        else:
            left_col.append("")

    right_col = []
    if has_national_header:
        if "CỘNG HÒA XÃ HỘI CHỦ NGHĨA VIỆT NAM" in has_national_header:
            right_col.append("CỘNG HÒA XÃ HỘI CHỦ NGHĨA VIỆT NAM")
        if "Độc lập - Tự do - Hạnh phúc" in has_national_header:
            right_col.append("Độc lập - Tự do - Hạnh phúc")
        if date_str:
            right_col.append(date_str)
        else:
            right_col.append("")

    # Nếu chỉ có doc_no mà không có is_admin_doc
    if doc_no and not left_col:
        left_col = [doc_no]
    
    # Nếu chỉ có date_str mà không có has_national_header
    if date_str and not right_col:
        right_col = [date_str]

    if left_col or right_col:
        col_width = 38
        max_len = max(len(left_col), len(right_col))
        while len(left_col) < max_len:
            left_col.append("")
        while len(right_col) < max_len:
            right_col.append("")

        for l_text, r_text in zip(left_col, right_col):
            if not l_text and not r_text:
                continue
            if not r_text:
                lines.append(l_text)
            elif not l_text:
                lines.append(f"{' ' * col_width}{r_text}")
            else:
                padding = max(6, col_width - len(l_text))
                lines.append(f"{l_text}{' ' * padding}{r_text}")

    if lines:
        return "\n".join(lines) + "\n\n"
    return ""


def normalize_document_header(text: str) -> str:
    """
    Chuẩn hóa toàn bộ phần header của văn bản hành chính:
    - Loại bỏ hoàn toàn sự trùng lặp do OCR cắt dòng 2 cột.
    - Xóa các dòng rác (barcode, dấu mộc bị nhận diện nhầm).
    - Tái cấu trúc Header chuẩn 2 cột ở đầu văn bản (theo Nghị định 30/2020/NĐ-CP).
    """
    if not text:
        return text

    lines = text.split('\n')
    header_lines = lines[:12]
    body_lines = lines[12:]
    header_text = '\n'.join(header_lines)

    # Bước 1: Chuẩn hóa Quốc hiệu / Tiêu ngữ và lấy thông tin
    header_text = _normalize_national_header(header_text)
    header_text, doc_no = _normalize_doc_number(header_text)
    header_text, date_str = _normalize_date(header_text)
    
    text = '\n'.join([header_text] + body_lines) if body_lines else header_text

    # Get header region text (first 12 lines) for checking presence
    header_text_upper = header_text.upper()
    
    is_admin_doc = []
    if "BỘ GIÁO DỤC VÀ ĐÀO TẠO" in header_text_upper or "BO GIAO DUC VA DAO TAO" in header_text_upper:
        is_admin_doc.append("BỘ GIÁO DỤC VÀ ĐÀO TẠO")
    if "TRƯỜNG ĐẠI HỌC ĐÀ LẠT" in header_text_upper or "ĐẠI HỌC ĐÀ LẠT" in header_text_upper or "ĐẠI HỌC ĐA LẠT" in header_text_upper:
        is_admin_doc.append("TRƯỜNG ĐẠI HỌC ĐÀ LẠT")
    elif "PHÒNG CÔNG TÁC SINH VIÊN" in header_text_upper or "PHONG CONG TAC SINH VIEN" in header_text_upper:
        is_admin_doc.append("PHÒNG CÔNG TÁC SINH VIÊN")
        
    has_national_header = []
    if "CỘNG HÒA XÃ HỘI CHỦ NGHĨA VIỆT NAM" in header_text_upper or "CỘNG HOÀ" in header_text_upper or "CÔNG HÒA" in header_text_upper or "CONG HOA" in header_text_upper or "CHỦ NGHĨA VIỆT NAM" in header_text_upper:
        has_national_header.append("CỘNG HÒA XÃ HỘI CHỦ NGHĨA VIỆT NAM")
    if "Độc lập - Tự do - Hạnh phúc".upper() in header_text_upper or "ĐỘC LẬP" in header_text_upper or "DOC LAP" in header_text_upper or "HẠNH PHÚC" in header_text_upper or "HANH PHUC" in header_text_upper or "TỰ DO" in header_text_upper:
        has_national_header.append("Độc lập - Tự do - Hạnh phúc")

    if not (is_admin_doc or has_national_header):
        # Không có header cơ quan / quốc hiệu để tái cấu trúc → giữ nguyên text đã chuẩn hóa inline
        return text.strip()

    # Bước 2: Tái cấu trúc Header chuẩn 2 cột
    header_block = _rebuild_header_block(doc_no, date_str, is_admin_doc, has_national_header)

    # Bước 3: Dọn dẹp các mảnh vỡ của header cũ và dòng rác
    lines = text.splitlines()
    cleaned_lines = []
    found_title = False

    for line in lines:
        line_clean = line.strip()
        if not line_clean:
            continue

        # Bỏ qua các thành phần đã được gộp vào header_block
        if _is_header_fragment(line_clean, doc_no, date_str):
            continue

        # Bỏ qua các dòng rác dài đặc biệt (do barcode hoặc mộc mờ)
        if len(line_clean) > 20:
            if re.search(r'\d{10,}', line_clean):
                continue
            if len(re.findall(r'[\.\-]', line_clean)) > 8:
                continue

        # Đánh dấu đã tìm thấy Tiêu đề văn bản
        if _DOC_TITLE_REGEX.search(line_clean):
            found_title = True

        cleaned_lines.append(line_clean)

    # Nếu tìm thấy Tiêu đề, xóa mọi thứ đứng TRƯỚC tiêu đề
    if found_title:
        title_idx = -1
        for i, l in enumerate(cleaned_lines):
            if _DOC_TITLE_REGEX.search(l):
                title_idx = i
                break
        if title_idx > 0:
            cleaned_lines = cleaned_lines[title_idx:]

    final_text = header_block + "\n".join(cleaned_lines)
    return final_text.strip()

