"""
backend/app/services/tag_service.py — AI Smart Tagging & Priority Taxonomy Service

Hệ thống AI Tự động Gán Nhãn và Phân loại Hồ sơ Sinh viên (Phòng CTSV):
- Phân cấp 5 tầng ưu tiên từ Cao đến Thấp (Priority Score: 100 -> 10).
- Tự động bóc tách và gán nhãn dựa trên ngữ nghĩa OCR và thực thể thực tế.
- TUYỆT ĐỐI KHÔNG tự sinh số hiệu văn bản (số hiệu chỉ bóc tách thực tế trên giấy).
"""
import re
from typing import Any

# Bảng trọng số điểm ưu tiên (Priority Score 100 -> 10)
TAG_PRIORITY_WEIGHTS: dict[str, int] = {
    # Mức 1: Khẩn cấp & Đối tượng chính sách đặc biệt (Điểm 90 - 100)
    "#CanXuLyGap": 100,
    "#ThieuMinhChung": 95,
    "#CanXacMinh": 92,
    "#HoNgheo": 90,
    "#KhuyetTat": 89,
    "#ConThuongBinh": 88,
    "#MoCoi": 87,
    "#CanNgheo": 85,

    # Mức 2: Thể loại văn bản & Chính sách trọng điểm (Điểm 70 - 84)
    "#QuyetDinh": 84,
    "#KeHoach": 82,
    "#MienGiamHocPhi": 80,
    "#HocBongKhuyenKhich": 79,
    "#HocBong": 78,
    "#ThongBao": 76,
    "#HuongDan": 74,
    "#ToTrinh": 72,
    "#VungSauVungXa": 71,
    "#DanTocThieuSo": 70,

    # Mức 3: Trạng thái duyệt & Xác thực (Điểm 50 - 69)
    "#ChoDuyet": 65,
    "#DaDuyetQR": 60,
    "#DaChinhSuaOCR": 55,
    "#TuChoi": 50,

    # Mức 4: Khóa & Khoa / Ngành (Điểm 30 - 49)
    # Tags dynamic: #K44, #K45, #K46, #K47, #K48, #KhoaCNTT, #KhoaKinhTe,... default 40

    # Mức 5: Thủ tục hành chính thường xuyên & Lưu trữ (Điểm 10 - 29)
    "#BaoLuu": 28,
    "#NghiHocTamThoi": 27,
    "#XacNhanSinhVien": 25,
    "#CapLaiTheSV": 22,
    "#ChuyenNganh": 20,
    "#ThoiHoc": 20,
    "#DaLuuTru": 10,
}

TAG_COLOR_MAP: dict[str, str] = {
    # Red: Critical / Urgent
    "#CanXuLyGap": "red",
    "#ThieuMinhChung": "red",
    "#CanXacMinh": "red",
    "#HoNgheo": "red",
    "#KhuyetTat": "red",
    "#ConThuongBinh": "red",
    "#MoCoi": "red",

    # Amber / Orange: Policies & Special Procedures
    "#CanNgheo": "amber",
    "#QuyetDinh": "amber",
    "#KeHoach": "amber",
    "#MienGiamHocPhi": "amber",
    "#HocBongKhuyenKhich": "amber",
    "#HocBong": "amber",
    "#VungSauVungXa": "amber",
    "#DanTocThieuSo": "amber",

    # Blue: Official Notices & Status
    "#ThongBao": "blue",
    "#HuongDan": "blue",
    "#ToTrinh": "blue",
    "#ChoDuyet": "blue",
    "#DaChinhSuaOCR": "blue",

    # Green: Approved
    "#DaDuyetQR": "green",

    # Purple: Cohort & Faculty
    "#KhoaCNTT": "purple",
    "#KhoaKinhTe": "purple",
    "#KhoaLuat": "purple",
    "#KhoaNgoaiNgu": "purple",
    "#KhoaSuPham": "purple",
    "#KhoaDuLich": "purple",
    "#KhoaToanTin": "purple",
    "#KhoaSinhHoc": "purple",

    # Gray: Administrative & Routine
    "#BaoLuu": "gray",
    "#NghiHocTamThoi": "gray",
    "#XacNhanSinhVien": "gray",
    "#CapLaiTheSV": "gray",
    "#ChuyenNganh": "gray",
    "#ThoiHoc": "gray",
    "#TuChoi": "gray",
    "#DaLuuTru": "gray",
}


