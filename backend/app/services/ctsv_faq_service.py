# ==============================================================================
# DocuCTSV - CTSV Intelligent Regulation FAQ & Acronym Normalizer Engine
# Hệ thống Hỏi đáp Thông minh Quy chế CTSV & Phân giải Viết tắt / Không dấu
# Trường Đại học Đà Lạt (DLU) - Cơ sở Nhà A11
# ==============================================================================

import re
import unicodedata
from typing import Any
from app.schemas.search import RequiredFormItem


def strip_accents(text: str) -> str:
    """Loại bỏ toàn bộ dấu tiếng Việt để đối sánh truy vấn không dấu."""
    if not text:
        return ""
    text = unicodedata.normalize("NFD", text)
    text = "".join(c for c in text if unicodedata.category(c) != "Mn")
    text = text.replace("đ", "d").replace("Đ", "d")
    return unicodedata.normalize("NFC", text).lower().strip()


# Từ điển 45+ từ viết tắt, tiếng lóng học vụ sinh viên ĐH Đà Lạt
CTSV_ACRONYM_RAW: dict[str, str] = {
    # Cơ quan & Địa điểm
    "nha a11": "Nhà A11 Phòng CTSV",
    "phong ctsv": "Phòng Công tác Sinh viên",
    "p ctsv": "Phòng Công tác Sinh viên",
    "a11": "Nhà A11",

    # Chế độ & Học bổng
    "mghp": "miễn giảm học phí",
    "mg hp": "miễn giảm học phí",
    "hb kkht": "học bổng khuyến khích học tập",
    "kkht": "học bổng khuyến khích học tập",
    "hbdn": "học bổng tài trợ doanh nghiệp",
    "hb dn": "học bổng tài trợ doanh nghiệp",
    "hb": "học bổng",
    "htcpht": "hỗ trợ chi phí học tập",
    "htcp": "hỗ trợ chi phí học tập",

    # Văn bản quy phạm pháp luật
    "nd81": "Nghị định 81/2021/NĐ-CP",
    "nd 81": "Nghị định 81/2021/NĐ-CP",
    "nđ81": "Nghị định 81/2021/NĐ-CP",
    "nđ 81": "Nghị định 81/2021/NĐ-CP",
    "qd66": "Quyết định 66/2013/QĐ-TTg",
    "qd 66": "Quyết định 66/2013/QĐ-TTg",
    "qđ66": "Quyết định 66/2013/QĐ-TTg",
    "qd688": "Quyết định 688/QĐ-ĐHĐL",
    "qđ688": "Quyết định 688/QĐ-ĐHĐL",
    "qd450": "Quyết định 450/QĐ-ĐHĐL",
    "qđ450": "Quyết định 450/QĐ-ĐHĐL",

    # Rèn luyện & Sinh hoạt
    "drl": "điểm rèn luyện",
    "dtrl": "điểm rèn luyện",
    "shcd": "sinh hoạt công dân sinh viên",
    "shcdsv": "sinh hoạt công dân sinh viên",

    # Điểm số & Học vụ
    "cpa": "điểm tích lũy CPA",
    "gpa": "điểm trung bình học kỳ GPA",
    "cdr": "chuẩn đầu ra tốt nghiệp",
    "ctdt": "chương trình đào tạo",
    "ctđt": "chương trình đào tạo",
    "cvht": "cố vấn học tập",
    "blht": "bảo lưu kết quả học tập",
    "gdtc": "giáo dục thể chất thể dục",
    "gdqp-an": "giáo dục quốc phòng an ninh",
    "gdqpan": "giáo dục quốc phòng an ninh",
    "gdqp": "giáo dục quốc phòng an ninh",

    # Nghĩa vụ & Chế độ phúc lợi
    "tam hoan nvqs": "tạm hoãn nghĩa vụ quân sự",
    "hoan nvqs": "tạm hoãn nghĩa vụ quân sự",
    "nvqs": "nghĩa vụ quân sự",
    "bhyt": "bảo hiểm y tế",
    "ktx": "Ký túc xá DLU",
    "ctsv": "Công tác Sinh viên",
    "the sv": "thẻ sinh viên",
    "the dlu": "thẻ sinh viên Đại học Đà Lạt",
    "tsv": "thẻ sinh viên",
    "nhcsxh": "Ngân hàng Chính sách Xã hội",
    "csxh": "Chính sách xã hội",
    "dhdl": "Đại học Đà Lạt",
    "dlu": "Đại học Đà Lạt",
    "stk": "số tài khoản đóng học phí",
    "hp": "học phí",

    # Biểu mẫu hành chính BM
    "bm01": "biểu mẫu BM-01-HBKK",
    "bm 01": "biểu mẫu BM-01-HBKK",
    "bm02": "biểu mẫu BM-02-MGHP",
    "bm 02": "biểu mẫu BM-02-MGHP",
    "bm03": "biểu mẫu BM-03-BLHT",
    "bm 03": "biểu mẫu BM-03-BLHT",
    "bm04": "biểu mẫu BM-04-XNSV",
    "bm 04": "biểu mẫu BM-04-XNSV",
    "bm05": "biểu mẫu BM-05-KTX",
    "bm 05": "biểu mẫu BM-05-KTX",
    "bm06": "biểu mẫu BM-06-HBDN",
    "bm 06": "biểu mẫu BM-06-HBDN",
    "bm07": "biểu mẫu BM-07-CTSV",
    "bm 07": "biểu mẫu BM-07-CTSV",
    "bm08": "biểu mẫu BM-08-GHHP",
    "bm 08": "biểu mẫu BM-08-GHHP",
}

# Sắp xếp các cụm từ theo chiều dài giảm dần để regex khớp cụm dài trước
_SORTED_ACRONYM_KEYS = sorted(CTSV_ACRONYM_RAW.keys(), key=lambda x: len(x), reverse=True)
_ACRONYM_REGEX = re.compile(r"\b(" + "|".join(re.escape(k) for k in _SORTED_ACRONYM_KEYS) + r")\b", re.IGNORECASE)


def resolve_acronyms_and_slang(text: str) -> tuple[str, bool]:
    """Phân giải từ viết tắt & thuật ngữ lóng của sinh viên thành từ ngữ quy chế chuẩn."""
    def _replacer(m: re.Match) -> str:
        token = m.group(0).lower()
        return CTSV_ACRONYM_RAW.get(token, m.group(0))

    resolved, count = _ACRONYM_REGEX.subn(_replacer, text)
    return resolved, count > 0


