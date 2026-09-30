"""
backend/app/services/tag_service.py — AI Smart Tagging & Priority Taxonomy Service

Quy chuẩn phân loại và gán nhãn tinh gọn đúng 5 nhóm cốt lõi theo thứ tự ưu tiên:
1. Số hiệu (nếu có) — vd: #1353_KH_DHDL, #245_QD_DHDL
2. Loại đơn / Loại văn bản — vd: #KeHoach, #QuyetDinh, #ThongBao, #MienGiamHocPhi, #HocBong, #BaoLuu
3. Ngành (nếu có) — vd: #NganhGDMN, #NganhCNTT, #NganhLuat, #NganhQTKD, #NganhKeToan
4. Khoa (nếu có) — vd: #KhoaCNTT, #KhoaSuPham, #KhoaKinhTe, #KhoaLuat, #KhoaNgoaiNgu
5. Khóa (nếu có) — vd: #K49, #K48, #K47, #K46, #K45, #K44
"""
import re
import unicodedata
from typing import Any


def _strip_accents(text: str) -> str:
    """Chuyển đổi chuỗi tiếng Việt sang không dấu để so khớp regex chuẩn xác."""
    if not text:
        return ""
    text = text.replace("đ", "d").replace("Đ", "D")
    normalized = unicodedata.normalize("NFD", text)
    return "".join(c for c in normalized if unicodedata.category(c) != "Mn").lower().strip()


# Bảng trọng số nhóm nhãn ưu tiên (Từ Cao đến Thấp)
TAG_GROUP_PRIORITY = {
    "SO_HIEU": 100,      # 1. Số hiệu văn bản
    "LOAI_DON": 80,      # 2. Loại đơn / loại văn bản
    "NGANH": 60,         # 3. Ngành đào tạo
    "KHOA": 40,          # 4. Khoa / Viện
    "KHOA_HOC": 20,      # 5. Khóa học (K49, K48...)
}


