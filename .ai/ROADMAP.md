# ROADMAP — Lộ trình phát triển

## Purpose

Lộ trình phát triển chính thức của dự án Student-Document-OCR theo 12 phase.
Mỗi phase có Objective, Tasks, Deliverables và Acceptance Criteria cụ thể.

## Scope

12 phase từ Architecture & Specification đến Thesis & Defense.

---

## Tổng quan các Phase

| Phase | Tên | Mục tiêu chính | Trạng thái |
|-------|-----|----------------|-----------|
| 1 | Architecture & Specification | Freeze spec, design, decisions | ✅ Completed |
| 2 | Dataset Preparation | Thu thập và annotate dataset CTSV | 🔄 In Progress |
| 3 | VietOCR Fine-tuning | Fine-tune model trên dataset | 🔲 Todo |
| 4 | OCR Evaluation | Đánh giá CER/WER, chọn model tốt nhất | 🔲 Todo |
| 5 | FastAPI OCR Service | Xây dựng backend API cốt lõi | 🔲 Todo |
| 6 | PostgreSQL + MinIO | Database schema, file storage | 🔲 Todo |
| 7 | Elasticsearch | Search engine, Vietnamese analyzer | 🔲 Todo |
| 8 | React Frontend | UI cho upload, search, OCR viewer | 🔲 Todo |
| 9 | Integration | End-to-end integration | 🔲 Todo |
| 10 | Testing & Evaluation | System testing, performance benchmark | 🔲 Todo |
| 11 | Docker & Deployment | Production-ready Docker stack | 🔲 Todo |
| 12 | Thesis & Defense | Báo cáo, thuyết trình bảo vệ | 🔲 Todo |

---

## PHASE 1 — Architecture & Specification

**Objective:** Hoàn thiện và đóng băng toàn bộ đặc tả kỹ thuật trước khi viết code.

**Tasks:**
- [x] Bootstrap project skeleton
- [x] Review project structure
- [ ] Hoàn thiện PROJECT_SPEC.md
- [ ] Hoàn thiện ARCHITECTURE.md
- [ ] Hoàn thiện TECH_STACK.md
- [ ] Hoàn thiện DECISIONS.md (ADR-001 → ADR-010)
- [ ] Hoàn thiện ERD.md (logical model)
- [ ] Hoàn thiện API.md (spec level)
- [ ] Hoàn thiện UseCase.md
- [ ] Hoàn thiện OCR pipeline spec (research/OCR.md)
- [ ] Hoàn thiện Training pipeline spec
- [ ] Quyết định ADR-002 (text detection engine)
- [ ] Review với GVHD

**Deliverables:**
- PROJECT_SPEC.md (approved)
- ARCHITECTURE.md (frozen)
- TECH_STACK.md (frozen)
- DECISIONS.md (ADR-001 → ADR-007 decided)
- design/ERD.md (logical)
- design/API.md (spec)
- design/UseCase.md (complete)

**Acceptance Criteria:**
- Không còn [TBD] trong ARCHITECTURE.md (ngoại trừ ADR-002 nếu chờ quyết định)
- Không có contradiction giữa các file spec
- GVHD đã review và approved (nếu có thể)

---

## PHASE 2 — Dataset Preparation

**Objective:** Thu thập, xử lý và annotate dataset tài liệu CTSV cho training và evaluation.

**Tasks:**
- [ ] Thu thập tài liệu CTSV (xin phép Phòng CTSV)
- [ ] Scan tài liệu ở độ phân giải ≥ 150 DPI
- [ ] Annotation text bằng LabelMe hoặc CVAT
- [ ] Tiền xử lý: denoise, deskew, normalize
- [ ] Tạo train/val/test split (80/10/10)
- [ ] Tính thống kê dataset (số trang, phân phối chữ)
- [ ] Ghi vào docs/Experiment.md — EXP-001

**Deliverables:**
- dataset/ với cấu trúc: raw/, processed/, train/, val/, test/, annotations/
- Dataset statistics report

