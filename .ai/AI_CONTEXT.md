# AI_CONTEXT — Context phiên làm việc với AI Agent

## Purpose

File này cung cấp context tức thời cho AI coding agent (Antigravity) về trạng thái
hiện tại của dự án, công việc đang làm và các quyết định quan trọng cần nhớ.

**Cập nhật file này trước mỗi phiên làm việc mới với agent.**

## Scope

Trạng thái hiện tại của dự án, task đang thực hiện, blocked items, next steps.

---

## Current Phase

**Phase 2 — Dataset Preparation (Step 2.1 & Step 2.1.5 Tooling Preparation Completed)**

Mục tiêu: Xây dựng nền tảng hạ tầng, chính sách quản lý, tiêu chuẩn kiểm kê, phân loại dữ liệu và bộ công cụ tự động (Tooling + Unit Tests) trước khi tiếp nhận tập tài liệu thật.

---

## Current Task

**Step 2.1.5 Completed**. Đã xây dựng hoàn chỉnh 4 công cụ tự động (`scripts/dataset_validator.py`, `scripts/dataset_inventory.py`, `scripts/dataset_statistics.py`, `scripts/dataset_report.py`) và bộ Unit Tests (`tests/test_dataset_tooling.py` - 8/8 tests pass).

Trạng thái dữ liệu hiện tại:
`DATASET_STATUS: NOT_PROVIDED`
`DATASET_REPORT: "No dataset available."`

---

## Completed (Phase 2 Step 2.1 & 2.1.5)

- [x] Tạo cấu trúc 10 thư mục con dưới `dataset/` (raw, source, images, annotations, crops, train, val, test, metadata, statistics)
- [x] Cập nhật `dataset/README.md` & `dataset/statistics/README.md` hướng dẫn quản lý & sử dụng tooling
- [x] Đã thực hiện Dataset Policy Audit & hoàn thiện `.ai/research/Dataset.md` (Line crop aspect ratio, Dynamic Charset, Raw vs Source, Text Line schema, Spelling fidelity, Special content rules, Reviewer workflow, Document-level split)
- [x] Định nghĩa Dataset Inventory Schema (13 trường metadata) & Document Taxonomy (11 loại tài liệu CTSV)
- [x] Định nghĩa Data Quality Checklist (13 tiêu chí) và 3 cấp chất lượng (GOOD, ACCEPTABLE, REJECT)
- [x] Định nghĩa Dataset Versioning Schema (`v0.1-draft` -> `v0.2` -> `v1.0`)
- [x] Viết `scripts/dataset_validator.py` (kiểm tra format, size, convention, duplicates, corruption mà không xóa file)
- [x] Viết `scripts/dataset_inventory.py` (sinh `inventory.json` & `inventory.csv` với 13 trường metadata, không tự đoán dữ liệu)
- [x] Viết `scripts/dataset_statistics.py` (thống kê chỉ số, trả về `NOT_PROVIDED` nếu rỗng)
- [x] Viết `scripts/dataset_report.py` (sinh `dataset_report.json` & `dataset_report.md`, ghi rõ `"No dataset available."` nếu rỗng)
- [x] Viết `tests/test_dataset_tooling.py` (8 Unit Tests kiểm thử độc lập - 100% PASS khi dataset/raw/ rỗng)
- [x] Cập nhật `.ai/ROADMAP.md`, `.ai/TASKS.md`, `.ai/AI_CONTEXT.md`

---

## In Progress

- [/] Chờ tiếp nhận tập file tài liệu thật từ người dùng / Phòng CTSV (`DATASET_STATUS = NOT_PROVIDED`)

---

## Blocked

- **TASK-105**: Tiếp nhận dữ liệu tài liệu CTSV thật
  - **Blocker**: Chưa có file tài liệu scan/ảnh chụp từ thực tế.
  - **Mitigation**: Khi có dữ liệu thật, chuyển sang Step 2.2 (Data Ingestion & Annotation).

- **ADR-002**: Text detection engine choice (PaddleOCR DBNet++ recommended)
- **ADR-008**: Frontend UI library choice (shadcn/ui recommended)

---

## Next Task

Khi nhận được dữ liệu thật từ người dùng:

1. Tiến hành **Step 2.2 — Data Ingestion & Preprocessing**:
   - Đưa file gốc vào `dataset/raw/`
   - Ghi bản ghi vào `dataset/metadata/inventory.json`
   - Convert trang ảnh sang `dataset/images/`
   - Tiến hành gán nhãn, cắt dòng và xuất `train/val/test` labels TSV.

---

## Important Decisions (Quick Reference)

| ADR | Decision | Status |
|-----|----------|--------|
| ADR-001 | VietOCR cho text recognition | ✅ Decided |
| ADR-002 | Text detection engine | ❓ TBD |
| ADR-003 | Celery + Redis cho async | ✅ Decided |
| ADR-004 | Elasticsearch 8.x | ✅ Decided |
| ADR-005 | Vietnamese ES analyzer | ❓ TBD (benchmark) |
| ADR-006 | MinIO cho file storage | ✅ Decided |
| ADR-007 | FastAPI framework | ✅ Decided |
| ADR-008 | Frontend UI library | ❓ TBD |
| ADR-009 | Frontend testing | ❓ TBD |
| ADR-010 | CI/CD platform | ❓ TBD |

---

## Known Issues / Risks

| # | Issue | Severity | Mitigation |
|---|-------|----------|-----------|
| 1 | Dataset CTSV chưa thu thập được | HIGH | Fallback: dùng public dataset tiếng Việt |
| 2 | Text detection engine chưa quyết định | MEDIUM | ADR-002 cần user confirm |
| 3 | GPU availability cho training | MEDIUM | Dùng Google Colab hoặc CPU (chậm hơn) |
| 4 | VietOCR compatibility Python 3.11 | LOW | Cần kiểm tra khi setup môi trường |

---

## Project Quick Facts

```
Project: Student-Document-OCR
Domain:  Công tác sinh viên document management
Stack:   FastAPI + React + VietOCR + Elasticsearch + PostgreSQL + MinIO
Phase:   1.1 — Specification Freeze
Files:   99 files, 21 directories
```

---

## Rules for AI Agent (Quick Ref)

1. **Đọc file này đầu tiên** trước khi làm bất kỳ task nào
2. **Không viết source code** cho đến hết Phase 1
3. **Không thêm framework** ngoài TECH_STACK.md đã freeze
4. **Đánh dấu [TBD]** nếu chưa có đủ thông tin
5. **Cập nhật file này** sau mỗi task hoàn thành

---

## TODO

- [ ] Cập nhật "Completed" section sau mỗi task xong
- [ ] Cập nhật "Blocked" khi có unblock
- [ ] Cập nhật "In Progress" → "Completed" khi xong

## References

- .ai/TASKS.md
- .ai/ROADMAP.md
- .ai/DECISIONS.md
- .ai/PROJECT_SPEC.md