# Thư viện 50 Tri thức Quy chế CTSV & Trợ lý Sinh viên Đại học Đà Lạt
FAQ_KNOWLEDGE_BASE: list[dict[str, Any]] = [
    # ── 1. ĐỜI SỐNG, THỜI TIẾT & GIAO TIẾP TRỢ LÝ ──────────────────────────────
    {
        "id": "faq_thoi_tiet_da_lat",
        "keywords": ["thoi tiet", "da lat", "thoi tiet da lat", "troi lanh", "nhiet do", "suong mu", "mac gi", "mua gio", "di choi"],
        "matched_article": "Cẩm nang Đời sống & Khí hậu Sinh viên Đà Lạt",
        "regulation_title": "Cẩm nang Sinh viên Đại học Đà Lạt — Xứ sở sương mù và ngàn hoa",
        "summary_answer": "Đà Lạt hôm nay thời tiết se lạnh đặc trưng (khoảng 16°C - 22°C), trời quang mây, sương mù nhẹ về đêm và sáng sớm. Các bạn sinh viên nên chuẩn bị áo ấm khi lên giảng đường.",
        "detail_content": (
            "Gợi ý sinh hoạt & học tập cho sinh viên DLU:\n"
            "• Ban ngày: Thời tiết mát dịu (19°C - 22°C), thích hợp học tập trên giảng đường và tự học tại Thư viện Nhà A26.\n"
            "• Chiều tối: Nhiệt độ giảm nhanh xuống 15°C - 17°C, sương lạnh; sinh viên nên trang bị áo khoác dày, khăn ấm khi đi học ca tối hoặc sinh hoạt câu lạc bộ.\n"
            "• Chú ý giữ gìn sức khỏe đường hô hấp trong mùa sương mù để đảm bảo tiến độ học tập và rèn luyện."
        ),
        "confidence_score": 0.99,
        "required_forms": [],
        "related_articles": [
            "Cẩm nang Văn hóa & Đời sống Sinh viên DLU",
            "Nội quy Sinh hoạt Người học Trường Đại học Đà Lạt",
        ],
    },
    {
        "id": "faq_chao_hoi_tro_ly",
        "keywords": ["chao", "xin chao", "hello", "hi", "ban la ai", "ai do", "gioi thieu", "tro ly la gi", "chao ban", "hoi dap"],
        "matched_article": "Giới thiệu Hệ thống Trợ lý DocuCTSV",
        "regulation_title": "Trợ lý Thông minh Pháp quy & Tra cứu Hồ sơ CTSV ĐH Đà Lạt",
        "summary_answer": "Chào bạn! Mình là Trợ lý AI DocuCTSV của Trường Đại học Đà Lạt. Mình sẵn sàng giải đáp mọi thắc mắc về quy chế đào tạo, học bổng KKHT, miễn giảm học phí NĐ 81, điểm rèn luyện và thủ tục một cửa tại Nhà A11.",
        "detail_content": (
            "Bạn có thể hỏi tự nhiên hoặc dùng từ viết tắt, ví dụ:\n"
            "• 'mghp can nhung gi' (Hồ sơ miễn giảm học phí Nghị định 81)\n"
            "• 'kkht dlu co duoc diem f khong' (Quy định xét học bổng khi nợ môn/điểm F)\n"
            "• 'lam sao de xin bao luu 1 nam' (Thủ tục nghỉ học tạm thời Mẫu BM-03)\n"
            "• 'xin hoan nvqs o dau' (Cấp giấy tạm hoãn nghĩa vụ quân sự tại Nhà A11)\n"
            "• 'cpa bao nhieu bi canh bao hoc vu' (Ngưỡng cảnh báo học tập theo từng năm)"
        ),
        "confidence_score": 0.99,
        "required_forms": [],
        "related_articles": ["Quy chế Công tác Sinh viên Trường Đại học Đà Lạt"],
    },
    {
        "id": "faq_cam_on_tro_ly",
        "keywords": ["cam on", "thanks", "thank you", "cam on ban", "thong minh qua", "hay qua", "tuyet voi", "ok cam on", "bye"],
        "matched_article": "Lời chào Trợ lý AI DocuCTSV",
        "regulation_title": "Trợ lý Thông minh CTSV — Trường Đại học Đà Lạt",
        "summary_answer": "Rất vui được hỗ trợ bạn! Chúc bạn có một kỳ học thật hiệu quả, đạt kết quả rèn luyện xuất sắc và nhận học bổng DLU.",
        "detail_content": (
            "Mẹo nhỏ cho sinh viên:\n"
            "• Hãy theo dõi bảng tin Phòng CTSV tại Nhà A11 và Cổng thông tin sinh viên để không bỏ lỡ hạn nộp biểu mẫu.\n"
            "• Mọi thắc mắc cần hỗ trợ trực tiếp, bạn có thể ghé Bộ phận Một cửa - Nhà A11 các ngày trong tuần."
        ),
        "confidence_score": 0.99,
        "required_forms": [],
        "related_articles": ["Quy chế Công tác Sinh viên Đại học Đà Lạt"],
    },

    # ── 2. BẢO LƯU, THÔI HỌC & TRỞ LẠI HỌC TẬP ────────────────────────────────
    {
        "id": "faq_bao_luu_nghi_hoc",
        "keywords": ["nghi hoc", "nghi hoc tam thoi", "bao luu", "bao luu ket qua", "nghi hoc 1 nam", "bao luu 1 nam", "bm03", "bm-03", "blht", "tam ngung hoc"],
        "matched_article": "Điều 12, Quy chế Đào tạo tín chỉ Trường Đại học Đà Lạt",
        "regulation_title": "Quy định về việc nghỉ học tạm thời và bảo lưu kết quả học tập",
        "summary_answer": "Sinh viên được xin nghỉ học tạm thời (bảo lưu) tối đa 02 học kỳ chính (1 năm) khi đã hoàn thành tối thiểu 01 học kỳ và không thuộc diện bị buộc thôi học. Nộp Mẫu BM-03-BLHT tại Bộ phận Một cửa Nhà A11.",
        "detail_content": (
            "Quy trình xin nghỉ học tạm thời (bảo lưu kết quả học tập):\n"
            "1. Điều kiện: Đã tích lũy tối thiểu 01 học kỳ chính tại trường, không trong thời gian bị kỷ luật từ cảnh cáo trở lên hoặc bị xem xét buộc thôi học.\n"
            "2. Thời hạn: Mỗi lần xin nghỉ tối đa 02 học kỳ (1 năm), tổng thời gian không vượt quá 02 năm trong suốt khóa học (ngoại trừ trường hợp thi hành Nghĩa vụ quân sự).\n"
            "3. Hồ sơ gồm có:\n"
            "   - Đơn xin nghỉ học tạm thời và bảo lưu kết quả (Mẫu BM-03-BLHT) có chữ ký đồng ý của phụ huynh.\n"
            "   - Minh chứng đính kèm: Bệnh án viện (nếu lý do sức khỏe), Lệnh gọi nhập ngũ (nếu đi NVQS), hoặc xác nhận lý do gia đình.\n"
            "   - Bảng điểm tích lũy và phiếu xác nhận hoàn thành công nợ học phí/thư viện.\n"
            "4. Địa điểm tiếp nhận: Bộ phận Một cửa - Phòng CTSV (Nhà A11)."
        ),
        "confidence_score": 0.98,
        "required_forms": [
            RequiredFormItem(
                form_code="BM-03-BLHT",
                form_name="Đơn xin nghỉ học tạm thời và bảo lưu kết quả học tập",
                download_url="/api/v1/documents/forms/BM-03-BLHT.pdf",
                guide="Kèm chữ ký xác nhận của phụ huynh và nộp tại Bộ phận Một cửa Nhà A11",
            )
        ],
        "related_articles": [
            "Điều 13. Tiếp nhận sinh viên trở lại học tập sau bảo lưu",
            "Điều 14. Thời gian tối đa hoàn thành chương trình đào tạo",
        ],
    },
    {
        "id": "faq_tro_lai_hoc_sau_bao_luu",
        "keywords": ["quay lai hoc", "tro lai hoc", "het han bao luu", "hoc lai sau bao luu", "don xin tro lai", "tiep tuc hoc"],
        "matched_article": "Điều 13, Quy chế Đào tạo tín chỉ Trường Đại học Đà Lạt",
        "regulation_title": "Thủ tục tiếp nhận sinh viên trở lại học tập sau thời gian nghỉ học tạm thời",
        "summary_answer": "Trước khi bắt đầu học kỳ mới ít nhất 02 đến 04 tuần, sinh viên phải nộp Đơn xin tiếp tục học tập kèm Quyết định nghỉ học tạm thời trước đó về Phòng CTSV Nhà A11 để được phục hồi mã sinh viên và mở cổng đăng ký tín chỉ.",
        "detail_content": (
            "Trình tự đăng ký trở lại học tập:\n"
            "1. Thời gian: Nộp đơn từ 2 - 4 tuần trước khi bắt đầu học kỳ dự kiến nhập học lại.\n"
            "2. Hồ sơ chuẩn bị: Đơn đề nghị tiếp tục học tập, bản sao Quyết định cho phép nghỉ học tạm thời, giấy xác nhận hoàn thành NVQS hoặc giấy chứng nhận đủ sức khỏe học tập của cơ sở y tế (nếu nghỉ vì lý do ốm đau).\n"
            "3. Tiếp nhận: Nộp tại Bộ phận Một cửa Nhà A11. Phòng CTSV sẽ trình Ban Giám hiệu ra Quyết định tiếp nhận sinh viên và Phòng Quản lý Đào tạo cấp quyền đăng ký tín chỉ."
        ),
        "confidence_score": 0.98,
        "required_forms": [
            RequiredFormItem(
                form_code="BM-03-TLH",
                form_name="Đơn xin tiếp tục học tập sau thời gian nghỉ học tạm thời",
                download_url="/api/v1/documents/forms/BM-03-TLH.pdf",
                guide="Nộp kèm Quyết định nghỉ học tạm thời tại Nhà A11 trước học kỳ mới 1 tháng",
            )
        ],
        "related_articles": ["Điều 12. Quy định nghỉ học tạm thời"],
    },
    {
        "id": "faq_thoi_hoc_tu_nguyen",
        "keywords": ["thoi hoc", "nghi hoc han", "rut ho so", "rut hoc ba", "rut ho so goc", "khong muon hoc nua", "thoi hoc tu nguyen", "rut bang cap 3"],
        "matched_article": "Điều 18, Quy chế Đào tạo đại học theo hệ thống tín chỉ",
        "regulation_title": "Quy trình giải quyết cho sinh viên thôi học tự nguyện và rút hồ sơ gốc",
        "summary_answer": "Sinh viên muốn thôi học tự nguyện nộp Đơn xin thôi học (có xác nhận của gia đình), thanh toán toàn bộ công nợ tại Thư viện, Ký túc xá và Phòng Tài chính; sau đó nhận lại Học bạ và Bằng tốt nghiệp THPT gốc tại Nhà A11.",
        "detail_content": (
            "Quy trình xin thôi học tự nguyện và rút hồ sơ gốc:\n"
            "1. Tải và điền Đơn xin thôi học tự nguyện (có chữ ký của sinh viên và cha/mẹ).\n"
            "2. Xin xác nhận không nợ sách tại Thư viện DLU (Nhà A26) và không nợ phí tại Ban Quản lý KTX.\n"
            "3. Phòng Kế hoạch - Tài chính xác nhận hoàn thành công nợ học phí.\n"
            "4. Nộp toàn bộ hồ sơ tại Bộ phận Một cửa Nhà A11. Sau 3 - 5 ngày làm việc, Nhà trường ban hành Quyết định thôi học và trả lại hồ sơ gốc THPT, kèm bảng điểm các học phần đã tích lũy."
        ),
        "confidence_score": 0.98,
        "required_forms": [
            RequiredFormItem(
                form_code="BM-03-THTN",
                form_name="Đơn xin thôi học tự nguyện và thanh toán công nợ",
                download_url="/api/v1/documents/forms/BM-03-THTN.pdf",
                guide="Hoàn tất xác nhận tại Thư viện, KTX, Tài chính rồi nộp tại Một cửa A11",
            )
        ],
        "related_articles": ["Điều 19. Xóa tên trong danh sách sinh viên"],
    },

    # ── 3. HỌC BỔNG KHUYẾN KHÍCH HỌC TẬP (KKHT) & TÀI TRỢ ─────────────────────
    {
        "id": "faq_hoc_bong_kkht_quy_che",
        "keywords": ["hoc bong", "kkht", "hoc bong khuyen khich", "hb kkht", "xet hoc bong", "dieu kien hoc bong", "quy dinh hoc bong", "qd688", "loai gioi", "loai xuat sac", "loai kha"],
        "matched_article": "Quyết định số 688/QĐ-ĐHĐL của Hiệu trưởng Trường Đại học Đà Lạt",
        "regulation_title": "Quy chế xét, cấp học bổng khuyến khích học tập đối với sinh viên ĐH Đà Lạt",
        "summary_answer": "Học bổng KKHT xét theo từng kỳ học chính căn cứ vào GPA và Điểm rèn luyện (DRL ≥ 65). Gồm 3 mức: Xuất sắc (GPA ≥ 3.6, DRL ≥ 90), Giỏi (GPA ≥ 3.2, DRL ≥ 80), Khá (GPA ≥ 2.5, DRL ≥ 65). Xét theo thứ tự điểm từ cao xuống thấp đến hết quỹ.",
        "detail_content": (
            "Tiêu chuẩn xét cấp học bổng KKHT (Quyết định 688/QĐ-ĐHĐL):\n"
            "1. Tích lũy tối thiểu 15 tín chỉ trong học kỳ xét (không tính GDTC, GDQP đối với kỳ thường).\n"
            "2. Không có môn học nào bị điểm F (kể cả GDTC và GDQP) trong kỳ xét.\n"
            "3. Phân hạng học bổng:\n"
            "   - Loại Xuất sắc: GPA ≥ 3.60 và DRL ≥ 90 (Mức học bổng cao nhất, vượt mức trần học phí).\n"
            "   - Loại Giỏi: GPA ≥ 3.20 và DRL ≥ 80 (Mức học bổng bằng hoặc cao hơn học phí chuẩn).\n"
            "   - Loại Khá: GPA ≥ 2.50 và DRL ≥ 65 (Mức học bổng bằng mức trần học phí tín chỉ).\n"
            "4. Điểm xét HB = (GPA * 0.7) + (DRL quy đổi * 0.3), lấy từ cao xuống thấp trong từng ngành/khóa học."
        ),
        "confidence_score": 0.99,
        "required_forms": [
            RequiredFormItem(
                form_code="BM-01-HBKK",
                form_name="Bảng tự kiểm tra tiêu chuẩn xét Học bổng Khuyến khích học tập",
                download_url="/api/v1/documents/forms/BM-01-HBKK.pdf",
                guide="Theo dõi danh sách dự kiến do Khoa/Phòng CTSV công bố và nộp phản hồi nếu có sai sót",
            )
        ],
        "related_articles": [
            "Điều 4. Nguyên tắc phân bổ quỹ học bổng theo từng ngành đào tạo",
            "Điều 7. Quy trình chi trả học bổng trực tiếp qua tài khoản ngân hàng sinh viên",
        ],
    },
    {
        "id": "faq_hoc_bong_f",
        "keywords": ["diem f", "rot mon", "the duc", "gdtc", "quan su", "gdqp", "bi f the duc", "bi f quan su", "hoc lai", "diem f co duoc hoc bong khong"],
        "matched_article": "Khoản 2 Điều 4, Quyết định số 688/QĐ-ĐHĐL",
        "regulation_title": "Quy chế xét, cấp học bổng khuyến khích học tập đối với sinh viên ĐH Đà Lạt",
        "summary_answer": "Sinh viên có bất kỳ học phần nào bị điểm F (kể cả môn Giáo dục thể chất và GDQP-AN) trong học kỳ xét thì KHÔNG được xét cấp học bổng Khuyến khích học tập của kỳ đó.",
        "detail_content": (
            "Căn cứ Khoản 2 Điều 4 Quy chế học bổng DLU:\n"
            "• Điều kiện tiên quyết: Trong học kỳ xét, sinh viên không được có bất kỳ học phần nào bị điểm F hoặc dưới điểm D.\n"
            "• Mặc dù điểm môn GDTC và GDQP-AN không tính vào GPA tích lũy, nhưng đây là học phần điều kiện; nếu bị điểm F, hồ sơ học bổng sẽ bị loại tự động.\n"
            "• Tuy nhiên, bạn vẫn được bảo lưu quyền xét học bổng ở các học kỳ tiếp theo nếu học kỳ sau đó đạt kết quả tốt và không có điểm F."
        ),
        "confidence_score": 0.99,
        "required_forms": [],
        "related_articles": ["Điều 5. Tiêu chuẩn xếp hạng học bổng theo thang điểm 4"],
    },
    {
        "id": "faq_hoc_bong_doanh_nghiep",
        "keywords": ["hoc bong doanh nghiep", "hbdn", "hoc bong tai tro", "quy tai tro", "bidv", "viettel", "agribank", "vietcombank", "hoc bong vuot kho", "bm06", "bm-06"],
        "matched_article": "Quy chế Quản lý và Tiếp nhận Học bổng tài trợ ngoài ngân sách",
        "regulation_title": "Quy định xét chọn và trao học bổng tài trợ doanh nghiệp ĐH Đà Lạt",
        "summary_answer": "Học bổng doanh nghiệp (Viettel, BIDV, Agribank, Vietcombank...) dành cho sinh viên có GPA ≥ 2.80, DRL ≥ 80 và ưu tiên sinh viên có hoàn cảnh khó khăn vươn lên trong học tập. Nộp Mẫu BM-06-HBDN tại Nhà A11 khi có thông báo.",
        "detail_content": (
            "Tiêu chí xét cấp học bổng doanh nghiệp & đối tác ngoài trường:\n"
            "1. Kết quả học tập: GPA tích lũy từ 2.80/4.0 trở lên (tùy quỹ, một số quỹ yêu cầu GPA ≥ 3.20).\n"
            "2. Kết quả rèn luyện: Xếp loại Tốt (DRL ≥ 80) trở lên trong năm học.\n"
            "3. Ưu tiên xét tuyển: Sinh viên hộ nghèo, cận nghèo, mồ côi, khuyết tật, hoặc có thành tích NCKH, sáng tạo khởi nghiệp.\n"
            "4. Giá trị học bổng: Từ 5.000.000đ đến 20.000.000đ/suất/năm học.\n"
            "5. Hồ sơ gồm: Đơn đề nghị học bổng (Mẫu BM-06-HBDN), Bảng điểm có xác nhận của Phòng Đào tạo, Giấy xác nhận hoàn cảnh khó khăn (nếu có)."
        ),
        "confidence_score": 0.98,
        "required_forms": [
            RequiredFormItem(
                form_code="BM-06-HBDN",
                form_name="Đơn đăng ký xét cấp Học bổng tài trợ ngoài ngân sách",
                download_url="/api/v1/documents/forms/BM-06-HBDN.pdf",
                guide="Kèm Bảng điểm học tập và minh chứng hoàn cảnh gia đình nộp về Nhà A11",
            )
        ],
        "related_articles": ["Danh mục các quỹ học bổng cựu sinh viên & đối tác ĐH Đà Lạt"],
    },
    {
        "id": "faq_hoc_bong_thu_khoa_khuyen_tai",
        "keywords": ["thu khoa", "hoc bong thu khoa", "khuyen tai", "tai nang", "mien hoc phi nam 1", "thu khoa dau vao"],
        "matched_article": "Chính sách Thu hút nhân tài & Học bổng Khuyến tài Trường ĐH Đà Lạt",
        "regulation_title": "Chính sách cấp học bổng cho Thủ khoa và Sinh viên xuất sắc đầu khóa",
        "summary_answer": "Thủ khoa các ngành/khối thi tuyển sinh vào ĐH Đà Lạt được trao Học bổng Khuyến tài tương đương 100% học phí năm thứ nhất, và tiếp tục được duy trì nếu các năm học sau đạt GPA từ 3.20 trở lên.",
        "detail_content": (
            "Chế độ đãi ngộ Thủ khoa tuyển sinh ĐH Đà Lạt:\n"
            "• Thủ khoa trường: Nhận học bổng trị giá 100% học phí toàn khóa học (duy trì từng năm với điều kiện GPA ≥ 3.20 và DRL ≥ 80).\n"
            "• Thủ khoa ngành tuyển sinh: Nhận học bổng 100% học phí năm thứ nhất.\n"
            "• Á khoa và thí sinh đạt giải Nhất/Nhì/Ba kỳ thi Học sinh giỏi Quốc gia: Miễn 100% học phí năm thứ nhất và ưu tiên bố trí chỗ ở miễn phí tại Ký túc xá DLU."
        ),
        "confidence_score": 0.98,
        "required_forms": [],
        "related_articles": ["Quyết định khen thưởng thủ khoa đầu khóa hằng năm"],
    },

    # ── 4. MIỄN GIẢM HỌC PHÍ & CHÍNH SÁCH XÃ HỘI (NĐ 81/2021 & QĐ 66/2013) ────
    {
        "id": "faq_mien_giam_hoc_phi_nd81",
        "keywords": ["mghp", "mien giam hoc phi", "nd81", "nghi dinh 81", "ho so mien giam", "mien 100", "giam 70", "giam 50", "bm02", "bm-02", "chinh sach hoc phi"],
        "matched_article": "Điều 15 & Điều 16, Nghị định số 81/2021/NĐ-CP của Chính phủ",
        "regulation_title": "Quy định cơ chế thu, quản lý học phí và chính sách miễn, giảm học phí",
        "summary_answer": "Chính sách miễn giảm học phí thực hiện theo Nghị định 81/2021/NĐ-CP gồm 3 mức: Miễn 100%, Giảm 70% và Giảm 50%. Sinh viên làm Đơn theo Mẫu BM-02-MGHP kèm bản sao công chứng giấy tờ chứng minh nộp tại Nhà A11 vào đầu mỗi học kỳ.",
        "detail_content": (
            "Các khung mức miễn giảm học phí cụ thể:\n"
            "1. Miễn 100% học phí:\n"
            "   - Sinh viên là con liệt sĩ, con thương binh, con bệnh binh, con người có công với CM.\n"
            "   - Sinh viên mồ côi cả cha lẫn mẹ không nơi nương tựa.\n"
            "   - Sinh viên khuyết tật mức độ nặng hoặc đặc biệt nặng.\n"
            "   - Sinh viên người DTTS rất ít người (dưới 10.000 người) ở vùng có điều kiện KT-XH khó khăn.\n"
            "2. Giảm 70% học phí:\n"
            "   - Sinh viên người dân tộc thiểu số ở thôn/bản đặc biệt khó khăn, xã vùng III, vùng đồng bào DTTS và miền núi.\n"
            "3. Giảm 50% học phí:\n"
            "   - Sinh viên là con cán bộ, công chức, viên chức, công nhân mà cha hoặc mẹ bị tai nạn lao động hoặc mắc bệnh nghề nghiệp hưởng trợ cấp thường xuyên.\n"
            "4. Thời hạn nộp hồ sơ: Trong vòng 45 ngày kể từ ngày khai giảng học kỳ chính."
        ),
        "confidence_score": 0.99,
        "required_forms": [
            RequiredFormItem(
                form_code="BM-02-MGHP",
                form_name="Đơn đề nghị miễn, giảm học phí (Kèm theo Nghị định 81/2021/NĐ-CP)",
                download_url="/api/v1/documents/forms/BM-02-MGHP.pdf",
                guide="Kèm Giấy xác nhận diện đối tượng chính sách có công chứng và CCCD nộp tại Nhà A11",
            )
        ],
        "related_articles": [
            "Điều 19. Trình tự và thủ tục thực hiện miễn giảm học phí",
            "Thông tư số 05/2023/TT-BLĐTBXH hướng dẫn thi hành",
        ],
    },
    {
        "id": "faq_mien_giam_ho_ngheo",
        "keywords": ["ho ngheo", "can ngheo", "so ho ngheo", "sv ho ngheo", "ho tro ho ngheo", "tro cap ho ngheo", "giam hoc phi ho ngheo"],
        "matched_article": "Khoản 1 Điều 16 Nghị định 81/2021/NĐ-CP & Quyết định 66/2013/QĐ-TTg",
        "regulation_title": "Chính sách ưu đãi và hỗ trợ đối với sinh viên thuộc hộ nghèo, hộ cận nghèo",
        "summary_answer": "Sinh viên thuộc hộ nghèo/cận nghèo được xem xét miễn giảm học phí theo NĐ 81, đồng thời nếu là người dân tộc thiểu số sẽ được nhận thêm Hỗ trợ chi phí học tập 60% mức lương cơ sở (QĐ 66/2013) và ưu tiên vay vốn Ngân hàng CSXH.",
        "detail_content": (
            "Chế độ dành cho sinh viên diện Hộ nghèo & Cận nghèo tại DLU:\n"
            "1. Miễn/giảm học phí: Căn cứ Nghị định 81, nộp bản sao công chứng Giấy chứng nhận/Sổ hộ nghèo/cận nghèo có hiệu lực trong năm học kèm Đơn BM-02-MGHP.\n"
            "2. Hỗ trợ chi phí học tập (QĐ 66/2013/QĐ-TTg): Sinh viên DTTS hộ nghèo/cận nghèo được cấp 60% lương cơ sở/tháng (10 tháng/năm học), tiền chi trả thẳng vào tài khoản sinh viên.\n"
            "3. Ưu tiên xét ở Ký túc xá DLU và miễn giảm phí phòng ở nội trú.\n"
            "4. Ưu tiên cấp học bổng tài trợ doanh nghiệp vượt khó học tốt (Mẫu BM-06-HBDN)."
        ),
        "confidence_score": 0.98,
        "required_forms": [
            RequiredFormItem(
                form_code="BM-02-MGHP",
                form_name="Đơn đề nghị miễn, giảm học phí",
                download_url="/api/v1/documents/forms/BM-02-MGHP.pdf",
                guide="Nộp bản sao công chứng Giấy chứng nhận hộ nghèo năm hiện hành",
            )
        ],
        "related_articles": ["Quyết định 66/2013/QĐ-TTg về chính sách hỗ trợ chi phí học tập"],
    },
    {
        "id": "faq_ho_tro_chi_phi_qd66",
        "keywords": ["qd66", "quyet dinh 66", "ho tro chi phi hoc tap", "htcp", "htcpht", "sv dtts ho ngheo", "tro cap chi phi", "60% luong co so"],
        "matched_article": "Quyết định số 66/2013/QĐ-TTg của Thủ tướng Chính phủ",
        "regulation_title": "Chính sách hỗ trợ chi phí học tập đối với sinh viên là người dân tộc thiểu số",
        "summary_answer": "Sinh viên người dân tộc thiểu số thuộc hộ nghèo hoặc cận nghèo được hỗ trợ chi phí học tập bằng 60% mức lương cơ sở/tháng, hưởng 10 tháng/năm học. Nộp hồ sơ tại Bộ phận Một cửa Nhà A11.",
        "detail_content": (
            "Quy định hỗ trợ chi phí học tập theo Quyết định 66:\n"
            "1. Đối tượng: Sinh viên là người dân tộc thiểu số thuộc diện hộ nghèo hoặc hộ cận nghèo theo chuẩn nghèo quốc gia, thi đỗ vào học đại học hệ chính quy.\n"
            "2. Mức hỗ trợ: Bằng 60% mức lương cơ sở/tháng (ví dụ với mức lương cơ sở 2.340.000đ thì nhận 1.404.000đ/tháng x 10 tháng = 14.040.000đ/năm).\n"
            "3. Hồ sơ gồm:\n"
            "   - Đơn đề nghị hỗ trợ chi phí học tập (Mẫu BM-02-HTCP).\n"
            "   - Giấy xác nhận hộ nghèo/cận nghèo cấp trong năm học.\n"
            "   - Bản sao Giấy khai sinh công chứng chứng minh thành phần dân tộc thiểu số.\n"
            "4. Tiền hỗ trợ được Nhà trường chi trả 2 lần/năm học trực tiếp qua số tài khoản BIDV của sinh viên."
        ),
        "confidence_score": 0.98,
        "required_forms": [
            RequiredFormItem(
                form_code="BM-02-HTCP",
                form_name="Đơn đề nghị hỗ trợ chi phí học tập theo Quyết định 66",
                download_url="/api/v1/documents/forms/BM-02-HTCP.pdf",
                guide="Kèm Sổ hộ nghèo công chứng và Giấy khai sinh nộp tại Nhà A11",
            )
        ],
        "related_articles": ["Thông tư liên tịch số 35/2014/TTLT-BGDĐT-BTC hướng dẫn thực hiện"],
    },
    {
        "id": "faq_con_thuong_binh_liet_si",
        "keywords": ["con thuong binh", "con liet si", "con benh binh", "nguoi co cong", "uu dai giao duc", "che do con thuong binh", "phap lenh nguoi co cong"],
        "matched_article": "Pháp lệnh Ưu đãi người có công với cách mạng & Nghị định 81/2021/NĐ-CP",
        "regulation_title": "Chế độ ưu đãi giáo dục đối với con của người có công với cách mạng",
        "summary_answer": "Sinh viên là con liệt sĩ, con thương binh, con bệnh binh được miễn 100% học phí chính khóa, được cấp trợ cấp ưu đãi giáo dục định kỳ hằng tháng từ Phòng LĐ-TB&XH địa phương và ưu tiên điểm cộng xét học bổng, KTX.",
        "detail_content": (
            "Hồ sơ và quyền lợi của sinh viên diện chính sách người có công:\n"
            "1. Quyền lợi: Miễn 100% học phí toàn khóa học (trong khung thời gian đào tạo chuẩn).\n"
            "2. Giấy tờ nộp tại trường:\n"
            "   - Đơn đề nghị miễn giảm học phí Mẫu BM-02-MGHP.\n"
            "   - Giấy khai sinh bản sao công chứng.\n"
            "   - Bản sao Thẻ thương binh/bệnh binh của cha/mẹ có chứng thực.\n"
            "   - Giấy xác nhận người có công do Phòng LĐ-TB&XH cấp huyện nơi cha mẹ cư trú cấp.\n"
            "3. Hằng kỳ, sinh viên xin Giấy xác nhận sinh viên tại Nhà A11 để gửi về địa phương nhận tiền trợ cấp ưu đãi hàng tháng theo quy định."
        ),
        "confidence_score": 0.98,
        "required_forms": [
            RequiredFormItem(
                form_code="BM-02-MGHP",
                form_name="Đơn đề nghị miễn giảm học phí diện chính sách Người có công",
                download_url="/api/v1/documents/forms/BM-02-MGHP.pdf",
                guide="Kèm thẻ thương binh/bệnh binh công chứng và xác nhận Phòng LĐTBXH",
            )
        ],
        "related_articles": ["Thông tư liên tịch số 13/2014/TTLT-BLĐTBXH-BGDĐT"],
    },

    # ── 5. NỘP HỌC PHÍ, GIA HẠN & CÔNG NỢ ──────────────────────────────────────
    {
        "id": "faq_nop_hoc_phi_online",
        "keywords": ["nop hoc phi", "dong hoc phi", "tai khoan dong hoc phi", "stk truong", "stk hoc phi", "ngan hang bidv", "cu phap dong tien", "chuyen khoan hoc phi"],
        "matched_article": "Quy chế Quản lý thu - nộp học phí Trường Đại học Đà Lạt",
        "regulation_title": "Hướng dẫn nộp học phí bằng phương thức thanh toán không dùng tiền mặt",
        "summary_answer": "Sinh viên nộp học phí qua chuyển khoản vào Tài khoản Ngân hàng BIDV của Trường ĐH Đà Lạt hoặc thanh toán trực tiếp qua Cổng thông tin sinh viên với cú pháp: MSSV + Họ tên sinh viên + Hoc phi HK...",
        "detail_content": (
            "Thông tin tài khoản thu học phí chính thức của ĐH Đà Lạt:\n"
            "• Tên đơn vị thụ hưởng: TRƯỜNG ĐẠI HỌC ĐÀ LẠT\n"
            "• Số tài khoản: 64110000006789 tại Ngân hàng BIDV Chi nhánh Lâm Đồng\n"
            "  (Hoặc thanh toán qua QR Code động trên Cổng thông tin sinh viên portal.dlu.edu.vn)\n"
            "• Cú pháp chuyển khoản chuẩn:\n"
            "  [Mã số sinh viên] [Họ và tên] Hoc phi HK[Kỳ] Nam hoc [Năm]\n"
            "  Ví dụ: '2110543 Le Van Binh Hoc phi HK1 Nam hoc 2024-2025'\n"
            "• Sau 24h - 48h làm việc, hệ thống tài chính sẽ tự động gạch nợ học phí trên Cổng thông tin."
        ),
        "confidence_score": 0.99,
        "required_forms": [],
        "related_articles": ["Thông báo thu học phí từng học kỳ của Phòng Kế hoạch - Tài chính"],
    },
    {
        "id": "faq_gia_han_hoc_phi",
        "keywords": ["gia han hoc phi", "xin cham nop hoc phi", "kho khan chua co tien dong hoc", "no hoc phi", "bm08", "bm-08", "don gia han"],
        "matched_article": "Quy chế Công tác Sinh viên & Quy định Thu học phí ĐH Đà Lạt",
        "regulation_title": "Quy trình giải quyết đơn xin gia hạn thời gian nộp học phí",
        "summary_answer": "Sinh viên có hoàn cảnh khó khăn đột xuất nộp Đơn xin gia hạn nộp học phí (Mẫu BM-08-GHHP) có xác nhận của Cố vấn học tập và Văn phòng Khoa về Bộ phận Một cửa Nhà A11 để được gia hạn tối đa trước kỳ thi kết thúc học phần 02 tuần.",
        "detail_content": (
            "Thủ tục xin gia hạn học phí:\n"
            "1. Điều kiện: Có lý do chính đáng (tai nạn đột xuất, biến cố gia đình, đang chờ vay vốn NHCSXH).\n"
            "2. Thời hạn được gia hạn: Tối đa đến trước thời điểm thi kết thúc học phần của học kỳ 02 tuần.\n"
            "3. Hồ sơ cần nộp:\n"
            "   - Đơn xin gia hạn nộp học phí (Mẫu BM-08-GHHP).\n"
            "   - Giấy tờ minh chứng hoàn cảnh khó khăn hoặc xác nhận của chính quyền địa phương.\n"
            "   - Ký cam kết thời hạn thanh toán cụ thể.\n"
            "4. Khi được phê duyệt gia hạn, sinh viên không bị khóa tài khoản đăng ký tín chỉ và được cấp quyền dự thi kết thúc học phần."
        ),
        "confidence_score": 0.98,
        "required_forms": [
            RequiredFormItem(
                form_code="BM-08-GHHP",
                form_name="Đơn xin gia hạn nộp học phí",
                download_url="/api/v1/documents/forms/BM-08-GHHP.pdf",
                guide="Kèm chữ ký Cố vấn học tập và nộp tại Bộ phận Một cửa Nhà A11",
            )
        ],
        "related_articles": ["Quy định xử lý sinh viên chậm nộp học phí"],
    },
    {
        "id": "faq_cham_nop_hoc_phi_hau_qua",
        "keywords": ["cham nop hoc phi", "khong dong hoc phi", "hau qua no hoc phi", "bi cam thi", "khoa tai khoan", "huy tin chi"],
        "matched_article": "Điều 8, Quy chế Đào tạo tín chỉ Trường Đại học Đà Lạt",
        "regulation_title": "Xử lý sinh viên chậm nộp học phí hoặc vi phạm nghĩa vụ tài chính",
        "summary_answer": "Sinh viên không đóng học phí đúng hạn và không có đơn xin gia hạn hợp lệ sẽ bị cấm thi kết thúc học phần của các môn đăng ký trong kỳ, bị nhận điểm F, và bị khóa quyền đăng ký tín chỉ ở học kỳ kế tiếp.",
        "detail_content": (
            "Các chế tài xử lý nợ học phí theo quy chế:\n"
            "• Giai đoạn 1 (Sau hạn chót 15 ngày): Cảnh báo học phí qua email và SMS đến phụ huynh/sinh viên.\n"
            "• Giai đoạn 2 (Trước kỳ thi): Khóa danh sách dự thi, sinh viên không có tên trong danh sách thi kết thúc môn học (điểm F môn học đó).\n"
            "• Giai đoạn 3 (Đầu học kỳ mới): Tạm dừng quyền đăng ký học phần trên Cổng tín chỉ cho đến khi hoàn thành công nợ.\n"
            "• Sinh viên cần chủ động nộp đơn BM-08-GHHP tại Nhà A11 nếu gia đình gặp khó khăn để được hỗ trợ kịp thời."
        ),
        "confidence_score": 0.98,
        "required_forms": [],
        "related_articles": ["Điều 11. Đăng ký học phần và đóng học phí tín chỉ"],
    },

    # ── 6. ĐIỂM RÈN LUYỆN (DRL) & KHIẾU NẠI ────────────────────────────────────
    {
        "id": "faq_diem_ren_luyen",
        "keywords": ["diem ren luyen", "drl", "dtrl", "xep loai ren luyen", "khung diem drl", "drl xuat sac", "drl tot", "drl kha", "bm03-drl"],
        "matched_article": "Quy chế Đánh giá kết quả rèn luyện sinh viên Trường ĐH Đà Lạt",
        "regulation_title": "Quy chế đánh giá kết quả rèn luyện của người học theo hệ thống tín chỉ",
        "summary_answer": "Điểm rèn luyện đánh giá theo thang điểm 100, chia 6 khung loại: Xuất sắc (90 - 100đ), Tốt (80 - 89đ), Khá (65 - 79đ), Trung bình (50 - 64đ), Yếu (35 - 49đ) và Kém (< 35đ). DRL là điều kiện bắt buộc để xét học bổng và tốt nghiệp.",
        "detail_content": (
            "Nội dung đánh giá Điểm rèn luyện gồm 5 tiêu chí chính:\n"
            "1. Ý thức học tập (tối đa 20 điểm): Đi học chuyên cần, không vi phạm quy chế thi, tham gia NCKH.\n"
            "2. Ý thức chấp hành pháp luật & nội quy trường (tối đa 25 điểm): Chấp hành nội quy KTX/ngoại trú, an toàn giao thông, nộp học phí đúng hạn.\n"
            "3. Ý thức tham gia hoạt động chính trị - xã hội, văn thể mỹ (tối đa 20 điểm): Mùa hè xanh, hiến máu, thể thao, văn nghệ, SHCD.\n"
            "4. Phẩm chất công dân & quan hệ cộng đồng (tối đa 25 điểm): Giúp đỡ bạn bè, sống văn minh, không tệ nạn xã hội.\n"
            "5. Ý thức tham gia phụ trách lớp, đoàn thể, thành tích đặc biệt (tối đa 10 điểm): Ban cán sự lớp, Đoàn Hội, đạt giải thưởng cấp tỉnh/quốc gia."
        ),
        "confidence_score": 0.99,
        "required_forms": [
            RequiredFormItem(
                form_code="BM-03-DRL",
                form_name="Phiếu đánh giá kết quả rèn luyện sinh viên",
                download_url="/api/v1/documents/forms/BM-03-DRL.pdf",
                guide="Sinh viên tự chấm điểm và nộp cho Ban cán sự lớp vào cuối mỗi học kỳ",
            )
        ],
        "related_articles": [
            "Điều 7. Quy trình đánh giá rèn luyện từ cấp Lớp đến Khoa và Nhà trường",
            "Điều 12. Thời hạn tiếp nhận khiếu nại điểm rèn luyện (trong vòng 07 ngày làm việc)",
        ],
    },
    {
        "id": "faq_drl_bi_ky_luat",
        "keywords": ["ky luat drl", "khien trach drl", "canh cao drl", "drl toi da", "bi ky luat drl bao nhieu", "bi khien trach"],
        "matched_article": "Khoản 3 Điều 9, Quy chế Đánh giá kết quả rèn luyện sinh viên",
        "regulation_title": "Quy định mức xếp loại rèn luyện đối với sinh viên bị kỷ luật",
        "summary_answer": "Sinh viên bị kỷ luật Khiển trách trong học kỳ thì DRL tối đa không vượt quá loại Khá (dưới 80 điểm); nếu bị kỷ luật Cảnh cáo thì DRL tối đa không vượt quá loại Trung bình (dưới 65 điểm).",
        "detail_content": (
            "Khống chế khung Điểm rèn luyện khi có vi phạm kỷ luật:\n"
            "• Bị kỷ luật Khiển trách cấp Khoa hoặc cấp Trường: Điểm rèn luyện học kỳ đó không được xếp vượt quá loại Khá (tối đa 79 điểm).\n"
            "• Bị kỷ luật Cảnh cáo cấp Trường: Điểm rèn luyện học kỳ đó không được xếp vượt quá loại Trung bình (tối đa 64 điểm).\n"
            "• Bị đình chỉ học tập có thời hạn: Xếp loại Kém (dưới 35 điểm).\n"
            "• Sinh viên bị kỷ luật từ khiển trách trở lên sẽ không đủ điều kiện xét các loại học bổng và danh hiệu khen thưởng trong kỳ đó."
        ),
        "confidence_score": 0.99,
        "required_forms": [],
        "related_articles": ["Quy định Kỷ luật người học Trường Đại học Đà Lạt"],
    },
    {
        "id": "faq_khieu_nai_drl",
        "keywords": ["khieu nai drl", "sai diem ren luyen", "thac mac drl", "sua diem ren luyen", "cham thieu drl", "han khieu nai"],
        "matched_article": "Điều 12, Quy chế Đánh giá kết quả rèn luyện sinh viên ĐH Đà Lạt",
        "regulation_title": "Thời hạn và quy trình giải quyết khiếu nại kết quả rèn luyện",
        "summary_answer": "Sinh viên có quyền khiếu nại kết quả DRL trong vòng 07 ngày làm việc kể từ ngày Khoa công bố điểm dự kiến. Nộp đơn khiếu nại kèm minh chứng hoạt động về Văn phòng Khoa hoặc Phòng CTSV Nhà A11.",
        "detail_content": (
            "Quy trình xử lý khiếu nại Điểm rèn luyện:\n"
            "1. Thời hạn: 07 ngày làm việc kể từ thời điểm công bố danh sách DRL sơ bộ trên Cổng thông tin sinh viên.\n"
            "2. Hồ sơ khiếu nại gồm:\n"
            "   - Đơn đề nghị xem xét lại Điểm rèn luyện (ghi rõ tiêu chí bị tính thiếu hoặc sai sót).\n"
            "   - Minh chứng đính kèm: Giấy chứng nhận hiến máu, giấy chứng nhận tình nguyện, chứng nhận tham gia hội thảo/cuộc thi.\n"
            "3. Nơi tiếp nhận: Trợ lý CTSV cấp Khoa tiếp nhận và trình Hội đồng đánh giá cấp Khoa họp điều chỉnh trong vòng 03 ngày làm việc trước khi gửi bảng điểm chuẩn y về Phòng CTSV Nhà A11."
        ),
        "confidence_score": 0.98,
        "required_forms": [
            RequiredFormItem(
                form_code="BM-KN-DRL",
                form_name="Đơn khiếu nại & phúc khảo Điểm rèn luyện",
                download_url="/api/v1/documents/forms/BM-KN-DRL.pdf",
                guide="Kèm bản photo minh chứng hoạt động nộp tại Văn phòng Khoa trong 7 ngày",
            )
        ],
        "related_articles": ["Điều 10. Quyền của người học về thông tin kết quả rèn luyện"],
    },
    {
        "id": "faq_hoat_dong_cong_diem_drl",
        "keywords": ["cong diem drl", "hoat dong cong diem", "mua he xanh", "tiep suc mua thi", "hien mau", "hoi thao", "cong drl the nao"],
        "matched_article": "Bảng phụ lục chấm điểm rèn luyện ban hành kèm Quy chế DRL",
        "regulation_title": "Danh mục hoạt động phong trào và mức cộng điểm rèn luyện",
        "summary_answer": "Sinh viên tham gia các phong trào được cộng điểm theo biểu quy định: Hiến máu nhân đạo (+5 điểm/lần), Chiến dịch Mùa hè xanh (+10 điểm), Tiếp sức mùa thi (+8 điểm), Nghiên cứu khoa học (+5 đến +10 điểm), Hội thao/văn nghệ (+3 đến +5 điểm).",
        "detail_content": (
            "Chi tiết mức điểm cộng hoạt động sinh viên ĐH Đà Lạt:\n"
            "• Hiến máu tình nguyện: +5 điểm vào Tiêu chí 3 (tối đa 2 lần/kỳ).\n"
            "• Tham gia Chiến dịch Mùa hè xanh / Tiếp sức mùa thi trọn vẹn: +8 đến +10 điểm vào Tiêu chí 3.\n"
            "• Đạt giải Nghiên cứu khoa học cấp Trường/Bộ: +10 điểm vào Tiêu chí 1.\n"
            "• Tham gia đầy đủ Tuần SHCD: +10 điểm vào Tiêu chí 2 (vắng không lý do bị trừ 10 điểm).\n"
            "• Tham gia Đội cờ đỏ, Đội tự quản, Câu lạc bộ tình nguyện: +3 đến +5 điểm vào Tiêu chí 5."
        ),
        "confidence_score": 0.98,
        "required_forms": [],
        "related_articles": ["Kế hoạch hoạt động Đoàn Thanh niên & Hội Sinh viên ĐH Đà Lạt"],
    },

    # ── 7. NGHĨA VỤ QUÂN SỰ (NVQS) & TẠM HOÃN ──────────────────────────────────
    {
        "id": "faq_giay_xac_nhan_nvqs",
        "keywords": ["nvqs", "hoan nvqs", "tam hoan nvqs", "giay hoan nvqs", "giay xac nhan sv", "bm04", "bm-04", "xnsv", "xin hoan nvqs o dau", "phuc vu quan su"],
        "matched_article": "Thông tư liên tịch số 13/2013/TTLT-BGDĐT-BQP & Quy trình CTSV Một cửa",
        "regulation_title": "Quy trình cấp Giấy xác nhận sinh viên phục vụ tạm hoãn gọi nhập ngũ",
        "summary_answer": "Sinh viên nộp Phiếu đề nghị cấp Giấy xác nhận (Mẫu BM-04-XNSV) trực tiếp tại Bộ phận Một cửa - Phòng CTSV (Nhà A11) hoặc gửi yêu cầu trên Cổng sinh viên để nhận Giấy xác nhận tạm hoãn NVQS nộp cho Ban CHQS cấp xã/phường.",
        "detail_content": (
            "Quy định cấp Giấy xác nhận tạm hoãn Nghĩa vụ quân sự:\n"
            "1. Đối tượng được cấp: Nam sinh viên đang theo học hệ đại học chính quy trong thời gian đào tạo chuẩn của khóa học (4 năm hoặc 4.5 năm tùy ngành).\n"
            "2. Không cấp giấy tạm hoãn cho sinh viên thuộc các trường hợp: Đã quá thời hạn đào tạo chuẩn (học kỳ kéo dài/nợ môn), sinh viên đang nghỉ học tạm thời (bảo lưu), sinh viên hệ vừa làm vừa học hoặc đang bị đình chỉ học tập.\n"
            "3. Các bước thực hiện:\n"
            "   - Bước 1: Tải mẫu BM-04-XNSV hoặc đăng ký cấp giấy online tại portal.dlu.edu.vn.\n"
            "   - Bước 2: Nhận giấy xác nhận có dấu mộc đỏ của Nhà trường tại Bộ phận Một cửa Nhà A11 (thời gian trả kết quả từ 1 - 2 ngày làm việc).\n"
            "   - Bước 3: Nộp giấy về Ban Chỉ huy Quân sự cấp xã/phường nơi đăng ký hộ khẩu thường trú trước ngày 15/10 hằng năm."
        ),
        "confidence_score": 0.99,
        "required_forms": [
            RequiredFormItem(
                form_code="BM-04-XNSV",
                form_name="Phiếu đề nghị cấp Giấy xác nhận sinh viên (Tạm hoãn NVQS)",
                download_url="/api/v1/documents/forms/BM-04-XNSV.pdf",
                guide="Nộp tại Bộ phận Một cửa Nhà A11 hoặc gửi yêu cầu trực tuyến trên Cổng sinh viên",
            )
        ],
        "related_articles": [
            "Điều 41 Luật Nghĩa vụ quân sự năm 2015",
            "Quy trình dịch vụ công một cửa Nhà A11",
        ],
    },
    {
        "id": "faq_dieu_kien_hoan_nvqs",
        "keywords": ["dieu kien hoan nvqs", "hoc nam 5 co duoc hoan nvqs", "hoc lai co duoc hoan nvqs", "bao luu co duoc hoan nvqs khong", "luat nvqs"],
        "matched_article": "Khoản 1 Điều 41, Luật Nghĩa vụ quân sự năm 2015",
        "regulation_title": "Quy định về đối tượng tạm hoãn gọi nhập ngũ trong thời bình",
        "summary_answer": "Chỉ sinh viên đang đào tạo trình độ đại học hệ chính quy trong MỘT khóa đào tạo của MỘT cơ sở giáo dục đại học và trong THỜI GIAN ĐÀO TẠO CHUẨN mới được tạm hoãn gọi nhập ngũ. Sinh viên học kéo dài (năm 5), học văn bằng 2 hoặc đang bảo lưu không thuộc diện được tạm hoãn.",
        "detail_content": (
            "Căn cứ Điều 41 Luật NVQS 2015:\n"
            "• Tạm hoãn gọi nhập ngũ đối với công dân: Đang học tại cơ sở giáo dục phổ thông; đang được đào tạo trình độ đại học hệ chính quy thuộc một cơ sở giáo dục đại học trong thời gian một khóa đào tạo của một trình độ đào tạo.\n"
            "• Trường hợp KHÔNG được tạm hoãn:\n"
            "  1. Sinh viên đã hết thời gian đào tạo chuẩn theo chương trình (ví dụ khóa 4 năm nhưng sang năm thứ 5 vẫn chưa tốt nghiệp).\n"
            "  2. Sinh viên theo học chương trình đại học thứ hai (văn bằng 2, song bằng).\n"
            "  3. Sinh viên chuyển trường hoặc học lại từ đầu sau khi đã học ở một trường khác.\n"
            "  4. Sinh viên đang trong thời gian nghỉ học tạm thời (bảo lưu) vì lý do cá nhân."
        ),
        "confidence_score": 0.98,
        "required_forms": [],
        "related_articles": ["Thông tư 148/2018/TT-BQP quy định tuyển chọn và gọi công dân nhập ngũ"],
    },

    # ── 8. THẺ SINH VIÊN, BẢO HIỂM Y TẾ & VAY VỐN ─────────────────────────────
    {
        "id": "faq_mat_the_sinh_vien",
        "keywords": ["mat the sinh vien", "tsv", "the sv", "lam lai the", "cap lai the", "the dlu", "bm07", "bm-07", "lam the moi", "lam the o dau"],
        "matched_article": "Quy trình Dịch vụ Một cửa Hỗ trợ Người học — Phòng CTSV",
        "regulation_title": "Quy định về quản lý, sử dụng và cấp lại Thẻ sinh viên tích hợp",
        "summary_answer": "Khi bị mất hoặc hỏng thẻ sinh viên, bạn nộp Đơn đề nghị cấp lại thẻ (Mẫu BM-07-CTSV) kèm 01 ảnh thẻ 3x4 tại Bộ phận Một cửa Nhà A11. Thời gian nhận thẻ từ 3 đến 5 ngày làm việc; trong lúc chờ thẻ cứng sinh viên được cấp Giấy xác nhận thay thế.",
        "detail_content": (
            "Trình tự cấp lại Thẻ sinh viên ĐH Đà Lạt:\n"
            "1. Hồ sơ chuẩn bị:\n"
            "   - Đơn đề nghị cấp lại Thẻ sinh viên (Mẫu BM-07-CTSV).\n"
            "   - 01 ảnh thẻ kích thước 3x4 (chụp phông nền xanh trong vòng 6 tháng gần nhất, ghi rõ MSSV, Họ tên sau ảnh).\n"
            "   - Bản photo CCCD (không cần công chứng).\n"
            "2. Nơi nộp: Bộ phận Một cửa - Phòng CTSV (Nhà A11).\n"
            "3. Lệ phí phôi thẻ tích hợp (thẻ từ liên kết Thư viện và Ngân hàng BIDV): Theo quy định của đơn vị phát hành thẻ.\n"
            "4. Thẻ tạm: Trong thời gian chờ in thẻ cứng, sinh viên được cấp Giấy chứng nhận sinh viên có dán ảnh đóng dấu giáp lai để vào phòng thi và vào Thư viện."
        ),
        "confidence_score": 0.99,
        "required_forms": [
            RequiredFormItem(
                form_code="BM-07-CTSV",
                form_name="Đơn đề nghị cấp lại Thẻ sinh viên",
                download_url="/api/v1/documents/forms/BM-07-CTSV.pdf",
                guide="Kèm 01 ảnh 3x4 và nộp tại Bộ phận Một cửa Nhà A11",
            )
        ],
        "related_articles": ["Quy chế sử dụng thẻ sinh viên tích hợp thẻ thư viện DLU"],
    },
    {
        "id": "faq_vay_von_ngan_hang_csxh",
        "keywords": ["vay von", "nhcsxh", "csxh", "ngan hang chinh sach", "vay tien di hoc", "giay xac nhan vay von", "vay tin dung sv", "4 trieu 1 thang"],
        "matched_article": "Quyết định 157/2007/QĐ-TTg & Quyết định 05/2022/QĐ-TTg của Thủ tướng Chính phủ",
        "regulation_title": "Chính sách tín dụng ưu đãi đối với học sinh, sinh viên",
        "summary_answer": "Sinh viên thuộc gia đình hộ nghèo, cận nghèo hoặc khó khăn đột xuất được vay vốn tín dụng học tập tối đa 4.000.000đ/tháng (40.000.000đ/năm). Sinh viên xin Giấy xác nhận (Mẫu 01/TDSV) tại Nhà A11 để gửi về Ngân hàng CSXH tại địa phương.",
        "detail_content": (
            "Thủ tục vay vốn tín dụng học sinh - sinh viên:\n"
            "1. Đối tượng được vay:\n"
            "   - Sinh viên mồ côi cả cha lẫn mẹ hoặc chỉ mồ côi cha hoặc mẹ nhưng người còn lại không có khả năng lao động.\n"
            "   - Sinh viên thuộc hộ nghèo, hộ cận nghèo theo chuẩn nghèo đa chiều.\n"
            "   - Sinh viên mà gia đình gặp khó khăn về tài chính do tai nạn, bệnh tật, thiên tai, dịch bệnh.\n"
            "2. Mức vốn vay: Tối đa 4.000.000 đồng/tháng/sinh viên (tương đương 40 triệu đồng/năm học 10 tháng).\n"
            "3. Lãi suất: Ưu đãi theo công bố của Ngân hàng CSXH từng thời kỳ.\n"
            "4. Hồ sơ nộp tại trường: Sinh viên tải Giấy xác nhận (Mẫu số 01/TDSV ban hành theo Quyết định 05/2022), điền thông tin và nộp tại Nhà A11 để Nhà trường ký tên đóng dấu xác nhận đang theo học và chưa bị kỷ luật."
        ),
        "confidence_score": 0.99,
        "required_forms": [
            RequiredFormItem(
                form_code="BM-01-TDSV",
                form_name="Giấy xác nhận học sinh, sinh viên vay vốn tín dụng Ngân hàng CSXH",
                download_url="/api/v1/documents/forms/BM-01-TDSV.pdf",
                guide="Nhà A11 ký xác nhận trong ngày để sinh viên nộp về UBND/Ngân hàng CSXH địa phương",
            )
        ],
        "related_articles": ["Quyết định số 05/2022/QĐ-TTg sửa đổi Quyết định 157/2007/QĐ-TTg"],
    },
    {
        "id": "faq_bao_hiem_y_te",
        "keywords": ["bhyt", "bao hiem y te", "dong bhyt", "the bhyt", "vssid", "bhyt bat buoc", "tra cuu bhyt", "gia bhyt"],
        "matched_article": "Luật Bảo hiểm y tế sửa đổi, bổ sung & Hướng dẫn liên ngành BHXH tỉnh Lâm Đồng",
        "regulation_title": "Quy định tham gia Bảo hiểm y tế bắt buộc đối với người học",
        "summary_answer": "BHYT là bảo hiểm BẮT BUỘC theo Luật BHYT đối với 100% sinh viên. Ngân sách Nhà nước hỗ trợ 30% mức đóng, sinh viên chỉ đóng 70%. Thẻ BHYT được tích hợp trực tiếp trên ứng dụng VssID và CCCD gắn chip.",
        "detail_content": (
            "Thông tin quan trọng về BHYT sinh viên ĐH Đà Lạt:\n"
            "1. Tính bắt buộc: 100% sinh viên đang theo học tại trường bắt buộc phải tham gia BHYT (trừ sinh viên đã có thẻ BHYT theo đối tượng khác như thân nhân quân nhân, hộ nghèo, DTTS có thẻ do địa phương cấp).\n"
            "2. Mức đóng: Bằng 4.5% mức lương cơ sở x số tháng tham gia, trong đó Nhà nước đã hỗ trợ 30% kinh phí, sinh viên chỉ nộp 70% còn lại.\n"
            "3. Tra cứu thẻ BHYT: Nhà trường không in thẻ giấy, sinh viên cài đặt ứng dụng VssID trên điện thoại hoặc xuất trình CCCD gắn chip khi đi khám chữa bệnh.\n"
            "4. Sinh viên đã có thẻ BHYT diện chính sách phải nộp bản photo thẻ BHYT về Trạm Y tế/Nhà A11 đầu năm học để không bị thu trùng tiền."
        ),
        "confidence_score": 0.98,
        "required_forms": [],
        "related_articles": ["Hướng dẫn tham gia BHYT học sinh sinh viên đầu năm học của DLU"],
    },
    {
        "id": "faq_kham_chua_benh_bhyt",
        "keywords": ["kham benh bhyt", "tram y te", "kham o dau", "chuyen tuyen bhyt", "benh vien da khoa lam dong", "quyen loi bhyt"],
        "matched_article": "Quy định Khám chữa bệnh ban đầu và chăm sóc sức khỏe ban đầu DLU",
        "regulation_title": "Quy trình khám chữa bệnh BHYT và chăm sóc y tế sinh viên",
        "summary_answer": "Sinh viên đăng ký KCB ban đầu tại Trạm Y tế Trường ĐH Đà Lạt hoặc Bệnh viện Đa khoa Lâm Đồng. Khi đi khám chỉ cần mang theo CCCD gắn chip hoặc mở ứng dụng VssID trên điện thoại.",
        "detail_content": (
            "Quyền lợi khám chữa bệnh BHYT của sinh viên:\n"
            "• Khám tại Trạm Y tế trường (Nhà A4): Khám bệnh thông thường, sơ cấp cứu, cấp phát thuốc miễn phí trong danh mục BHYT.\n"
            "• Khám tại Cơ sở đăng ký ban đầu (thường là Bệnh viện Đa khoa tỉnh Lâm Đồng hoặc Trung tâm Y tế TP Đà Lạt): Được hưởng 80% chi phí KCB trong phạm vi BHYT.\n"
            "• Khám trái tuyến/vượt tuyến: Được quỹ BHYT chi trả theo tỷ lệ quy định của Luật BHYT hiện hành (nội trú bệnh viện tuyến tỉnh hưởng 100% chi phí theo phạm vi mức hưởng).\n"
            "• Trường hợp cấp cứu: Được tiếp nhận tại bất kỳ cơ sở y tế nào và hưởng đầy đủ quyền lợi BHYT đúng tuyến."
        ),
        "confidence_score": 0.98,
        "required_forms": [],
        "related_articles": ["Nội quy Trạm Y tế Trường Đại học Đà Lạt"],
    },

    # ── 9. KÝ TÚC XÁ (KTX) & QUẢN LÝ NGOẠI TRÚ ─────────────────────────────────
    {
        "id": "faq_ky_tuc_xa_dlu",
        "keywords": ["ktx", "ky tuc xa", "o ktx", "dang ky ktx", "noi tru", "bm05", "bm-05", "vao ktx", "uu tien ktx", "ban quan ly ktx"],
        "matched_article": "Quy chế Quản lý Ký túc xá sinh viên Trường Đại học Đà Lạt",
        "regulation_title": "Quy định đăng ký, xét duyệt và bố trí chỗ ở Ký túc xá sinh viên DLU",
        "summary_answer": "Sinh viên đăng ký nội trú Ký túc xá nộp Đơn (Mẫu BM-05-KTX) tại Ban Quản lý KTX hoặc Phòng CTSV Nhà A11 vào đầu năm học. Ưu tiên xét theo thứ tự: Mồ côi, khuyết tật, hộ nghèo/cận nghèo, con thương binh, vùng sâu vùng xa, và tân sinh viên.",
        "detail_content": (
            "Thứ tự ưu tiên xét duyệt vào Ký túc xá ĐH Đà Lạt:\n"
            "1. Sinh viên mồ côi cả cha lẫn mẹ; sinh viên khuyết tật nặng.\n"
            "2. Sinh viên là con liệt sĩ, con thương binh, bệnh binh.\n"
            "3. Sinh viên thuộc hộ nghèo, hộ cận nghèo theo quy định hiện hành.\n"
            "4. Sinh viên người dân tộc thiểu số ở vùng đặc biệt khó khăn.\n"
            "5. Sinh viên có hộ khẩu thường trú tại vùng sâu, vùng xa, hải đảo.\n"
            "6. Tân sinh viên khóa mới nhập học.\n"
            "Hồ sơ đăng ký gồm: Đơn xin vào nội trú KTX (BM-05-KTX), bản photo CCCD, 02 ảnh thẻ 3x4 và các giấy tờ minh chứng diện ưu tiên chính sách (nếu có)."
        ),
        "confidence_score": 0.99,
        "required_forms": [
            RequiredFormItem(
                form_code="BM-05-KTX",
                form_name="Đơn đăng ký nội trú Ký túc xá sinh viên",
                download_url="/api/v1/documents/forms/BM-05-KTX.pdf",
                guide="Nộp tại Ban Quản lý KTX hoặc Bộ phận Một cửa Nhà A11 đầu năm học",
            )
        ],
        "related_articles": [
            "Nội quy An ninh trật tự Ký túc xá Trường ĐH Đà Lạt",
            "Biểu mức thu phí phòng ở Ký túc xá hằng năm",
        ],
    },
    {
        "id": "faq_gia_phong_ktx",
        "keywords": ["gia ktx", "tien phong ktx", "phi ktx", "phong ktx bao nhieu", "tien dien nuoc ktx", "co so vat chat ktx"],
        "matched_article": "Bảng biểu phí dịch vụ nội trú ban hành kèm Quyết định KTX DLU",
        "regulation_title": "Mức thu phí nội trú và tiện ích sinh hoạt Ký túc xá ĐH Đà Lạt",
        "summary_answer": "Phí phòng ở KTX ĐH Đà Lạt dao động từ 200.000đ đến 450.000đ/tháng/sinh viên tùy loại phòng (phòng 4 người hoặc phòng 8 người). Phòng có giường tầng, bàn học, wifi internet, bình nước nóng lạnh và bảo vệ 24/7.",
        "detail_content": (
            "Chi tiết các loại phòng và tiện ích KTX ĐH Đà Lạt:\n"
            "• Phòng tiêu chuẩn 8 sinh viên: Khoảng 200.000đ - 250.000đ/tháng/người (vệ sinh khép kín, có bình tắm nước nóng).\n"
            "• Phòng tiện nghi 4 - 6 sinh viên: Khoảng 350.000đ - 450.000đ/tháng/người (giường đơn/tầng cao cấp, bàn học cá nhân).\n"
            "• Tiền điện, nước: Tính theo chỉ số đồng hồ thực tế tiêu thụ của từng phòng theo giá quy định của Nhà nước.\n"
            "• Tiện ích đi kèm: Hệ thống wifi phủ sóng, phòng tự học chung, sân bóng chuyền, bảo vệ trực camera an ninh 24/24."
        ),
        "confidence_score": 0.98,
        "required_forms": [],
        "related_articles": ["Nội quy sử dụng điện, nước và bảo quản tài sản công KTX"],
    },
    {
        "id": "faq_dang_ky_tam_tru_ngoai_tru",
        "keywords": ["ngoai tru", "o ngoai", "thue tro", "tam tru", "dang ky tam tru", "khai bao tam tru", "cong an phuong", "phieu ngoai tru"],
        "matched_article": "Quy chế Quản lý Sinh viên Ngoại trú Trường Đại học Đà Lạt",
        "regulation_title": "Quy định về việc cư trú ngoại trú và đăng ký tạm trú của sinh viên",
        "summary_answer": "Sinh viên không ở KTX phải thuê trọ ngoại trú có trách nhiệm đăng ký tạm trú với Công an phường/xã nơi cư trú trong vòng 30 ngày, đồng thời cập nhật địa chỉ trọ trên Cổng thông tin sinh viên và nộp Phiếu thông tin ngoại trú cho Cố vấn học tập.",
        "detail_content": (
            "Nghĩa vụ của sinh viên ở trọ ngoại trú:\n"
            "1. Đăng ký tạm trú: Xuất trình CCCD cho chủ nhà trọ để thực hiện khai báo tạm trú qua Cổng dịch vụ công quản lý cư trú hoặc tại Công an phường sở tại.\n"
            "2. Cập nhật thông tin trên hệ thống trường: Đăng nhập Cổng portal.dlu.edu.vn, vào mục 'Thông tin ngoại trú' để điền chính xác số nhà, tên đường, tổ dân phố, số điện thoại chủ nhà trọ.\n"
            "3. Sinh hoạt tại khu dân cư: Giữ gìn an ninh trật tự, văn minh đô thị, tham gia phong trào khu phố nơi tạm trú.\n"
            "4. Nhà trường phối hợp cùng Công an các phường (Phường 8, Phường 2, v.v.) định kỳ kiểm tra đột xuất tình hình cư trú của sinh viên."
        ),
        "confidence_score": 0.98,
        "required_forms": [],
        "related_articles": ["Kế hoạch liên tịch An ninh trật tự khu vực giáp ranh trường học"],
    },

    # ── 10. HỌC VỤ: CẢNH BÁO, ĐIỂM F, HỌC LẠI & HỌC CẢI THIỆN ─────────────────
    {
        "id": "faq_canh_bao_hoc_vu",
        "keywords": ["canh bao hoc vu", "canh bao hoc tap", "bi canh bao", "cpa", "diem trung binh thap", "no tin chi", "nguong canh bao", "dieu 16"],
        "matched_article": "Điều 16, Quy chế Đào tạo trình độ đại học theo hệ thống tín chỉ",
        "regulation_title": "Quy chế Xử lý học vụ và Cảnh báo kết quả học tập sinh viên ĐH Đà Lạt",
        "summary_answer": "Sinh viên bị cảnh báo học vụ nếu CPA tích lũy dưới 1.20 (năm thứ nhất), dưới 1.40 (năm thứ hai), dưới 1.60 (từ năm thứ ba trở đi), hoặc có số tín chỉ nợ đọng vượt quá 24 tín chỉ. Bị cảnh báo 2 lần liên tiếp có nguy cơ bị buộc thôi học.",
        "detail_content": (
            "Quy định chi tiết về các mức cảnh báo học vụ:\n"
            "1. Ngưỡng CPA tích lũy bị cảnh báo học vụ:\n"
            "   - Kết thúc năm học thứ 1: CPA < 1.20\n"
            "   - Kết thúc năm học thứ 2: CPA < 1.40\n"
            "   - Kết thúc năm học thứ 3 trở đi: CPA < 1.60\n"
            "2. Hoặc tổng số tín chỉ nợ đọng (điểm F) chưa cải thiện vượt quá 24 tín chỉ.\n"
            "3. Sinh viên nhận thông báo cảnh báo học vụ phải gặp trực tiếp Cố vấn học tập (CVHT) để điều chỉnh kế hoạch học tập, chỉ được đăng ký tối đa 14 tín chỉ trong kỳ tiếp theo để tập trung trả nợ môn."
        ),
        "confidence_score": 0.99,
        "required_forms": [],
        "related_articles": [
            "Điều 17. Buộc thôi học do kết quả học tập kém",
            "Quy định vai trò và trách nhiệm của Cố vấn học tập",
        ],
    },
    {
        "id": "faq_buoc_thoi_hoc_hoc_vu",
        "keywords": ["buoc thoi hoc", "duoi hoc", "thoi hoc vi diem kem", "canh bao 3 lan", "bi duoi", "het thoi gian dao tao", "dieu 17"],
        "matched_article": "Điều 17, Quy chế Đào tạo tín chỉ Trường Đại học Đà Lạt",
        "regulation_title": "Các trường hợp bị buộc thôi học do kết quả học tập không đạt yêu cầu",
        "summary_answer": "Sinh viên bị buộc thôi học nếu: Bị cảnh báo học vụ 02 lần liên tiếp hoặc tổng cộng 03 lần trong cả khóa học, hoặc vượt quá thời gian tối đa được phép học tập tại trường (khóa 4 năm tối đa không quá 6 năm).",
        "detail_content": (
            "Căn cứ Điều 17 Quy chế Đào tạo: Sinh viên bị buộc thôi học trong các trường hợp sau:\n"
            "1. Bị cảnh báo học vụ 02 lần liên tiếp theo quy định.\n"
            "2. Tổng số lần bị cảnh báo học vụ vượt quá 03 lần trong toàn bộ khóa học.\n"
            "3. Vượt quá thời gian tối đa hoàn thành chương trình: Thời gian tối đa bằng 1.5 lần thời gian thiết kế chuẩn (ngành 4 năm tối đa 6 năm; ngành 4.5 năm tối đa 7 năm).\n"
            "4. Bị kỷ luật ở mức buộc thôi học do vi phạm pháp luật hoặc quy chế thi.\n"
            "Sinh viên bị buộc thôi học được Nhà trường cấp Giấy chứng nhận kết quả học tập các môn đã hoàn thành."
        ),
        "confidence_score": 0.98,
        "required_forms": [],
        "related_articles": ["Điều 14. Thời gian tối đa hoàn thành chương trình đào tạo"],
    },
    {
        "id": "faq_hoc_lai_cai_thien",
        "keywords": ["hoc lai", "hoc cai thien", "mon no", "rot mon", "diem d", "nang diem", "diem f", "hoc lai diem f", "diem f hoc lai", "hoc phi hoc lai", "cai thien diem d", "dieu 10"],
        "matched_article": "Điều 10, Quy chế Đào tạo tín chỉ Trường Đại học Đà Lạt",
        "regulation_title": "Quy định về việc học lại và học cải thiện điểm tích lũy",
        "summary_answer": "Học phần bị điểm F bắt buộc phải đăng ký học lại. Học phần đạt điểm D hoặc D+ được phép đăng ký học cải thiện; điểm số mới cao hơn sẽ thay thế điểm cũ để tính lại CPA tích lũy. Học phí học lại tính theo đơn giá tín chỉ thực tế.",
        "detail_content": (
            "Quy định cụ thể về học lại & học cải thiện điểm:\n"
            "1. Học lại (Bắt buộc với điểm F):\n"
            "   - Sinh viên có học phần bắt buộc bị điểm F phải đăng ký học lại môn đó khi trường mở lớp.\n"
            "   - Nếu là học phần tự chọn bị điểm F, sinh viên có thể học lại chính môn đó hoặc chọn học môn tự chọn khác cùng khối kiến thức tương đương.\n"
            "2. Học cải thiện (Không bắt buộc):\n"
            "   - Áp dụng cho các học phần đã đạt điểm D, D+ (hoặc C nếu có nguyện vọng nâng hạng tốt nghiệp).\n"
            "   - Điểm học phần sau khi học cải thiện (nếu cao hơn) sẽ được ghi nhận vào bảng điểm tích lũy; điểm cũ được lưu trong lịch sử điểm nhưng không tính vào CPA.\n"
            "3. Học phí: Học lại và học cải thiện đều phải đóng học phí theo số lượng tín chỉ của học phần đó."
        ),
        "confidence_score": 0.99,
        "required_forms": [],
        "related_articles": ["Điều 11. Đăng ký học phần tín chỉ"],
    },
    {
        "id": "faq_dang_ky_tin_chi",
        "keywords": ["dang ky tin chi", "so tin chi toi thieu", "so tin chi toi da", "14 tin chi", "25 tin chi", "hoc ky he", "dang ky mon hoc", "dieu 8"],
        "matched_article": "Điều 8, Quy chế Đào tạo đại học theo hệ thống tín chỉ",
        "regulation_title": "Quy định về đăng ký khối lượng học tập tín chỉ mỗi học kỳ",
        "summary_answer": "Mỗi học kỳ chính, sinh viên phải đăng ký tối thiểu 14 tín chỉ (trừ học kỳ cuối khóa) và tối đa 25 tín chỉ nếu có học lực Khá trở lên. Học kỳ hè không bắt buộc, được đăng ký tối đa 8 tín chỉ.",
        "detail_content": (
            "Khung khối lượng tín chỉ đăng ký mỗi kỳ học:\n"
            "1. Học kỳ chính (HK1 và HK2):\n"
            "   - Khối lượng tối thiểu: 14 tín chỉ/học kỳ đối với sinh viên xếp hạng học lực bình thường (học kỳ cuối khóa không áp dụng giới hạn tối thiểu nếu đã gần hoàn thành CTĐT).\n"
            "   - Khối lượng tối thiểu đối với sinh viên đang bị cảnh báo học vụ: 10 tín chỉ; tối đa: 14 tín chỉ.\n"
            "   - Khối lượng tối đa: 25 tín chỉ/học kỳ đối với sinh viên có học lực từ loại Khá (GPA ≥ 2.50) trở lên.\n"
            "2. Học kỳ phụ (Học kỳ hè):\n"
            "   - Không bắt buộc, dành cho sinh viên có nhu cầu học lại, học vượt hoặc học cải thiện.\n"
            "   - Khối lượng tối đa: 08 tín chỉ."
        ),
        "confidence_score": 0.98,
        "required_forms": [],
        "related_articles": ["Điều 9. Rút bớt học phần đã đăng ký"],
    },
    {
        "id": "faq_hoan_thi_hoan_hoc_phan",
        "keywords": ["hoan thi", "xin hoan thi", "bi om khong thi duoc", "tai nan khong di thi duoc", "don hoan thi", "thi dot 2", "diem i"],
        "matched_article": "Điều 21, Quy chế Đào tạo tín chỉ Trường Đại học Đà Lạt",
        "regulation_title": "Quy định về việc hoãn thi kết thúc học phần và nhận điểm I",
        "summary_answer": "Sinh viên vì lý do bất khả kháng (ốm đau cấp cứu, tai nạn, việc tang gia đình) không thể dự thi phải nộp Đơn xin hoãn thi kèm giấy xác nhận của bệnh viện về Phòng Đào tạo/Một cửa A11 trước giờ thi để được nhận điểm I và dự thi bổ sung ở đợt sau.",
        "detail_content": (
            "Thủ tục xin hoãn thi kết thúc học phần:\n"
            "1. Lý do hợp lệ: Ốm đau đột xuất có xác nhận điều trị của bệnh viện tuyến huyện trở lên, tai nạn giao thông có biên bản, hoặc việc hiếu của gia đình (cha mẹ, tứ thân phụ mẫu mất).\n"
            "2. Thời hạn nộp đơn: Nộp trước giờ thi hoặc muộn nhất trong vòng 03 ngày làm việc sau buổi thi.\n"
            "3. Xử lý học vụ: Môn học được hoãn thi sẽ tạm thời nhận điểm 'I' (Incomplete - Chưa hoàn thành) và không tính vào CPA học kỳ đó.\n"
            "4. Thi bổ sung: Sinh viên phải dự thi ở kỳ thi gần nhất có tổ chức học phần đó để chuyển đổi điểm I thành điểm học phần chính thức; nếu không thi sẽ tự động chuyển thành điểm F."
        ),
        "confidence_score": 0.98,
        "required_forms": [
            RequiredFormItem(
                form_code="BM-HT-01",
                form_name="Đơn xin hoãn thi kết thúc học phần",
                download_url="/api/v1/documents/forms/BM-HT-01.pdf",
                guide="Kèm giấy ra viện/chứng nhận viện có mộc tròn nộp tại Một cửa A11",
            )
        ],
        "related_articles": ["Quy chế Khảo thí và Đảm bảo chất lượng giáo dục"],
    },

    # ── 11. CHUYỂN NGÀNH, SONG BẰNG & CHUẨN ĐẦU RA TỐT NGHIỆP ─────────────────
    {
        "id": "faq_chuyen_nganh_dao_tao",
        "keywords": ["chuyen nganh", "doi nganh", "chuyen nganh hoc", "dieu kien chuyen nganh", "cpa 2.5", "chuyen nganh sau nam 1"],
        "matched_article": "Điều 15, Quy chế Đào tạo đại học theo hệ thống tín chỉ",
        "regulation_title": "Điều kiện và thủ tục xét chuyển ngành đào tạo đối với sinh viên",
        "summary_answer": "Sinh viên được xét chuyển sang ngành khác sau khi hoàn thành năm học thứ nhất nếu: Không bị cảnh báo học vụ, có CPA tích lũy ≥ 2.50 và điểm thi tuyển sinh đầu vào bằng hoặc cao hơn điểm chuẩn ngành muốn chuyển đến.",
        "detail_content": (
            "Điều kiện chuyển ngành đào tạo tại ĐH Đà Lạt:\n"
            "1. Thời điểm xét: Chỉ xét sau khi kết thúc năm học thứ 1 và trước khi bắt đầu năm học thứ 3.\n"
            "2. Điều kiện bắt buộc:\n"
            "   - Sinh viên không đang trong thời gian bị kỷ luật hoặc cảnh báo học vụ.\n"
            "   - Điểm trúng tuyển đầu vào của sinh viên đạt mức điểm chuẩn trúng tuyển của ngành xin chuyển đến trong cùng năm tuyển sinh.\n"
            "   - Điểm trung bình chung tích lũy CPA đạt từ 2.50/4.0 trở lên.\n"
            "   - Ngành xin chuyển đến còn chỉ tiêu tiếp nhận sinh viên theo thông báo của Nhà trường.\n"
            "3. Hồ sơ nộp tại Phòng Quản lý Đào tạo (Nhà A1)."
        ),
        "confidence_score": 0.98,
        "required_forms": [
            RequiredFormItem(
                form_code="BM-CN-01",
                form_name="Đơn đề nghị chuyển ngành đào tạo",
                download_url="/api/v1/documents/forms/BM-CN-01.pdf",
                guide="Kèm Bảng điểm tích lũy năm 1 nộp tại Phòng Quản lý Đào tạo Nhà A1",
            )
        ],
        "related_articles": ["Thông báo chỉ tiêu tiếp nhận chuyển ngành hằng năm"],
    },
    {
        "id": "faq_hoc_song_bang_hai_chuong_trinh",
        "keywords": ["song bang", "hoc hai nganh", "hai chuong trinh", "hoc van bang 2", "nganh 2", "dieu kien hoc song bang"],
        "matched_article": "Điều 18, Quy chế Đào tạo tín chỉ Trường Đại học Đà Lạt",
        "regulation_title": "Quy định học cùng lúc hai chương trình đào tạo (song bằng)",
        "summary_answer": "Sinh viên được đăng ký học chương trình thứ hai (song bằng) sau khi hoàn thành năm học thứ nhất nếu có CPA tích lũy từ 2.50 trở lên và không thuộc diện bị cảnh báo học vụ. Khi tốt nghiệp được cấp 02 bằng cử nhân/kỹ sư độc lập.",
        "detail_content": (
            "Tiêu chuẩn đăng ký học cùng lúc hai chương trình:\n"
            "1. Ngành đào tạo thứ hai phải khác ngành đào tạo thứ nhất.\n"
            "2. Sinh viên đã hoàn thành năm học thứ 1 của chương trình thứ nhất và đạt CPA ≥ 2.50.\n"
            "3. Trong quá trình học song bằng, nếu điểm CPA chương trình 1 bị tụt xuống dưới 2.00 thì sinh viên phải tạm dừng học chương trình 2 ở học kỳ tiếp theo.\n"
            "4. Quyền lợi: Các học phần đại cương chung (Triết học, Ngoại ngữ, GDTC, GDQP...) được công nhận chuyển đổi điểm tự động, chỉ cần học các học phần chuyên ngành của ngành thứ hai."
        ),
        "confidence_score": 0.98,
        "required_forms": [],
        "related_articles": ["Quy định công nhận giá trị chuyển đổi tín chỉ tương đương"],
    },
    {
        "id": "faq_tot_nghiep_chuan_dau_ra",
        "keywords": ["tot nghiep", "chuan dau ra", "dieu kien tot nghiep", "cdr", "xet tot nghiep", "cpa 2.0", "b1", "toeic", "tin hoc"],
        "matched_article": "Điều 25, Quy chế Đào tạo đại học hệ chính quy Trường Đại học Đà Lạt",
        "regulation_title": "Quy định công nhận tốt nghiệp và cấp bằng cử nhân, kỹ sư",
        "summary_answer": "Điều kiện tốt nghiệp: Tích lũy đủ số tín chỉ quy định của CTĐT, CPA toàn khóa ≥ 2.00, đạt Chuẩn đầu ra Ngoại ngữ (B1/TOEIC 450) và Tin học chuẩn quốc gia, hoàn thành môn GDTC, GDQP và không bị kỷ luật từ cảnh cáo trở lên.",
        "detail_content": (
            "Các tiêu chuẩn bắt buộc để được xét tốt nghiệp tại DLU:\n"
            "1. Tích lũy đủ khối lượng học phần theo khung chương trình đào tạo của ngành (từ 125 - 150 tín chỉ tùy ngành).\n"
            "2. Điểm trung bình chung tích lũy toàn khóa CPA đạt từ 2.00/4.0 trở lên.\n"
            "3. Chuẩn đầu ra Ngoại ngữ: Có chứng chỉ B1 Khung VSTEP bậc 3 hoặc tương đương (TOEIC 450, IELTS 4.5).\n"
            "4. Chuẩn đầu ra Tin học: Chứng chỉ Ứng dụng CNTT cơ bản theo Thông tư 03/2014/TT-BTTTT.\n"
            "5. Chứng chỉ Giáo dục Quốc phòng - An ninh và hoàn thành các học phần Giáo dục thể chất.\n"
            "6. Hoàn thành đầy đủ nghĩa vụ học phí và nghĩa vụ nộp lưu chiểu khóa luận tại Thư viện DLU."
        ),
        "confidence_score": 0.99,
        "required_forms": [],
        "related_articles": [
            "Quy định Chuẩn đầu ra Ngoại ngữ và Tin học sinh viên ĐH Đà Lạt",
            "Hướng dẫn nộp hồ sơ xét tốt nghiệp từng đợt của Phòng Đào tạo",
        ],
    },
    {
        "id": "faq_chuan_dau_ra_ngoai_ngu",
        "keywords": ["vstep", "toeic 450", "ielts", "chuan ngoai ngu", "bang tieng anh", "chung chi b1", "quy doi tieng anh"],
        "matched_article": "Quyết định ban hành Quy định Chuẩn đầu ra Ngoại ngữ Trường ĐH Đà Lạt",
        "regulation_title": "Bảng quy đổi chứng chỉ ngoại ngữ tương đương Chuẩn đầu ra tốt nghiệp",
        "summary_answer": "Sinh viên không chuyên ngữ phải đạt Chuẩn Ngoại ngữ Bậc 3 (B1) theo Khung năng lực ngoại ngữ 6 bậc dùng cho Việt Nam (VSTEP), hoặc các chứng chỉ quốc tế tương đương còn hạn: TOEIC 450, IELTS 4.5, TOEFL iBT 45.",
        "detail_content": (
            "Khung quy đổi Chuẩn đầu ra Tiếng Anh tại ĐH Đà Lạt:\n"
            "• VSTEP: Bậc 3/6 (Đạt kỳ thi đánh giá năng lực tiếng Anh B1 do Trường ĐH Đà Lạt hoặc các đơn vị được Bộ GD&ĐT cấp phép tổ chức).\n"
            "• TOEIC: Từ 450 điểm trở lên (nghe - đọc).\n"
            "• IELTS: Từ 4.5 điểm trở lên.\n"
            "• TOEFL: iBT từ 45 điểm trở lên.\n"
            "• Sinh viên chuyên ngành Ngoại ngữ (Sư phạm Tiếng Anh, Ngôn ngữ Anh): Phải đạt chuẩn Bậc 5 (C1 VSTEP hoặc IELTS 6.5+).\n"
            "• Hạn nộp chứng chỉ: Nộp bản sao công chứng kèm bản gốc để đối chiếu tại Trung tâm Ngoại ngữ - Tin học DLU trước đợt xét tốt nghiệp 1 tháng."
        ),
        "confidence_score": 0.98,
        "required_forms": [],
        "related_articles": ["Lịch thi VSTEP định kỳ do Trường Đại học Đà Lạt tổ chức"],
    },

    # ── 12. HOẠT ĐỘNG SINH VIÊN, SHCD & KHEN THƯỞNG - KỶ LUẬT ─────────────────
    {
        "id": "faq_sinh_hoat_cong_dan_shcd",
        "keywords": ["shcd", "sinh hoat cong dan", "tuan sinh hoat cong dan", "shcd dau khoa", "shcd giua khoa", "shcd cuoi khoa", "vang shcd"],
        "matched_article": "Thông tư số 10/2016/TT-BGDĐT & Hướng dẫn tổ chức Tuần SHCD ĐH Đà Lạt",
        "regulation_title": "Quy định tham gia Tuần sinh hoạt công dân - sinh viên đầu, giữa và cuối khóa",
        "summary_answer": "Tuần SHCD là hoạt động BẮT BUỘC hằng năm. Sinh viên tham gia đầy đủ và làm bài thu hoạch đạt yêu cầu được cộng 10 điểm rèn luyện. Vắng không lý do bị trừ điểm rèn luyện và phải học bù, nộp lệ phí học lại.",
        "detail_content": (
            "Quy định tham gia Tuần sinh hoạt công dân sinh viên:\n"
            "1. Các đợt tổ chức:\n"
            "   - Tuần SHCD đầu khóa: Dành cho tân sinh viên (phổ biến quy chế đào tạo, quyền lợi và nghĩa vụ).\n"
            "   - Tuần SHCD giữa khóa: Dành cho sinh viên năm 2 và năm 3 (pháp luật, kỹ năng mềm, khởi nghiệp).\n"
            "   - Tuần SHCD cuối khóa: Dành cho sinh viên chuẩn bị tốt nghiệp (kỹ năng xin việc, hội chợ việc làm).\n"
            "2. Đánh giá kết quả: Tham gia điểm danh đầy đủ và làm bài kiểm tra trắc nghiệm/thu hoạch online đạt từ 5.0 điểm trở lên.\n"
            "3. Xử lý vi phạm: Vắng mặt không có lý do chính đáng bị xếp loại Kém tiêu chí SHCD trong Điểm rèn luyện và bắt buộc tham gia lớp học bù do Phòng CTSV tổ chức vào cuối kỳ."
        ),
        "confidence_score": 0.99,
        "required_forms": [],
        "related_articles": ["Kế hoạch tổ chức Tuần Sinh hoạt công dân sinh viên hằng năm"],
    },
    {
        "id": "faq_thu_vien_dlu",
        "keywords": ["thu vien", "muon sach", "gio lam viec thu vien", "a26", "the thu vien", "tra sach", "phong tu hoc", "opac"],
        "matched_article": "Nội quy Trung tâm Thông tin - Thư viện Trường Đại học Đà Lạt (Nhà A26)",
        "regulation_title": "Quy định mượn, trả tài liệu và sử dụng phòng tự học Thư viện DLU",
        "summary_answer": "Thư viện ĐH Đà Lạt (Nhà A26) mở cửa từ 07:30 đến 21:00 từ Thứ Hai đến Thứ Bảy. Sinh viên sử dụng Thẻ sinh viên tích hợp để qua cổng kiểm soát, mượn tối đa 05 cuốn sách giáo trình trong 30 ngày và được gia hạn online qua Cổng OPAC.",
        "detail_content": (
            "Thông tin dịch vụ Thư viện DLU (Nhà A26):\n"
            "• Giờ mở cửa: 07:30 - 21:00 (Thứ 2 đến Thứ 6), 07:30 - 17:00 (Thứ 7). Trong mùa thi Thư viện mở cửa phục vụ đến 22:00.\n"
            "• Tầng 1 & 2: Không gian đọc mở, khu mượn trả tài liệu tự động và các phòng tự học nhóm có máy lạnh, wifi tốc độ cao.\n"
            "• Tầng 3: Phòng máy tính tra cứu cơ sở dữ liệu khoa học quốc tế (ScienceDirect, Springer, IEEE).\n"
            "• Mượn sách giáo trình: Tối đa 5 tài liệu/lần, thời hạn 30 ngày. Sinh viên có thể gia hạn trực tuyến trước ngày hết hạn tại opac.dlu.edu.vn."
        ),
        "confidence_score": 0.99,
        "required_forms": [],
        "related_articles": ["Quy chế mượn trả giáo trình và sử dụng học liệu số"],
    },
    {
        "id": "faq_ho_tro_tam_ly",
        "keywords": ["stress", "ap luc hoc tap", "buon", "tram cam", "tu van tam ly", "lo au", "met moi", "nha a11 tam ly", "chia se"],
        "matched_article": "Trung tâm Tư vấn & Hỗ trợ Tâm lý Người học DLU",
        "regulation_title": "Chương trình tham vấn tâm lý học đường và hỗ trợ tinh thần sinh viên",
        "summary_answer": "Nếu bạn gặp khó khăn tâm lý, căng thẳng học tập hay biến cố cá nhân, Phòng Tham vấn Tâm lý (Tầng 1 Nhà A11) luôn sẵn sàng đồng hành, tư vấn miễn phí và bảo mật tuyệt đối. Đặt lịch qua email: hotrosinhvien@dlu.edu.vn.",
        "detail_content": (
            "Kênh hỗ trợ và tư vấn tâm lý học đường sinh viên DLU:\n"
            "• Địa điểm trực tiếp: Phòng Tham vấn & Hỗ trợ Tâm lý Sinh viên (Tầng 1, Nhà A11).\n"
            "• Thời gian làm việc: 08:00 - 11:30 và 13:30 - 17:00 các ngày làm việc trong tuần.\n"
            "• Đặt lịch bảo mật: Gửi thư đến hotrosinhvien@dlu.edu.vn hoặc đăng ký qua Cổng CTSV.\n"
            "• Đội ngũ tham vấn: Các giảng viên tâm lý học và chuyên gia giàu kinh nghiệm luôn lắng nghe, tôn trọng và đồng hành cùng bạn vượt qua mọi áp lực."
        ),
        "confidence_score": 0.99,
        "required_forms": [],
        "related_articles": ["Chính sách bảo trợ và chăm sóc sức khỏe tinh thần người học"],
    },
    {
        "id": "faq_khen_thuong_sv",
        "keywords": ["khen thuong", "sinh vien tieu bieu", "sinh vien xuat sac", "sinh vien 5 tot", "bang khen", "giai thuong sv"],
        "matched_article": "Quy định Khen thưởng người học Trường Đại học Đà Lạt",
        "regulation_title": "Quy chế xét tặng danh hiệu thi đua và khen thưởng sinh viên hằng năm",
        "summary_answer": "Nhà trường định kỳ khen thưởng danh hiệu 'Sinh viên Xuất sắc', 'Sinh viên Giỏi' và Danh hiệu 'Sinh viên 5 tốt' vào dịp tổng kết năm học kèm tiền thưởng và Giấy khen của Hiệu trưởng.",
        "detail_content": (
            "Tiêu chuẩn khen thưởng sinh viên hằng năm:\n"
            "• Sinh viên Xuất sắc: GPA cả năm đạt từ 3.60 trở lên và DRL đạt từ 90 điểm trở lên.\n"
            "• Sinh viên Giỏi: GPA cả năm đạt từ 3.20 trở lên và DRL đạt từ 80 điểm trở lên.\n"
            "• Danh hiệu 'Sinh viên 5 tốt': Đạt 5 tiêu chí: Đạo đức tốt, Học tập tốt, Thể lực tốt, Tình nguyện tốt và Hội nhập tốt.\n"
            "• Khen thưởng đột xuất: Dành cho sinh viên đạt thành tích xuất sắc trong NCKH cấp Bộ, giải thưởng sáng tạo khởi nghiệp, hoặc hành động dũng cảm cứu người, nhặt được của rơi trả người đánh mất."
        ),
        "confidence_score": 0.98,
        "required_forms": [],
        "related_articles": ["Hướng dẫn xét chọn Sinh viên 5 tốt của Hội Sinh viên ĐH Đà Lạt"],
    },
    {
        "id": "faq_ky_luat_sinh_vien",
        "keywords": ["ky luat", "hinh thuc ky luat", "khien trach", "canh cao", "dinh chi hoc tap", "vi pham noi quy", "dieu 20"],
        "matched_article": "Điều 20, Quy chế Công tác Sinh viên Trường Đại học Đà Lạt",
        "regulation_title": "Các hình thức kỷ luật đối với sinh viên vi phạm quy chế và nội quy",
        "summary_answer": "Có 4 mức kỷ luật sinh viên: Khiển trách, Cảnh cáo, Đình chỉ học tập có thời hạn (1 học kỳ hoặc 1 năm) và Buộc thôi học. Sinh viên bị kỷ luật sẽ bị thông báo về gia đình và lưu hồ sơ.",
        "detail_content": (
            "Khung kỷ luật người học tại ĐH Đà Lạt:\n"
            "1. Khiển trách: Áp dụng đối với sinh viên vi phạm nội quy lần đầu ở mức độ nhẹ (gian lận thi cử lần 1, vi phạm quy định cư trú).\n"
            "2. Cảnh cáo: Áp dụng đối với sinh viên đã bị khiển trách mà tái phạm, hoặc vi phạm nghiêm trọng (thi hộ, nhờ người thi hộ lần 1, vi phạm trật tự an ninh).\n"
            "3. Đình chỉ học tập 1 năm: Áp dụng đối với sinh viên đang trong thời gian cảnh cáo mà tiếp tục vi phạm, hoặc đánh nhau gây thương tích, vi phạm pháp luật hình sự nhẹ.\n"
            "4. Buộc thôi học: Gian lận có tổ chức, sử dụng bằng giả, vi phạm pháp luật bị kết án phạt tù."
        ),
        "confidence_score": 0.98,
        "required_forms": [],
        "related_articles": ["Quy chế Kỷ luật và Xử lý người học vi phạm pháp luật"],
    },
    {
        "id": "faq_doi_song_an_uong",
        "keywords": ["an uong", "quan an", "an gi", "cang tin", "com sinh vien", "an trua", "an toi", "ca phe quanh truong", "ngu hanh son", "phu dong thien vuong"],
        "matched_article": "Cẩm nang Ẩm thực & Đời sống Sinh viên DLU",
        "regulation_title": "Gợi ý các địa điểm ăn uống, tự học ngon - bổ - rẻ quanh Đại học Đà Lạt",
        "summary_answer": "Quanh khuôn viên trường có rất nhiều điểm ăn uống sinh viên phong phú: Căng tin sinh viên A1, phố ăn uống Phù Đổng Thiên Vương, ngã 5 Đại học, chợ đêm sinh viên với mức giá bình dân từ 20.000đ - 35.000đ/suất.",
        "detail_content": (
            "Gợi ý địa chỉ ăn uống & tự học cho sinh viên DLU:\n"
            "• Ăn trưa nhanh: Căng tin sinh viên ĐH Đà Lạt (cạnh giảng đường A1), cơm trưa bình dân đường Phù Đổng Thiên Vương và Bùi Thị Xuân.\n"
            "• Món ăn vặt buổi chiều tối: Bánh tráng nướng, xắp xắp ngã 5 Đại học, sữa đậu nành nóng đường Tăng Bạt Hổ.\n"
            "• Quán cà phê yên tĩnh tự học: The Married Beans, Windmills Coffee, An Cafe gần trường với wifi mạnh và không gian học nhóm thoáng mát."
        ),
        "confidence_score": 0.99,
        "required_forms": [],
        "related_articles": ["Cẩm nang Văn hóa Sinh viên Đại học Đà Lạt"],
    },
    {
        "id": "faq_lien_he_phong_ctsv",
        "keywords": ["lien he ctsv", "so dien thoai ctsv", "email ctsv", "nha a11 o dau", "phong ctsv lam viec luc nao", "gio tiep sinh vien"],
        "matched_article": "Cổng Thông tin Dịch vụ Một cửa Sinh viên Trường Đại học Đà Lạt",
        "regulation_title": "Thông tin liên hệ và Giờ tiếp nhận sinh viên Phòng Công tác Sinh viên",
        "summary_answer": "Phòng CTSV đặt tại Tầng 1, Nhà A11 (Trường ĐH Đà Lạt - Số 01 Phù Đổng Thiên Vương). Giờ làm việc: 07:30 - 11:30 và 13:30 - 17:00 từ Thứ 2 đến Thứ 6. Hotline: (0263) 3822246 | Email: ctsv@dlu.edu.vn.",
        "detail_content": (
            "Thông tin liên hệ chính thức Phòng Công tác Sinh viên (CTSV) DLU:\n"
            "• Địa chỉ: Tòa nhà A11, Trường Đại học Đà Lạt, số 01 Phù Đổng Thiên Vương, Phường 8, TP Đà Lạt, tỉnh Lâm Đồng.\n"
            "• Bộ phận Một cửa: Quầy tiếp nhận và trả hồ sơ sinh viên tại Tầng trệt Nhà A11.\n"
            "• Thời gian tiếp sinh viên: Sáng từ 07:30 đến 11:30; Chiều từ 13:30 đến 17:00 (Thứ Hai đến Thứ Sáu, trừ ngày lễ).\n"
            "• Điện thoại hỗ trợ: (0263) 3822246 (nhánh máy Bộ phận Một cửa).\n"
            "• Email hỗ trợ giải đáp trực tuyến: phongctsv@dlu.edu.vn | Website: ctsv.dlu.edu.vn"
        ),
        "confidence_score": 0.99,
        "required_forms": [],
        "related_articles": ["Quy trình Dịch vụ Một cửa hỗ trợ người học Nhà A11"],
    },
    {
        "id": "faq_tai_cac_bieu_mau_ctsv",
        "keywords": ["danh muc bieu mau", "tai bieu mau", "bm01 bm08", "cac mau don ctsv", "bieu mau mot cua", "tong hop bieu mau"],
        "matched_article": "Danh mục Biểu mẫu Hành chính Sinh viên — Bộ phận Một cửa A11",
        "regulation_title": "Tổng hợp hệ thống biểu mẫu hành chính sinh viên chuẩn Trường ĐH Đà Lạt",
        "summary_answer": "Hệ thống biểu mẫu hành chính CTSV gồm: BM-01 (Xét học bổng), BM-02 (Miễn giảm học phí), BM-03 (Bảo lưu/thôi học), BM-04 (Tạm hoãn NVQS), BM-05 (Đăng ký KTX), BM-06 (Học bổng doanh nghiệp), BM-07 (Làm lại thẻ SV), BM-08 (Gia hạn học phí).",
        "detail_content": (
            "Hệ thống biểu mẫu hành chính chuẩn hóa tại Bộ phận Một cửa Nhà A11:\n"
            "• BM-01-HBKK: Phiếu đề nghị xét cấp Học bổng Khuyến khích học tập\n"
            "• BM-02-MGHP: Đơn đề nghị miễn, giảm học phí (theo Nghị định 81/2021/NĐ-CP)\n"
            "• BM-03-BLHT: Đơn xin nghỉ học tạm thời và bảo lưu kết quả học tập\n"
            "• BM-04-XNSV: Phiếu đề nghị cấp Giấy xác nhận sinh viên (tạm hoãn NVQS, vay vốn)\n"
            "• BM-05-KTX: Đơn đăng ký nội trú Ký túc xá sinh viên\n"
            "• BM-06-HBDN: Đơn đăng ký học bổng tài trợ doanh nghiệp\n"
            "• BM-07-CTSV: Đơn đề nghị cấp lại Thẻ sinh viên do mất hoặc hư hỏng\n"
            "• BM-08-GHHP: Đơn xin gia hạn thời gian nộp học phí\n"
            "Sinh viên có thể tải trực tiếp file PDF bên dưới hoặc nhận bản in tại Nhà A11."
        ),
        "confidence_score": 0.99,
        "required_forms": [
            RequiredFormItem(form_code="BM-01-HBKK", form_name="Đơn xét Học bổng KKHT", download_url="/api/v1/documents/forms/BM-01-HBKK.pdf"),
            RequiredFormItem(form_code="BM-02-MGHP", form_name="Đơn miễn giảm học phí NĐ 81", download_url="/api/v1/documents/forms/BM-02-MGHP.pdf"),
            RequiredFormItem(form_code="BM-03-BLHT", form_name="Đơn xin nghỉ học tạm thời (bảo lưu)", download_url="/api/v1/documents/forms/BM-03-BLHT.pdf"),
            RequiredFormItem(form_code="BM-04-XNSV", form_name="Giấy xác nhận tạm hoãn NVQS", download_url="/api/v1/documents/forms/BM-04-XNSV.pdf"),
            RequiredFormItem(form_code="BM-05-KTX", form_name="Đơn đăng ký Ký túc xá", download_url="/api/v1/documents/forms/BM-05-KTX.pdf"),
            RequiredFormItem(form_code="BM-06-HBDN", form_name="Đơn học bổng doanh nghiệp", download_url="/api/v1/documents/forms/BM-06-HBDN.pdf"),
            RequiredFormItem(form_code="BM-07-CTSV", form_name="Đơn cấp lại Thẻ sinh viên", download_url="/api/v1/documents/forms/BM-07-CTSV.pdf"),
            RequiredFormItem(form_code="BM-08-GHHP", form_name="Đơn xin gia hạn học phí", download_url="/api/v1/documents/forms/BM-08-GHHP.pdf"),
        ],
        "related_articles": ["Quy chế văn thư lưu trữ và tiếp nhận đơn thư một cửa"],
    },
    {
        "id": "faq_quy_che_thi_kiem_tra",
        "keywords": ["quy che thi", "mang dien thoai vao phong thi", "gian lan thi cu", "phao thi", "dinh chi thi", "quy che khao thi"],
        "matched_article": "Quy chế Thi và Kiểm tra kết thúc học phần Trường ĐH Đà Lạt",
        "regulation_title": "Quy định xử lý vi phạm trong phòng thi và kỷ luật phòng thi",
        "summary_answer": "Sinh viên mang điện thoại hoặc thiết bị truyền tin vào phòng thi (dù tắt nguồn hay mở nguồn) đều bị lập biên bản ĐÌNH CHỈ THI ngay lập tức, nhận điểm 0 học phần đó và bị hạ điểm rèn luyện xuống loại Yếu.",
        "detail_content": (
            "Quy tắc nghiêm ngặt trong phòng thi kết thúc học phần DLU:\n"
            "• Tuyệt đối KHÔNG mang điện thoại, đồng hồ thông minh, máy ghi âm hoặc tài liệu không được phép vào khu vực bàn thi.\n"
            "• Nếu mang điện thoại vào phòng thi (kể cả để trong túi quần hoặc đã tắt nguồn): Giám thị lập biên bản đình chỉ thi ngay lập tức.\n"
            "• Hậu quả đình chỉ thi: Nhận điểm 0 học phần đó, bị thông báo phê bình toàn trường và Điểm rèn luyện học kỳ không vượt quá loại Yếu.\n"
            "• Sinh viên chỉ được mang thẻ sinh viên/CCCD, bút viết, bút chì, compa và máy tính bỏ túi nằm trong danh mục Bộ GD&ĐT cho phép."
        ),
        "confidence_score": 0.99,
        "required_forms": [],
        "related_articles": ["Quy chế Khảo thí và Kiểm định chất lượng Trường Đại học Đà Lạt"],
    },
]


