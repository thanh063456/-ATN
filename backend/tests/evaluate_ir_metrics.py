"""
backend/tests/evaluate_ir_metrics.py — Đánh giá Độ chính xác Hệ thống Tìm kiếm (IR Evaluation)

Đo lường độ chính xác tìm kiếm tiếng Việt trên Elasticsearch 8:
- Precision@5, Precision@10 (Mẫu số cố định = 5 và = 10)
- Recall@10 (Dựa trên Ground Truth thực tế từ dataset/ir_ground_truth.json)
- F1-Score (Tính từ Precision@10 và Recall@10 thật)
- Mean Average Precision (MAP)
- Mean Reciprocal Rank (MRR)
"""

from __future__ import annotations

import asyncio
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import httpx

# Thiết lập encoding UTF-8 cho Windows console
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

# Định vị thư mục gốc dự án bằng pathlib
REPO_ROOT = Path(__file__).resolve().parents[2]
BACKEND_ROOT = REPO_ROOT / "backend"
sys.path.insert(0, str(BACKEND_ROOT))

from app.main import create_app

# ==============================================================================
# DATA MODELS
# ==============================================================================


@dataclass(frozen=True)
class QueryItem:
    """Đại diện cho 1 truy vấn kiểm thử từ Ground Truth dataset."""

    id: str
    type: str  # EASY, HARD, NEGATIVE
    query: str
    fuzzy: bool
    total_relevant: int
    relevant_doc_ids: set[str]


@dataclass
class MetricResult:
    """Kết quả đo lường định lượng của 1 truy vấn."""

    query_id: str
    query_type: str
    query_text: str
    total_relevant_in_index: int
    retrieved_count: int
    relevant_retrieved: int
    precision_at_5: float
    precision_at_10: float
    recall_at_10: float
    f1_score: float
    mrr: float
    average_precision: float

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.query_id,
            "type": self.query_type,
            "query": self.query_text,
            "total_relevant_in_index": self.total_relevant_in_index,
            "retrieved_count": self.retrieved_count,
            "relevant_retrieved": self.relevant_retrieved,
            "p@5": round(self.precision_at_5 * 100, 1),
            "p@10": round(self.precision_at_10 * 100, 1),
            "recall@10": round(self.recall_at_10 * 100, 1),
            "f1": round(self.f1_score * 100, 1),
            "mrr": round(self.mrr, 4),
            "ap": round(self.average_precision * 100, 1),
        }


# ==============================================================================
# PURE MATHEMATICAL METRIC FUNCTIONS
# ==============================================================================


def compute_precision_at_k(rel_vector: list[int], k: int, is_negative: bool, retrieved_count: int) -> float:
    """Tính Precision@K với mẫu số cố định là K."""
    if is_negative:
        return 1.0 if retrieved_count == 0 else 0.0
    return sum(rel_vector[:k]) / float(k)


def compute_recall_at_k(relevant_retrieved: int, total_relevant: int, is_negative: bool, retrieved_count: int) -> float:
    """Tính Recall@K dựa trên tổng số tài liệu liên quan thực tế."""
    if is_negative or total_relevant == 0:
        return 1.0 if retrieved_count == 0 else 0.0
    return relevant_retrieved / float(total_relevant)


def compute_f1(precision: float, recall: float) -> float:
    """Tính F1-score điều hòa giữa Precision và Recall."""
    if (precision + recall) <= 0:
        return 0.0
    return 2.0 * (precision * recall) / (precision + recall)


def compute_mrr(rel_vector: list[int], is_negative: bool, retrieved_count: int) -> float:
    """Tính Reciprocal Rank (thứ hạng nghịch đảo của kết quả đúng đầu tiên)."""
    if is_negative:
        return 1.0 if retrieved_count == 0 else 0.0
    for rank, is_rel in enumerate(rel_vector, start=1):
        if is_rel == 1:
            return 1.0 / rank
    return 0.0


