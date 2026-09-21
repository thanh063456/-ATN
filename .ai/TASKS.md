# TASKS — Task Management

## Purpose

Danh sách task có cấu trúc theo Epic → Feature → Task cho dự án Student-Document-OCR.
Đây là nguồn sự thật cho trạng thái công việc hiện tại.

## Scope

Phase 1 tasks (chi tiết). Phase 2-12 tasks (overview, sẽ expand khi đến phase đó).

---

## Quy ước

| Symbol | Trạng thái |
|--------|-----------|
| `[ ]` | Todo |
| `[/]` | In Progress |
| `[x]` | Done |
| `[-]` | Blocked |
| `[~]` | Cancelled / Out of scope |

Priority: `P0` = Critical · `P1` = High · `P2` = Medium · `P3` = Low

---

## EPIC-01 — Phase 1: Architecture & Specification

**Objective:** Freeze toàn bộ spec trước khi viết code.  
**Status:** 🔄 In Progress

---

### FEAT-01-01 — Project Setup

| ID | Title | Priority | Status | Dependency |
|----|-------|----------|--------|-----------|
| TASK-001 | Bootstrap project skeleton | P0 | [x] Done | — |
| TASK-002 | Review và audit project structure | P0 | [x] Done | TASK-001 |
| TASK-003 | Configure .gitignore, .editorconfig, .env.example | P1 | [x] Done | TASK-001 |
| TASK-004 | Khởi tạo pyproject.toml, requirements.txt, Makefile | P1 | [x] Done | TASK-001 |

---

### FEAT-01-02 — Specification Writing

| ID | Title | Priority | Status | Dependency |
|----|-------|----------|--------|-----------|
| TASK-010 | Viết PROJECT_SPEC.md đầy đủ 16 sections | P0 | [x] Done | TASK-002 |
| TASK-011 | Freeze TECH_STACK.md | P0 | [x] Done | TASK-010 |
| TASK-012 | Viết ARCHITECTURE.md với đầy đủ pipeline | P0 | [x] Done | TASK-011 |
| TASK-013 | Viết DECISIONS.md (ADR-001 → ADR-010) | P0 | [x] Done | TASK-012 |
| TASK-014 | Viết ROADMAP.md với 12 phases đầy đủ | P1 | [x] Done | TASK-013 |
| TASK-015 | Cập nhật TASKS.md (file này) | P1 | [x] Done | TASK-014 |
| TASK-016 | Cập nhật AI_CONTEXT.md | P1 | [x] Done | TASK-015 |

**Acceptance Criteria FEAT-01-02:**
- Không còn [TBD] quan trọng trong ARCHITECTURE.md
- Không có contradiction giữa các spec file
- Tất cả decisions có ADR rõ ràng

---

### FEAT-01-03 — Database Design

| ID | Title | Priority | Status | Dependency |
|----|-------|----------|--------|-----------|
| TASK-020 | Thiết kế ERD logical model (8 entities) | P0 | [x] Done | TASK-012 |
| TASK-021 | Viết design/Database.md (schema chi tiết) | P1 | [x] Done | TASK-020 |

**Subtasks TASK-020:**
- [ ] TASK-020a: Define User entity (attributes, PK, FK)
- [ ] TASK-020b: Define Role entity
- [ ] TASK-020c: Define Document entity
- [ ] TASK-020d: Define DocumentCategory entity
- [ ] TASK-020e: Define OCRResult entity
- [ ] TASK-020f: Define DocumentMetadata entity
- [ ] TASK-020g: Define AuditLog entity
- [ ] TASK-020h: Define ProcessingJob entity (Celery task tracking)
- [ ] TASK-020i: Vẽ ERD diagram (text/PlantUML)

**Acceptance Criteria FEAT-01-03:**
- Tất cả entities có purpose, attributes, PK, FK, relationships
- ERD không có circular dependency
- Normalization ≥ 3NF

---

### FEAT-01-04 — API Design