def search_faq(query_raw: str) -> dict[str, Any] | None:
    """
    Thuật toán tìm kiếm tri thức quy chế thông minh:
    1. Tự động phân giải các từ viết tắt / từ lóng học vụ sinh viên (mghp, kkht, drl, ktx, nvqs...).
    2. Chuyển đổi không dấu (strip accents) đối với cả câu hỏi gốc và câu đã phân giải.
    3. Tính điểm đối sánh ngữ nghĩa đa tầng (Exact Phrase Match + Token Overlap + Topic Matching).
    4. Trả về kết quả khớp nhất kèm thuộc tính `resolved_query`.
    """
    if not query_raw or len(query_raw.strip()) < 2:
        return None

    raw_trimmed = query_raw.strip()
    resolved_text, was_modified = resolve_acronyms_and_slang(raw_trimmed)

    query_norm = strip_accents(raw_trimmed)
    resolved_norm = strip_accents(resolved_text)

    # Tách từ cho cả bản gốc và bản phân giải
    words_raw = [w for w in re.split(r"\W+", query_norm) if len(w) >= 2]
    words_res = [w for w in re.split(r"\W+", resolved_norm) if len(w) >= 2]
    all_query_words = set(words_raw + words_res)

    best_match = None
    max_score = 0

    for item in FAQ_KNOWLEDGE_BASE:
        score = 0
        keywords = item.get("keywords", [])

        for kw in keywords:
            kw_norm = strip_accents(str(kw))

            # Khớp nguyên cụm từ chính xác (ưu tiên rất cao)
            if kw_norm in resolved_norm or kw_norm in query_norm:
                score += 35 * len(kw_norm.split())
            else:
                # Đối sánh token overlap
                kw_tokens = kw_norm.split()
                if len(kw_tokens) >= 2:
                    overlap = sum(1 for tok in kw_tokens if tok in all_query_words)
                    if overlap >= 2:
                        score += overlap * 8
                elif len(kw_tokens) == 1 and kw_tokens[0] in all_query_words:
                    score += 4

        # Điểm thưởng nếu id khớp ngữ cảnh
        for tok in all_query_words:
            if tok in item["id"]:
                score += 5

        if score > max_score:
            max_score = score
            best_match = item

    # Ngưỡng chấp nhận khớp thông minh (score >= 12)
    if best_match and max_score >= 12:
        return {
            "entry": best_match,
            "resolved_query": resolved_text if was_modified else None,
            "score": max_score,
        }

    return None
