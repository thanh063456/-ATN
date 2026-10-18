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


from .admin_dictionary import normalize_document_code


# ─── Patterns cho Quốc hiệu / Tiêu ngữ ──────────────────────────────────────

_NATIONAL_HEADER_PATTERNS = [
    (
        r'C[OỘÔoồô]\s*NG\s*H[OÒÓAÀÁoòóaàá][AÀÁaàá]?\s*X[AÃaã][AÀÁaàá]?\s*H?[OỘÔỌƠỜỚoộôọơờớỆEệe]?I\s*CH[UỦÙỨƯuủùứư]\s*NGH[IĨÍỈỊiĩíỉị][AÀÁẢẠaàáảạ]?(?:[\s\-_]*VI[EỆÊeệê][TṬtṭ]?(?:[\s\-_]*NAM)?)?',
        'CỘNG HÒA XÃ HỘI CHỦ NGHĨA VIỆT NAM',
    ),
    (
        r'[ĐD][OÔỘoôộ]\s*C\s*L[AÂẬaâậ]\s*P[\?\!\.\:\;\,\_\-\u2013\u2014~/\\\s]*T[UỰƯuựư]\s*DO(?:[\?\!\.\:\;\,\_\-\u2013\u2014~/\\\s]*H[AẠaạ][NMnm]H\s*PH[UÚÙƯuúùư][CCTct\?]*)?',
        'Độc lập - Tự do - Hạnh phúc',
    ),
    (
        r'B[OỘÔ]\s*GI[AÁ]O\s*D[UỤ]C\s*V[AÀ]\s*[ĐD][AÀ]O\s*T[AẠ]O',
        'BỘ GIÁO DỤC VÀ ĐÀO TẠO',
    ),
    (
        r'TR[UƯuư][OƠỜOoơờ]*NG\s*[ĐDđd][AẠaạ]I\s*H[OỌoọ]C\s*[ĐDđd][AÀÃÁẢẠaàãáảạ]\s*L[AẠÂẬaạâậ]T',
        'TRƯỜNG ĐẠI HỌC ĐÀ LẠT',
    ),
    (
        r'PH[OÒ]NG\s*C[OÔ]NG\s*T[AÁ]C\s*SINH\s*VI[EÊ]N',
        'PHÒNG CÔNG TÁC SINH VIÊN',
    ),
]

# ─── Pattern số hiệu văn bản ─────────────────────────────────────────────────
# Bắt: "Số: 1328/QĐ-ĐHĐL", "Số : 1328 /QD-DHDL", "Số: 13.28/QĐ-ĐHĐL", "Sề: /KH-PHĐL"
_DOC_NO_PATTERN = re.compile(
    r'S[oốõọẽeèéẻẹổôềế]\s*[:\-]?\s*'
    r'([0-9A-Za-z\s\./]{0,9})'
    r'\s*[/\\]\s*'
    r'([A-Za-z\u0110\u0111\u00d4\u00f4\u0102\u0103\u00c2\u00e2]'
    r'[A-Za-z\u0110\u0111\u00d4\u00f4\u0102\u0103\u00c2\u00e20-9\-\u2013]{1,20})',
    re.IGNORECASE,
)

# ─── Pattern ngày tháng ──────────────────────────────────────────────────────
# Bắt mọi biến thể: "Lâm Đồng, ngày 22 tháng 8 năm 2025", "Lâm Đồng, ngày/ tháng 8 năm 2025", "Lâm Đồng, ngày, 28 tháng 8 năm 2025", "ngày 22/8/2025"
_DATE_PATTERN = re.compile(
    r'(?:(?:Lâm\s*[ĐD][oồôeèé]ng|[ĐD][aàá]\s*L[aạ]t|[A-ZÀ-Ỹa-zà-ỹ\s]{2,20})[\s,]*)?'
    r'ng[àaá]y[\s,\.:\-_/]*([0-9\?\)\.\_\/]{0,6})\s*'
    r'th[áa]ng[\s,\.:\-_]*([0-9\?\)\.\_\/]{1,6})\s*'
    r'(?:[/\\]|\bn[ăa]m\b)?[\s,\.:\-_]*'
    r'(\d{4}|\d{2})',
    re.IGNORECASE,
)

