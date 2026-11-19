import urllib.request
import urllib.parse
import json
import time
import sys

BASE_URL = "http://127.0.0.1:8000"

def run_test(category, name, url, method="GET", payload=None, validator=None):
    start = time.perf_counter()
    headers = {"User-Agent": "BenchmarkRunner/2.0"}
    data_bytes = None
    if payload is not None:
        data_bytes = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"

    try:
        req = urllib.request.Request(url, data=data_bytes, headers=headers, method=method)
        with urllib.request.urlopen(req, timeout=12) as resp:
            status = resp.status
            body = resp.read().decode("utf-8")
            elapsed_ms = (time.perf_counter() - start) * 1000.0
            data = json.loads(body)
            passed, reason = validator(status, data)
            return {
                "category": category,
                "name": name,
                "url": url,
                "method": method,
                "status_code": status,
                "latency_ms": round(elapsed_ms, 2),
                "passed": passed,
                "reason": reason,
            }
    except Exception as exc:
        elapsed_ms = (time.perf_counter() - start) * 1000.0
        return {
            "category": category,
            "name": name,
            "url": url,
            "method": method,
            "status_code": 0,
            "latency_ms": round(elapsed_ms, 2),
            "passed": False,
            "reason": str(exc),
        }

def build_250_scenarios():
    scenarios = []

    # =========================================================================
    # NHÓM 1: TÌM KIẾM TOÀN VĂN TIẾNG VIỆT, TỪ VIẾT TẮT & SỐ HIỆU (65 KỊCH BẢN)
    # =========================================================================
    acronyms = [
        ("mghp", "Miễn giảm học phí"),
        ("kkht", "Học bổng khuyến khích học tập"),
        ("drl", "Điểm rèn luyện"),
        ("bhyt", "Bảo hiểm y tế"),
        ("ktx", "Ký túc xá"),
        ("nvqs", "Nghĩa vụ quân sự"),
    ]
    for acr, desc in acronyms:
        scenarios.append((
            "Nhóm 1: Toàn văn & Từ viết tắt",
            f"Từ viết tắt: {acr} ({desc})",
            f"{BASE_URL}/api/v1/search?q={urllib.parse.quote(acr)}",
            "GET", None,
            lambda s, d: (s == 200 and d.get("total_hits", 0) > 0, f"Hits: {d.get('total_hits', 0)}")
        ))

    doc_numbers = [
        "688/QĐ-ĐHĐL", "13/2013/TTLT", "315/QĐ-ĐHĐL", "88/HD-CTSV", "55/TB-CTSV", "890/QĐ-ĐHĐL",
        "688/QD-DHDL", "13/2013/TTLT-BGDDT", "315/QD-DHDL", "88/HD", "55/TB", "1353/KH-ĐHĐL",
        "205/HD-CTSV", "77/BC-CTSV", "12/BB-CTSV", "450/QĐ-ĐHĐL", "1413/TB-ĐHĐL"
    ]
    for num in doc_numbers:
        scenarios.append((
            "Nhóm 1: Toàn văn & Từ viết tắt",
            f"Số hiệu văn bản: {num}",
            f"{BASE_URL}/api/v1/search?q={urllib.parse.quote(num)}",
            "GET", None,
            lambda s, d: (s == 200 and d.get("total_hits", 0) > 0, f"Hits: {d.get('total_hits', 0)}")
        ))

    unaccented_queries = [
        "hoc bong khuyen khich hoc tap", "mien giam hoc phi", "danh gia diem ren luyen",
        "tam hoan nghia vu quan su", "noi tru ky tuc xa", "bao hiem y te sinh vien",
        "don de nghi mien giam hoc phi", "quyet dinh ve viec ban hanh quy che",
        "thong bao thu bao hiem y te", "huong dan danh gia ren luyen",
        "sinh vien dai hoc da lat", "phong cong tac sinh vien", "nha a11",
        "nghi dinh 81 chinh phu", "quyet dinh 688", "thong tu lien tich 13",
        "ho ngheo vung sau vung xa", "mo coi ca cha lan me", "khuyet tat nang",
        "diem trung binh chung tich luy", "cpa tren 2.5", "khong bi diem f",
        "tieu chi xet hoc bong", "danh sach sinh vien nhan hoc bong",
        "tien ho tro chi phi hoc tap", "chinh sach tro cap xa hoi",
        "noi quy ky tuc xa sinh vien", "kiem tra bounding box", "so sanh phien ban diff",
        "kiem toan tai lieu ocr", "phan luong percolator", "goi y mo rong query",
        "so luong tin chi tich luy", "mon giao duc the chat", "mon giao duc quoc phong",
        "chuan dau ra ngoai ngu", "chuan dau ra tin hoc", "bien lai thu hoc phi",
        "so ho ngheo nam 2024", "chung nhan gia dinh chinh sach", "giay goi nhap ngu"
    ]
    for q in unaccented_queries:
        scenarios.append((
            "Nhóm 1: Toàn văn & Từ viết tắt",
            f"Tìm kiếm không dấu: '{q}'",
            f"{BASE_URL}/api/v1/search?q={urllib.parse.quote(q)}",
            "GET", None,
            lambda s, d: (s == 200 and d.get("total_hits", 0) > 0, f"Hits: {d.get('total_hits', 0)}")
        ))

    students = ["20210678", "20210892", "20210543", "20210123", "20210999", "Nguyễn Hoàng Nam", "Trần Thị Mai", "Lê Văn Bình"]
    for st in students:
        scenarios.append((
            "Nhóm 1: Toàn văn & Từ viết tắt",
            f"Tìm theo MSSV/Họ tên: '{st}'",
            f"{BASE_URL}/api/v1/search?q={urllib.parse.quote(st)}",
            "GET", None,
            lambda s, d: (s == 200 and d.get("total_hits", 0) > 0, f"Hits: {d.get('total_hits', 0)}")
        ))

    # =========================================================================
    # NHÓM 2: TÌM KIẾM MỜ (FUZZY) & CHỊU LỖI CHÍNH TẢ OCR (40 KỊCH BẢN)
    # =========================================================================
    typos = [
        ("hock bong", "học bổng"), ("hoc bongg", "học bổng"), ("mieng giam", "miễn giảm"),
        ("hoc phii", "học phí"), ("khuyen khit", "khuyến khích"), ("nghie vu", "nghĩa vụ"),
        ("ki tuc xa", "ký túc xá"), ("tam hoang", "tạm hoãn"), ("bao hiem y tee", "bảo hiểm y tế"),
        ("ren luyenn", "rèn luyện"), ("hco bong", "học bổng"), ("khueyn khich", "khuyến khích"),
        ("hoan ngih vu", "hoãn nghĩa vụ"), ("sinh vine", "sinh viên"), ("da lta", "Đà Lạt"),
        ("quyey dinh", "quyết định"), ("thong baao", "thông báo"), ("huongg dan", "hướng dẫn"),
        ("donn tu", "đơn từ"), ("ho ngheoo", "hộ nghèo"), ("can ngheoo", "cận nghèo"),
        ("mo coii", "mồ côi"), ("khuyet tatt", "khuyết tật"), ("chinhh sach", "chính sách"),
        ("tro capp", "trợ cấp"), ("hoc vuu", "học vụ"), ("buocc thoi hoc", "buộc thôi học"),
        ("canh baao", "cảnh báo"), ("tinn chi", "tín chỉ"), ("giao ducc", "giáo dục"),
        ("the ducc", "thể dục"), ("quan suu", "quân sự"), ("xett tot nghiep", "xét tốt nghiệp"),
        ("the sinhh vien", "thẻ sinh viên"), ("vayy von", "vay vốn"), ("ngann hang", "ngân hàng"),
        ("khenn thuong", "khen thưởng"), ("kyy luat", "kỷ luật"), ("khien trach", "khiển trách"),
        ("chamm diem", "chấm điểm")
    ]
    for typo, target in typos:
        scenarios.append((
            "Nhóm 2: Fuzzy & Chịu lỗi OCR",
            f"Lỗi chính tả/OCR: '{typo}' -> '{target}'",
            f"{BASE_URL}/api/v1/search?q={urllib.parse.quote(typo)}&fuzzy=true",
            "GET", None,
            lambda s, d: (s == 200 and d.get("total_hits", 0) > 0, f"Hits: {d.get('total_hits', 0)}")
        ))

    # =========================================================================
    # NHÓM 3: TÌM KIẾM LAI NGỮ NGHĨA RRF (RECIPROCAL RANK FUSION) (40 KỊCH BẢN)
    # =========================================================================
    hybrid_queries = [
        "sinh viên nghèo không có tiền đóng học",
        "thủ tục hoãn đi lính quân sự khi đang học đại học",
        "chỗ ở giá rẻ cho sinh viên khó khăn xa nhà",
        "bị điểm rớt môn có được nhận tiền thưởng học giỏi không",
        "sinh viên dân tộc thiểu số vùng sâu vùng xa xin miễn tiền trường",
        "xin giấy xác nhận đang học tại trường để nộp về ban chỉ huy quân sự",
        "thủ tục xin ở nội trú tại trường cho tân sinh viên",
        "làm mất thẻ bảo hiểm y tế thì xin cấp lại thế nào",
        "điểm rèn luyện bị trừ vì vi phạm quy chế lớp",
        "hướng dẫn xin tạm ngừng việc học vì lý do sức khỏe",
        "chính sách hỗ trợ chi phí học tập cho người nghèo",
        "hồ sơ đề nghị trợ cấp xã hội gồm những giấy tờ gì",
        "tiêu chuẩn xếp loại sinh viên khá giỏi xuất sắc",
        "sinh viên bị khiển trách có được học bổng không",
        "cách tính điểm học tập trung bình chung hệ 4",
        "quy định đăng ký nội trú ký túc xá đại học đà lạt",
        "hồ sơ xin miễn giảm học phí nộp ở phòng nào",
        "thời hạn nộp đơn xin tạm hoãn nghĩa vụ quân sự",
        "điều kiện tốt nghiệp ra trường cần bao nhiêu tín chỉ",
        "bị cảnh báo học vụ bao nhiêu lần thì bị đuổi học",
        "thủ tục rút hồ sơ gốc thôi học tự nguyện",
        "cách thức chấm điểm rèn luyện của ban cán sự lớp",
        "sinh viên mồ côi cả cha lẫn mẹ được hỗ trợ gì",
        "chế độ ưu đãi giáo dục theo nghị định 81",
        "tiêu chuẩn xét học bổng khuyến khích học tập qđ 688",
        "giấy xác nhận sinh viên dùng để làm gì",
        "đăng ký bảo hiểm y tế bắt buộc vào thời gian nào",
        "sinh viên khuyết tật nặng được hưởng mức giảm học phí bao nhiêu",
        "vay vốn sinh viên tại ngân hàng chính sách xã hội",
        "thẻ sinh viên tích hợp thẻ ngân hàng bị mất",
        "điều kiện để được cấp học bổng doanh nghiệp",
        "làm sao để không bị nợ môn và cải thiện điểm tích lũy",
        "mức phạt trừ điểm rèn luyện khi không đi sinh hoạt công dân",
        "quy trình tiếp nhận đơn từ của sinh viên tại phòng một cửa a11",
        "tiêu chí xét chọn học bổng tài trợ ngoài ngân sách",
        "chế độ miễn giảm phí nội trú ký túc xá cho sinh viên nghèo",
        "giấy chứng nhận hộ nghèo năm 2024 có giá trị đến khi nào",
        "quy định về thời gian đào tạo tối đa của một khóa học",
        "học phí một tín chỉ của trường đại học đà lạt là bao nhiêu",
        "sinh viên năm nhất có bắt buộc phải ở ký túc xá không"
    ]
    for hq in hybrid_queries:
        scenarios.append((
            "Nhóm 3: Tìm kiếm Lai Ngữ nghĩa RRF",
            f"Ngữ nghĩa tự nhiên: '{hq}'",
            f"{BASE_URL}/api/v1/search/hybrid-rrf",
            "POST", {"query": hq, "limit": 10, "rank_constant_k": 60},
            lambda s, d: (s == 200 and d.get("total_results", 0) > 0, f"Results: {d.get('total_results', 0)} (Top: {d.get('results', [{}])[0].get('title', '')[:35]})")
        ))

    # =========================================================================
    # NHÓM 4: BỘ LỌC ĐA TIÊU CHÍ & TỰ ĐỘNG LỌC TỨC THÌ (30 KỊCH BẢN)
    # =========================================================================
    doc_types = ["QUYET_DINH", "THONG_BAO", "DON_TU", "HUONG_DAN"]
    tags = ["#HocBong", "#MienGiamHocPhi", "#DonTu"]
    statuses = [
        ("APPROVED", lambda s, d: (s == 200 and d.get("total_hits", 0) > 0, f"Hits: {d.get('total_hits', 0)}")),
        ("PENDING", lambda s, d: (s == 200 and isinstance(d.get("total_hits"), int), f"Hits: {d.get('total_hits', 0)}")),
    ]

    for st, val_fn in statuses:
        scenarios.append((
            "Nhóm 4: Bộ lọc Đa tiêu chí & Tức thì",
            f"Lọc theo OCR Status: {st}",
            f"{BASE_URL}/api/v1/search?q=&ocr_status={st}",
            "GET", None,
            val_fn
        ))

    combinations = [
        ("học bổng", "QUYET_DINH", "#HocBong"),
        ("học phí", "DON_TU", "#MienGiamHocPhi"),
        ("rèn luyện", "HUONG_DAN", "#DRL"),
        ("nghĩa vụ quân sự", "THONG_BAO", "#NVQS"),
        ("ký túc xá", "QUYET_DINH", "#KTX"),
        ("miễn giảm", "DON_TU", "#MienGiamHocPhi"),
        ("688", "QUYET_DINH", "#HocBong"),
        ("13/2013", "THONG_BAO", "#NVQS"),
        ("315", "QUYET_DINH", "#KTX"),
        ("88", "HUONG_DAN", "#DRL"),
        ("55", "THONG_BAO", "#BHYT"),
        ("quy chế", "QUYET_DINH", ""),
        ("thông báo", "THONG_BAO", ""),
        ("đơn", "DON_TU", ""),
        ("hướng dẫn", "HUONG_DAN", ""),
        ("bảo lưu", "DON_TU", "#DonTu"),
        ("doanh nghiệp", "QUYET_DINH", "#HocBong"),
        ("hộ nghèo", "DON_TU", "#MienGiamHocPhi"),
        ("sinh viên", "QUYET_DINH", "#HocBong"),
        ("công tác", "HUONG_DAN", ""),
        ("kế hoạch", "KE_HOACH", "#SinhHoatCongDan"),
    ]
    for q_comb, dt_comb, tg_comb in combinations:
        query_str = f"q={urllib.parse.quote(q_comb)}&doc_type_code={dt_comb}"
        if tg_comb:
            query_str += f"&tag={urllib.parse.quote(tg_comb)}"
        scenarios.append((
            "Nhóm 4: Bộ lọc Đa tiêu chí & Tức thì",
            f"Kết hợp: '{q_comb}' + {dt_comb} + {tg_comb or 'All'}",
            f"{BASE_URL}/api/v1/search?{query_str}",
            "GET", None,
            lambda s, d: (s == 200 and d.get("total_hits", 0) > 0, f"Hits: {d.get('total_hits', 0)}")
        ))

    # =========================================================================
    # NHÓM 5: TRỢ LÝ HỎI ĐÁP PHÁP QUY & THÔNG MINH NGOÀI LỀ (35 KỊCH BẢN)
    # =========================================================================
    faq_scenarios = [
        ("Thời tiết hôm nay ở Đà Lạt thế nào có đi chơi được không?", "thời tiết"),
        ("Đà Lạt trời mưa hay nắng có nên đi dạo hồ Xuân Hương không?", "thời tiết"),
        ("Nhiệt độ Đà Lạt hôm nay bao nhiêu độ?", "thời tiết"),
        ("Quán cà phê nào view đẹp ở gần trường Đại học Đà Lạt?", "thời tiết"),
        ("Cuối tuần đi chơi săn mây ở đâu Đà Lạt?", "thời tiết"),
        ("Chào bạn!", "chào"),
        ("Xin chào trợ lý ảo DocuCTSV", "chào"),
        ("Bạn là ai và có thể giúp gì cho sinh viên?", "chào"),
        ("Giới thiệu về hệ thống trợ lý quy chế CTSV", "chào"),
        ("Học hành áp lực và mệt mỏi quá phải làm sao?", "áp lực"),
        ("Làm thế nào để xin nghỉ học tạm thời 1 năm?", "Điều 12"),
        ("Thủ tục bảo lưu kết quả học tập gồm những bước nào?", "bảo lưu"),
        ("Nghỉ học tạm thời tối đa được bao nhiêu học kỳ?", "Điều 12"),
        ("Học bổng tài trợ của doanh nghiệp cần điều kiện gì?", "GPA"),
        ("Doanh nghiệp Viettel hay BIDV tài trợ học bổng yêu cầu điểm bao nhiêu?", "2.80"),
        ("Bị điểm F môn thể dục có được xét học bổng không?", "KHÔNG đủ điều kiện"),
        ("Bị điểm F môn Giáo dục quốc phòng có được xét học bổng KKHT?", "KHÔNG đủ điều kiện"),
        ("Điểm GPA 3.5 nhưng dính điểm F thể dục có được nhận học bổng?", "KHÔNG đủ điều kiện"),
        ("Sinh viên nghèo có được miễn giảm học phí không?", "Nghị định 81"),
        ("Hồ sơ miễn giảm học phí cho sinh viên hộ nghèo gồm giấy tờ gì?", "BM-02-MGHP"),
        ("Sinh viên mồ côi cả cha lẫn mẹ được miễn học phí bao nhiêu phần trăm?", "100%"),
        ("Sinh viên khuyết tật được hưởng chính sách miễn giảm học phí thế nào?", "Nghị định 81"),
        ("Điểm rèn luyện chia thành mấy loại?", "6 khung bậc"),
        ("Bị kỷ luật khiển trách thì điểm rèn luyện tối đa được loại gì?", "Trung bình"),
        ("Bị cảnh cáo thì điểm rèn luyện bị khống chế ở mức nào?", "Yếu"),
        ("Làm sao để xin hoãn nghĩa vụ quân sự khi đang học đại học?", "13/2013/TTLT"),
        ("Giấy xác nhận tạm hoãn NVQS xin ở phòng nào và mất bao lâu?", "Nhà A11"),
        ("Ưu tiên phòng ký túc xá cho những sinh viên nào?", "mồ côi"),
        ("Mức trợ cấp xã hội cho sinh viên khó khăn là bao nhiêu?", "100.000"),
        ("Bị cảnh báo học vụ bao nhiêu lần thì bị buộc thôi học?", "2 lần liên tiếp"),
        ("Học phần bị điểm F có bắt buộc phải học lại không?", "bắt buộc"),
        ("Điều kiện để được xét tốt nghiệp ra trường cần những chứng chỉ gì?", "Ngoại ngữ"),
        ("Bị mất thẻ sinh viên thì làm lại ở đâu và cần giấy tờ gì?", "BM-07-CTSV"),
        ("Thủ tục xin vay vốn sinh viên tại Ngân hàng Chính sách xã hội?", "01/TDSV"),
        ("Bảo hiểm y tế sinh viên có bắt buộc phải tham gia không?", "bắt buộc"),
    ]
    for q_faq, expected_term in faq_scenarios:
        scenarios.append((
            "Nhóm 5: Trợ lý Hỏi đáp Pháp quy Thông minh",
            f"FAQ: '{q_faq}'",
            f"{BASE_URL}/api/v1/search/faq/ask?q={urllib.parse.quote(q_faq)}",
            "GET", None,
            lambda s, d, exp=expected_term: (
                s == 200 and (exp.lower() in d.get("summary_answer", "").lower() or exp.lower() in d.get("matched_article", "").lower() or exp.lower() in d.get("detail_content", "").lower()),
                f"Answer: {d.get('summary_answer')[:60]}... (Conf: {d.get('confidence_score')})"
            )
        ))

    # =========================================================================
    # NHÓM 6: ELASTICSEARCH MLT TRÙNG LẶP & ĐỐI SOÁT GIAN LẬN (25 KỊCH BẢN)
    # =========================================================================
    req = urllib.request.urlopen(f"{BASE_URL}/api/v1/search?q=")
    doc_res_data = json.loads(req.read().decode("utf-8")).get("results", [])
    valid_doc_ids = [r["document_id"] for r in doc_res_data if "document_id" in r]

    if valid_doc_ids:
        # MLT Duplicate Check
        for i, did in enumerate(valid_doc_ids[:6]):
            scenarios.append((
                "Nhóm 6: MLT Trùng lặp & Đối soát Gian lận",
                f"So khớp trùng lặp More-Like-This doc #{i+1}",
                f"{BASE_URL}/api/v1/search/documents/{did}/similar",
                "GET", None,
                lambda s, d: (s == 200 and "total_similar" in d, f"Similar found: {d.get('total_similar', 0)}")
            ))

        # Fraud Collision Audit
        for i, did in enumerate(valid_doc_ids[:6]):
            scenarios.append((
                "Nhóm 6: MLT Trùng lặp & Đối soát Gian lận",
                f"Đối soát gian lận & trùng lặp CCCD/Sổ hộ nghèo doc #{i+1}",
                f"{BASE_URL}/api/v1/search/fraud-detection/audit?document_id={did}",
                "GET", None,
                lambda s, d: (s == 200 and "risk_level" in d, f"Risk: {d.get('risk_level')} (Tamper: {d.get('tamper_score')})")
            ))

        # Significant Text Auto-Tagging
        for i, did in enumerate(valid_doc_ids[:6]):
            scenarios.append((
                "Nhóm 6: MLT Trùng lặp & Đối soát Gian lận",
                f"Trích xuất thực thể & gán nhãn significant_text doc #{i+1}",
                f"{BASE_URL}/api/v1/search/documents/{did}/auto-tags",
                "POST", {},
                lambda s, d: (s == 200 and "tags" in d, f"Tags: {d.get('total_tags')} | Policy: {d.get('suggested_policy_category')}")
            ))

        # Audit Trail & Diffs
        for i, did in enumerate(valid_doc_ids[:7]):
            scenarios.append((
                "Nhóm 6: MLT Trùng lặp & Đối soát Gian lận",
                f"Nhật ký kiểm toán phiên bản & so sánh Diffs doc #{i+1}",
                f"{BASE_URL}/api/v1/search/documents/{did}/audit-trail",
                "GET", None,
                lambda s, d: (s == 200 and "current_version" in d, f"Ver: v{d.get('current_version')} | Revs: {len(d.get('revisions', []))}")
            ))

    # =========================================================================
    # NHÓM 7: POLICY AUTO-AUDIT NĐ 81 & PERCOLATOR ROUTING (20 KỊCH BẢN)
    # =========================================================================
    if valid_doc_ids:
        policy_codes = ["NGHI_DINH_81", "HOC_BONG_KKHT", "TRO_CAP_XAH_HOI"]
        for pc in policy_codes:
            for i, did in enumerate(valid_doc_ids[:4]):
                scenarios.append((
                    "Nhóm 7: Thẩm định Tự động NĐ 81 & Percolator",
                    f"Thẩm định tính hợp lệ pháp lý: {pc} doc #{i+1}",
                    f"{BASE_URL}/api/v1/search/documents/{did}/policy-audit?policy_code={pc}",
                    "GET", None,
                    lambda s, d: (s == 200 and "status" in d, f"Status: {d.get('status')} | Checks: {len(d.get('criteria_checks', []))}")
                ))

        for i, did in enumerate(valid_doc_ids[:6]):
            scenarios.append((
                "Nhóm 7: Thẩm định Tự động NĐ 81 & Percolator",
                f"Phân luồng tự động bằng Elasticsearch Percolator doc #{i+1}",
                f"{BASE_URL}/api/v1/search/documents/{did}/percolate-routing",
                "GET", None,
                lambda s, d: (s == 200 and "matched_rules_count" in d, f"Rules: {d.get('matched_rules_count', 0)} ({d.get('assigned_department')})")
            ))

        for i, did in enumerate(valid_doc_ids[:2]):
            scenarios.append((
                "Nhóm 7: Thẩm định Tự động NĐ 81 & Percolator",
                f"Truy xuất tọa độ Bounding Box OCR doc #{i+1}",
                f"{BASE_URL}/api/v1/search/documents/{did}/spatial-highlights?q=hoc",
                "GET", None,
                lambda s, d: (s == 200 and "highlights" in d, f"Highlights: {d.get('total_occurrences')}")
            ))

    return scenarios

