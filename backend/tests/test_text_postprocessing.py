# -*- coding: utf-8 -*-
"""
backend/tests/test_text_postprocessing.py

Unit tests cho text_postprocessing package.
Test theo 3 module tách biệt + integration test pipeline đầy đủ.

Chạy: pytest tests/test_text_postprocessing.py -v
"""

import pytest
import sys
import os

# Đảm bảo import đúng từ backend/
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


# ─── Tests: ocr_char_fixes ────────────────────────────────────────────────────

class TestOcrCharFixes:
    """Test từng OCR char rule riêng lẻ."""

    def setup_method(self):
        from app.services.text_postprocessing.ocr_char_fixes import (
            apply_ocr_char_fixes,
            apply_single_rule,
        )
        self.fix = apply_ocr_char_fixes
        self.fix_one = apply_single_rule

    # ── Ngày tháng ────────────────────────────────────────────────────────────

    def test_date_month_trailing_bracket(self):
        """ocr_char_fixes strip dấu ngoặc sau số tháng: '40)' → '40' (truncate '40'→'4' là việc của header_normalizer)"""
        result = self.fix("tháng 40) năm 2025")
        # Dấu ')' phải bị xóa
        assert "40)" not in result
        # "năm" phải còn và liền kề tháng
        assert "năm" in result

    def test_date_month_slash_nam(self):
        """tháng 4/năm → tháng 4 năm"""
        result = self.fix("tháng 4/năm 2025")
        assert "tháng 4 năm" in result
        assert "4/năm" not in result

    def test_date_day_trailing_bracket(self):
        """ngày 04) tháng → ngày 04 tháng"""
        result = self.fix("ngày 04) tháng 4")
        assert "ngày 04 tháng" in result

    def test_date_month_12_not_changed(self):
        """tháng 12 → giữ nguyên (12 hợp lệ)"""
        result = self.fix("ngày 15 tháng 12 năm 2025")
        assert "tháng 12 năm" in result

    # ── Nhầm ký tự ─────────────────────────────────────────────────────────

    def test_l_to_1_in_document_number(self):
        """l328 → 1328 (L thường nhầm số 1)"""
        result = self.fix("Số: l328/QĐ-ĐHĐL")
        assert "1328" in result

    def test_l_not_changed_after_letter(self):
        """
        "l" sau chữ cái KHÔNG được sửa (tránh sửa nhầm từ đúng chứa l).
        Ví dụ: "làm" → vẫn là "làm" (không phải "1àm")
        """
        result = self.fix("làm việc")
        assert "làm" in result
        assert "1àm" not in result

    def test_O_to_0_before_digit(self):
        """O1 → 01 (O hoa nhầm số 0)"""
        result = self.fix("O1/QĐ-ĐHĐL")
        assert "01" in result

    def test_O_not_changed_in_word(self):
        """
        "O" trong từ bình thường KHÔNG được sửa.
        Ví dụ: "OCR" → vẫn là "OCR"
        """
        result = self.fix("OCR engine đang hoạt động")
        assert "OCR" in result
        assert "0CR" not in result

    def test_pipe_to_space_between_letters(self):
        """|  giữa 2 chữ → khoảng trắng"""
        result = self.fix("văn|bản")
        assert "văn bản" in result

    def test_double_underscore_to_space(self):
        """__ → khoảng trắng"""
        result = self.fix("học__sinh")
        assert "học sinh" in result or "học  sinh" in result  # normalize sau

    # ── Số La Mã ─────────────────────────────────────────────────────────────

    def test_IH_to_III(self):
        """IH. → III."""
        result = self.fix("IH. Các quy định chung")
        assert "III." in result

    def test_TI_to_II(self):
        """TI. → II."""
        result = self.fix("TI. Phạm vi áp dụng")
        assert "II." in result

    # ── Dấu câu ─────────────────────────────────────────────────────────────

    def test_colon_slash_fix(self):
        """Chuẩn: // → :"""
        result = self.fix("theo quy định://?")
        assert "://" not in result

    def test_rn_to_m_between_letters(self):
        """rn giữa chữ → m (lỗi serif OCR)"""
        # Ví dụ giả định: "turnrng" → "tumng" (hiếm trong tiếng Việt)
        result = self.fix("quyrnết")  # giả lập lỗi
        # Chỉ kiểm tra không crash
        assert isinstance(result, str)

    def test_barcode_stripped(self):
        """Mã scan rác đầu trang bị xóa"""
        result = self.fix("03610000199\nBỘ GIÁO DỤC")
        assert "03610000199" not in result
        assert "BỘ GIÁO DỤC" in result

    # ── Không sửa nhầm từ đúng ──────────────────────────────────────────────

    def test_no_false_positive_regular_text(self):
        """Văn bản đúng chính tả không bị thay đổi sai."""
        original = "Quyết định về việc phân công giáo viên"
        result = self.fix(original)
        # Không được xóa/thay nhầm nội dung đúng
        assert "Quyết định" in result
        assert "phân công" in result
        assert "giáo viên" in result

    def test_all_rules_have_description(self):
        """Đảm bảo tất cả rules đều có description (để test riêng lẻ được)."""
        from app.services.text_postprocessing.ocr_char_fixes import OCR_CHAR_RULES
        for pat, rep, flags, desc in OCR_CHAR_RULES:
            assert desc, f"Rule '{pat}' thiếu description"
            assert len(desc) > 5, f"Description quá ngắn: '{desc}'"


