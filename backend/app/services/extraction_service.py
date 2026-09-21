"""
backend/app/services/extraction_service.py — Smart Form Field & Entity Extraction

Trích xuất tự động các trường dữ liệu thực thể từ văn bản OCR của hồ sơ sinh viên:
- Họ và tên sinh viên (student_name)
- Mã số sinh viên (student_id / mssv)
- Lớp học (class_name)
- Khoa / Viện đào tạo (faculty)
- Loại văn bản / Đơn từ (document_type)
- Lý do làm đơn (reason)
- Ngày tháng văn bản (document_date)
"""
import re
from datetime import datetime
from typing import Any


class ExtractionService:
    """Service trích xuất thông tin có cấu trúc từ văn bản OCR tự do."""

    @staticmethod
    def extract_metadata(text: str) -> dict[str, Any]:
        if not text:
            return {}

        clean_text = text.replace("\r\n", "\n")
        extracted: dict[str, Any] = {
            "student_name": None,
            "student_id": None,
            "class_name": None,
            "faculty": None,
            "document_type": None,
            "reason": None,
            "document_date": None,
            "extra": {},
        }

        # 1. Trích xuất MSSV (6 - 10 chữ số hoặc tiền tố SV)
        # Các mẫu: MSSV: 20210678, Mã số sinh viên: 2212461, Mã SV: 20198812
        mssv_patterns = [
            r"(?:MSSV|Mã\s*số\s*sinh\s*viên|Mã\s*SV|Mã\s*số\s*SV)[\s:\.\-]+([A-Za-z0-9]{6,12})",
            r"(?:Sinh\s*viên|SV)\s*số[\s:\.\-]+([0-9]{6,10})",
            r"\b(20[12][0-9]{5,7}|2[1-9][0-9]{5,6})\b",  # Heuristic năm nhập học (vd: 2212461, 20210678)
        ]
        for pat in mssv_patterns:
            m = re.search(pat, clean_text, re.IGNORECASE)
            if m:
                extracted["student_id"] = m.group(1).strip()
                break

        # 2. Trích xuất Họ và tên
        # Các mẫu: Em tên là: Nguyễn Văn A, Họ và tên: Trần Thị B, Tên sinh viên: Lê C
        name_patterns = [
            r"(?:Họ\s*và\s*tên|Họ\s*tên|Em\s*tên\s*là|Tôi\s*tên\s*là|Tên\s*sinh\s*viên|Sinh\s*viên)[\s:\.\-]+([A-ZÀ-Ỹa-zà-ỹ\s]{3,35})(?=\n|,|\.|\s{2,}|MSSV|Lớp|Mã)",
            r"(?:Người\s*làm\s*đơn|Người\s*viết\s*đơn)\s*\n+\s*(?:\([^\)]+\)\s*\n+)?([A-ZÀ-Ỹa-zà-ỹ\s]{3,35})",
        ]
        for pat in name_patterns:
            m = re.search(pat, clean_text, re.IGNORECASE)
            if m:
                name_candidate = m.group(1).strip()
                # Loại bỏ các từ thừa
                name_candidate = re.sub(r"^(là|em|tôi)\s+", "", name_candidate, flags=re.IGNORECASE)
                if len(name_candidate.split()) >= 2 and len(name_candidate) >= 4:
                    extracted["student_name"] = name_candidate.title()
                    break

        # 3. Trích xuất Lớp học
        class_patterns = [
            r"(?:Lớp|Chi\s*đoàn)[\s:\.\-]+([A-Za-z0-9\-\s/]{3,20})(?=\n|,|\.|\s{2,}|Khoa|MSSV)",
        ]
        for pat in class_patterns:
            m = re.search(pat, clean_text, re.IGNORECASE)
            if m:
                cls = m.group(1).strip()
                if len(cls) >= 3:
                    extracted["class_name"] = cls
                    extracted["extra"]["class_name"] = cls
                    break

        # 4. Trích xuất Khoa / Viện
        faculty_patterns = [
            r"(?:Khoa|Viện|Trường)[\s:\.\-]+([A-ZÀ-Ỹa-zà-ỹ\s\(\)\-]{4,40})(?=\n|,|\.|\s{2,}|Lớp)",
        ]
        for pat in faculty_patterns:
            m = re.search(pat, clean_text, re.IGNORECASE)
            if m:
                extracted["faculty"] = m.group(1).strip().title()
                extracted["extra"]["faculty"] = extracted["faculty"]
                break

        # 5. Trích xuất Loại văn bản / Đơn từ
        doc_type_keywords = [
            ("DON_NGHI_HOC", ["nghỉ học tạm thời", "xin bảo lưu", "tạm ngừng học"]),
            ("HOC_BONG", ["học bổng", "khuyến khích học tập", "xét học bổng"]),
            ("MIEN_GIAM_HOC_PHI", ["miễn giảm học phí", "giảm học phí", "trợ cấp xã hội"]),
            ("GIAY_XAC_NHAN", ["giấy xác nhận sinh viên", "xác nhận sinh viên", "cấp lại thẻ"]),
            ("KHEN_THUONG", ["khen thưởng", "nckh", "nghiên cứu khoa học"]),
        ]
        lower_text = clean_text.lower()
        for type_code, kws in doc_type_keywords:
            if any(kw in lower_text for kw in kws):
                extracted["document_type"] = type_code
                extracted["extra"]["document_type"] = type_code
                break

        # 6. Trích xuất Lý do làm đơn
        reason_patterns = [
            r"(?:Lý\s*do|Lí\s*do|Vì\s*lý\s*do|Nguyên\s*nhân)[\s:\.\-]+([^\n\.]{8,150})",
        ]
        for pat in reason_patterns:
            m = re.search(pat, clean_text, re.IGNORECASE)
            if m:
                extracted["reason"] = m.group(1).strip()
                extracted["extra"]["reason"] = extracted["reason"]
                break

        # 7. Trích xuất Ngày làm đơn (vd: Đà Lạt, ngày 20 tháng 08 năm 2026 hoặc 20/08/2026)
        date_patterns = [
            r"(?:ngày\s*(\d{1,2})\s*tháng\s*(\d{1,2})\s*năm\s*(\d{4}))",
            r"(\d{1,2})[/\-\.](\d{1,2})[/\-\.](\d{4})",
        ]
        for pat in date_patterns:
            m = re.search(pat, clean_text, re.IGNORECASE)
            if m:
                try:
                    d, month, y = int(m.group(1)), int(m.group(2)), int(m.group(3))
                    extracted["document_date"] = datetime(y, month, d)
                except ValueError:
                    pass
                break

        return extracted


extraction_service = ExtractionService()