def main():
    print("=" * 80)
    print("  HỆ THỐNG KIỂM THỬ TỰ ĐỘNG TOÀN DIỆN DOCUCTSV — 250+ KỊCH BẢN BENCHMARK")
    print("  Đánh giá Năng lực & Tính Quan trọng Cốt lõi của Elasticsearch 8 trong Dự án")
    print("=" * 80)

    scenarios = build_250_scenarios()
    print(f"\n[INFO] Khởi tạo thành công {len(scenarios)} kịch bản kiểm thử độc lập.")
    print("[INFO] Đang tiến hành thực thi tuần tự và đo lường hiệu năng thời gian thực...\n")

    results = []
    category_stats = {}
    latencies = []

    passed_count = 0
    failed_count = 0

    for idx, (cat, name, url, method, payload, validator) in enumerate(scenarios, 1):
        res = run_test(cat, name, url, method, payload, validator)
        results.append(res)
        latencies.append(res["latency_ms"])

        if cat not in category_stats:
            category_stats[cat] = {"total": 0, "passed": 0, "failed": 0, "latencies": []}
        category_stats[cat]["total"] += 1
        category_stats[cat]["latencies"].append(res["latency_ms"])

        if res["passed"]:
            passed_count += 1
            category_stats[cat]["passed"] += 1
            status_tag = "[PASS]"
        else:
            failed_count += 1
            category_stats[cat]["failed"] += 1
            status_tag = "[FAIL]"

        print(f"[{idx:03d}/{len(scenarios):03d}] {status_tag} {res['latency_ms']:6.1f}ms | {cat[:25]:25s} | {name[:45]:45s} -> {res['reason']}")

    latencies.sort()
    avg_latency = sum(latencies) / len(latencies) if latencies else 0
    p50 = latencies[int(len(latencies) * 0.50)] if latencies else 0
    p95 = latencies[int(len(latencies) * 0.95)] if latencies else 0
    p99 = latencies[int(len(latencies) * 0.99)] if latencies else 0
    pass_rate = (passed_count / len(scenarios) * 100.0) if scenarios else 0

    print("\n" + "=" * 80)
    print("                      BẢNG TỔNG KẾT KẾT QUẢ KIỂM THỬ")
    print("=" * 80)
    print(f"  • Tổng số kịch bản thực thi : {len(scenarios)}")
    print(f"  • Số kịch bản Thành công    : {passed_count} ({pass_rate:.1f}%)")
    print(f"  • Số kịch bản Thất bại      : {failed_count}")
    print(f"  • Độ trễ trung bình         : {avg_latency:.2f} ms")
    print(f"  • Độ trễ P50 (Trung vị)     : {p50:.2f} ms")
    print(f"  • Độ trễ P95 (95% tốt nhất) : {p95:.2f} ms")
    print(f"  • Độ trễ P99 (99% tốt nhất) : {p99:.2f} ms")
    print("-" * 80)
    print(f"  {'NHÓM CHỨC NĂNG':<40} | {'TỔNG':<6} | {'PASS':<6} | {'TỈ LỆ':<8} | {'AVG(ms)':<8}")
    print("-" * 80)
    for cat, stats in category_stats.items():
        cat_rate = (stats["passed"] / stats["total"] * 100) if stats["total"] else 0
        cat_avg = sum(stats["latencies"]) / len(stats["latencies"]) if stats["latencies"] else 0
        print(f"  {cat:<40} | {stats['total']:<6} | {stats['passed']:<6} | {cat_rate:6.1f}% | {cat_avg:6.2f}ms")
    print("=" * 80)

    output_path = "E:/Download/-ATN-main/-ATN-main/scripts/benchmark_results.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump({
            "summary": {
                "total_scenarios": len(scenarios),
                "passed": passed_count,
                "failed": failed_count,
                "pass_rate_percent": pass_rate,
                "avg_latency_ms": round(avg_latency, 2),
                "p50_ms": p50,
                "p95_ms": p95,
                "p99_ms": p99,
            },
            "category_breakdown": {
                c: {
                    "total": s["total"],
                    "passed": s["passed"],
                    "failed": s["failed"],
                    "pass_rate": round(s["passed"] / s["total"] * 100, 1),
                    "avg_latency_ms": round(sum(s["latencies"]) / len(s["latencies"]), 2),
                } for c, s in category_stats.items()
            },
            "detailed_results": results
        }, f, ensure_ascii=False, indent=2)
    print(f"[SUCCESS] Đã lưu chi tiết kết quả benchmark vào file: {output_path}")

if __name__ == "__main__":
    main()