def compute_average_precision(
    rel_vector: list[int], total_relevant: int, is_negative: bool, retrieved_count: int, k: int = 10
) -> float:
    """Tính Average Precision (AP) cho 1 truy vấn."""
    if is_negative:
        return 1.0 if retrieved_count == 0 else 0.0
    if total_relevant == 0:
        return 0.0

    cum_rel = 0
    prec_sum = 0.0
    for rank, is_rel in enumerate(rel_vector[:k], start=1):
        if is_rel == 1:
            cum_rel += 1
            prec_sum += cum_rel / float(rank)

    denom = min(total_relevant, k)
    return (prec_sum / denom) if denom > 0 else 0.0


# ==============================================================================
# DATA LOADER & EVALUATION ENGINE
# ==============================================================================


def load_ground_truth_dataset(filepath: Path | None = None) -> list[QueryItem]:
    """Nạp bộ Ground Truth độc lập từ tệp JSON."""
    gt_file = filepath or (REPO_ROOT / "dataset" / "ir_ground_truth.json")
    if not gt_file.exists():
        raise FileNotFoundError(f"Không tìm thấy file Ground Truth tại: {gt_file}")

    with open(gt_file, "r", encoding="utf-8") as f:
        raw_data = json.load(f)

    return [
        QueryItem(
            id=item["id"],
            type=item["type"],
            query=item["query"],
            fuzzy=item.get("fuzzy", True),
            total_relevant=item.get("total_relevant_in_index", 0),
            relevant_doc_ids=set(item.get("relevant_doc_ids", [])),
        )
        for item in raw_data
    ]


class IREvaluationEngine:
    """Bộ thực thi đánh giá Information Retrieval."""

    def __init__(self, queries: list[QueryItem]) -> None:
        self.queries = queries
        self.app = create_app()

    async def evaluate_query(self, client: httpx.AsyncClient, item: QueryItem) -> MetricResult | None:
        """Gửi truy vấn và tính toán các metric cho 1 query."""
        params = {"q": item.query, "fuzzy": item.fuzzy, "page_size": 10}
        response = await client.get("/api/v1/search", params=params)

        if response.status_code != 200:
            print(f"[WARN] Query {item.id} ('{item.query}') thất bại: HTTP {response.status_code}")
            return None

        hits = response.json().get("results", [])
        retrieved_count = len(hits)
        is_neg = item.type == "NEGATIVE"

        # Vector nhị phân xác định tài liệu liên quan
        rel_vector = [1 if str(h.get("document_id", "")) in item.relevant_doc_ids else 0 for h in hits]
        rel_retrieved_10 = sum(rel_vector[:10])

        p5 = compute_precision_at_k(rel_vector, k=5, is_negative=is_neg, retrieved_count=retrieved_count)
        p10 = compute_precision_at_k(rel_vector, k=10, is_negative=is_neg, retrieved_count=retrieved_count)
        recall = compute_recall_at_k(
            rel_retrieved_10, item.total_relevant, is_negative=is_neg, retrieved_count=retrieved_count
        )
        f1 = compute_f1(p10, recall)
        mrr = compute_mrr(rel_vector, is_negative=is_neg, retrieved_count=retrieved_count)
        ap = compute_average_precision(
            rel_vector, item.total_relevant, is_negative=is_neg, retrieved_count=retrieved_count
        )

        return MetricResult(
            query_id=item.id,
            query_type=item.type,
            query_text=item.query,
            total_relevant_in_index=item.total_relevant,
            retrieved_count=retrieved_count,
            relevant_retrieved=rel_retrieved_10,
            precision_at_5=p5,
            precision_at_10=p10,
            recall_at_10=recall,
            f1_score=f1,
            mrr=mrr,
            average_precision=ap,
        )

    async def run(self) -> dict[str, Any]:
        """Chạy toàn bộ quy trình đánh giá IR."""
        transport = httpx.ASGITransport(app=self.app)
        results: list[MetricResult] = []
        by_tier: dict[str, list[MetricResult]] = {"EASY": [], "HARD": [], "NEGATIVE": []}

        async with httpx.AsyncClient(transport=transport, base_url="http://testserver", timeout=15.0) as client:
            for q in self.queries:
                metric = await self.evaluate_query(client, q)
                if metric:
                    results.append(metric)
                    by_tier.setdefault(metric.query_type, []).append(metric)

        total = len(results) or 1
        summary = {
            "total_queries": len(results),
            "precision_at_5": round(sum(m.precision_at_5 * 100 for m in results) / total, 2),
            "precision_at_10": round(sum(m.precision_at_10 * 100 for m in results) / total, 2),
            "recall_at_10": round(sum(m.recall_at_10 * 100 for m in results) / total, 2),
            "f1_score": round(sum(m.f1_score * 100 for m in results) / total, 2),
            "mean_average_precision_map": round(sum(m.average_precision * 100 for m in results) / total, 2),
            "mean_reciprocal_rank_mrr": round(sum(m.mrr for m in results) / total, 4),
        }

        tier_summary = {
            tier: {
                "count": len(items),
                "precision_at_5": round(sum(m.precision_at_5 * 100 for m in items) / len(items), 2) if items else 0.0,
                "precision_at_10": round(sum(m.precision_at_10 * 100 for m in items) / len(items), 2) if items else 0.0,
                "recall_at_10": round(sum(m.recall_at_10 * 100 for m in items) / len(items), 2) if items else 0.0,
                "f1_score": round(sum(m.f1_score * 100 for m in items) / len(items), 2) if items else 0.0,
                "map": round(sum(m.average_precision * 100 for m in items) / len(items), 2) if items else 0.0,
                "mrr": round(sum(m.mrr for m in items) / len(items), 4) if items else 0.0,
            }
            for tier, items in by_tier.items()
        }

        return {
            "summary": summary,
            "by_tier": tier_summary,
            "per_query": [m.to_dict() for m in results],
        }