class TagService:
    """Service xử lý tự động gán nhãn tinh gọn 5 nhóm theo yêu cầu."""

    @staticmethod
    def get_tag_category(tag: str) -> str:
        """Phân nhóm cho thẻ nhãn."""
        t = tag.upper()
        if t.startswith("#SO_") or re.search(r"^#[0-9]+", t):
            return "SO_HIEU"
        if t.startswith("#NGANH"):
            return "NGANH"
        if t.startswith("#KHOA") and not re.match(r"^#K[0-9]{2}", t):
            return "KHOA"
        if re.match(r"^#K[0-9]{2}", t) or "KHOA" in t:
            return "KHOA_HOC"
        return "LOAI_DON"

    @classmethod
    def get_tag_priority(cls, tag: str) -> int:
        cat = cls.get_tag_category(tag)
        return TAG_GROUP_PRIORITY.get(cat, 50)

    @classmethod
    def get_tag_color(cls, tag: str) -> str:
        cat = cls.get_tag_category(tag)
        if cat == "SO_HIEU":
            return "red"
        if cat == "LOAI_DON":
            return "amber"
        if cat == "NGANH":
            return "green"
        if cat == "KHOA":
            return "blue"
        if cat == "KHOA_HOC":
            return "purple"
        return "gray"

    @classmethod
    def calculate_priority_score(cls, tags: list[str]) -> int:
        """
        Tính điểm ưu tiên cao nhất của tài liệu.
        Nếu có số hiệu -> 100đ (Mức 1).
        Nếu có Loại đơn/VB -> 80đ (Mức 2).
        Nếu có Ngành/Khoa -> 60đ (Mức 3).
        """
        if not tags:
            return 0
        return max(cls.get_tag_priority(t) for t in tags)

    @classmethod
    def sort_tags_by_priority(cls, tags: list[str]) -> list[str]:
        """Sắp xếp đúng thứ tự: 1.Số hiệu -> 2.Loại đơn -> 3.Ngành -> 4.Khoa -> 5.Khóa."""
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
        AI Tự động trích xuất đúng 5 nhóm nhãn theo thứ tự ưu tiên:
        1. Số hiệu (nếu có)
        2. Loại đơn / Loại văn bản
        3. Ngành (nếu có)
        4. Khoa (nếu có)
        5. Khóa (nếu có)
        """
        tags: list[str] = []
        raw_text = text or ""
        clean_text = raw_text.lower()
        ascii_text = _strip_accents(raw_text)
        meta = metadata or {}
        extra = meta.get("extra", {}) or {}

        # ── 1. SỐ HIỆU (NẾU CÓ) ──────────────────────────────────────
        doc_num = meta.get("document_number") or extra.get("document_number")
        if not doc_num:
            # Tìm số hiệu thực tế trong text (vd: Số: 1353/KH-ĐHĐL, Số: 245/QĐ-ĐHĐL)
            m_num = re.search(r"(?:Số|So)[\s:\.\-]+([0-9]{1,6}\s*/\s*[A-ZĐa-z0-9\-/]+)", raw_text, re.IGNORECASE)
            if m_num:
                doc_num = re.sub(r"\s+", "", m_num.group(1))

        if doc_num:
            ascii_num = _strip_accents(doc_num).upper()
            clean_num_tag = "#" + re.sub(r"[^A-Za-z0-9]+", "_", ascii_num).strip("_")
            tags.append(clean_num_tag)

        # ── 2. LOẠI ĐƠN / LOẠI VĂN BẢN ──────────────────────────────
        # Kiểm tra tiêu đề văn bản hành chính
        if re.search(r"\b(ke\s*hoach|kế\s*hoạch)\b", clean_text) or "/kh-" in clean_text or "/kh-" in ascii_text:
            tags.append("#KeHoach")
        elif re.search(r"\b(quyet\s*dinh|quyết\s*định)\b", clean_text) or "/qđ-" in clean_text or "/qd-" in ascii_text:
            tags.append("#QuyetDinh")
        elif re.search(r"\b(thong\s*bao|thông\s*báo)\b", clean_text) or "/tb-" in clean_text or "/tb-" in ascii_text:
            tags.append("#ThongBao")
        elif re.search(r"\b(huong\s*dan|hướng\s*dẫn)\b", clean_text) or "/hd-" in clean_text:
            tags.append("#HuongDan")
        elif re.search(r"\b(to\s*trinh|tờ\s*trình)\b", clean_text) or "/ttr-" in clean_text:
            tags.append("#ToTrinh")
        elif re.search(r"\b(bao\s*cao|báo\s*cáo)\b", clean_text) or "/bc-" in clean_text:
            tags.append("#BaoCao")
        # Đơn từ sinh viên
        elif re.search(r"mi[eễ]n\s*gi[aả]m\s*h[oọ]c\s*ph[ií]", clean_text):
            tags.append("#MienGiamHocPhi")
        elif re.search(r"h[oọ]c\s*b[oổ]ng\s*khuy[eế]n\s*kh[ií]ch", clean_text):
            tags.append("#HocBongKhuyenKhich")
        elif re.search(r"h[oọ]c\s*b[oổ]ng", clean_text):
            tags.append("#HocBong")
        elif re.search(r"b[aả]o\s*l[uư]u", clean_text):
            tags.append("#BaoLuu")
        elif re.search(r"ngh[iỉ]\s*h[oọ]c\s*t[aạ]m\s*th[oờ]i", clean_text):
            tags.append("#NghiHocTamThoi")
        elif re.search(r"x[aá]c\s*nh[aậ]n\s*sinh\s*vi[eê]n", clean_text):
            tags.append("#XacNhanSinhVien")
        elif re.search(r"c[aấ]p\s*l[aạ]i\s*th[eẻ]\s*sinh\s*vi[eê]n", clean_text):
            tags.append("#CapLaiTheSV")

        # ── 3. NGÀNH (NẾU CÓ) ────────────────────────────────────────
        if re.search(r"(giao\s*duc\s*mam\s*non|mầm\s*non|su\s*pham\s*mam\s*non)", ascii_text):
            tags.append("#NganhGDMN")
        elif re.search(r"(giao\s*duc\s*tieu\s*hoc|tiểu\s*học)", ascii_text):
            tags.append("#NganhGDTH")
        elif re.search(r"(ky\s*thuat\s*phan\s*mem|ktpm)", ascii_text):
            tags.append("#NganhKTPM")
        elif re.search(r"(khoa\s*hoc\s*may\s*tinh|khmt)", ascii_text):
            tags.append("#NganhKHMT")
        elif re.search(r"(cong\s*nghe\s*thong\s*tin|nganh\s*cntt)", ascii_text):
            tags.append("#NganhCNTT")
        elif re.search(r"(quan\s*tri\s*kinh\s*doanh|qtkd)", ascii_text):
            tags.append("#NganhQTKD")
        elif re.search(r"\b(ke\s*toan|kế\s*toán)\b", ascii_text):
            tags.append("#NganhKeToan")
        elif re.search(r"(tai\s*chinh\s*ngan\s*hang|ngan\s*hang)", ascii_text):
            tags.append("#NganhTCNH")
        elif re.search(r"\b(luat\s*hoc|luat\s*kinh\s*te|nganh\s*luat)\b", ascii_text):
            tags.append("#NganhLuat")
        elif re.search(r"(ngon\s*ngu\s*anh|tieng\s*anh)", ascii_text):
            tags.append("#NganhNgonNguAnh")
        elif re.search(r"(quan\s*tri\s*du\s*lich|du\s*lich|khach\s*san)", ascii_text):
            tags.append("#NganhDuLich")
        elif re.search(r"(toan\s*ung\s*dung|toan\s*tin)", ascii_text):
            tags.append("#NganhToanTin")
        elif re.search(r"(nong\s*nghiep|nong\s*lam|sinh\s*hoc)", ascii_text):
            tags.append("#NganhSinhHoc")

        # ── 4. KHOA (NẾU CÓ) ─────────────────────────────────────────
        # Chỉ bóc tách khi có từ "Khoa ..." rõ ràng hoặc từ ngành suy luận chính xác
        faculty_meta = str(meta.get("faculty") or extra.get("faculty") or "").lower()
        full_fac_text = f"{faculty_meta} {ascii_text}"

        if re.search(r"(khoa\s*cong\s*nghe\s*thong\s*tin|khoa\s*cntt)", full_fac_text):
            tags.append("#KhoaCNTT")
        elif re.search(r"(khoa\s*su\s*pham|su\s*pham\s*mam\s*non|giao\s*duc\s*mam\s*non|giao\s*duc\s*tieu\s*hoc)", full_fac_text):
            tags.append("#KhoaSuPham")
        elif re.search(r"(khoa\s*kinh\s*te|khoa\s*qtkd|khoa\s*tai\s*chinh)", full_fac_text):
            tags.append("#KhoaKinhTe")
        elif re.search(r"(khoa\s*luat)", full_fac_text):
            tags.append("#KhoaLuat")
        elif re.search(r"(khoa\s*ngoai\s*ngu)", full_fac_text):
            tags.append("#KhoaNgoaiNgu")
        elif re.search(r"(khoa\s*du\s*lich)", full_fac_text):
            tags.append("#KhoaDuLich")
        elif re.search(r"(khoa\s*toan|khoa\s*toan\s*tin)", full_fac_text):
            tags.append("#KhoaToanTin")
        elif re.search(r"(khoa\s*sinh|khoa\s*nong\s*lam)", full_fac_text):
            tags.append("#KhoaSinhHoc")

        # ── 5. KHÓA (NẾU CÓ) ─────────────────────────────────────────
        # Bóc tách trực tiếp từ cụm từ: "khóa 49", "khoa 49", "k49", "khóa 48", ...
        match_khoa_text = re.search(r"(?:khoa|khóa|k)\s*([0-9]{2})\b", ascii_text)
        if match_khoa_text:
            num = int(match_khoa_text.group(1))
            if 30 <= num <= 55:  # Niên khóa hợp lệ của ĐH Đà Lạt
                tags.append(f"#K{num}")

        # Hoặc từ tên lớp: CTK44, QTK45, DHKTPM18
        class_name = str(meta.get("class_name") or extra.get("class_name") or "").upper()
        if class_name and not any(t.startswith("#K") for t in tags):
            match_k_class = re.search(r"K(\d{2})", class_name)
            if match_k_class:
                tags.append(f"#K{match_k_class.group(1)}")

        # Hoặc từ MSSV: 2412461 -> K48, 2011425 -> K44
        student_id = str(meta.get("student_id") or "").strip()
        if student_id and len(student_id) >= 2 and student_id[:2].isdigit() and not any(t.startswith("#K") for t in tags):
            prefix = int(student_id[:2])
            if 15 <= prefix <= 35:
                tags.append(f"#K{prefix + 24}")

        # Sắp xếp đúng theo thứ tự ưu tiên: Số hiệu -> Loại đơn -> Ngành -> Khoa -> Khóa
        return cls.sort_tags_by_priority(tags)


tag_service = TagService()
