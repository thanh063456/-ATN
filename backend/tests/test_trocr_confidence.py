from app.services.trocr_service import trocr_service


class TestTrOCRConfidenceAndDegeneracy:
    def test_clean_admin_doc_not_degenerate(self):
        """Văn bản hành chính thông thường chứa từ lặp tự nhiên KHÔNG được coi là degenerate."""
        text = (
            "TRƯỜNG ĐẠI HỌC ĐÀ LẠT\n"
            "Số: <hw>1395</hw>/KH-ĐHĐL\n"
            "Lâm Đồng, ngày <hw>25</hw> tháng 8 năm 2025\n"
            "KẾ HOẠCH\n"
            "Về việc tổ chức khai giảng năm học 2025 - 2026\n"
            "Kính gửi: Các phòng, khoa, viện, trung tâm thuộc Trường Đại học Đà Lạt;\n"
            "Căn cứ Quyết định số 123/QĐ-ĐHĐL của Hiệu trưởng Trường Đại học Đà Lạt;\n"
            "Căn cứ Kế hoạch năm học 2025 - 2026 của Trường Đại học Đà Lạt;\n"
            "Nhà trường thông báo kế hoạch tổ chức khai giảng cho toàn thể sinh viên các khóa.\n"
            "Đề nghị các phòng, khoa thông báo tới sinh viên đúng thời gian quy định."
        )
        is_degen, reason = trocr_service._is_degenerate(text)
        assert is_degen is False
        assert reason == ""

        # Score phải cao (>= 0.90), không được bị ép về 0.35
        score = trocr_service.heuristic_quality_score(text)
        assert score >= 0.90

    def test_word_loop_detected_as_degenerate(self):
        """Lặp từ đơn liên tiếp >= 4 lần phải bị phát hiện."""
        text = "Thông báo này học học học học cho sinh viên"
        is_degen, reason = trocr_service._is_degenerate(text)
        assert is_degen is True
        assert "consecutive word loop" in reason

    def test_phrase_loop_detected_as_degenerate(self):
        """Lặp cụm từ liên tiếp >= 3 lần phải bị phát hiện."""
        text = "Sinh viên đại học Sinh viên đại học Sinh viên đại học nhập học"
        is_degen, reason = trocr_service._is_degenerate(text)
        assert is_degen is True
        assert "consecutive phrase loop" in reason

    def test_character_stuttering_detected(self):
        """Ký tự lặp bất thường kéo dài >= 10 lần phải bị phát hiện."""
        text = "Năm học 2025-2026 .................... 0000000000"
        is_degen, reason = trocr_service._is_degenerate(text)
        assert is_degen is True
        assert "character stuttering" in reason

    def test_hw_tags_do_not_penalize_quality_score(self):
        """Thẻ viết tay <hw>...</hw> không bị tính là ký tự rác làm tụt điểm."""
        plain_text = "Số: 1395/KH-ĐHĐL ngày 25 tháng 8 năm 2025 tại Trường Đại học Đà Lạt"
        hw_text = "Số: <hw>1395</hw>/KH-ĐHĐL ngày <hw>25</hw> tháng 8 năm 2025 tại Trường Đại học Đà Lạt"

        score_plain = trocr_service.heuristic_quality_score(plain_text)
        score_hw = trocr_service.heuristic_quality_score(hw_text)

        assert abs(score_plain - score_hw) <= 0.01
        assert score_hw >= 0.90