# ==============================================================================
# REPORTING
# ==============================================================================


def print_comparison_report(results: dict[str, Any]) -> None:
    """In báo cáo định dạng bảng đối chiếu số liệu."""
    summary = results["summary"]
    by_tier = results["by_tier"]

    print("\n" + "=" * 90)
    print(" BÁO CÁO ĐÁNH GIÁ ĐỘ CHÍNH XÁC TRA CỨU THÔNG TIN (INFORMATION RETRIEVAL)")
    print("=" * 90)

    print("\n[BẢNG 1] ĐỐI CHIẾU SỐ LIỆU THỰC NGHIỆM")
    print("-" * 90)
    print(f"{'Chỉ số đo lường':<32} | {'Kết quả đạt được':<25}")
    print("-" * 90)
    print(f"{'Tổng số truy vấn (Queries)':<32} | {summary['total_queries']} truy vấn")
    print(f"{'Precision@5 (Top 5 tài liệu)':<32} | {summary['precision_at_5']} %")
    print(f"{'Precision@10 (Top 10 tài liệu)':<32} | {summary['precision_at_10']} %")
    print(f"{'Recall@10 (Độ bao phủ thực tế)':<32} | {summary['recall_at_10']} %")
    print(f"{'F1-Score (Hài hòa P@10 & R@10)':<32} | {summary['f1_score']} %")
    print(f"{'Mean Average Precision (MAP)':<32} | {summary['mean_average_precision_map']} %")
    print(f"{'Mean Reciprocal Rank (MRR)':<32} | {summary['mean_reciprocal_rank_mrr']:.4f}")
    print("-" * 90)

    print("\n[BẢNG 2] PHÂN TÍCH THEO NHÓM ĐỘ KHÓ (EASY / HARD / NEGATIVE)")
    print("-" * 90)
    print(
        f"{'Nhóm':<10} | {'SL':<4} | {'P@5 (%)':<8} | {'P@10 (%)':<9} | {'Recall (%)':<10} | {'F1 (%)':<8} | {'MAP (%)':<8} | {'MRR':<6}"
    )
    print("-" * 90)
    for tier, data in by_tier.items():
        print(
            f"{tier:<10} | {data['count']:<4} | {data['precision_at_5']:<8} | {data['precision_at_10']:<9} | {data['recall_at_10']:<10} | {data['f1_score']:<8} | {data['map']:<8} | {data['mrr']:<6}"
        )
    print("-" * 90)


async def main() -> None:
    queries = load_ground_truth_dataset()
    engine = IREvaluationEngine(queries)
    results = await engine.run()
    print_comparison_report(results)


if __name__ == "__main__":
    asyncio.run(main())