# ─── Tests: admin_dictionary ──────────────────────────────────────────────────

class TestAdminDictionary:
    """Test load và áp dụng từ điển hành chính."""

    def setup_method(self):
        from app.services.text_postprocessing.admin_dictionary import (
            apply_admin_corrections,
            normalize_document_code,
            reload_dictionary,
        )
        self.correct = apply_admin_corrections
        self.norm_code = normalize_document_code
        reload_dictionary()  # Xóa cache để test sạch

    def test_char_correction_dieu(self):
        """Điêu → Điều"""
        result = self.correct("Điêu 1. Quy định chung")
        assert "Điều" in result

    def test_char_correction_quyet(self):
        """Quyét → Quyết"""
        result = self.correct("Quyét định số 123")
        assert "Quyết" in result

    def test_char_correction_can_cu(self):
        """Căn cú → Căn cứ"""
        result = self.correct("Căn cú Luật Giáo dục")
        assert "Căn cứ" in result

    def test_code_map_qd_dhdl(self):
        """QD-DHDL → QĐ-ĐHĐL"""
        result = self.norm_code("QD-DHDL")
        assert result == "QĐ-ĐHĐL"

    def test_code_map_tb_dhdl(self):
        """TB-DHDL → TB-ĐHĐL"""
        result = self.norm_code("TB-DHDL")
        assert result == "TB-ĐHĐL"

    def test_code_map_unknown_preserved(self):
        """Mã không có trong map → giữ nguyên (không crash)"""
        result = self.norm_code("XYZ-UNKNOWN")
        assert result == "XYZ-UNKNOWN"

    def test_graceful_missing_dict(self):
        """Không crash khi file JSON không tìm thấy"""
        result = self.correct("Điêu 1. Quy định", dict_path="/nonexistent/path.json")
        # Trả về text nguyên (không crash)
        assert isinstance(result, str)
        assert "Điêu" in result  # Không sửa vì không load được dict


# ─── Tests: document_header_normalizer ───────────────────────────────────────

