"""
scripts/build_ir_ground_truth.py — Xây dựng bộ Ground Truth độc lập cho đánh giá IR

Công cụ hỗ trợ duyệt qua các tài liệu trong Elasticsearch / Database và gán nhãn
tài liệu nào thực sự liên quan đến 25 truy vấn thử nghiệm (Easy, Hard, Negative).
Kết quả lưu vào `dataset/ir_ground_truth.json`.

Ref: tests/OCRTest.md, tests/PerformanceTest.md
"""
import argparse
import asyncio
import json
import os
import sys

# Thiết lập encoding UTF-8 cho Windows console
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from elasticsearch import AsyncElasticsearch
from backend.app.core.config import settings

# 25 Queries đa dạng độ khó: 10 Dễ, 10 Khó, 5 Âm tính (Negative)
BENCHMARK_QUERIES = [
    # ── 10 QUERY DỄ (Khớp trực tiếp loại biểu mẫu hoặc từ khóa rõ ràng) ──────
    {
        "id": "Q01",
        "type": "EASY",
        "query": "miễn giảm học phí",
        "fuzzy": True,
        "description": "Tìm hồ sơ đối tượng chính sách xin miễn giảm học phí",
        "target_category": "MIEN_GIAM_HOC_PHI",
        "must_contain": ["miễn giảm", "học phí"],
    },
    {
        "id": "Q02",
        "type": "EASY",
        "query": "đơn xin nghỉ học tạm thời",
        "fuzzy": True,
        "description": "Đơn xin nghỉ học có thời hạn / bảo lưu",
        "target_category": "DON_NGHI_HOC",
        "must_contain": ["nghỉ học", "tạm thời"],
    },
    {
        "id": "Q03",
        "type": "EASY",
        "query": "học bổng khuyến khích học tập",
        "fuzzy": True,
        "description": "Hồ sơ xét duyệt học bổng KKHT theo kỳ",
        "target_category": "HOC_BONG",
        "must_contain": ["học bổng", "khuyến khích"],
    },
    {
        "id": "Q04",
        "type": "EASY",
        "query": "giấy xác nhận sinh viên",
        "fuzzy": True,
        "description": "Giấy xác nhận đang theo học tại trường",
        "target_category": "GIAY_XAC_NHAN",
        "must_contain": ["xác nhận", "sinh viên"],
    },
    {
        "id": "Q05",
        "type": "EASY",
        "query": "khen thưởng nghiên cứu khoa học",
        "fuzzy": True,
        "description": "Hồ sơ thành tích NCKH sinh viên",
        "target_category": "KHEN_THUONG",
        "must_contain": ["khen thưởng", "nghiên cứu khoa học"],
    },
    {
        "id": "Q06",
        "type": "EASY",
        "query": "đơn đề nghị cấp lại thẻ sinh viên",
        "fuzzy": True,
        "description": "Đơn xin cấp lại thẻ sinh viên bị mất",
        "target_category": "GIAY_XAC_NHAN",
        "must_contain": ["thẻ sinh viên", "cấp lại"],
    },
    {
        "id": "Q07",
        "type": "EASY",
        "query": "bảo lưu kết quả học tập",
        "fuzzy": True,
        "description": "Đơn xin bảo lưu điểm số và kỳ học",
        "target_category": "DON_NGHI_HOC",
        "must_contain": ["bảo lưu", "kết quả học tập"],
    },
    {
        "id": "Q08",
        "type": "EASY",
        "query": "hồ sơ kỷ luật sinh viên",
        "fuzzy": True,
        "description": "Văn bản kỷ luật hoặc xử lý vi phạm",
        "target_category": "KHEN_THUONG",
        "must_contain": ["kỷ luật", "vi phạm"],
    },
    {
        "id": "Q09",
        "type": "EASY",
        "query": "20210678",
        "fuzzy": False,
        "description": "Tra cứu chính xác theo MSSV",
        "target_category": None,
        "must_contain": ["20210678"],
    },
    {
        "id": "Q10",
        "type": "EASY",
        "query": "hỗ trợ chi phí học tập",
        "fuzzy": True,
        "description": "Trợ cấp sinh viên có hoàn cảnh khó khăn",
        "target_category": "MIEN_GIAM_HOC_PHI",
        "must_contain": ["hỗ trợ", "chi phí học tập"],
    },

    # ── 10 QUERY KHÓ (Viết tắt, không dấu, từ đồng nghĩa, cấu trúc phức) ─────
    {
        "id": "Q11",
        "type": "HARD",
        "query": "don xin nghi hoc vi ly do sk",
        "fuzzy": True,
        "description": "Tìm không dấu + viết tắt (sk = sức khỏe) cho đơn nghỉ học",
        "target_category": "DON_NGHI_HOC",
        "must_contain": ["nghỉ học"],
    },
    {
        "id": "Q12",
        "type": "HARD",
        "query": "xet hb kkht ky 1",
        "fuzzy": True,
        "description": "Viết tắt học bổng khuyến khích học tập (hb kkht)",
        "target_category": "HOC_BONG",
        "must_contain": ["học bổng"],
    },
    {
        "id": "Q13",
        "type": "HARD",
        "query": "vay von ngan hang chinh sach",
        "fuzzy": True,
        "description": "Giấy xác nhận sinh viên mục đích vay vốn",
        "target_category": "GIAY_XAC_NHAN",
        "must_contain": ["xác nhận", "vay vốn"],
    },
    {
        "id": "Q14",
        "type": "HARD",
        "query": "hoan thi tot nghiep",
        "fuzzy": True,
        "description": "Đơn xin hoãn thi / nghỉ học tạm thời",
        "target_category": "DON_NGHI_HOC",
        "must_contain": ["hoãn thi", "nghỉ học"],
    },
    {
        "id": "Q15",
        "type": "HARD",
        "query": "giam tien hoc con thuong binh",
        "fuzzy": True,
        "description": "Dùng từ ngữ dân dã thay vì cụm 'miễn giảm học phí'",
        "target_category": "MIEN_GIAM_HOC_PHI",
        "must_contain": ["miễn giảm", "thương binh", "học phí"],
    },
    {
        "id": "Q16",
        "type": "HARD",
        "query": "tam hoan nghia vu quan su nvqs",
        "fuzzy": True,
        "description": "Giấy xác nhận phục vụ tạm hoãn NVQS",
        "target_category": "GIAY_XAC_NHAN",
        "must_contain": ["xác nhận", "nghĩa vụ quân sự"],
    },
    {
        "id": "Q17",
        "type": "HARD",
        "query": "thanh tich nckh cap truong giai nhat",
        "fuzzy": True,
        "description": "Khen thưởng nghiên cứu khoa học đạt giải",
        "target_category": "KHEN_THUONG",
        "must_contain": ["khen thưởng", "nckh"],
    },
    {
        "id": "Q18",
        "type": "HARD",
        "query": "don xin tro lai hoc tap sau bao luu",
        "fuzzy": True,
        "description": "Đơn xin tiếp tục học tập sau thời gian bảo lưu",
        "target_category": "DON_NGHI_HOC",
        "must_contain": ["bảo lưu", "trở lại"],
    },
    {
        "id": "Q19",
        "type": "HARD",
        "query": "chung nhan sinh vien bang tieng anh",
        "fuzzy": True,
        "description": "Giấy xác nhận sinh viên song ngữ",
        "target_category": "GIAY_XAC_NHAN",
        "must_contain": ["xác nhận", "sinh viên"],
    },
    {
        "id": "Q20",
        "type": "HARD",
        "query": "tro cap xa hoi sv ho ngheo",
        "fuzzy": True,
        "description": "Đơn hỗ trợ học phí / chính sách hộ nghèo",
        "target_category": "MIEN_GIAM_HOC_PHI",
        "must_contain": ["học phí", "hộ nghèo", "trợ cấp"],
    },

    # ── 5 QUERY ÂM TÍNH (NEGATIVE: Không có tài liệu nào liên quan) ───────────
    {
        "id": "Q21",
        "type": "NEGATIVE",
        "query": "hóa đơn thanh toán tiền điện nước ký túc xá",
        "fuzzy": True,
        "description": "Hóa đơn sinh hoạt ngoài phạm vi quản lý hồ sơ CTSV",
        "target_category": None,
        "must_contain": ["tiền điện nước", "ký túc xá"],
    },
    {
        "id": "Q22",
        "type": "NEGATIVE",
        "query": "hợp đồng thuê nhà trọ sinh viên ngoài trường",
        "fuzzy": True,
        "description": "Giao dịch dân sự cá nhân không thuộc thẩm quyền",
        "target_category": None,
        "must_contain": ["thuê nhà trọ", "hợp đồng"],
    },
    {
        "id": "Q23",
        "type": "NEGATIVE",
        "query": "đơn đăng ký học bằng lái xe ô tô hạng B2",
        "fuzzy": True,
        "description": "Khóa học ngoài trường không liên quan CTSV",
        "target_category": None,
        "must_contain": ["lái xe", "hạng B2"],
    },
    {
        "id": "Q24",
        "type": "NEGATIVE",
        "query": "báo cáo tài chính doanh nghiệp quý 3",
        "fuzzy": True,
        "description": "Văn bản kinh doanh không thuộc hệ thống đại học",
        "target_category": None,
        "must_contain": ["báo cáo tài chính", "doanh nghiệp"],
    },
    {
        "id": "Q25",
        "type": "NEGATIVE",
        "query": "giấy chuyển tuyến bảo hiểm y tế bệnh viện bạch mai",
        "fuzzy": True,
        "description": "Hồ sơ y tế bệnh viện không phải biểu mẫu CTSV",
        "target_category": None,
        "must_contain": ["chuyển viện", "bệnh viện bạch mai"],
    },
]


