"""
backend/tests/evaluate_ir_metrics.py — Đánh giá Độ chính xác Hệ thống Tìm kiếm (IR Evaluation)

Đo lường độ chính xác tìm kiếm tiếng Việt trên Elasticsearch 8:
- Precision@5, Precision@10 (mẫu số cố định = 5 và = 10)
- Recall@10 (dựa trên Ground Truth thực tế từ dataset/ir_ground_truth.json)
- F1-Score (tính từ Precision@10 và Recall@10 thật)
- Mean Average Precision (MAP)
- Mean Reciprocal Rank (MRR)

Ref: tests/OCRTest.md, tests/PerformanceTest.md
"""
import asyncio
import json
import os
import sys
from typing import Any

# Thiết lập encoding UTF-8 cho Windows console
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app.main import create_app
import httpx


def load_ground_truth_dataset() -> list[dict[str, Any]]:
    """Đọc bộ Ground Truth độc lập từ dataset/ir_ground_truth.json."""
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    gt_file = os.path.join(base_dir, "dataset", "ir_ground_truth.json")

    if not os.path.exists(gt_file):
        raise FileNotFoundError(f"Không tìm thấy file Ground Truth tại: {gt_file}. Hãy chạy scripts/build_ir_ground_truth.py trước.")

    with open(gt_file, "r", encoding="utf-8") as f:
        return json.load(f)


def is_relevant(hit: dict[str, Any], ground_truth: dict[str, Any]) -> bool:
    """
    Kiểm tra một kết quả tìm kiếm có thuộc tập ID tài liệu liên quan hay không.
    (Độc lập hoàn toàn với cơ chế matching của Elasticsearch).
    """
    doc_id = str(hit.get("document_id", ""))
    relevant_ids = set(ground_truth.get("relevant_doc_ids", []))
    return doc_id in relevant_ids