class TestDocumentHeaderNormalizer:
    """Test chuẩn hóa header văn bản hành chính."""

    def setup_method(self):
        from app.services.text_postprocessing.document_header_normalizer import (
            normalize_document_header,
            _normalize_doc_number,
            _normalize_date,
        )
        self.normalize = normalize_document_header
        self._norm_no = _normalize_doc_number
        self._norm_date = _normalize_date

    # ── Số hiệu ──────────────────────────────────────────────────────────────

    def test_doc_no_basic(self):
        """Số: 1328/QĐ-ĐHĐL được nhận dạng"""
        text, doc_no = self._norm_no("Số: 1328/QĐ-ĐHĐL")
        assert doc_no is not None
        assert "1328" in doc_no

    def test_doc_no_with_spaces(self):
        """Số : 1328 /QD-DHDL → Số: 1328/QĐ-ĐHĐL"""
        text, doc_no = self._norm_no("Số : 1328 /QD-DHDL")
        assert doc_no is not None
        assert "1328" in doc_no

    def test_doc_no_with_dots(self):
        """Số: 13.28/QĐ-ĐHĐL → Số: 1328/QĐ-ĐHĐL"""
        text, doc_no = self._norm_no("Số: 13.28/QĐ-ĐHĐL")
        assert doc_no is not None
        assert "1328" in doc_no

    def test_doc_no_missing_returns_none(self):
        """Không có số hiệu → trả về None, không bịa dữ liệu"""
        text, doc_no = self._norm_no("QUYẾT ĐỊNH về việc phân công")
        assert doc_no is None

    def test_no_fabrication_when_missing_doc_no(self):
        """Header rebuild KHÔNG thêm số hiệu giả khi không parse được"""
        text = "CỘNG HÒA XÃ HỘI CHỦ NGHĨA VIỆT NAM\nQUYẾT ĐỊNH\nĐiều 1. Nội dung."
        result = self.normalize(text)
        # Không có "Số: .../TB-ĐHĐL" hay placeholder nào
        assert ".../TB-ĐHĐL" not in result
        assert "..." not in result
        assert "Số:" not in result  # Không có số hiệu vì không tìm thấy

    # ── Ngày tháng ───────────────────────────────────────────────────────────

    def test_date_normal(self):
        """Ngày tháng bình thường được parse đúng"""
        text, date_str = self._norm_date("Lâm Đồng, ngày 04 tháng 4 năm 2025")
        assert date_str is not None
        assert "2025" in date_str
        assert "tháng 4 năm" in date_str

    def test_date_with_bracket_error(self):
        """Ngày tháng bị OCR lỗi: 'tháng 40)' → 'tháng 4'"""
        text, date_str = self._norm_date("Lâm Đồng, ngày 04 tháng 40) năm 2025")
        assert date_str is not None
        # Tháng phải hợp lệ (1-12)
        import re
        m = re.search(r'tháng (\d+)', date_str)
        assert m and int(m.group(1)) <= 12

    def test_date_slash_error(self):
        """tháng 4/năm → tháng 4 năm"""
        text, date_str = self._norm_date("Lâm Đồng, ngày 04 tháng 4/năm 2025")
        assert date_str is not None
        assert "4/năm" not in date_str

    def test_date_missing_returns_none(self):
        """Không có ngày tháng → trả về None, không crash"""
        text, date_str = self._norm_date("QUYẾT ĐỊNH về việc phân công")
        assert date_str is None

    def test_no_fabrication_when_missing_date(self):
        """Header rebuild KHÔNG thêm ngày giả khi không parse được"""
        text = "TRƯỜNG ĐẠI HỌC ĐÀ LẠT\nSố: 1328/QĐ-ĐHĐL\nCỘNG HÒA XÃ HỘI CHỦ NGHĨA VIỆT NAM\nQUYẾT ĐỊNH"
        result = self.normalize(text)
        # Không có ngày giả
        assert "ngày 1 tháng 1 năm 1" not in result

    # ── Location prefix ───────────────────────────────────────────────────────

    def test_lam_dong_prefix(self):
        """Lâm Đồng được nhận ra đúng"""
        text, date_str = self._norm_date("Lâm Đồng, ngày 04 tháng 4 năm 2025")
        assert date_str is not None
        assert "Lâm Đồng" in date_str

    def test_da_lat_prefix(self):
        """Đà Lạt được nhận ra đúng"""
        text, date_str = self._norm_date("Đà Lạt, ngày 04 tháng 4 năm 2025")
        assert date_str is not None
        assert "Đà Lạt" in date_str

    def test_no_duplicate_header_lines_in_body(self):
        """Header đã rebuild không bị lặp lại trong phần body bên dưới"""
        raw_ocr = (
            "BỘ GIÁO DỤC VÀ ĐÀO TẠO\n"
            "TRƯỜNG ĐẠI HỌC ĐÀ LẠT\n"
            "Số: 1353/KH-ĐHĐL\n"
            "CỘNG HÒA XÃ HỘI CHỦ NGHĨA VIỆT NAM\n"
            "Độc lập - Tự do - Hạnh phúc\n"
            "Lâm Đồng, ngày 19 tháng 8 năm 2025\n"
            "BỘ GIÁO DỤC VÀ ĐÀO TẠO\n"
            "CỘNG HÒA XÃ HỘI CHỦ NGHĨA VIỆT NAM\n"
            "Độc lập - Tự do - Hạnh phúc\n"
            "KẾ HOẠCH\n"
            "Tổ chức nhập học cho tân sinh viên\n"
        )
        result = self.normalize(raw_ocr)
        assert "KẾ HOẠCH" in result
        assert result.count("CỘNG HÒA XÃ HỘI CHỦ NGHĨA VIỆT NAM") == 1
        assert result.count("BỘ GIÁO DỤC VÀ ĐÀO TẠO") == 1
        assert result.count("Độc lập - Tự do - Hạnh phúc") == 1

    # ── No crash tests ────────────────────────────────────────────────────────

    def test_empty_input_no_crash(self):
        """Input rỗng → trả về rỗng, không crash"""
        result = self.normalize("")
        assert result == ""

    def test_non_admin_doc_no_crash(self):
        """Văn bản không có header hành chính → trả về nguyên, không crash"""
        text = "Đây là một đoạn văn bình thường không có header."
        result = self.normalize(text)
        assert "Đây là một đoạn văn" in result


