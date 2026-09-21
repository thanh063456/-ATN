# Performance Tests — Kiem thu hieu nang

## Purpose

Huong dan performance testing: load test, stress test, API latency, OCR throughput.

## Scope

Locust cho load testing API. Muc tieu: API p95 < 200ms, OCR < 5s/trang.

## TODO

- [ ] Viet Locust test scenarios (upload, search, browse)
- [ ] Benchmark API response time (p50, p95, p99)
- [ ] Benchmark OCR throughput (pages/minute tren CPU)
- [ ] Benchmark Elasticsearch query latency
- [ ] Load test: 50 concurrent users trong 5 phut
- [ ] Xac dinh bottleneck va de xuat toi uu

## References

- IntegrationTest.md
- OCRTest.md
- .ai/design/NonFunctionalRequirement.md