**Acceptance Criteria:**
- Có ít nhất 500 text line samples để fine-tuning (nếu đạt)
- Annotation format đúng với VietOCR training requirement
- Tập test có ground truth chất lượng cao (100% verified)

---

## PHASE 3 — VietOCR Fine-tuning

**Objective:** Fine-tune VietOCR pre-trained model trên dataset tài liệu CTSV.

**Tasks:**
- [ ] Setup GPU environment (nếu có)
- [ ] Load VietOCR pre-trained weights (vgg_transformer.pth)
- [ ] Implement training script (training/train.py)
- [ ] Implement data loader cho dataset format
- [ ] Chạy baseline evaluation trước fine-tuning
- [ ] Fine-tune với dataset CTSV
- [ ] Monitor training qua TensorBoard
- [ ] Save best checkpoint theo validation CER

**Deliverables:**
- training/train.py
- training/configs/finetune.yaml
- models/best_finetune.pth
- TensorBoard logs

**Acceptance Criteria:**
- Fine-tuned model có CER thấp hơn pre-trained trên test set CTSV
- Training không bị diverge

---

## PHASE 4 — OCR Evaluation

**Objective:** Đánh giá định lượng chất lượng OCR, chọn model tốt nhất cho production.

**Tasks:**
- [ ] Implement evaluation script (training/evaluate.py)
- [ ] Tính CER/WER cho: pre-trained VietOCR, fine-tuned VietOCR, Tesseract baseline
- [ ] Phân tích lỗi: loại ký tự hay sai, font, quality ảnh
- [ ] Ghi vào docs/Experiment.md — EXP-002, EXP-003, EXP-004
- [ ] Quyết định model cho production

**Deliverables:**
- training/evaluate.py
- docs/Experiment.md (EXP-002, 003, 004)
- Evaluation report (bảng so sánh)

**Acceptance Criteria:**
- CER < 5% trên test set (tài liệu in, scan chuẩn)
- WER < 10% trên cùng điều kiện
- Có bảng so sánh rõ ràng

---

## PHASE 5 — FastAPI OCR Service

**Objective:** Xây dựng backend API với OCR service và authentication.

**Tasks:**
- [ ] Khởi tạo FastAPI project structure
- [ ] Implement Auth router (login, logout, refresh)
- [ ] Implement Document router (upload, list, get, delete)
- [ ] Implement OCR Service (tích hợp VietOCR pipeline)
- [ ] Implement Celery task: process_ocr
- [ ] Implement OCR router (trigger, status, result)
- [ ] Implement MinIO file storage service

**Deliverables:**
- backend/app/ với full structure
- Tất cả routers theo API spec
- Celery worker

**Acceptance Criteria:**
- Tất cả API endpoints trả đúng theo spec (API.md)
- OCR task chạy async thành công
- Unit tests ≥ 70% coverage

---

## PHASE 6 — PostgreSQL + MinIO

**Objective:** Implement database layer và file storage.

**Tasks:**
- [ ] Implement SQLAlchemy ORM models
- [ ] Viết Alembic initial migration
- [ ] Implement Repository layer (UserRepo, DocumentRepo, OCRResultRepo)
- [ ] Implement MinIO service (upload, download, presigned URL)
- [ ] Seed admin user

**Deliverables:**
- backend/app/models/ (tất cả ORM models)
- backend/app/repositories/
- alembic/versions/001_initial.py

**Acceptance Criteria:**
- Migration chạy thành công
- Repository tests pass
- File upload/download MinIO hoạt động

---

## PHASE 7 — Elasticsearch

**Objective:** Implement search service với Elasticsearch.

**Tasks:**
- [ ] Tạo ES index mapping cho documents
- [ ] Benchmark Vietnamese analyzer (ADR-005)
- [ ] Implement SearchService
- [ ] Implement Search router
- [ ] Implement indexing sau OCR completion
- [ ] Test full-text search, fuzzy, filter, highlight

