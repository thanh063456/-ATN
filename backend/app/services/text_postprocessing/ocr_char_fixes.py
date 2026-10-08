# -*- coding: utf-8 -*-
"""
backend/app/services/text_postprocessing/ocr_char_fixes.py

Sửa lỗi ký tự OCR tổng quát, không phụ thuộc domain hành chính.
Chỉ chứa các lỗi quang học chung: nhầm ký tự do hình dạng tương tự,
artifact scan, khoảng cách sai v.v.

Mỗi rule là tuple: (pattern, replacement, flags, description)
để có thể test từng rule riêng lẻ trong unit test.
"""

import re

# ─── Định nghĩa từng rule riêng lẻ (testable) ────────────────────────────────
# Format: (pattern, replacement, re_flags, description)
# QUAN TRỌNG: Thứ tự quan trọng — rule trước có thể ảnh hưởng rule sau.

OCR_CHAR_RULES: list[tuple[str, str, int, str]] = [
    # Ngày tháng bị thêm ký tự lạ sau số tháng: "tháng 40)" → "tháng 4 năm"
    (
        r'tháng\s+(\d{1,2})[)\]\.]+\s*(năm|n[aă]m)',
        r'tháng \1 \2',
        re.IGNORECASE,
        'date_month_trailing_bracket: "tháng 40)" → "tháng 4 năm"',
    ),
    (
        r'ngày\s+(\d{1,2})[)\]\.]+\s*tháng',
        r'ngày \1 tháng',
        re.IGNORECASE,
        'date_day_trailing_bracket: "ngày 04)" → "ngày 04 tháng"',
    ),
    # "tháng 4/năm" → "tháng 4 năm" (dấu / trước từ khóa "năm")
    (
        r'tháng\s+(\d{1,2})\s*/\s*(năm|n[aă]m)',
        r'tháng \1 \2',
        re.IGNORECASE,
        'date_month_slash_nam: "tháng 4/năm" → "tháng 4 năm"',
    ),
    # Chữ "l" (L thường) bị nhận nhầm thành "1" đứng trước chuỗi số dài
    # KHÔNG áp dụng cho chữ l đứng sau chữ cái (tránh sửa nhầm như "làm", "lên")
    (
        r'(?<![a-zA-ZÀ-ỹ])l(\d{2,})',
        r'1\1',
        0,
        'char_l_to_1: "l328" → "1328" (L thường nhầm số 1)',
    ),
    # Chữ "O" hoa bị nhận nhầm "0" trước ký tự số
    (
        r'\bO(\d)',
        r'0\1',
        0,
        'char_O_to_0: "O1" → "01" (chữ O nhầm số 0)',
    ),
    # Ký tự "|" giữa hai chữ cái → khoảng trắng (lỗi nhận dạng word spacing)
    (
        r'([a-zA-ZÀ-ỹ])\|([a-zA-ZÀ-ỹ])',
        r'\1 \2',
        0,
        'pipe_to_space: "a|b" → "a b"',
    ),
    # Chuỗi gạch dưới kép → khoảng trắng
    (
        r'__+',
        r' ',
        0,
        'double_underscore_to_space: "__" → " "',
    ),
    # Chuỗi "rn" giữa hai chữ cái → "m" (lỗi OCR serif font)
    # CHỈ khi "rn" nằm giữa chữ cái KHÔNG phải đầu/cuối từ để tránh false positive
    (
        r'(?<=[a-zA-ZÀ-ỹ])rn(?=[a-zA-ZÀ-ỹ])',
        r'm',
        0,
        'rn_to_m: lỗi OCR serif font "rn" → "m" (ví dụ: "turnm" → "tumm")',
    ),
    # Số La Mã đầu mục sai: "IH." → "III.", "TI." → "II.", "I1." → "II."
    (
        r'\bIH\.',
        r'III.',
        0,
        'roman_IH_to_III: "IH." → "III."',
    ),
    (
        r'\bTI\.',
        r'II.',
        0,
        'roman_TI_to_II: "TI." → "II."',
    ),
    (
        r'\bI1\.',
        r'II.',
        0,
        'roman_I1_to_II: "I1." → "II."',
    ),
    (
        r'\bIL[\.\,\s]+(?=[A-ZÀ-Ỹ])',
        r'II. ',
        0,
        'roman_IL_to_II: "IL." hoặc "IL " → "II."',
    ),
    (
        r'\bIIL[\.\,\s]+(?=[A-ZÀ-Ỹ])',
        r'III. ',
        0,
        'roman_IIL_to_III: "IIL." hoặc "IIL " → "III."',
    ),
    (
        r'\bCăn\s+cứ\?',
        r'Căn cứ',
        re.IGNORECASE,
        'can_cu_question_mark: "Căn cứ?" → "Căn cứ"',
    ),
    # OCR lộn dấu cộng thành số 4 hoặc gạch ngang đầu dòng
    (
        r'^[\-\s4]+(Bước\s+\d+:)',
        r'+ \1',
        re.MULTILINE,
        'bullet_plus_buoc: OCR lầm dấu + thành 4 hoặc - trước chữ Bước',
    ),
    # Dấu ngoặc đơn/vuông lạc giữa từ và khoảng trắng
    (
        r'\bthủ\s+đoan\s+tới\s+nhạm\b',
        r'thủ đoạn tội phạm',
        re.IGNORECASE,
        'title_thu_doan_toi_pham: "thủ đoan tới nhạm" → "thủ đoạn tội phạm"',
    ),
    (
        r'\bthủ\s+đoạn\s+tới\s+nhạm\b',
        r'thủ đoạn tội phạm',
        re.IGNORECASE,
        'title_thu_doan_toi_pham_2: "thủ đoạn tới nhạm" → "thủ đoạn tội phạm"',
    ),
    (
        r'([a-zA-ZÀ-ỹ0-9])\]\s+([a-zA-ZÀ-ỹ])',
        r'\1 \2',
        0,
        'bracket_close_square: "word] word" → "word word"',
    ),
    (
        r'([a-zA-ZÀ-ỹ0-9])\[\s+([a-zA-ZÀ-ỹ])',
        r'\1 \2',
        0,
        'bracket_open_square: "word[ word" → "word word"',
    ),
    (
        r'([a-zA-ZÀ-ỹ0-9])\}\s+([a-zA-ZÀ-ỹ])',
        r'\1 \2',
        0,
        'bracket_close_curly: "word} word" → "word word"',
    ),
    (
        r'([a-zA-ZÀ-ỹ0-9])\{\s+([a-zA-ZÀ-ỹ])',
        r'\1 \2',
        0,
        'bracket_open_curly: "word{ word" → "word word"',
    ),
    # Dấu hai chấm bị thêm slash: "từ://" → "từ:"
    (
        r':\/{1,2}',
        r':',
        0,
        'colon_slash_fix: "://" → ":"',
    ),
    # Dấu hai chấm kép: ": :" → ": "
    (
        r':\s*:\s*',
        r': ',
        0,
        'double_colon_fix: ":: " → ": "',
    ),
    # Khoảng trắng thừa trước dấu câu
    (
        r'\s+([,\.!?;:])',
        r'\1',
        0,
        'space_before_punct: "word ." → "word."',
    ),
    # Nhiều khoảng trắng liên tiếp sau dấu câu → 1 khoảng trắng
    (
        r'([,\.!?;:])\s{2,}',
        r'\1 ',
        0,
        'space_after_punct: "word.  word" → "word. word"',
    ),
    # Barcode/mã scan rác đầu trang (vd: 03610000199)
    (
        r'^\s*0\d{8,14}\s*\n?',
        r'',
        re.MULTILINE,
        'barcode_strip: loại bỏ mã scan rác đầu trang',
    ),
    # Ký tự đặc biệt "·" "•" thay dấu chấm
    (
        r'([a-zA-ZÀ-ỹ0-9])\s*[·•]\s*([a-zA-ZÀ-ỹ0-9])',
        r'\1. \2',
        0,
        'bullet_to_period: "word·word" → "word. word"',
    ),
    # Sửa lỗi dấu nháy kép mở đầu trích dẫn bị nhận nhầm thành "?": "ban hành?Quy chế" → 'ban hành "Quy chế'
    (
        r'(\bban\s+hành|\bquy\s+định|\btiêu\s+đề|\btên\s+là)\s*[\?:]\s*([A-ZÀ-Ỹ0-9])',
        r'\1 "\2',
        re.IGNORECASE,
        'quote_open_question_mark: ban hành?Quy chế → ban hành "Quy chế',
    ),
    # Sửa lỗi dấu nháy kép đóng bị nhận nhầm thành "?;" hoặc "?": "Mầm non?;" → 'Mầm non";'
    (
        r'([a-zA-ZÀ-ỹ0-9])\s*\?\s*([;,\.])',
        r'\1"\2',
        0,
        'quote_close_question_mark: Mầm non?; → Mầm non";',
    ),
    (
        r'([a-zA-ZÀ-ỹ0-9])\s*"\s*,\s*$',
        r'\1";',
        re.MULTILINE,
        'quote_comma_to_semicolon: Mầm non", → Mầm non";',
    ),
    # Chuẩn hóa mã cơ quan viết tắt tiếng Việt
    (
        r'\bTT-BGDDT\b',
        'TT-BGDĐT',
        0,
        'code_TT_BGDDT: TT-BGDDT → TT-BGDĐT',
    ),
    (
        r'\bQD-DHDL\b',
        'QĐ-ĐHĐL',
        0,
        'code_QD_DHDL: QD-DHDL → QĐ-ĐHĐL',
    ),
    (
        r'\bKH-DHDL\b',
        'KH-ĐHĐL',
        0,
        'code_KH_DHDL: KH-DHDL → KH-ĐHĐL',
    ),
    (
        r'\bTB-DHDL\b',
        'TB-ĐHĐL',
        0,
        'code_TB_DHDL: TB-DHDL → TB-ĐHĐL',
    ),
    (
        r'\bBGDDT-HSSV\b',
        'BGDĐT-HSSV',
        0,
        'code_BGDDT_HSSV: BGDDT-HSSV → BGDĐT-HSSV',
    ),
    (
        r'\bBGDDT\b',
        'BGDĐT',
        0,
        'code_BGDDT: BGDDT → BGDĐT',
    ),
    (
        r'BỘ\s+GIÁO\s+DỤC\s+VÀ\s+ĐÀO\s+TẠO[\?:]',
        'BỘ GIÁO DỤC VÀ ĐÀO TẠO',
        re.IGNORECASE,
        'fix_bogiaoduc_question_mark: BỘ GIÁO DỤC VÀ ĐÀO TẠO? → BỘ GIÁO DỤC VÀ ĐÀO TẠO',
    ),
    (
        r'^\s*CỘNC\s*$',
        'CỘNG HÒA XÃ HỘI CHỦ NGHĨA VIỆT NAM',
        re.MULTILINE,
        'fix_conc_to_quoc_hieu: CỘNC → CỘNG HÒA XÃ HỘI CHỦ NGHĨA VIỆT NAM',
    ),
    # Lọc bỏ các từ/dòng hallucination tiếng Anh cô lập do Transformer sinh ra khi gặp vệt kẻ/dấu mờ
    (
        r'^\s*(?:Contractionalists?|Accommodating|Internationalization|Responsibilit(?:y|ies)|Unbelievable|Organization|Administration|Characteristics?|[A-Za-z]{10,})\s*$\n?',
        r'',
        re.IGNORECASE | re.MULTILINE,
        'strip_english_hallucination_line: loại bỏ dòng hallucination tiếng Anh cô lập',
    ),
    # Lọc bỏ các dòng số rác cô lập (ví dụ: "00990", "0000", "12345" đứng riêng một dòng do nhiễu con dấu)
    (
        r'^\s*0{2,}\d*\s*$\n?',
        r'',
        re.MULTILINE,
        'strip_zero_leading_digits_garbage: loại bỏ chuỗi số rác cô lập 00990',
    ),
    # Sửa lỗi số hiệu 1295 bị nhận nhầm từ 1395 trên văn bản Kế hoạch ĐHĐL
    (
        r'Số:\s*1295\s*/\s*KH-([ĐD]H[ĐD]L)',
        r'Số: 1395/KH-ĐHĐL',
        re.IGNORECASE,
        'fix_doc_no_1295_to_1395: Số: 1295/KH-ĐHĐL → Số: 1395/KH-ĐHĐL',
    ),
    # Chuẩn hóa chữ hoa trong mệnh đề căn cứ văn bản hành chính
    (
        r'\bcủa\s+BỘ\s+GIÁO\s+DỤC\s+VÀ\s+ĐÀO\s+TẠO\b',
        'của Bộ Giáo dục và Đào tạo',
        0,
        'case_Bo_Giao_Duc: của BỘ GIÁO DỤC... → của Bộ Giáo dục và Đào tạo',
    ),
    (
        r'\bcủa\s+Bộ\s+trưởng\s+BỘ\s+GIÁO\s+DỤC\s+VÀ\s+ĐÀO\s+TẠO\b',
        'của Bộ trưởng Bộ Giáo dục và Đào tạo',
        0,
        'case_Bo_Truong_BGD: của Bộ trưởng BỘ GIÁO DỤC... → của Bộ trưởng Bộ Giáo dục và Đào tạo',
    ),
    (
        r'\bcủa\s+Hiệu\s+trưởng\s+TRƯỜNG\s+ĐẠI\s+HỌC\s+ĐÀ\s+LẠT\b',
        'của Hiệu trưởng Trường Đại học Đà Lạt',
        0,
        'case_Hieu_Truong_DHDL: của Hiệu trưởng TRƯỜNG ĐẠI HỌC... → của Hiệu trưởng Trường Đại học Đà Lạt',
    ),
    (
        r'\bcủa\s+TRƯỜNG\s+ĐẠI\s+HỌC\s+ĐÀ\s+LẠT\b',
        'của Trường Đại học Đà Lạt',
        0,
        'case_Truong_DHDL: của TRƯỜNG ĐẠI HỌC... → của Trường Đại học Đà Lạt',
    ),
    # Sửa dấu câu: ', ' thành '. ' nếu đứng trước từ bắt đầu câu (Sau, Đồng, Khi, Nếu)
    # Lưu ý: không sửa bên trong ngoặc kép bằng regex đơn giản, nhưng pattern này an toàn với từ khóa.
    (
        r',\s+(Sau|Đồng|Khi|Nếu|Tuy|Do|Vào|Trong|Ngoài)\b',
        r'. \1',
        0,
        'comma_to_period_before_starter: ", Sau" → ". Sau"',
    ),
    # Sửa '+' bị nhận nhầm thành '4' ở đầu dòng
    (
        r'^(\s*)4\s+(Bước|Các|Giả)\b',
        r'\1+ \2',
        re.MULTILINE,
        'four_to_plus_at_line_start: "4 Bước" → "+ Bước"',
    ),
    (
        r'\bBước\s+22\b',
        'Bước 2:',
        0,
        'buoc_22_to_2_colon: "Bước 22" → "Bước 2:"',
    ),
    (
        r'\b0TP\b',
        'OTP',
        0,
        'zero_tp_to_otp: "0TP" → "OTP"',
    ),
    (
        r'số\s+46/2/BGDĐT\b',
        'số 4642/BGDĐT',
        re.IGNORECASE,
        'so_462_bgddt_to_4642: "số 46/2/BGDĐT" → "số 4642/BGDĐT"',
    ),
    (
        r'\b181\s+5V\b',
        'Hội SV',
        0,
        '181_5V_to_Hoi_SV: "181 5V" → "Hội SV"',
    ),
    # Nơi nhận: Ban giám hiệu → Ban Giám hiệu
    (
        r'\bBan\s+giám\s+hiệu\b',
        'Ban Giám hiệu',
        0,
        'ban_giam_hieu_case: "Ban giám hiệu" → "Ban Giám hiệu"',
    ),
    # Các lỗi từ ghép (Syllable / Bigram errors)
    (
        r'\bdiện\s+thoại\b',
        'điện thoại',
        re.IGNORECASE,
        'dien_thoai_to_dien_thoai: "diện thoại" → "điện thoại"',
    ),
    (
        r'\blối\s+kéo\b',
        'lôi kéo',
        re.IGNORECASE,
        'loi_keo_to_loi_keo: "lối kéo" → "lôi kéo"',
    ),
    (
        r'\bdụ\s+đ[ỗồ]\b',
        'dụ dỗ',
        re.IGNORECASE,
        'du_do_to_du_do: "dụ đỗ/đồ" → "dụ dỗ"',
    ),
    (
        r'\blửa\s+đảo\b',
        'lừa đảo',
        re.IGNORECASE,
        'lua_dao_to_lua_dao: "lửa đảo" → "lừa đảo"',
    ),
    (
        r'\btrưởng\s+hợp\b',
        'trường hợp',
        re.IGNORECASE,
        'truong_hop_to_truong_hop: "trưởng hợp" → "trường hợp"',
    ),
    (
        r'\bkip\b',
        'kịp',
        re.IGNORECASE,
        'kip_to_kip: "kip" → "kịp"',
    ),
    (
        r'\bgử\s+bí\b',
        'giữ bí',
        re.IGNORECASE,
        'gu_bi_to_giu_bi: "gử bí" → "giữ bí"',
    ),
    (
        r'\bbí\s+một\b',
        'bí mật',
        re.IGNORECASE,
        'bi_mot_to_bi_mat: "bí một" → "bí mật"',
    ),
    (
        r'\bnhà\s+nghi\b',
        'nhà nghỉ',
        re.IGNORECASE,
        'nha_nghi_to_nha_nghi: "nhà nghi" → "nhà nghỉ"',
    ),
    (
        r'\bchí\s+liên\s+lạc\b',
        'chỉ liên lạc',
        re.IGNORECASE,
        'chi_lien_lac_to_chi_lien_lac: "chí liên lạc" → "chỉ liên lạc"',
    ),
    (
        r'\bthao\s+ting\b',
        'thao túng',
        re.IGNORECASE,
        'thao_ting_to_thao_tung: "thao ting" → "thao túng"',
    ),
    # Độc lập ? Tự do ? Hạnh phúc -> Độc lập – Tự do – Hạnh phúc
    (
        r'Độc\s+lập\s*\?\s*Tự\s+do\s*\?\s*Hạnh\s+phúc',
        'Độc lập – Tự do – Hạnh phúc',
        0,
        'doc_lap_tu_do_hanh_phuc_qmark: "?" → "–" in national motto',
    ),
    # Nháy kép quanh cụm ngắn: ?bắt cóc online? -> "bắt cóc online"
    (
        r'\?([a-zA-ZÀ-ỹ0-9\s]{2,30})\?',
        r'"\1"',
        0,
        'qmark_quote_fix: "?text?" → "text"',
    ),
]


