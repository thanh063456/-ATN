"""
backend/tests/test_ocr_service.py — OCR Service & Metadata Extraction Unit Tests

Tuân thủ AAA Pattern (Arrange - Act - Assert).
"""

from app.services.ocr_service import ocr_service


def test_extract_metadata_success():
    """Kiểm tra trích xuất đầy đủ MSSV, Họ tên, Ngày tháng và Phân loại từ văn bản OCR."""
    # ── Arrange ───────────────────────────────────────────────────────────
    sample_text = (
        "CỘNG HÒA XÃ HỘI CHỦ NGHĨA VIỆT NAM\n"
        "Độc lập - Tự do - Hạnh phúc\n\n"
        "ĐƠN XIN MIỄN GIẢM HỌC PHÍ\n\n"
        "Kính gửi: Phòng Công tác Sinh viên\n"
        "Em tên là: Lê Hoàng Nam\n"
        "MSSV: 20214567    Lớp: KTTT-01 K66\n"
        "Số: 45/ĐN-CTSV\n"
        "Hà Nội, ngày 15 tháng 09 năm 2026\n"
        "Người làm đơn\n"
        "Lê Hoàng Nam"
    )

    # ── Act ───────────────────────────────────────────────────────────────
    metadata = ocr_service.extract_metadata(sample_text)

    # ── Assert ────────────────────────────────────────────────────────────
    assert metadata["student_id"] == "20214567"
    assert metadata["student_name"] == "Lê Hoàng Nam"
    assert metadata["document_date"] == "2026-09-15"
    assert metadata["document_number"] == "45/ĐN-CTSV"
    assert metadata["detected_category"] == "MIEN_GIAM_HOC_PHI"


def test_extract_metadata_leave_request():
    """Kiểm tra phân loại đơn nghỉ học / bảo lưu."""
    # ── Arrange ───────────────────────────────────────────────────────────
    sample_text = (
        "ĐƠN XIN NGHỈ HỌC TẠM THỜI VÀ BẢO LƯU KẾT QUẢ HỌC TẬP\n"
        "Họ và tên: Trần Thị Thu Hà\n"
        "Mã số sinh viên: 20208899\n"
        "Ngày: 10/08/2026"
    )

    # ── Act ───────────────────────────────────────────────────────────────
    metadata = ocr_service.extract_metadata(sample_text)

    # ── Assert ────────────────────────────────────────────────────────────
    assert metadata["student_id"] == "20208899"
    assert metadata["student_name"] == "Trần Thị Thu Hà"
    assert metadata["document_date"] == "2026-08-10"
    assert metadata["detected_category"] == "DON_NGHI_HOC"


def test_extract_header_document_number_not_body_cancu():
    """Kiểm tra bóc tách số hiệu từ Header, không bị nhầm với số hiệu ở phần căn cứ pháp lý."""
    from app.services.extraction_service import extraction_service
    from app.services.tag_service import tag_service

    text = (
        "BỘ GIÁO DỤC VÀ ĐÀO TẠO                CỘNG HÒA XÃ HỘI CHỦ NGHĨA VIỆT NAM\n"
        "TRƯỜNG ĐẠI HỌC ĐÀ LẠT                 Độc lập - Tự do - Hạnh phúc\n"
        "Số: 1395/KH-ĐHĐL                      Lâm Đồng, ngày 22 tháng 8 năm 2025\n\n"
        "KẾ HOẠCH\n"
        "Tổ chức Lễ kỷ niệm 80 năm thành lập Bộ Quốc gia Giáo dục\n"
        "(nay là Bộ Giáo dục và Đào tạo) và Khai giảng năm học 2025-2026\n\n"
        "Căn cứ kế hoạch số 1153/KH-BGDĐT ngày 08/8/2025 của Bộ Giáo dục và Đào tạo\n"
        "về việc tổ chức Lễ kỷ niệm 80 năm thành lập Bộ Quốc gia Giáo dục\n"
        "Căn cứ công văn số 4746/BGDĐT-VP ngày 13/8/2025 của Bộ Giáo dục và Đào tạo\n"
    )

    metadata = extraction_service.extract_metadata(text)
    assert metadata["document_number"] == "1395/KH-ĐHĐL"

    tags = tag_service.generate_auto_tags(text, metadata=metadata)
    assert "#1395_KH_DHDL" in tags
    assert "#115_KH_BGDDT" not in tags
    assert "#1153_KH_BGDDT" not in tags
    assert "#KeHoach" in tags
    assert "#KhaiGiang" in tags


def test_extract_document_number_with_trocr_hw_tags():
    """Kiểm tra bóc tách số hiệu khi văn bản chứa thẻ viết tay <hw>...</hw> từ TrOCR."""
    from app.services.extraction_service import extraction_service
    from app.services.tag_service import tag_service

    trocr_text = (
        "BỘ GIÁO DỤC VÀ ĐÀO TẠO\n"
        "TRƯỜNG ĐẠI HỌC ĐÀ LẬT\n"
        "Số: <hw>1895</hw>/KH-ĐHĐL\n"
        "CỘNG HÒA XÃ HỆI CHỦ NGHĨA VIỊT NAM\n"
        "Độc lập - Tự do - Hạnh phúc\n"
        "Lâm Đồng, ngày <hw>22</hw> tháng 8 năm 2025\n"
        "KẾ HOẠCH\n"
        "Căn cứ kế hoạch số 115/KH-BGDDT ngày 08/8/2025 của Bộ Giáo dục\n"
    )

    metadata = extraction_service.extract_metadata(trocr_text)
    assert metadata["document_number"] == "1895/KH-ĐHĐL"

    tags = tag_service.generate_auto_tags(trocr_text, metadata=metadata)
    assert "#1895_KH_DHDL" in tags
    assert "#115_KH_BGDDT" not in tags