**Deliverables:**
- backend/app/services/search_service.py
- scripts/create_es_index.py
- Elasticsearch index mapping

**Acceptance Criteria:**
- Search trả kết quả đúng với highlight
- Fuzzy search bắt được lỗi OCR phổ biến
- Search latency p95 < 500ms

---

## PHASE 8 — React Frontend

**Objective:** Xây dựng giao diện web đầy đủ chức năng.

**Tasks:**
- [ ] Khởi tạo Vite React + TypeScript project
- [ ] Implement Auth feature (Login page)
- [ ] Implement Document Upload (drag-and-drop)
- [ ] Implement Document List + pagination
- [ ] Implement OCR Result Viewer
- [ ] Implement Search page với highlight
- [ ] Implement Admin: User Management
- [ ] Implement Admin: Audit Log

**Deliverables:**
- frontend/src/ với full structure
- Tất cả pages theo UI spec

**Acceptance Criteria:**
- Tất cả use cases từ UseCase.md hoạt động
- Responsive trên desktop

---

## PHASE 9 — Integration

**Objective:** Tích hợp frontend ↔ backend ↔ OCR ↔ ES end-to-end.

**Tasks:**
- [ ] Integration test: upload → OCR → index → search
- [ ] Fix integration bugs
- [ ] Performance profiling
- [ ] Docker Compose integration test

**Deliverables:**
- Integration test suite
- Bug fix list

**Acceptance Criteria:**
- Happy path end-to-end hoạt động hoàn toàn
- Không còn critical bugs

---

## PHASE 10 — Testing & Evaluation

**Objective:** System testing, performance benchmark và final evaluation.

**Tasks:**
- [ ] Viết đầy đủ unit tests (target ≥ 70% coverage)
- [ ] Viết integration tests cho tất cả API
- [ ] Load test với Locust (20 concurrent users)
- [ ] OCR accuracy evaluation trên final test set
- [ ] Benchmark: API latency, search latency

**Deliverables:**
- Test reports
- Performance benchmark report
- Final CER/WER report

**Acceptance Criteria:**
- Coverage ≥ 70%
- NFR-01 → NFR-10 đều đạt target

---

## PHASE 11 — Docker & Deployment

**Objective:** Production-ready containerization và deployment documentation.

**Tasks:**
- [ ] Viết Dockerfile cho backend (multi-stage)
- [ ] Viết Dockerfile cho frontend (nginx)
- [ ] Viết docker-compose.prod.yml
- [ ] Setup Nginx reverse proxy
- [ ] Test production stack trên clean machine
- [ ] Viết deployment guide

**Deliverables:**
- Production-ready Docker Compose stack
- Deployment documentation

**Acceptance Criteria:**
- Stack khởi động từ `docker compose up` trên máy sạch
- HTTPS hoạt động (hoặc documented for setup)

---

## PHASE 12 — Thesis & Defense

**Objective:** Hoàn thiện báo cáo tốt nghiệp và chuẩn bị bảo vệ.

**Tasks:**
- [ ] Viết Chương 1: Giới thiệu
- [ ] Viết Chương 2: Cơ sở lý thuyết
- [ ] Viết Chương 3: Phân tích và thiết kế
- [ ] Viết Chương 4: Xây dựng hệ thống
- [ ] Viết Chương 5: Thực nghiệm và đánh giá
- [ ] Viết Chương 6: Kết luận
- [ ] Thiết kế slide thuyết trình (20 slides)
- [ ] Chạy thử bảo vệ

**Deliverables:**
- Báo cáo tốt nghiệp (PDF)
- Slide thuyết trình (20 slides)
- Demo video (backup)

**Acceptance Criteria:**
- Báo cáo được GVHD duyệt
- Demo hoạt động ổn định

---

## TODO

- [ ] Xác nhận timeline với GVHD
- [ ] Ước lượng effort (days) cho từng phase
- [ ] Xác nhận deadline từng phase

## References

- .ai/PROJECT_SPEC.md
- .ai/TASKS.md
- docs/Proposal.md