class TagService:
    """Service xử lý tự động gán nhãn, xếp hạng ưu tiên và phân loại hồ sơ."""

    @staticmethod
    def get_tag_priority(tag: str) -> int:
        """Lấy điểm ưu tiên của tag. Nếu là tag Khóa/Khoa dynamic thì gán 40, còn lại mặc định 30."""
        if tag in TAG_PRIORITY_WEIGHTS:
            return TAG_PRIORITY_WEIGHTS[tag]
        if tag.startswith("#K") and len(tag) <= 5:
            return 45  # Ví dụ #K44, #K48
        if tag.startswith("#Khoa") or tag.startswith("#Lop"):
            return 40
        return 30

    @staticmethod
    def get_tag_color(tag: str) -> str:
        """Lấy màu hiển thị cho badge của nhãn."""
        if tag in TAG_COLOR_MAP:
            return TAG_COLOR_MAP[tag]
        if tag.startswith("#K") or tag.startswith("#Khoa"):
            return "purple"
        return "gray"

    @classmethod
    def calculate_priority_score(cls, tags: list[str]) -> int:
        """Tính tổng điểm ưu tiên của tài liệu dựa trên các nhãn hiện có."""
        if not tags:
            return 0
        return sum(cls.get_tag_priority(t) for t in set(tags))

    @classmethod
    def sort_tags_by_priority(cls, tags: list[str]) -> list[str]:
        """Sắp xếp danh sách nhãn theo thứ tự ưu tiên TỪ CAO ĐẾN THẤP."""
        unique_tags = list(dict.fromkeys(tags))
        return sorted(unique_tags, key=lambda t: cls.get_tag_priority(t), reverse=True)

    @classmethod
    def generate_auto_tags(
        cls,
        text: str,
        metadata: dict[str, Any] | None = None,
        ocr_status: str | None = None,
        is_corrected: bool = False,
        confidence_score: float | None = None,
    ) -> list[str]:
        """
        AI Tự động phân tích ngữ nghĩa nội dung và metadata để sinh bộ nhãn chuẩn hóa.
        Tuyệt đối không sinh số hiệu ngẫu nhiên.
        """
        tags: list[str] = []
        clean_text = (text or "").lower()
        meta = metadata or {}
        extra = meta.get("extra", {}) or {}

        # ── 1. NHÓM KHẨN CẤP & ĐỐI TƯỢNG CHÍNH SÁCH ĐẶC BIỆT ───────────
        if any(k in clean_text for k in ["khẩn", "gấp", "hạn chót", "hạn cuối", "ưu tiên giải quyết", "xử lý ngay"]):
            tags.append("#CanXuLyGap")

        if any(k in clean_text for k in ["bổ sung minh chứng", "thiếu sổ", "thiếu giấy xác nhận", "chưa đủ hồ sơ", "bổ sung hồ sơ"]):
            tags.append("#ThieuMinhChung")

        if (confidence_score is not None and confidence_score < 0.75) or "nghi vấn" in clean_text:
            tags.append("#CanXacMinh")

        if any(k in clean_text for k in ["hộ nghèo", "mã hộ nghèo", "sổ hộ nghèo", "hộ gia đình nghèo"]):
            tags.append("#HoNgheo")
        elif any(k in clean_text for k in ["hộ cận nghèo", "sổ cận nghèo", "cận nghèo"]):
            tags.append("#CanNgheo")

        if any(k in clean_text for k in ["thương binh", "liệt sĩ", "bệnh binh", "người có công", "con thương binh"]):
            tags.append("#ConThuongBinh")

        if any(k in clean_text for k in ["khuyết tật", "tàn tật"]):
            tags.append("#KhuyetTat")

        if any(k in clean_text for k in ["mồ côi", "mất cả cha lẫn mẹ", "không nơi nương tựa"]):
            tags.append("#MoCoi")

        if any(k in clean_text for k in ["vùng sâu", "vùng xa", "khu vực iii", "khu vực 3", "đặc biệt khó khăn", "vùng cao"]):
            tags.append("#VungSauVungXa")

        if any(k in clean_text for k in ["dân tộc thiểu số", "dân tộc: k'ho", "dân tộc k'ho", "ê đê", "tày", "nùng", "h'mông", "chăm", "khmer", "mạ", "chu ru", "ba na"]):
            tags.append("#DanTocThieuSo")

        # ── 2. NHÓM THỂ LOẠI VĂN BẢN HÀNH CHÍNH & THỦ TỤC ───────────────
        if "kế hoạch" in clean_text or "/kh-" in clean_text:
            tags.append("#KeHoach")
        elif "quyết định" in clean_text or "/qđ-" in clean_text or "/qd-" in clean_text:
            tags.append("#QuyetDinh")
        elif "thông báo" in clean_text or "/tb-" in clean_text:
            tags.append("#ThongBao")
        elif "hướng dẫn" in clean_text or "/hd-" in clean_text:
            tags.append("#HuongDan")
        elif "tờ trình" in clean_text or "/ttr-" in clean_text:
            tags.append("#ToTrinh")
        elif "báo cáo" in clean_text or "/bc-" in clean_text:
            tags.append("#BaoCao")

        # Đơn từ sinh viên
        if any(k in clean_text for k in ["miễn giảm học phí", "trợ cấp xã hội", "giảm học phí", "nghị định 81"]):
            tags.append("#MienGiamHocPhi")

        if any(k in clean_text for k in ["học bổng khuyến khích", "học bổng kkht"]):
            tags.append("#HocBongKhuyenKhich")
        elif any(k in clean_text for k in ["học bổng", "xét học bổng"]):
            tags.append("#HocBong")

        if any(k in clean_text for k in ["bảo lưu", "tạm hoãn học tập"]):
            tags.append("#BaoLuu")
        elif any(k in clean_text for k in ["nghỉ học tạm thời", "tạm dừng học"]):
            tags.append("#NghiHocTamThoi")

        if any(k in clean_text for k in ["giấy xác nhận sinh viên", "xác nhận sinh viên", "vay vốn ngân hàng", "hoãn nghĩa vụ"]):
            tags.append("#XacNhanSinhVien")

        if any(k in clean_text for k in ["cấp lại thẻ", "thẻ sinh viên", "làm lại thẻ"]):
            tags.append("#CapLaiTheSV")

        if any(k in clean_text for k in ["chuyển ngành", "chuyển ngành học"]):
            tags.append("#ChuyenNganh")
        elif any(k in clean_text for k in ["thôi học", "xin thôi học"]):
            tags.append("#ThoiHoc")

        # ── 3. NHÓM ĐỊNH DANH KHÓA HỌC & KHOA/NGÀNH ──────────────────
        # Bóc tách Khóa từ MSSV hoặc Lớp
        student_id = str(meta.get("student_id") or "").strip()
        class_name = str(meta.get("class_name") or extra.get("class_name") or "").upper().strip()
        faculty_name = str(meta.get("faculty") or extra.get("faculty") or "").lower().strip()

        # Suy luận Khóa từ MSSV (vd: 2412461 -> K48, 23... -> K47, 22... -> K46, 21... -> K45, 20... -> K44)
        if len(student_id) >= 2 and student_id[:2].isdigit():
            prefix = int(student_id[:2])
            # Mapping niên khóa ĐH Đà Lạt: Khóa 44 = năm 2020 (prefix 20), K48 = 2024 (prefix 24)
            if 15 <= prefix <= 35:
                cohort_num = prefix + 24
                tags.append(f"#K{cohort_num}")

        # Hoặc bóc tách từ tên lớp: CTK44, QTK45, DHKTPM18
        if class_name:
            match_k = re.search(r"K(\d{2})", class_name)
            if match_k:
                tags.append(f"#K{match_k.group(1)}")

        # Bóc tách Khoa / Ngành
        fac_text = f"{faculty_name} {class_name} {clean_text}"
        if any(k in fac_text for k in ["công nghệ thông tin", "cntt", "khoa học máy tính", "kỹ thuật phần mềm", "ktpm", "ctk"]):
            tags.append("#KhoaCNTT")
        elif any(k in fac_text for k in ["kinh tế", "quản trị kinh doanh", "qtkd", "kế toán", "tài chính", "ngân hàng"]):
            tags.append("#KhoaKinhTe")
        elif any(k in fac_text for k in ["luật", "luật học", "luat"]):
            tags.append("#KhoaLuat")
        elif any(k in fac_text for k in ["ngoại ngữ", "tiếng anh", "ngôn ngữ anh", "anh văn"]):
            tags.append("#KhoaNgoaiNgu")
        elif any(k in fac_text for k in ["sư phạm", "giáo dục tiểu học", "su pham"]):
            tags.append("#KhoaSuPham")
        elif any(k in fac_text for k in ["du lịch", "khách sạn", "nhà hàng", "lữ hành"]):
            tags.append("#KhoaDuLich")
        elif any(k in fac_text for k in ["toán", "toán tin", "thống kê"]):
            tags.append("#KhoaToanTin")
        elif any(k in fac_text for k in ["sinh học", "nông lâm", "công nghệ sinh học"]):
            tags.append("#KhoaSinhHoc")

        # ── 4. NHÓM TRẠNG THÁI XỬ LÝ ─────────────────────────────────
        if is_corrected:
            tags.append("#DaChinhSuaOCR")

        if ocr_status:
            status_up = ocr_status.upper()
            if status_up == "APPROVED":
                tags.append("#DaDuyetQR")
            elif status_up == "REJECTED":
                tags.append("#TuChoi")
            elif status_up in ("DONE", "PROCESSING", "PENDING"):
                tags.append("#ChoDuyet")

        # Sắp xếp nhãn theo thứ tự ưu tiên từ cao đến thấp
        return cls.sort_tags_by_priority(tags)


tag_service = TagService()
