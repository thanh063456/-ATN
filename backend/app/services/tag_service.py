"""
backend/app/services/tag_service.py — AI Smart Tagging & Priority Taxonomy Service

Quy chuẩn phân loại và gán nhãn AI thông minh đa chiều theo thứ tự ưu tiên:
1. Số hiệu (nếu có) — vd: #1353_KH_DHDL, #1429_TB_DHDL, #245_QD_DHDL
2. Loại đơn / Loại văn bản — vd: #ThongBao, #KeHoach, #QuyetDinh, #DonTu, #HuongDan, #BaoCao
3. Chủ đề & Nội dung chi tiết (Thông báo về gì? Kế hoạch gì? Đơn gì?):
   - An ninh, an toàn: #AnNinhTratTu, #AnToanGiaoThong, #AnNinhMang, #PhongChongToiPham
   - Nghỉ lễ, Tết: #NghiTet, #TetNguyenDan, #NghiLe, #QuocKhanh2_9
   - Hoạt động CTSV: #DiemRenLuyen, #SinhHoatCongDan, #KhamSucKhoe, #BaoHiemYTe, #BauCu
   - Đào tạo, học vụ: #KhaiGiang, #NhapHoc, #TanSinhVien, #NamHocMoi, #HocPhi, #XuLyHocVu, #DangKyHocPhan, #LichThi, #TotNghiep, #ThucTap
   - Phong trào: #KhoiNghiep, #DLUStartup, #CuocThi, #VanNghe, #HoiThao, #NCKH, #KyNiem80Nam
   - Chi tiết đơn từ: #MienGiamHocPhi, #HocBongKhuyenKhich, #HocBong, #TroCapXaHoi, #BaoLuu, #NghiHocTamThoi, #TroLaiHocTap, #XinThoiHoc, #GiaHanHocTap, #GiaHanHocPhi, #XacNhanSinhVien, #CapLaiTheSV, #CapBangDiem, #ChuyenNganh, #ChuyenLop, #PhucKhao, #CuuXet, #HoanThi, #MienHocGDTC, #MienHocGDQP, #VayVonSinhVien
4. Ngành đào tạo (nếu có) — vd: #NganhGDMN, #NganhCNTT, #NganhLuat, #NganhQTKD, #NganhKeToan
5. Khoa quản lý (nếu có) — vd: #KhoaCNTT, #KhoaSuPham, #KhoaKinhTe, #KhoaLuat, #KhoaNgoaiNgu
6. Khóa học (nếu có) — vd: #K49, #K48, #K47, #K46, #K45, #K44
"""
import re
import unicodedata
from typing import Any


def _strip_accents(text: str) -> str:
    """Chuyển đổi chuỗi tiếng Việt sang không dấu để so khớp regex chuẩn xác."""
    if not text:
        return ""
    text = (
        text.replace("đ", "d")
        .replace("Đ", "D")
        .replace("ð", "d")
        .replace("Ð", "D")
    )
    normalized = unicodedata.normalize("NFD", text)
    return "".join(c for c in normalized if unicodedata.category(c) != "Mn").lower().strip()


# Bảng trọng số nhóm nhãn ưu tiên (Từ Cao đến Thấp)
TAG_GROUP_PRIORITY = {
    "SO_HIEU": 100,      # 1. Số hiệu văn bản
    "LOAI_DON": 85,      # 2. Loại đơn / Loại văn bản hành chính
    "CHU_DE": 70,        # 3. Chủ đề nội dung chi tiết (Thông báo gì, Kế hoạch gì, Đơn gì)
    "NGANH": 55,         # 4. Ngành đào tạo
    "KHOA": 40,          # 5. Khoa / Viện
    "KHOA_HOC": 25,      # 6. Khóa học (K49, K48...)
}