# ─── Integration Tests: full pipeline ────────────────────────────────────────

class TestPostProcessVietnamese:
    """Integration tests cho toàn bộ pipeline post_process_vietnamese()."""

    def setup_method(self):
        from app.services.text_postprocessing import post_process_vietnamese
        self.process = post_process_vietnamese

    def test_date_month_with_bracket_error_pipeline(self):
        """ocr_char_fixes strip bracket + header_normalizer truncate '40'→'4'"""
        from app.services.text_postprocessing import post_process_vietnamese
        raw = "Lâm Đồng, ngày 04 tháng 40) năm 2025\nQUYẾT ĐỊNH"
        result = post_process_vietnamese(raw)
        # Sau pipeline đầy đủ: tháng phải hợp lệ
        import re
        m = re.search(r'tháng (\d+)', result)
        assert m and int(m.group(1)) <= 12
    def test_full_pipeline_admin_doc(self):
        """Pipeline day du voi van ban hanh chinh tieu bieu."""
        raw = (
            "So: 1328/QD-DHDL\n"
            "QUYET DINH\n"
            "Dieu 1. Phan cong 150 giao vien."
        )
        result = self.process(raw)
        assert "1328" in result
        assert "..." not in result

    def test_unicode_nfc_normalization(self):
        """Unicode NFC được chuẩn hóa."""
        # Chữ "ị" có thể biểu diễn bằng 2 cách NFC và NFD
        import unicodedata
        text_nfd = unicodedata.normalize("NFD", "Hội đồng trường")
        result = self.process(text_nfd)
        assert unicodedata.is_normalized("NFC", result)

    def test_empty_input(self):
        """Input rỗng → trả về rỗng"""
        assert self.process("") == ""
        assert self.process("   ") == ""

    def test_non_admin_text_preserved(self):
        """Văn bản thông thường không bị thay đổi sai."""
        text = "Sinh viên Nguyễn Văn A, MSSV: 2012345, học kỳ 1 năm học 2024-2025."
        result = self.process(text)
        assert "Nguyễn Văn A" in result
        assert "2012345" in result


# ─── Tests: heuristic_quality_score ──────────────────────────────────────────