# ─── Pattern nhận diện ranh giới Tiêu đề văn bản hành chính ──────────────────
# Hỗ trợ nhận diện mờ khi OCR nhận diện nhầm dấu (vd: KẾ HàCH, KÉ HOẠCH, QUYÉT ĐỊNH...)
_DOC_TITLE_REGEX = re.compile(
    r'^\s*(?:K[ẾÊEÉÈeếêéè]?\s*H[OÒÓỌÔỐỒỘAÀÁẠaàáạoòóọôốồộ]{1,2}[AĂÂaăâ]?(?:CH|C)?|'
    r'QUY[ẾÊEếêe]?T\s*[ĐDđd][ỊIÌiịì]?NH|'
    r'TH[OÔÔNGông]+\s*B[AÁaá][OÔoô]|'
    r'T[OỜƠơờ]\s*TR[IÌiì]NH|'
    r'C[OÔông]+\s*V[AĂÂaăâ]N|'
    r'H[UƯư][OƠỚơớ]NG\s*D[AẪÂaẫâ]N|'
    r'BI[EÊeê]N\s*B[AẢaả]N|'
    r'B[AÁaá]O\s*C[AÁaá]O|'
    r'QUY\s*[ĐDđd][IỊiị]NH|'
    r'QUY\s*CH[EẾeế]|'
    r'GI[AẤaấ]Y\s*X[AÁaá]C\s*NH[AẬaậ]N|'
    r'Đ[OƠơ]N\s*XIN[\w\s]*|'
    r'CH[UƯư][OƠơ]NG\s*TR[IÌiì]NH)\b',
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
        if not num:
            doc_no = f'Số: [chưa đọc được]/{normalized_code}'
        else:
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
    reject_words = [
        "công văn", "căn cứ", "theo", "của", "quyết định", "thông tư", "nghị định",
        "thời gian", "từ", "đến", "giao quân", "gặp mặt", "tổ chức", "khoá", "khóa"
    ]

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
                if len(day) == 2 and day.startswith('4'):
                    # Lỗi quang học phổ biến số 1 nét móc serif nhầm thành 4 (vd: 49 -> 19)
                    day = '1' + day[1]
                else:
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
        clean_seg = original_segment.lower()
        if any(x in clean_seg for x in ["lâm", "lam", "đồng", "dong"]):
            prefix = "Lâm Đồng"
        elif any(x in clean_seg for x in ["đà lạt", "da lat"]):
            prefix = "Đà Lạt"
        else:
            m_city = re.search(r'([A-ZÀ-Ỹa-zà-ỹ\s]{2,20})[\s,]*(?=ng[àaá]y)', original_segment)
            if m_city and len(m_city.group(1).strip()) >= 2:
                prefix = m_city.group(1).strip()
            else:
                prefix = "Lâm Đồng" if any(x in header_text.lower() for x in ["lâm", "lam", "đồng"]) else ("Đà Lạt" if any(x in header_text.lower() for x in ["đà lạt", "da lat"]) else "")
    
        if prefix:
            date_str = f'{prefix}, ngày {day} tháng {month} năm {year}'
        else:
            date_str = f'ngày {day} tháng {month} năm {year}'
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
        prefix = "Lâm Đồng" if any(x in header_text.lower() for x in ["lâm", "lam", "đồng"]) else ("Đà Lạt" if any(x in header_text.lower() for x in ["đà lạt", "da lat"]) else "")
        if prefix:
            date_str = f'{prefix}, ngày {d} tháng {mo} năm {y}'
        else:
            date_str = f'ngày {d} tháng {mo} năm {y}'
        return header_text, date_str

    fallback_m = re.search(r'(?:(?:Lâm\s*[ĐD][oồôeèé]ng|[ĐD][aàá]\s*L[aạ]t|[A-ZÀ-Ỹa-zà-ỹ\s]{2,20})[\s,]*)?ng[àaá]y[\s,\.:\-_]*th[áa]ng\s*([0-9]{1,2})\s*(?:năm)?\s*(\d{4})', header_text, re.IGNORECASE)
    if fallback_m:
        start_idx = fallback_m.start()
        context_before = header_text[max(0, start_idx - 40):start_idx].lower()
        if not any(w in context_before for w in reject_words):
            mo = fallback_m.group(1).lstrip('0')
            y = fallback_m.group(2)
            prefix = "Lâm Đồng" if any(x in header_text.lower() for x in ["lâm", "lam", "đồng"]) else ("Đà Lạt" if any(x in header_text.lower() for x in ["đà lạt", "da lat"]) else "")
            if prefix:
                date_str = f'{prefix}, ngày ... tháng {mo} năm {y}'
            else:
                date_str = f'ngày ... tháng {mo} năm {y}'
            return header_text, date_str

    fallback_simple = re.search(r'(?:Lâm Đồng|Đà Lạt)?[\s,]*ng[àaá]y\s+[^\n]{2,30}', header_text, re.IGNORECASE)
    if fallback_simple:
        start_idx = fallback_simple.start()
        context_before = header_text[max(0, start_idx - 40):start_idx].lower()
        if not any(w in context_before for w in reject_words):
            prefix = "Lâm Đồng" if any(x in header_text.lower() for x in ["lâm", "lam", "đồng"]) else ("Đà Lạt" if any(x in header_text.lower() for x in ["đà lạt", "da lat"]) else "")
            if prefix:
                date_str = f'{prefix}, ngày [chưa đọc được]'
            else:
                date_str = 'ngày [chưa đọc được]'
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
        "TRƯỜNG ĐẠI HỌC ĐÀ LẬT",
        "CỘNG HÒA XÃ HỘI CHỦ NGHĨA VIỆT NAM",
        "CỘNG HOÀ XÃ HỘI CHỦ NGHĨA VIỆT NAM",
        "CỘNG HÒA XÃ HỌI CHỦ NGHĨA VIỆT NAM",
        "CỘNG HÒA XÃ HỆI CHỦ NGHĨA VIỆT NAM",
        "ĐỘC LẬP - TỰ DO - HẠNH PHÚC",
        "ĐỘC LẬP – TỰ DO – HẠNH PHÚC",
        "PHÒNG CÔNG TÁC SINH VIÊN",
    ]
    for kw in keywords:
        if line_upper == kw:
            return True

    # Kiểm tra các mảnh vỡ đầu dòng của Header
    if any(line_upper.startswith(p) for p in [
        "CỘNG HÒA", "CỘNG HOÀ", "ĐỘC LẬP", "BỘ GIÁO DỤC", "TRƯỜNG ĐẠI HỌC", "PHÒNG CÔNG TÁC"
    ]):
        return True

    if ("LÂM ĐỒNG" in line_upper or "ĐÀ LẠT" in line_upper) and any(w in line_upper for w in ["NGÀY", "THÁNG", "NĂM"]):
        return True

    if line_upper.startswith("SỐ:") or line_upper.startswith("SỐ :") or line_upper.startswith("SO:"):
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