async def run_ir_evaluation() -> dict[str, Any]:
    """Thực thi đánh giá trên 25 truy vấn thử nghiệm độc lập."""
    ground_truth_list = load_ground_truth_dataset()
    app_instance = create_app()
    transport = httpx.ASGITransport(app=app_instance)

    per_query_results = []
    category_metrics = {"EASY": [], "HARD": [], "NEGATIVE": []}

    async with httpx.AsyncClient(transport=transport, base_url="http://testserver", timeout=15.0) as client:
        for q_item in ground_truth_list:
            qid = q_item["id"]
            qtype = q_item["type"]
            query_str = q_item["query"]
            fuzzy = q_item.get("fuzzy", True)
            total_relevant = q_item.get("total_relevant_in_index", 0)
            relevant_ids = set(q_item.get("relevant_doc_ids", []))

            # Thực hiện tìm kiếm
            res = await client.get("/api/v1/search", params={"q": query_str, "fuzzy": fuzzy, "page_size": 10})
            if res.status_code != 200:
                print(f"Query {qid} ({query_str}) returned status {res.status_code}")
                continue

            data = res.json()
            hits = data.get("results", [])
            retrieved_count = len(hits)

            # Vector nhị phân biểu thị độ liên quan của từng vị trí kết quả trong Top-10
            rel_vector = [1 if is_relevant(h, q_item) else 0 for h in hits]
            relevant_retrieved_in_top10 = sum(rel_vector[:10])

            # ── 1. Tính Precision@5 & Precision@10 (Mẫu số cố định bằng 5 và 10) ─
            if qtype == "NEGATIVE":
                # Đối với truy vấn âm tính (không có doc liên quan trong dataset):
                # Nếu hệ thống trả về 0 kết quả -> P@5 = P@10 = 1.0 (nhận diện chính xác là không có)
                # Nếu hệ thống trả về kết quả rác -> P@5 = P@10 = 0.0
                p5 = 1.0 if retrieved_count == 0 else 0.0
                p10 = 1.0 if retrieved_count == 0 else 0.0
            else:
                p5 = sum(rel_vector[:5]) / 5.0
                p10 = sum(rel_vector[:10]) / 10.0

            # ── 2. Tính Recall@10 thật (Số relevant trong top-10 / Tổng số relevant trong dataset) ─
            if total_relevant == 0:
                # Không có tài liệu liên quan trong dataset
                recall10 = 1.0 if retrieved_count == 0 else 0.0
            else:
                recall10 = relevant_retrieved_in_top10 / float(total_relevant)

            # ── 3. Tính F1-Score chuẩn ─────────────────────────────────────────
            if (p10 + recall10) > 0:
                f1 = 2.0 * (p10 * recall10) / (p10 + recall10)
            else:
                f1 = 0.0

            # ── 4. Tính MRR (Mean Reciprocal Rank) ─────────────────────────────
            rr = 0.0
            if qtype == "NEGATIVE":
                rr = 1.0 if retrieved_count == 0 else 0.0
            else:
                for rank, r in enumerate(rel_vector, start=1):
                    if r == 1:
                        rr = 1.0 / rank
                        break

            # ── 5. Tính Average Precision (AP) ─────────────────────────────────
            ap = 0.0
            if qtype == "NEGATIVE":
                ap = 1.0 if retrieved_count == 0 else 0.0
            else:
                cum_rel = 0
                prec_sum = 0.0
                for rank, r in enumerate(rel_vector, start=1):
                    if r == 1:
                        cum_rel += 1
                        prec_sum += cum_rel / float(rank)
                denom = min(total_relevant, 10)
                ap = (prec_sum / denom) if denom > 0 else 0.0

            metric_entry = {
                "id": qid,
                "type": qtype,
                "query": query_str,
                "total_relevant_in_index": total_relevant,
                "retrieved_count": retrieved_count,
                "relevant_retrieved": relevant_retrieved_in_top10,
                "p@5": round(p5 * 100, 1),
                "p@10": round(p10 * 100, 1),
                "recall@10": round(recall10 * 100, 1),
                "f1": round(f1 * 100, 1),
                "mrr": round(rr, 4),
                "ap": round(ap * 100, 1),
            }

            per_query_results.append(metric_entry)
            category_metrics[qtype].append(metric_entry)

    # ── Tính Macro-Average Metrics ────────────────────────────────────────────
    total_q = len(per_query_results)
    avg_p5 = sum(m["p@5"] for m in per_query_results) / total_q if total_q else 0.0
    avg_p10 = sum(m["p@10"] for m in per_query_results) / total_q if total_q else 0.0
    avg_recall = sum(m["recall@10"] for m in per_query_results) / total_q if total_q else 0.0
    avg_f1 = sum(m["f1"] for m in per_query_results) / total_q if total_q else 0.0
    avg_mrr = sum(m["mrr"] for m in per_query_results) / total_q if total_q else 0.0
    avg_map = sum(m["ap"] for m in per_query_results) / total_q if total_q else 0.0

    return {
        "summary": {
            "total_queries": total_q,
            "precision_at_5": round(avg_p5, 2),
            "precision_at_10": round(avg_p10, 2),
            "recall_at_10": round(avg_recall, 2),
            "f1_score": round(avg_f1, 2),
            "mean_average_precision_map": round(avg_map, 2),
            "mean_reciprocal_rank_mrr": round(avg_mrr, 4),
        },
        "by_tier": {
            tier: {
                "count": len(items),
                "precision_at_5": round(sum(m["p@5"] for m in items) / len(items), 2) if items else 0.0,
                "precision_at_10": round(sum(m["p@10"] for m in items) / len(items), 2) if items else 0.0,
                "recall_at_10": round(sum(m["recall@10"] for m in items) / len(items), 2) if items else 0.0,
                "f1_score": round(sum(m["f1"] for m in items) / len(items), 2) if items else 0.0,
                "map": round(sum(m["ap"] for m in items) / len(items), 2) if items else 0.0,
                "mrr": round(sum(m["mrr"] for m in items) / len(items), 4) if items else 0.0,
            }
            for tier, items in category_metrics.items()
        },
        "per_query": per_query_results,
    }