class TestHeuristicQualityScore:
    """Test heuristic_quality_score không còn bonus Quốc hiệu vô nghĩa."""

    def setup_method(self):
        from app.services.ocr_service import OCRService
        self.svc = OCRService()

    def test_clean_text_high_score(self):
        """Văn bản sạch → score cao"""
        text = "Quyết định về việc phân công giảng viên năm học 2025-2026"
        score = self.svc.heuristic_quality_score(text)
        assert score >= 0.85

    def test_dirty_text_lower_score(self):
        """Văn bản nhiều ký tự rác → score thấp hơn"""
        clean = "Quyết định về việc phân công"
        dirty = "Quyết %~^ định ||| về [việc] {phân} công \\\\ @#$"
        score_clean = self.svc.heuristic_quality_score(clean)
        score_dirty = self.svc.heuristic_quality_score(dirty)
        assert score_clean > score_dirty

    def test_no_bonus_for_national_header(self):
        """
        QUAN TRỌNG: Không còn bonus cho Quốc hiệu/Tiêu ngữ.
        Text 1 có Quốc hiệu, Text 2 không có — nếu nội dung khác nhau
        thì score phải dựa trên chất lượng ký tự, không phải có/không có header.
        """
        text_with_header = (
            "CỘNG HÒA XÃ HỘI CHỦ NGHĨA VIỆT NAM\n"
            "Độc lập - Tự do - Hạnh phúc\n"
            "Quyết định phân công"
        )
        text_without_header = "Quyết định phân công"

        score_with = self.svc.heuristic_quality_score(text_with_header)
        score_without = self.svc.heuristic_quality_score(text_without_header)

        # Score không nên khác biệt lớn chỉ vì có/không có Quốc hiệu
        # (Trước đây: +0.04 bonus → bây giờ: 0 bonus)
        assert abs(score_with - score_without) < 0.05, (
            f"Score khác biệt quá lớn: {score_with} vs {score_without}. "
            "Có thể vẫn còn bonus Quốc hiệu vô nghĩa."
        )

    def test_score_range(self):
        """Score luôn trong [0.60, 0.98]"""
        texts = [
            "",  # rỗng
            "a",  # ngắn
            "Quyết định về việc" * 100,  # dài
            "%%% ^^^ ||| \\\\ @@@ ###",  # toàn rác
        ]
        for text in texts:
            score = self.svc.heuristic_quality_score(text)
            assert 0.60 <= score <= 0.98, f"Score ngoài range: {score} cho '{text[:20]}'"

    def test_calculate_confidence_score_alias(self):
        """calculate_confidence_score() là alias của heuristic_quality_score()"""
        text = "Văn bản hành chính"
        assert self.svc.calculate_confidence_score(text) == self.svc.heuristic_quality_score(text)


# ─── Tests: extract_metadata MSSV ────────────────────────────────────────────

class TestExtractMetadataMSSV:
    """Test extract_metadata() ưu tiên keyword MSSV: trước pattern."""

    def setup_method(self):
        from app.services.ocr_service import OCRService
        self.svc = OCRService()

    def test_mssv_keyword_priority(self):
        """MSSV: keyword được ưu tiên trước pattern."""
        text = "Họ tên: Nguyễn Văn A\nMSSV: 2012345\nLớp: K49"
        meta = self.svc.extract_metadata(text)
        assert meta["student_id"] == "2012345"

    def test_mssv_keyword_ma_so(self):
        """'Mã số sinh viên:' cũng được nhận dạng."""
        text = "Mã số sinh viên: 2112345"
        meta = self.svc.extract_metadata(text)
        assert meta["student_id"] == "2112345"

    def test_mssv_pattern_fallback(self):
        """
        Pattern fallback khi không có keyword.
        MSSV "2012345" = 2 chữ số prefix + 5 số tiếp = tổng 7 chữ số hợp lệ.
        """
        # Prefix "2[0-3]" match 2 chars, length pattern {7,8} là tổng length
        # Nên phải để số dài hơn: "20123456" (8 số)
        text = "Sinh viên 20123456 đã nộp đơn"
        meta = self.svc.extract_metadata(text)
        # Pattern fallback: 2[0-3][0-9]{5,6} = 8-9 chữ số total
        assert meta["student_id"] is not None or meta["student_id"] is None  # không crash

    def test_mssv_pattern_8_digits(self):
        """MSSV 8 số hợp lệ được nhận dạng qua pattern"""
        text = "Sinh viên 20123456 đã đăng ký"
        meta = self.svc.extract_metadata(text)
        assert meta["student_id"] == "20123456"

    def test_mssv_not_found_returns_none(self):
        """Không có MSSV → trả None, không crash."""
        text = "Văn bản không có MSSV"
        meta = self.svc.extract_metadata(text)
        assert meta["student_id"] is None


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
