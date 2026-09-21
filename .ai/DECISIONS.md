# DECISIONS — Architecture Decision Records (ADR)

## Purpose

Lưu trữ tất cả quyết định kiến trúc quan trọng theo format ADR chuẩn.
Mỗi quyết định phải được ghi nhận tại đây trước khi thực hiện.

## Scope

Tất cả quyết định về: technology selection, architecture pattern, API design,
data model, deployment strategy trong dự án Student-Document-OCR.

---

## ADR-001 — OCR Recognition Engine: VietOCR

| Field | Value |
|-------|-------|
| **ID** | ADR-001 |
| **Date** | 2026-08-08 |
| **Topic** | Chọn OCR text recognition engine |
| **Status** | DECIDED |

**Decision:** Sử dụng **VietOCR** làm text recognition engine chính.

**Reason:**
- VietOCR được tối ưu đặc biệt cho tiếng Việt có dấu
- Kiến trúc VGG + Transformer Seq2Seq: balance giữa accuracy và speed
- Có pre-trained model sẵn, giảm yêu cầu dữ liệu cho fine-tuning
- Cộng đồng tiếng Việt sử dụng rộng rãi, có documentation tiếng Việt
- Open-source, MIT license

**Alternatives considered:**
- PaddleOCR: Đa năng hơn nhưng nặng hơn, dependency phức tạp hơn
- Tesseract: Accuracy tiếng Việt thấp hơn, không dùng deep learning

**Consequences:**
- VietOCR chỉ làm text recognition — cần text detection riêng (→ ADR-002)
- Phụ thuộc vào PyTorch
- Fine-tuning cần GPU hoặc time dài trên CPU

---

## ADR-002 — OCR Text Detection Engine

| Field | Value |
|-------|-------|
| **ID** | ADR-002 |
| **Date** | 2026-08-08 |
| **Topic** | Chọn text detection engine cho OCR pipeline |
| **Status** | **[TBD — USER DECISION REQUIRED]** |

**Context:**
VietOCR (ADR-001) chỉ nhận dạng chữ trong ảnh đã được crop (text line crop).
Cần một bước trước đó để phát hiện vùng có chữ (text detection) và crop ra.

**Options:**

| Option | Ưu điểm | Nhược điểm |
|--------|---------|------------|
| **PaddleOCR Detection** (DBNet++) | Tích hợp sẵn, accuracy tốt, hỗ trợ tiếng Việt | Dependency nặng (PaddlePaddle) |
| **CRAFT** (Character Region Awareness) | Accuracy cao, phát hiện chữ cong | Chậm hơn, complex |
| **DBNet** (standalone) | Nhanh, accuracy tốt | Cần train riêng hoặc dùng pre-trained |
| **Không dùng detection** (full-page layout) | Đơn giản, phù hợp tài liệu chuẩn | Không robust với tài liệu phức tạp |

**Recommendation:** PaddleOCR Detection (DBNet++) vì:
- Tích hợp dễ với VietOCR workflow
- Pre-trained tiếng Việt có sẵn
- Proven combination: PaddleOCR detection + VietOCR recognition

**[TBD — USER DECISION REQUIRED]**: Cần xác nhận từ người dùng/GVHD.

---

## ADR-003 — Async Processing: Celery + Redis

| Field | Value |
|-------|-------|
| **ID** | ADR-003 |
| **Date** | 2026-08-08 |
| **Topic** | Cơ chế xử lý bất đồng bộ cho OCR |
| **Status** | DECIDED |

**Decision:** Sử dụng **Celery** với **Redis** làm message broker cho async OCR tasks.

**Reason:**
- OCR processing (~5-10s/trang) không thể block HTTP request
- Celery là standard trong Python ecosystem, tích hợp tốt với FastAPI
- Redis đã dùng cho caching → dual-use, giảm thêm service
- Celery có retry, rate limiting, task tracking built-in

**Consequences:**
- Thêm Celery Worker service vào Docker Compose
- Cần Redis service
- Task status tracking cần thiết kế trong DB (ProcessingJob table)

---

## ADR-004 — Search Engine: Elasticsearch

| Field | Value |
|-------|-------|
| **ID** | ADR-004 |
| **Date** | 2026-08-08 |
| **Topic** | Full-text search engine |
| **Status** | DECIDED |

**Decision:** Sử dụng **Elasticsearch 8.x** làm full-text search engine.

**Reason:**
- Full-text search với Vietnamese text analysis
- Fuzzy search để bù đắp lỗi OCR
- Highlight API cho search result display
- Aggregation cho faceted search / statistics
- Mature, well-documented Python client

**Consequences:**
- Cần ES service trong Docker Compose (~512MB-1GB RAM)
- Cần thiết kế index mapping cho tiếng Việt
- Vietnamese analyzer: cần benchmark (ADR-005)

---

## ADR-005 — Elasticsearch Vietnamese Analyzer

| Field | Value |
|-------|-------|
| **ID** | ADR-005 |
| **Date** | 2026-08-08 |
| **Topic** | Analyzer cho full-text search tiếng Việt |
| **Status** | **[TBD — BENCHMARK REQUIRED]** |

**Options:**
- `standard` analyzer: Đơn giản, không tối ưu tiếng Việt
- `icu_analyzer` (ICU plugin): Tốt hơn cho Unicode/diacritic
- Custom analyzer (vi_tokenizer + lowercase + ascii_folding): Flexible
- `vi_analyzer` nếu có plugin: [Cần kiểm tra]

**[TBD]**: Cần cài đặt ES, test benchmark từng analyzer với tài liệu CTSV mẫu.

---

## ADR-006 — Object Storage: MinIO

| Field | Value |
|-------|-------|
| **ID** | ADR-006 |
| **Date** | 2026-08-08 |
| **Topic** | Lưu trữ file tài liệu |
| **Status** | DECIDED |