class TagService:
    """Service xử lý tự động gán nhãn thông minh đa chiều theo yêu cầu CTSV."""

    @classmethod
    def get_tag_category(cls, tag: str) -> str:
        """Phân nhóm cho thẻ nhãn."""
        t = tag.upper()
        if t.startswith("#SO_") or re.search(r"^#[0-9]+", t):
            return "SO_HIEU"
        if t.startswith("#NGANH"):
            return "NGANH"
        if t.startswith("#KHOA") and not re.match(r"^#K[0-9]{2}", t):
            return "KHOA"
        if re.match(r"^#K[0-9]{2}", t) or "KHOA_HOC" in t:
            return "KHOA_HOC"
        # Thể loại văn bản hành chính chung
        if t in [
            "#THONGBAO", "#KEHOACH", "#QUYETDINH", "#HUONGDAN",
            "#TOTRINH", "#BAOCAO", "#CONGVAN", "#GIAYMOI",
            "#BIENBAN", "#DANHSACH", "#DONTU"
        ]:
            return "LOAI_DON"
        # Tất cả các nhãn chủ đề nghiệp vụ / loại đơn chi tiết
        return "CHU_DE"

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
        if cat == "CHU_DE":
            return "teal"
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
        - Mức 1 (100đ): Có Số hiệu văn bản
        - Mức 2 (85đ): Có Thể loại văn bản
        - Mức 3 (70đ): Có Chủ đề nghiệp vụ
        - Mức 4 (55đ): Có Ngành đào tạo
        - Mức 5 (40đ): Có Khoa quản lý
        - Mức 6 (25đ): Có Khóa học
        """
        if not tags:
            return 0
        return max(cls.get_tag_priority(t) for t in tags)

    @classmethod
    def sort_tags_by_priority(cls, tags: list[str]) -> list[str]:
        """Sắp xếp đúng thứ tự: 1.Số hiệu -> 2.Loại đơn -> 3.Chủ đề nội dung -> 4.Ngành -> 5.Khoa -> 6.Khóa."""
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
        AI Tự động trích xuất các nhóm nhãn:
        1. Số hiệu (nếu có)
        2. Thể loại văn bản (Thông báo, Kế hoạch, Quyết định, Đơn từ...)
        3. Chủ đề & Nội dung chi tiết:
           - Thông báo về gì? (An ninh trật tự, Nghỉ lễ tết, Học phí, Lịch thi, Khám sức khỏe...)
           - Kế hoạch gì? (Khai giảng, Nhập học, Khởi nghiệp, Điểm rèn luyện, NCKH...)
           - Đơn gì? (Miễn giảm học phí, Bảo lưu, Nghỉ học tạm thời, Xác nhận sinh viên, Cấp lại thẻ...)
        4. Ngành đào tạo (nếu có)
        5. Khoa (nếu có)
        6. Khóa (nếu có)
        """
        tags: list[str] = []
        raw_text = text or ""
        clean_text = raw_text.lower()
        ascii_text = _strip_accents(raw_text)
        meta = metadata or {}
        extra = meta.get("extra", {}) or {}

        trich_yeu = str(meta.get("trich_yeu") or extra.get("trich_yeu") or "").lower()
        title_meta = str(meta.get("title") or "").lower()
        all_ascii = f"{ascii_text} {_strip_accents(trich_yeu)} {_strip_accents(title_meta)}"

        # Vùng tiêu đề & trích yếu (Subject Zone) — loại trừ các căn cứ pháp lý & nơi nhận để tránh nhiễu
        subject_lines = []
        for line in raw_text.split("\n")[:25]:
            l_low = line.strip().lower()
            if l_low.startswith("căn cứ") or l_low.startswith("can cu") or l_low.startswith("điều 1") or l_low.startswith("dieu 1"):
                break
            subject_lines.append(line)
        subject_zone = " ".join(subject_lines)
        focus_ascii = f"{_strip_accents(subject_zone)} {_strip_accents(trich_yeu)} {_strip_accents(title_meta)}"
        topic_target = focus_ascii if len(focus_ascii.strip()) > 15 else all_ascii

        # ── 1. SỐ HIỆU (NẾU CÓ) ──────────────────────────────────────
        doc_num = meta.get("document_number") or extra.get("document_number") or meta.get("so_ky_hieu")
        if not doc_num:
            m_num = re.search(r"(?:Số|So)[\s:\.\-]+([0-9]{1,6}\s*/\s*[A-ZĐa-z0-9\-/]+)", raw_text, re.IGNORECASE)
            if m_num:
                doc_num = re.sub(r"\s+", "", m_num.group(1))

        if doc_num:
            ascii_num = _strip_accents(doc_num).upper()
            clean_num_tag = "#" + re.sub(r"[^A-Za-z0-9]+", "_", ascii_num).strip("_")
            tags.append(clean_num_tag)

        # ── 2. THỂ LOẠI VĂN BẢN CHÍNH ───────────────────────────────
        if re.search(r"\b(ke\s*hoach|kế\s*hoạch)\b", clean_text) or "/kh-" in clean_text or "/kh-" in ascii_text or "kế hoạch" in trich_yeu or "kế hoạch" in title_meta:
            tags.append("#KeHoach")
        elif re.search(r"\b(quyet\s*dinh|quyết\s*định)\b", clean_text) or "/qđ-" in clean_text or "/qd-" in ascii_text or "quyết định" in trich_yeu or "quyết định" in title_meta:
            tags.append("#QuyetDinh")
        elif re.search(r"\b(thong\s*bao|thông\s*báo)\b", clean_text) or "/tb-" in clean_text or "/tb-" in ascii_text or "thông báo" in trich_yeu or "thông báo" in title_meta:
            tags.append("#ThongBao")
        elif re.search(r"\b(huong\s*dan|hướng\s*dẫn)\b", clean_text) or "/hd-" in clean_text:
            tags.append("#HuongDan")
        elif re.search(r"\b(to\s*trinh|tờ\s*trình)\b", clean_text) or "/ttr-" in clean_text:
            tags.append("#ToTrinh")
        elif re.search(r"\b(bao\s*cao|báo\s*cáo)\b", clean_text) or "/bc-" in clean_text:
            tags.append("#BaoCao")
        elif re.search(r"\b(cong\s*van|công\s*văn)\b", clean_text) or "/cv-" in clean_text:
            tags.append("#CongVan")
        elif re.search(r"\b(giay\s*moi|giấy\s*mời)\b", clean_text) or "/gm-" in clean_text:
            tags.append("#GiayMoi")
        elif re.search(r"\b(bien\s*ban|biên\s*bản)\b", clean_text) or "/bb-" in clean_text:
            tags.append("#BienBan")
        elif re.search(r"\b(danh\s*sach|danh\s*sách)\b", clean_text) or "/ds-" in clean_text:
            tags.append("#DanhSach")

        # ── 3. CHỦ ĐỀ NỘI DUNG CHI TIẾT (THÔNG BÁO VỀ GÌ? KẾ HOẠCH GÌ? ĐƠN GÌ?) ───────
        # A. An ninh trật tự & An toàn giao thông
        if re.search(r"\b(an\s*ninh\s*trat\s*tu|antt|trat\s*tu\s*an\s*ninh)\b", topic_target) or "an ninh trat tu" in topic_target:
            tags.append("#AnNinhTratTu")
        if re.search(r"\b(an\s*toan\s*giao\s*thong|atgt|trat\s*tu\s*an\s*toan\s*giao\s*thong)\b", topic_target) or "an toan giao thong" in topic_target:
            tags.append("#AnToanGiaoThong")
        if re.search(r"(phong\s*chong\s*toi\s*pham|te\s*nan\s*xa\s*hoi)", topic_target):
            tags.append("#PhongChongToiPham")

        # B. Nghỉ Lễ & Nghỉ Tết
        if re.search(r"\b(nghi\s*tet|tet\s*nguyen\s*dan|tet\s*binh\s*ngo|tet\s*am\s*lich|tet\s*duong\s*lich)\b", topic_target):
            tags.append("#NghiTet")
            if "tet nguyen dan" in topic_target or "binh ngo" in topic_target:
                tags.append("#TetNguyenDan")
        elif re.search(r"\b(nghi\s*le|nghi\s*dip\s*le|dip\s*nghi\s*le)\b", topic_target) or "quoc khanh" in topic_target:
            tags.append("#NghiLe")

        if re.search(r"(quoc\s*khanh|2[\/\-_]9|02[\/\-_]09)", topic_target) or "quoc khanh" in topic_target:
            tags.append("#QuocKhanh2_9")

        # C. An ninh mạng & Tuyên truyền
        if re.search(r"(khong\s*gian\s*mang|an\s*ninh\s*mang|phat\s*tan.*video|binh\s*luan.*tieu\s*cuc)", topic_target):
            tags.append("#AnNinhMang")
        if re.search(r"(tuyen\s*truyen|quan\s*triet|pho\s*bien\s*phap\s*luat)", topic_target) and "#AnNinhMang" in tags:
            tags.append("#TuyenTruyen")

        # D. Khởi nghiệp & Cuộc thi
        if re.search(r"(khoi\s*nghiep|dlu[\-_]startup|dlu\s*startup|y\s*tuong\s*sang\s*tao)", topic_target):
            tags.append("#KhoiNghiep")
            if "dlu" in topic_target and "startup" in topic_target:
                tags.append("#DLUStartup")
        if re.search(r"\b(cuoc\s*thi|hoi\s*thi|vong\s*chung\s*ket)\b", topic_target):
            tags.append("#CuocThi")

        # E. Khai giảng & Nhập học & Năm học mới
        if re.search(r"(khai\s*giang|le\s*khai\s*giang)", topic_target):
            tags.append("#KhaiGiang")
        if re.search(r"(nhap\s*hoc|don\s*tan\s*sinh\s*vien|thu\s*tuc\s*nhap\s*hoc)", topic_target):
            tags.append("#NhapHoc")
        if re.search(r"(tan\s*sinh\s*vien|sinh\s*vien\s*moi)", topic_target):
            tags.append("#TanSinhVien")
        if re.search(r"\b(nam\s*hoc\s*moi)\b", topic_target):
            tags.append("#NamHocMoi")

        # F. Điểm rèn luyện
        if re.search(r"(diem\s*ren\s*luyen|ket\s*qua\s*ren\s*luyen|danh\s*gia\s*ren\s*luyen|\bdrl\b)", topic_target):
            tags.append("#DiemRenLuyen")

        # G. Y tế, Khám sức khỏe & Bảo hiểm y tế
        if re.search(r"(kham\s*suc\s*khoe|cong\s*tac\s*y\s*te|y\s*te\s*hoc\s*duong)", topic_target):
            tags.append("#KhamSucKhoe")
        if re.search(r"(bao\s*hiem\s*y\s*te|\bbhyt\b)", topic_target):
            tags.append("#BaoHiemYTe")

        # H. Sinh hoạt công dân
        if re.search(r"(sinh\s*hoat\s*cong\s*dan|tuan\s*shcd|\bshcd\b)", topic_target):
            tags.append("#SinhHoatCongDan")

        # I. Học phí, Học bổng & Chế độ chính sách
        if re.search(r"mi[eễ]n\s*gi[aả]m\s*h[oọ]c\s*ph[ií]", clean_text) or "mien giam hoc phi" in topic_target:
            tags.append("#MienGiamHocPhi")
        elif re.search(r"\b(thu\s*hoc\s*phi|nop\s*hoc\s*phi|dong\s*hoc\s*phi|thong\s*bao\s*hoc\s*phi|tien\s*hoc\s*phi)\b", topic_target):
            tags.append("#HocPhi")

        if re.search(r"h[oọ]c\s*b[oổ]ng\s*khuy[eế]n\s*kh[ií]ch", clean_text) or "hoc bong khuyen khich" in topic_target:
            tags.append("#HocBongKhuyenKhich")
        elif re.search(r"h[oọ]c\s*b[oổ]ng", clean_text) or "hoc bong" in topic_target:
            tags.append("#HocBong")

        if re.search(r"(tro\s*cap\s*xa\s*hoi|chinh\s*sach\s*xa\s*hoi)", topic_target):
            tags.append("#TroCapXaHoi")
        if re.search(r"(chi\s*phi\s*hoc\s*tap|ho\s*tro\s*chi\s*phi)", topic_target):
            tags.append("#ChiPhiHocTap")

        # J. Học vụ, Lịch thi, Đăng ký học phần, Tốt nghiệp
        if re.search(r"(xu\s*ly\s*hoc\s*vu|canh\s*bao\s*hoc\s*vu)", topic_target):
            tags.append("#XuLyHocVu")
        if re.search(r"(dang\s*ky\s*hoc\s*phan|dang\s*ky\s*mon\s*hoc|thoi\s*khoa\s*bieu)", topic_target):
            tags.append("#DangKyHocPhan")
        if re.search(r"(lich\s*thi|thi\s*ket\s*thuc|thi\s*hoc\s*ky)", topic_target):
            tags.append("#LichThi")
        if re.search(r"(tot\s*nghiep|xet\s*tot\s*nghiep|trao\s*bang|nhan\s*bang)", topic_target):
            tags.append("#TotNghiep")

        # K. Bầu cử
        if re.search(r"(bau\s*cu|quoc\s*hoi\s*khoa|hoi\s*dong\s*nhan\s*dan|the\s*cu\s*tri)", topic_target):
            tags.append("#BauCu")

        # L. Kiến tập / Thực tập
        if re.search(r"(kien\s*tap|thuc\s*tap\s*tot\s*nghiep|thuc\s*tap\s*su\s*pham|thuc\s*tap\s*doanh\s*nghiep)", topic_target):
            tags.append("#ThucTap")

        # M. Nghiên cứu khoa học
        if re.search(r"(nghien\s*cuu\s*khoa\s*hoc|\bnckh\b)", topic_target):
            tags.append("#NCKH")

        # N. Văn nghệ & Thể thao
        if re.search(r"(dem\s*tho|nguyen\s*tieu|giao\s*luu\s*van\s*hoa|van\s*nghe|hoi\s*dien)", topic_target):
            tags.append("#VanNghe")
        if re.search(r"(hoi\s*thao|giai\s*bong\s*da|the\s*thao|the\s*duc\s*the\s*thao)", topic_target):
            tags.append("#HoiThao")

        # O. Kỷ niệm
        if re.search(r"(ky\s*niem\s*80\s*nam|bo\s*quoc\s*gia\s*giao\s*duc)", topic_target):
            tags.append("#KyNiem80Nam")

        # P. Ban cán sự, Ban chấp hành
        if re.search(r"(ban\s*can\s*su|ban\s*chap\s*hanh|\bbcs\b|\bbch\b)", topic_target):
            tags.append("#BanCanSu")

        # Q. Đơn từ sinh viên chi tiết (Đơn gì?)
        if re.search(r"b[aả]o\s*l[uư]u", clean_text) or "bao luu" in all_ascii:
            tags.append("#BaoLuu")
        if re.search(r"ngh[iỉ]\s*h[oọ]c\s*t[aạ]m\s*th[oờ]i", clean_text) or "nghi hoc tam thoi" in all_ascii:
            tags.append("#NghiHocTamThoi")
        if re.search(r"tr[oờ]\s*l[aạ]i\s*h[oọ]c\s*t[aậ]p", clean_text) or "tro lai hoc tap" in all_ascii:
            tags.append("#TroLaiHocTap")
        if re.search(r"xin\s*th[oô]i\s*h[oọ]c|r[uú]t\s*h[oồ]\s*s[oơ]", clean_text) or "thoi hoc" in all_ascii or "rut ho so" in all_ascii:
            tags.append("#XinThoiHoc")
        if re.search(r"gia\s*h[aạ]n\s*th[oờ]i\s*gian\s*h[oọ]c\s*t[aậ]p|gia\s*h[aạ]n\s*h[oọ]c\s*t[aậ]p", clean_text) or "gia han hoc tap" in all_ascii:
            tags.append("#GiaHanHocTap")
        if re.search(r"gia\s*h[aạ]n\s*n[oọ]p\s*h[oọ]c\s*ph[ií]", clean_text) or "gia han nop hoc phi" in all_ascii or "gia han hoc phi" in all_ascii:
            tags.append("#GiaHanHocPhi")
        if re.search(r"x[aá]c\s*nh[aậ]n\s*sinh\s*vi[eê]n", clean_text) or "xac nhan sinh vien" in all_ascii:
            tags.append("#XacNhanSinhVien")
        if re.search(r"c[aấ]p\s*l[aạ]i\s*th[eẻ]\s*sinh\s*vi[eê]n|l[aà]m\s*l[aạ]i\s*th[eẻ]", clean_text) or "cap lai the" in all_ascii or "lam lai the" in all_ascii:
            tags.append("#CapLaiTheSV")
        if re.search(r"c[aấ]p\s*b[aả]ng\s*đi[eể]m", clean_text) or "cap bang diem" in all_ascii:
            tags.append("#CapBangDiem")
        if re.search(r"chuy[eể]n\s*ng[aà]nh", clean_text) or "chuyen nganh" in all_ascii:
            tags.append("#ChuyenNganh")
        if re.search(r"chuy[eể]n\s*l[oớ]p", clean_text) or "chuyen lop" in all_ascii:
            tags.append("#ChuyenLop")
        if re.search(r"ph[uú]c\s*kh[aả]o", clean_text) or "phuc khao" in all_ascii:
            tags.append("#PhucKhao")
        if re.search(r"c[uứ]u\s*x[eé]t", clean_text) or "cuu xet" in all_ascii:
            tags.append("#CuuXet")
        if re.search(r"ho[aã]n\s*thi", clean_text) or "hoan thi" in all_ascii:
            tags.append("#HoanThi")
        if re.search(r"mi[eễ]n\s*h[oọ]c\s*(?:gdtc|gi[aá]o\s*d[uụ]c\s*th[eể]\s*ch[aấ]t)", clean_text) or "mien hoc gdtc" in all_ascii:
            tags.append("#MienHocGDTC")
        if re.search(r"mi[eễ]n\s*h[oọ]c\s*(?:gdqp|qu[oố]c\s*ph[oò]ng)", clean_text) or "mien hoc gdqp" in all_ascii:
            tags.append("#MienHocGDQP")
        if re.search(r"vay\s*v[oố]n|ng[aâ]n\s*h[aà]ng\s*ch[ií]nh\s*s[aá]ch", clean_text) or "vay von" in all_ascii:
            tags.append("#VayVonSinhVien")

        don_tu_specific = [
            "#MienGiamHocPhi", "#HocBongKhuyenKhich", "#BaoLuu", "#NghiHocTamThoi",
            "#TroLaiHocTap", "#XinThoiHoc", "#GiaHanHocTap", "#GiaHanHocPhi",
            "#XacNhanSinhVien", "#CapLaiTheSV", "#CapBangDiem", "#ChuyenNganh",
            "#ChuyenLop", "#PhucKhao", "#CuuXet", "#HoanThi",
            "#MienHocGDTC", "#MienHocGDQP", "#VayVonSinhVien", "#TroCapXaHoi"
        ]
        if any(t in don_tu_specific for t in tags) or "đơn xin" in clean_text or "đơn đề nghị" in clean_text or "don xin" in all_ascii:
            if "#DonTu" not in tags:
                tags.append("#DonTu")

        # ── 4. NGÀNH ĐÀO TẠO (NẾU CÓ) ───────────────────────────────
        if re.search(r"(giao\s*duc\s*mam\s*non|mầm\s*non|su\s*pham\s*mam\s*non)", all_ascii):
            tags.append("#NganhGDMN")
        elif re.search(r"(giao\s*duc\s*tieu\s*hoc|tiểu\s*học)", all_ascii):
            tags.append("#NganhGDTH")
        elif re.search(r"(ky\s*thuat\s*phan\s*mem|ktpm)", all_ascii):
            tags.append("#NganhKTPM")
        elif re.search(r"(khoa\s*hoc\s*may\s*tinh|khmt)", all_ascii):
            tags.append("#NganhKHMT")
        elif re.search(r"(cong\s*nghe\s*thong\s*tin|nganh\s*cntt)", all_ascii):
            tags.append("#NganhCNTT")
        elif re.search(r"(quan\s*tri\s*kinh\s*doanh|qtkd)", all_ascii):
            tags.append("#NganhQTKD")
        elif re.search(r"\b(ke\s*toan|kế\s*toán)\b", all_ascii):
            tags.append("#NganhKeToan")
        elif re.search(r"(tai\s*chinh\s*ngan\s*hang|ngan\s*hang)", all_ascii):
            tags.append("#NganhTCNH")
        elif re.search(r"\b(luat\s*hoc|luat\s*kinh\s*te|nganh\s*luat)\b", all_ascii):
            tags.append("#NganhLuat")
        elif re.search(r"(ngon\s*ngu\s*anh|tieng\s*anh)", all_ascii):
            tags.append("#NganhNgonNguAnh")
        elif re.search(r"(quan\s*tri\s*du\s*lich|du\s*lich|khach\s*san)", all_ascii):
            tags.append("#NganhDuLich")
        elif re.search(r"(toan\s*ung\s*dung|toan\s*tin)", all_ascii):
            tags.append("#NganhToanTin")
        elif re.search(r"(nong\s*nghiep|nong\s*lam|sinh\s*hoc)", all_ascii):
            tags.append("#NganhSinhHoc")

        # ── 5. KHOA QUẢN LÝ (NẾU CÓ) ─────────────────────────────────
        faculty_meta = str(meta.get("faculty") or extra.get("faculty") or "").lower()
        full_fac_text = f"{faculty_meta} {all_ascii}"

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

        # ── 6. KHÓA HỌC (NẾU CÓ) ─────────────────────────────────────
        match_khoa_text = re.search(r"(?:khoa|khóa|k)\s*([0-9]{2})\b", all_ascii)
        if match_khoa_text:
            num = int(match_khoa_text.group(1))
            if 30 <= num <= 55:  # Niên khóa hợp lệ của ĐH Đà Lạt
                tags.append(f"#K{num}")

        class_name = str(meta.get("class_name") or extra.get("class_name") or "").upper()
        if class_name and not any(t.startswith("#K") for t in tags):
            match_k_class = re.search(r"K(\d{2})", class_name)
            if match_k_class:
                tags.append(f"#K{match_k_class.group(1)}")

        student_id = str(meta.get("student_id") or "").strip()
        if student_id and len(student_id) >= 2 and student_id[:2].isdigit() and not any(t.startswith("#K") for t in tags):
            prefix = int(student_id[:2])
            if 15 <= prefix <= 35:
                tags.append(f"#K{prefix + 24}")

        # Giới hạn tối đa 4 nhãn chủ đề chi tiết để đảm bảo độ súc tích, thẩm mỹ
        topic_tags = [t for t in tags if cls.get_tag_category(t) == "CHU_DE"]
        if len(topic_tags) > 4:
            keep_topics = set(topic_tags[:4])
            tags = [t for t in tags if cls.get_tag_category(t) != "CHU_DE" or t in keep_topics]

        return cls.sort_tags_by_priority(tags)


tag_service = TagService()
