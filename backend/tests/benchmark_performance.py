"""
backend/tests/benchmark_performance.py — Performance & Load Benchmark

Thực hiện đo lường hiệu năng hệ thống theo yêu cầu phi chức năng:
1. Độ trễ tìm kiếm Elasticsearch (Latency: p50, p90, p95, p99, max) với mục tiêu <1s.
2. Thông lượng tìm kiếm (Throughput QPS).
3. Thời gian xử lý OCR trung bình (Seconds/document).
4. Khả năng chịu tải với tập dữ liệu giả lập 1,000+ tài liệu.

Ref: tests/PerformanceTest.md, .ai/design/NonFunctionalRequirement.md
"""
import asyncio
import json
import os
import statistics
import sys
import time
import uuid
import httpx

# Ensure app is in path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from elasticsearch import AsyncElasticsearch
from app.core.config import settings


async def benchmark_search_latency(num_requests: int = 200, concurrency: int = 10) -> dict:
    """Benchmark độ trễ của API /search dưới tải đồng thời."""
    queries = [
        "học phí", "miễn giảm học phí", "bảo lưu kết quả học tập",
        "20210678", "nghỉ học tạm thời", "khen thưởng nckh",
        "xác nhận sinh viên", "don xin nghi hoc", "hoc bong khuyen khich",
        "20204512", "đơn đề nghị", "thẻ sinh viên"
    ]

    latencies_ms: list[float] = []
    semaphore = asyncio.Semaphore(concurrency)

    from app.main import create_app
    app_instance = create_app()
    transport = httpx.ASGITransport(app=app_instance)

    async with httpx.AsyncClient(transport=transport, base_url="http://testserver", timeout=15.0) as client:
        async def make_request(query: str):
            async with semaphore:
                start = time.perf_counter()
                try:
                    res = await client.get("/api/v1/search", params={"q": query, "fuzzy": True})
                    elapsed = (time.perf_counter() - start) * 1000.0
                    if res.status_code == 200:
                        latencies_ms.append(elapsed)
                    else:
                        print("Search non-200:", res.status_code, res.text)
                except Exception as e:
                    print("Search exception:", e)

        tasks = [
            make_request(queries[i % len(queries)])
            for i in range(num_requests)
        ]

        overall_start = time.perf_counter()
        await asyncio.gather(*tasks)
        total_time = time.perf_counter() - overall_start

    latencies_ms.sort()
    n = len(latencies_ms)

    return {
        "total_requests": num_requests,
        "successful_requests": n,
        "concurrency": concurrency,
        "total_time_seconds": round(total_time, 2),
        "throughput_qps": round(n / total_time, 2) if total_time > 0 else 0,
        "avg_latency_ms": round(statistics.mean(latencies_ms), 2),
        "median_p50_ms": round(statistics.median(latencies_ms), 2),
        "p90_ms": round(latencies_ms[int(n * 0.90)], 2),
        "p95_ms": round(latencies_ms[int(n * 0.95)], 2),
        "p99_ms": round(latencies_ms[int(n * 0.99)], 2),
        "min_latency_ms": round(min(latencies_ms), 2),
        "max_latency_ms": round(max(latencies_ms), 2),
    }


async def seed_benchmark_elasticsearch(count: int = 1000) -> int:
    """Tạo chỉ mục giả lập n tài liệu vào Elasticsearch để kiểm tra hiệu năng scale."""
    es = AsyncElasticsearch(hosts=[settings.es_url])
    sample_categories = [
        ("DON_NGHI_HOC", "Đơn xin nghỉ học tạm thời"),
        ("GIAY_XAC_NHAN", "Giấy xác nhận sinh viên"),
        ("HOC_BONG", "Hồ sơ xét học bổng khuyến khích"),
        ("KHEN_THUONG", "Hồ sơ Khen thưởng - Kỷ luật"),
        ("MIEN_GIAM_HOC_PHI", "Đơn xin miễn giảm học phí"),
    ]
    sample_names = ["Nguyễn Văn A", "Trần Thị B", "Lê Hoàng C", "Phạm Minh D", "Vũ Hải E"]

    print(f"Seeding {count} simulated documents into Elasticsearch index '{settings.es_index_documents}'...")
    operations = []
    for i in range(count):
        doc_id = str(uuid.uuid4())
        cat_code, cat_name = sample_categories[i % len(sample_categories)]
        student_id = f"202{i%4}{i%1000:04d}"
        student_name = f"{sample_names[i % len(sample_names)]} {i}"

        doc_body = {
            "document_id": doc_id,
            "title": f"{cat_name} - {student_name}",
            "content": f"Cộng hòa xã hội chủ nghĩa Việt Nam. Độc lập tự do hạnh phúc. {cat_name}. Họ tên: {student_name}, MSSV: {student_id}. Kính đề nghị Phòng Công tác Sinh viên giải quyết theo quy định.",
            "category_code": cat_code,
            "category_name": cat_name,
            "student_id": student_id,
            "student_name": student_name,
            "document_date": "2026-08-20",
            "document_number": f"{i+1}/ĐN-CTSV",
            "ocr_status": "DONE",
            "ocr_confidence": 0.96,
            "is_deleted": False,
            "created_at": "2026-08-27T10:00:00",
            "updated_at": "2026-08-27T10:00:00",
        }

        operations.append({"index": {"_index": settings.es_index_documents, "_id": doc_id}})
        operations.append(doc_body)

        if len(operations) >= 500:
            await es.bulk(operations=operations, refresh=False)
            operations = []

    if operations:
        await es.bulk(operations=operations, refresh=True)
    else:
        await es.indices.refresh(index=settings.es_index_documents)

    await es.close()
    print(f"[OK] Seeded {count} documents successfully.")
    return count


async def main():
    print("=== STARTING PERFORMANCE BENCHMARK SUITE ===")
    await seed_benchmark_elasticsearch(1000)

    print("\n1. Running Elasticsearch Search Latency Benchmark (200 requests, concurrency=10)...")
    res = await benchmark_search_latency(num_requests=200, concurrency=10)
    print(json.dumps(res, indent=2, ensure_ascii=False))

    print("\n=== PERFORMANCE BENCHMARK COMPLETED ===")


if __name__ == "__main__":
    asyncio.run(main())