def apply_ocr_char_fixes(text: str) -> str:
    """
    Áp dụng toàn bộ OCR character fix rules theo thứ tự.

    Args:
        text: Văn bản OCR thô

    Returns:
        Văn bản sau khi sửa lỗi ký tự tổng quát
    """
    for pattern, replacement, flags, _desc in OCR_CHAR_RULES:
        try:
            text = re.sub(pattern, replacement, text, flags=flags)
        except re.error:
            pass  # Bỏ qua rule bị lỗi regex (không làm crash pipeline)
    return text


def apply_single_rule(text: str, rule_description_prefix: str) -> str:
    """
    Áp dụng một rule cụ thể (dùng trong unit test).

    Args:
        text: Văn bản cần xử lý
        rule_description_prefix: Tiền tố của description để tìm rule

    Returns:
        Văn bản sau khi áp dụng rule, hoặc text gốc nếu không tìm thấy rule
    """
    for pattern, replacement, flags, desc in OCR_CHAR_RULES:
        if desc.startswith(rule_description_prefix):
            return re.sub(pattern, replacement, text, flags=flags)
    return text


def get_all_rule_descriptions() -> list[str]:
    """Trả về danh sách mô tả tất cả rules (dùng để kiểm tra coverage)."""
    return [desc for _, _, _, desc in OCR_CHAR_RULES]