| ID | Title | Priority | Status | Dependency |
|----|-------|----------|--------|-----------|
| TASK-030 | Viết API spec: Authentication group | P0 | [x] Done | TASK-012 |
| TASK-031 | Viết API spec: Documents group | P0 | [x] Done | TASK-030 |
| TASK-032 | Viết API spec: OCR group | P0 | [x] Done | TASK-031 |
| TASK-033 | Viết API spec: Search group | P1 | [x] Done | TASK-032 |
| TASK-034 | Viết API spec: Users group | P1 | [x] Done | TASK-033 |
| TASK-035 | Viết API spec: Metadata group | P2 | [x] Done | TASK-034 |
| TASK-036 | Viết API spec: Administration group | P2 | [x] Done | TASK-034 |

**Acceptance Criteria FEAT-01-04:**
- Tất cả endpoints có: Method, Path, Purpose, Request schema, Response schema, Auth, Error cases
- Không có duplicate endpoint
- Versioning: /api/v1/

---

### FEAT-01-05 — OCR Pipeline Specification

| ID | Title | Priority | Status | Dependency |
|----|-------|----------|--------|-----------|
| TASK-040 | Viết chi tiết OCR.md (full pipeline spec) | P0 | [x] Done | TASK-013 |
| TASK-041 | Viết VietOCR.md (architecture chi tiết) | P1 | [x] Done | TASK-040 |
| TASK-042 | Viết PaddleOCR.md (detection engine research) | P1 | [x] Done | TASK-040 |
| TASK-043 | Quyết định ADR-002 (text detection engine) | P0 | [-] Blocked | ADR-002 cần user input |

**Acceptance Criteria FEAT-01-05:**
- OCR pipeline có input/output cho từng bước
- VietOCR và Text Detection được mô tả riêng biệt rõ ràng

---

### FEAT-01-06 — Training Pipeline Specification

| ID | Title | Priority | Status | Dependency |
|----|-------|----------|--------|-----------|
| TASK-050 | Viết Training.md (training pipeline spec) | P1 | [x] Done | TASK-012 |
| TASK-051 | Viết Dataset.md (annotation format, split strategy) | P1 | [x] Done | TASK-050 |
| TASK-052 | Viết Evaluation.md (metrics, benchmark plan) | P1 | [x] Done | TASK-051 |
| TASK-053 | Viết CER.md và WER.md (metrics detail) | P2 | [x] Done | TASK-052 |

---

### FEAT-01-07 — UI & Use Case Design

| ID | Title | Priority | Status | Dependency |
|----|-------|----------|--------|-----------|
| TASK-060 | Viết UseCase.md đầy đủ (actors, use cases, flows) | P1 | [x] Done | TASK-010 |
| TASK-061 | Viết UI.md đầy đủ (11 screens) | P1 | [x] Done | TASK-060 |

---

### FEAT-01-08 — Elasticsearch Design

| ID | Title | Priority | Status | Dependency |
|----|-------|----------|--------|-----------|
| TASK-070 | Viết Elasticsearch.md (index mapping spec) | P1 | [x] Done | TASK-012 |
| TASK-071 | Viết VietnameseSearch.md (analyzer strategy) | P1 | [x] Done | TASK-070 |

---

## EPIC-02 — Phase 2: Dataset Preparation

**Objective:** Xây dựng khung quản lý, thu thập, xử lý và annotate dataset tài liệu CTSV.  
**Status:** 🔄 In Progress

---

### FEAT-02-01 — Step 2.1 & Step 2.1.5: Dataset Inventory & Tooling Preparation