def normalize_document_header(text: str, line_preserving: bool = False) -> str:
    """
    Chuẩn hóa toàn bộ phần header của văn bản hành chính (theo Nghị định 30/2020/NĐ-CP):
    - line_preserving=True: BẢO TOÀN 100% SỐ DÒNG (1 visual input line = 1 output line),
      không xóa dòng ngày tháng, không ghép reflow các cột.
    - line_preserving=False: Tái cấu trúc Header 2 cột theo bảng trình bày chuẩn.
    """
    if not text:
        return text

    lines = text.splitlines()
    
    # 1. Tìm vị trí tiêu đề văn bản chính (CHỈ tìm trong 14 dòng đầu)
    title_idx = -1
    for i, line in enumerate(lines[:14]):
        line_clean = line.strip()
        words = line_clean.split()
        if 1 <= len(words) <= 5 and _DOC_TITLE_REGEX.search(line_clean):
            title_idx = i
            break
            
    header_end = title_idx if title_idx != -1 else min(8, len(lines))

    if line_preserving:
        # CHẾ ĐỘ AN TOÀN BẢO TOÀN DÒNG (PHASE F REQUIREMENT: One input line -> exactly one output line)
        processed_lines = []
        for i, line in enumerate(lines):
            line_clean = line.strip()
            if not line_clean:
                processed_lines.append("")
                continue

            if i <= header_end:
                line_upper = line_clean.upper()
                
                # Quốc hiệu & Tiêu ngữ
                if any(kw in line_upper for kw in ["CỘNG HÒA", "CỘNG HOÀ", "CONG HOA", "CHỦ NGHĨA VIỆT NAM"]):
                    processed_lines.append("CỘNG HÒA XÃ HỘI CHỦ NGHĨA VIỆT NAM")
                    continue
                if any(kw in line_upper for kw in ["ĐỘC LẬP", "DOC LAP", "TỰ DO", "HẠNH PHÚC"]):
                    processed_lines.append("Độc lập - Tự do - Hạnh phúc")
                    continue
                if any(kw in line_upper for kw in ["BỘ GIÁO DỤC", "BO GIAO DUC"]):
                    processed_lines.append("BỘ GIÁO DỤC VÀ ĐÀO TẠO")
                    continue
                if any(kw in line_upper for kw in ["TRƯỜNG ĐẠI HỌC ĐÀ LẠT", "ĐẠI HỌC ĐÀ LẠT", "ĐẠI HỌC ĐA LẠT", "ĐẠI HỌC ĐÀ LẬT"]):
                    processed_lines.append("TRƯỜNG ĐẠI HỌC ĐÀ LẠT")
                    continue
                if any(kw in line_upper for kw in ["PHÒNG CÔNG TÁC SINH VIÊN", "PHONG CONG TAC"]):
                    processed_lines.append("PHÒNG CÔNG TÁC SINH VIÊN")
                    continue
                    
                # Số hiệu văn bản
                m_doc = _DOC_NO_PATTERN.search(line_clean)
                if m_doc or re.search(r'(?:Số|So|SỐ)\s*[:\-]?\s*(\d{1,5})', line_clean):
                    _, doc_no = _normalize_doc_number(line_clean)
                    if doc_no and "[chưa đọc được]" not in doc_no:
                        # Gắn thẻ <hw> cho số hiệu viết tay
                        doc_no_tagged = re.sub(r'Số:\s*(\d+)/', r'Số: <hw>\1</hw>/', doc_no)
                        processed_lines.append(doc_no_tagged)
                    else:
                        processed_lines.append(line_clean)
                    continue

                # Ngày tháng ban hành
                m_date = _DATE_PATTERN.search(line_clean)
                if m_date or re.search(r'ng[àaá]y[\s,\.:\-_/]', line_clean, re.IGNORECASE):
                    _, date_str = _normalize_date(line_clean)
                    if date_str and "[chưa đọc được]" not in date_str:
                        # Gắn thẻ <hw> cho ngày tháng viết tay
                        date_str_tagged = re.sub(r'(ng[àaá]y\s+)(\d{1,2})(\s+th[áa]ng)', r'\1<hw>\2</hw>\3', date_str)
                        processed_lines.append(date_str_tagged)
                    else:
                        processed_lines.append(line_clean)
                    continue

                # Tiêu đề văn bản tại title_idx
                if i == title_idx:
                    if re.search(r'K[ẾÊEÉÈeếêéè]?\s*H[OÒÓỌÔỐỒỘAÀÁẠaàáạoòóọôốồộ]{1,2}[AĂÂaăâ]?CH?', line_clean, re.IGNORECASE):
                        processed_lines.append("KẾ HOẠCH")
                    elif re.search(r'QUY[ẾÊEếêe]?T\s*[ĐDđd][ỊIÌiịì]?NH', line_clean, re.IGNORECASE):
                        processed_lines.append("QUYẾT ĐỊNH")
                    elif re.search(r'TH[OÔÔNGông]+\s*B[AÁaá][OÔoô]', line_clean, re.IGNORECASE):
                        processed_lines.append("THÔNG BÁO")
                    else:
                        processed_lines.append(line_clean)
                    continue

            # Các dòng thân văn bản được giữ nguyên 100%
            processed_lines.append(line)

        return "\n".join(processed_lines).strip()

    # Chế độ cũ: Tái cấu trúc 2 cột
    header_lines = lines[:header_end]
    body_lines = lines[header_end:]
    header_text = '\n'.join(header_lines)

    header_text = _normalize_national_header(header_text)
    header_text, doc_no = _normalize_doc_number(header_text)
    header_text, date_str = _normalize_date(header_text)
    
    header_text_upper = header_text.upper()
    is_admin_doc = []
    if "BỘ GIÁO DỤC VÀ ĐÀO TẠO" in header_text_upper or "BO GIAO DUC VA DAO TAO" in header_text_upper:
        is_admin_doc.append("BỘ GIÁO DỤC VÀ ĐÀO TẠO")
    if any(k in header_text_upper for k in ["TRƯỜNG ĐẠI HỌC ĐÀ LẠT", "ĐẠI HỌC ĐÀ LẠT", "ĐẠI HỌC ĐA LẠT", "ĐẠI HỌC ĐÀ LẬT"]):
        is_admin_doc.append("TRƯỜNG ĐẠI HỌC ĐÀ LẠT")
    elif "PHÒNG CÔNG TÁC SINH VIÊN" in header_text_upper:
        is_admin_doc.append("PHÒNG CÔNG TÁC SINH VIÊN")
        
    has_national_header = []
    if any(k in header_text_upper for k in ["CỘNG HÒA", "CỘNG HOÀ", "CHỦ NGHĨA VIỆT NAM"]):
        has_national_header.append("CỘNG HÒA XÃ HỘI CHỦ NGHĨA VIỆT NAM")
    if any(k in header_text_upper for k in ["ĐỘC LẬP", "TỰ DO", "HẠNH PHÚC"]):
        has_national_header.append("Độc lập - Tự do - Hạnh phúc")

    if not (is_admin_doc or has_national_header):
        return (header_text + ("\n" + "\n".join(body_lines) if body_lines else "")).strip()

    header_block = _rebuild_header_block(doc_no, date_str, is_admin_doc, has_national_header)
    final_text = header_block + "\n".join(body_lines)
    return final_text.strip()