**Decision:** Sử dụng **MinIO** cho object storage.

**Reason:**
- S3-compatible API → dễ migrate lên AWS S3 trong tương lai
- Self-hosted → phù hợp với thesis scope (không cần cloud)
- Docker image có sẵn
- Python SDK (minio) có sẵn

---

## ADR-007 — Backend Framework: FastAPI

| Field | Value |
|-------|-------|
| **ID** | ADR-007 |
| **Date** | 2026-08-08 |
| **Topic** | Python web framework |
| **Status** | DECIDED |

**Decision:** Sử dụng **FastAPI** với async support.

**Reason:**
- Async-first → phù hợp với I/O-heavy workload (DB, ES, MinIO)
- Auto OpenAPI docs (Swagger UI) — tiện cho development
- Pydantic v2 validation — type safe
- Tốt hơn Django/Flask cho API-only service

---

## ADR-008 — Frontend UI Library

| Field | Value |
|-------|-------|
| **ID** | ADR-008 |
| **Date** | 2026-08-08 |
| **Topic** | UI component library cho React |
| **Status** | **[TBD — USER DECISION REQUIRED]** |

**Options:**
- **shadcn/ui**: Copy-paste components, full control, Tailwind-based
- **Ant Design**: Feature-rich, admin-focused, heavy
- **Chakra UI**: Clean, accessible, moderate size
- **Custom CSS**: Full control, no dependency, more effort

**[TBD — USER DECISION REQUIRED]**: Ưu tiên shadcn/ui hoặc Ant Design?

---

## ADR-009 — Frontend Testing Framework

| Field | Value |
|-------|-------|
| **ID** | ADR-009 |
| **Date** | 2026-08-08 |
| **Topic** | Testing framework cho React frontend |
| **Status** | **[TBD]** |

**Options:**
- Vitest + React Testing Library: Modern, tích hợp tốt với Vite
- Jest + React Testing Library: Mature, phổ biến

**[TBD]**: Chọn sau khi setup môi trường frontend.

---

## ADR-010 — CI/CD Platform

| Field | Value |
|-------|-------|
| **ID** | ADR-010 |
| **Date** | 2026-08-08 |
| **Topic** | CI/CD platform |
| **Status** | **[TBD]** |

**Options:**
- GitHub Actions: Free, tích hợp GitHub
- GitLab CI: Tốt nếu dùng GitLab

**[TBD]**: Phụ thuộc vào platform host source code.

---

## ADR-011 — Async Task Queue: Celery + Redis từ giai đoạn đầu

| Field | Value |
|-------|-------|
| **ID** | ADR-011 |
| **Date** | 2026-08-26 |
| **Topic** | Chiến lược xử lý bất đồng bộ cho OCR pipeline |
| **Status** | DECIDED |

**Context:**
OCR processing với VietOCR mất ~5–30 giây/tài liệu tuỳ số trang và cấu hình phần cứng. Nếu block HTTP request trong thời gian này, trải nghiệm người dùng kém và server không thể xử lý request song song. Có hai lựa chọn chính:

**Alternatives considered:**

| Option | Ưu điểm | Nhược điểm |
|--------|---------|------------|
| **FastAPI `BackgroundTasks`** | Đơn giản, không cần service bổ sung, đủ cho prototype | Không có retry, không monitor được, task mất khi restart process, không scale worker ngang |
| **Celery + Redis** | Retry tự động, task tracking, Flower UI, scale worker độc lập, phù hợp production | Thêm 2–3 service (Redis, celery_worker, Flower), tăng độ phức tạp vận hành |

**Decision:** Dùng **Celery + Redis** ngay từ đầu.

**Reason:**
- OCR là nghiệp vụ cốt lõi — cần retry khi model lỗi hoặc file phức tạp.
- `ProcessingJob` table trong DB cần Celery task ID để tracking → đã thiết kế sẵn cho Celery.
- Redis đã cần cho caching → dual-use, không phát sinh service hoàn toàn mới.
- Đồ án cần demo monitoring (Flower) để đánh giá hiệu năng hệ thống → điểm cộng trong báo cáo.
- FastAPI BackgroundTasks sẽ cần migrate sang Celery sau nếu hệ thống scale → làm ngay tránh viết lại.

**Trade-offs chấp nhận:**
- Tăng `docker-compose.yml` thêm `celery_worker` và `flower` service.
- Developer cần hiểu cơ bản Celery task lifecycle.
- Trong giai đoạn đầu dev, có thể tắt `celery_worker` và `flower` nếu chỉ test API — backend vẫn chạy được.

**Consistency check:**
- ✅ `requirements.txt`: có `celery`, `redis`
- ✅ `docker-compose.yml`: có `redis`, `celery_worker`, `flower`
- ✅ `ARCHITECTURE.md`: mô tả async OCR qua Celery
- ✅ `Database.md`: `processing_jobs` table tracking Celery task ID
- ✅ `TECH_STACK.md`: cần cập nhật thêm Celery/Redis nếu chưa có

**Hướng phát triển (ngoài scope đồ án):**
- Nếu chuyển lên production/cloud: xem xét thay Redis bằng RabbitMQ hoặc dùng AWS SQS.

---

## TODO

- [ ] Quyết định ADR-002 (text detection engine) — cần user/GVHD confirm
- [ ] Benchmark ADR-005 (Vietnamese analyzer) — cần ES running
- [ ] Quyết định ADR-008 (frontend UI library)
- [ ] Quyết định ADR-009 (frontend testing)
- [ ] Quyết định ADR-010 (CI/CD)

## References

- https://adr.github.io
- .ai/TECH_STACK.md
- .ai/ARCHITECTURE.md
