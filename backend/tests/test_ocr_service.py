"""
backend/tests/test_ocr_service.py — OCR Service & Metadata Extraction Unit Tests

Tuân thủ AAA Pattern (Arrange - Act - Assert).
"""
import pytest
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