def print_comparison_report(new_results: dict[str, Any]) -> None:
    """In bảng so sánh chi tiết: Số liệu CŨ (Lỗi) vs Số liệu MỚI (Độc lập)."""
    old_flawed = {
        "precision_at_5": "100.0%",
        "precision_at_10": "100.0%",
        "recall_at_10": "94.0% (Hardcoded gán cứng)",
        "f1_score": "96.91% (Tính từ số bịa)",
        "map": "100.0%",
        "mrr": "1.000",
        "num_queries": 5,
        "method": "Circular matching (Tự so khớp category/keyword)",
    }

    summary = new_results["summary"]
    by_tier = new_results["by_tier"]

    print("\n" + "=" * 90)
    print(" BÁO CÁO ĐÁNH GIÁ ĐỘ CHÍNH XÁC TRA CỨU THÔNG TIN (INFORMATION RETRIEVAL)")
    print("=" * 90)

    print("\n[BẢNG 1] ĐỐI CHIẾU SỐ LIỆU CŨ (BỊ LỖI) VÀ SỐ LIỆU MỚI (GROUND TRUTH ĐỘC LẬP)")
    print("-" * 90)
    print(f"{'Chỉ số đo lường':<28} | {'Số liệu CŨ (Bị lỗi)':<28} | {'Số liệu MỚI (Đã sửa)':<26}")
    print("-" * 90)
    tot_q_str = f"{summary['total_queries']} queries (Đa dạng độ khó)"
    p5_str = f"{summary['precision_at_5']} %"
    p10_str = f"{summary['precision_at_10']} %"
    rec_str = f"{summary['recall_at_10']} %"
    f1_str = f"{summary['f1_score']} %"
    map_str = f"{summary['mean_average_precision_map']} %"
    mrr_str = f"{summary['mean_reciprocal_rank_mrr']:.4f}"

    print(f"{'Số lượng truy vấn (Queries)':<28} | {'5 queries (quá ít)':<28} | {tot_q_str:<26}")
    print(f"{'Cơ chế xác định Relevance':<28} | {'Circular keyword-match':<28} | {'Ground Truth ID độc lập':<26}")
    print(f"{'Precision@5 (Mẫu số = 5)':<28} | {old_flawed['precision_at_5']:<28} | {p5_str:<26}")
    print(f"{'Precision@10 (Mẫu số = 10)':<28} | {old_flawed['precision_at_10']:<28} | {p10_str:<26}")
    print(f"{'Recall@10 (Công thức thật)':<28} | {old_flawed['recall_at_10']:<28} | {rec_str:<26}")
    print(f"{'F1-Score (Tính từ P@10 & R@10)':<28} | {old_flawed['f1_score']:<28} | {f1_str:<26}")
    print(f"{'Mean Average Precision (MAP)':<28} | {old_flawed['map']:<28} | {map_str:<26}")
    print(f"{'Mean Reciprocal Rank (MRR)':<28} | {old_flawed['mrr']:<28} | {mrr_str:<26}")
    print("-" * 90)

    print("\n[BẢNG 2] PHÂN TÍCH THEO TỪNG NHÓM ĐỘ KHÓ (EASY / HARD / NEGATIVE)")
    print("-" * 90)
    print(f"{'Nhóm truy vấn':<18} | {'Số lượng':<8} | {'P@5 (%)':<8} | {'P@10 (%)':<9} | {'Recall (%)':<10} | {'F1 (%)':<8} | {'MAP (%)':<8} | {'MRR':<6}")
    print("-" * 90)
    for tier, data in by_tier.items():
        print(f"{tier:<18} | {data['count']:<8} | {data['precision_at_5']:<8} | {data['precision_at_10']:<9} | {data['recall_at_10']:<10} | {data['f1_score']:<8} | {data['map']:<8} | {data['mrr']:<6}")
    print("-" * 90)

    print("\n[BẢNG 3] CHI TIẾT KẾT QUẢ TỪNG TRUY VẤN (TOP 25 BENCHMARK QUERIES)")
    print("-" * 90)
    print(f"{'Mã':<4} | {'Loại':<8} | {'Truy vấn':<36} | {'Rel In Index':<12} | {'P@5':<6} | {'P@10':<6} | {'R@10':<6} | {'F1':<6}")
    print("-" * 90)
    for q in new_results["per_query"]:
        q_text = q['query'][:34]
        print(f"{q['id']:<4} | {q['type']:<8} | {q_text:<36} | {q['total_relevant_in_index']:<12} | {q['p@5']:<6} | {q['p@10']:<6} | {q['recall@10']:<6} | {q['f1']:<6}")
    print("-" * 90)


async def main():
    results = await run_ir_evaluation()
    print_comparison_report(results)


if __name__ == "__main__":
    asyncio.run(main())