| ID | Title | Priority | Status | Dependency |
|----|-------|----------|--------|-----------|
| TASK-100 | Tạo cấu trúc thư mục dataset/ (10 subfolders + .gitkeep) | P0 | [x] Done | FEAT-01-01 |
| TASK-101 | Viết dataset/README.md hướng dẫn quản lý | P0 | [x] Done | TASK-100 |
| TASK-102 | Cập nhật Dataset Policy & Quality Checklist (.ai/research/Dataset.md) | P0 | [x] Done | TASK-101 |
| TASK-103 | Định nghĩa Dataset Inventory Schema & Document Taxonomy | P0 | [x] Done | TASK-102 |
| TASK-104 | Định nghĩa Dataset Versioning Schema (v0.1-draft) | P1 | [x] Done | TASK-103 |
| TASK-105 | Dataset Policy Audit (Line crop aspect ratio, Dynamic Charset, Raw vs Source, Annotations, Review Workflow) | P0 | [x] Done | TASK-104 |
| TASK-106 | Viết Dataset Validator tool (scripts/dataset_validator.py) | P0 | [x] Done | TASK-105 |
| TASK-107 | Viết Dataset Inventory Generator (scripts/dataset_inventory.py) | P0 | [x] Done | TASK-106 |
| TASK-108 | Viết Dataset Statistics Calculator (scripts/dataset_statistics.py) | P0 | [x] Done | TASK-107 |
| TASK-109 | Viết Dataset Report Generator (scripts/dataset_report.py) | P0 | [x] Done | TASK-108 |
| TASK-110 | Viết Dataset Tooling Unit Tests (tests/test_dataset_tooling.py - 8 tests pass) | P0 | [x] Done | TASK-109 |
| TASK-111 | Tiếp nhận tập file tài liệu thật từ Phòng CTSV (`DATASET_STATUS`) | P0 | [-] Blocked | Chờ cấp dữ liệu thật |

**Acceptance Criteria FEAT-02-01:**
- Cấu trúc 10 thư mục con dưới `dataset/` được tạo đầy đủ.
- Policy chống rò rỉ dữ liệu (Data leakage) ở cấp độ Document Level được quy định rõ.
- Tooling Dataset Validator, Inventory, Statistics, Report hoạt động hoàn hảo với `dataset/raw/` rỗng.
- 8 Unit Tests kiểm thử Tooling pass 100% khi `dataset/raw/` rỗng.
- `DATASET_STATUS = NOT_PROVIDED` và `"No dataset available."` được ghi nhận minh bạch, không tạo dữ liệu giả thay thế.

---

### FEAT-02-02 — Step 2.2: Data Ingestion & Preprocessing

*(Sẽ thực hiện khi có dữ liệu thật)*

- [ ] TASK-110: Upload file thô vào `dataset/raw/` và ghi `metadata/inventory.json`
- [ ] TASK-111: Trích xuất trang ảnh (PDF -> PNG DPI 200/300) vào `dataset/images/`
- [ ] TASK-112: Tiền xử lý ảnh (Deskew, Denoise, Binarize)
- [ ] TASK-113: Gán nhãn Bounding box và Ground Truth Text (`dataset/annotations/`)
- [ ] TASK-114: Cắt dòng chữ (Line Cropping h=32px) vào `dataset/crops/`
- [ ] TASK-115: Chia tập Train/Val/Test (80/10/10) và xuất file `labels.txt` (TSV)
- [ ] TASK-116: Cập nhật Dataset Version lên `v1.0` và thống kê vocabulary

---

## EPIC-03 — Phase 3: VietOCR Fine-tuning

*(Sẽ expand chi tiết khi bắt đầu Phase 3)*

- [ ] TASK-200: Setup training environment
- [ ] TASK-201: Implement training script
- [ ] TASK-202: Fine-tune VietOCR
- [ ] TASK-203: Save best checkpoint

---

## EPIC-04 → EPIC-12 — Phase 4 → Phase 12

*(Sẽ expand khi đến từng phase)*

---

## TODO

- [ ] Review TASKS.md với GVHD
- [ ] Estimate effort (hours/days) cho từng TASK trong Phase 1
- [ ] Setup project board (GitHub Issues hoặc Notion) theo TASKS.md

## References

- .ai/ROADMAP.md
- .ai/AI_CONTEXT.md
- .ai/PROJECT_SPEC.md