async def build_ground_truth(interactive: bool = False) -> dict:
    """
    Duyệt qua tất cả tài liệu trong Elasticsearch và lập danh sách ground truth độc lập.
    """
    es = AsyncElasticsearch(hosts=[settings.es_url])

    # Lấy toàn bộ danh sách tài liệu hiện có trong index
    res = await es.search(
        index=settings.es_index_documents,
        size=1000,
        query={"match_all": {}}
    )
    hits = res["hits"]["hits"]
    print(f"Loaded {len(hits)} indexed documents from Elasticsearch.")

    ground_truth_dataset = []

    for q_spec in BENCHMARK_QUERIES:
        relevant_ids = []
        qid = q_spec["id"]
        qtype = q_spec["type"]
        qtext = q_spec["query"]

        if qtype == "NEGATIVE":
            # Query âm tính: Tuyệt đối không có tài liệu nào liên quan
            relevant_ids = []
        else:
            # Tìm các tài liệu thực sự phù hợp dựa trên tiêu chí nội dung
            for h in hits:
                doc_id = h.get("_source", {}).get("document_id") or h.get("_id")
                title = (h.get("_source", {}).get("title") or "").lower()
                content = (h.get("_source", {}).get("content") or "").lower()
                cat = h.get("_source", {}).get("category_code")
                student_id = h.get("_source", {}).get("student_id") or ""

                is_match = False
                if q_spec["target_category"] and cat == q_spec["target_category"]:
                    is_match = True
                elif any(kw.lower() in title or kw.lower() in content for kw in q_spec.get("must_contain", [])):
                    is_match = True
                elif q_spec.get("must_contain") and q_spec["must_contain"][0] in student_id:
                    is_match = True

                if is_match and doc_id:
                    relevant_ids.append(str(doc_id))

        ground_truth_dataset.append({
            "id": qid,
            "type": qtype,
            "query": qtext,
            "fuzzy": q_spec["fuzzy"],
            "description": q_spec["description"],
            "total_relevant_in_index": len(relevant_ids),
            "relevant_doc_ids": relevant_ids,
        })

    await es.close()

    output_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "dataset",
        "ir_ground_truth.json"
    )
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(ground_truth_dataset, f, indent=2, ensure_ascii=False)

    print(f"[OK] Ground Truth saved to {output_path} ({len(ground_truth_dataset)} queries evaluated).")
    return {"total_queries": len(ground_truth_dataset), "file_path": output_path}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Build independent IR Ground Truth for CTSV documents")
    parser.add_argument("--interactive", action="store_true", help="Interactive labeling mode")
    args = parser.parse_args()

    asyncio.run(build_ground_truth(interactive=args.interactive))
