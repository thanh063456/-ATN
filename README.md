# Student-Document-OCR

> **Đề tài**: Xây dựng hệ thống số hóa và quản lý tài liệu Công tác sinh viên ứng dụng OCR và Elasticsearch

## Giới thiệu

Hệ thống cho phép tự động số hóa (OCR) các tài liệu giấy của Phòng Công tác sinh viên, lưu trữ, phân loại
và tìm kiếm full-text toàn văn bản trên Elasticsearch.

**Vấn đề giải quyết:**  
Tài liệu CTSV hiện lưu trữ dạng giấy → khó tra cứu, dễ thất lạc, tốn thời gian xử lý thủ công.

**Giải pháp:**  
Upload ảnh/PDF → OCR tự động (VietOCR/PaddleOCR) → Elasticsearch full-text search → giao diện web quản lý.

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend API | FastAPI, SQLAlchemy, Alembic, Celery |
| OCR Engine | VietOCR / PaddleOCR |
| Search | Elasticsearch 8.x |
| Storage | MinIO (S3-compatible) |
| Database | PostgreSQL 15 |
| Cache / Queue | Redis 7 |
| Frontend | React + Vite |
| Infra | Docker Compose |

---

## Cấu trúc dự án

```
ĐATN/
├── .ai/                  # AI engineering context (specs, roadmap, design docs)
│   ├── research/         # Nghiên cứu: OCR, Elasticsearch, dataset
│   ├── design/           # Thiết kế: SRS, ERD, API, UI, Security
│   └── prompts/          # AI prompt library (Phase01–Phase06)
├── backend/              # FastAPI backend service
├── frontend/             # React + Vite frontend
├── training/             # OCR model training pipeline
├── dataset/              # Training & test dataset (managed via DVC)
├── models/               # Trained model checkpoints
├── notebooks/            # Jupyter research notebooks
├── docker/               # Docker configuration docs
├── deployments/          # Deployment configs (nginx, CI/CD)
├── docs/                 # Project documentation (proposal, meeting notes, report)
├── scripts/              # Utility scripts (dataset, training, deploy)
├── tests/                # Test suites
├── docker-compose.yml    # Full stack orchestration
├── pyproject.toml        # Python project config
├── Makefile              # Developer shortcuts
└── requirements.txt      # Python dependencies
```

---

## Quickstart

```bash
# 1. Clone và setup environment
git clone <repo-url> && cd ĐATN
cp .env.example .env          # Điền các giá trị cần thiết

# 2. Khởi động toàn bộ stack
make docker-up                # Hoặc: docker compose up -d

# 3. Chạy migrations
make migrate

# 4. Xem logs
make docker-logs
```

> **Lưu ý**: Xem chi tiết tại [`backend/README.md`](backend/README.md) và [`docker/README.md`](docker/README.md).

---

## Roadmap

| Phase | Nội dung | Trạng thái |
|-------|----------|-----------|
| Phase 1 | Research & Environment Setup | 🔲 Todo |
| Phase 2 | Data Collection & Model Training | 🔲 Todo |
| Phase 3 | Backend API Development | 🔲 Todo |
| Phase 4 | Frontend Development | 🔲 Todo |
| Phase 5 | Integration & Testing | 🔲 Todo |
| Phase 6 | Evaluation & Report | 🔲 Todo |

Xem chi tiết: [`.ai/ROADMAP.md`](.ai/ROADMAP.md)

---

## Tài liệu kỹ thuật

| Tài liệu | Mô tả |
|----------|-------|
| [`.ai/PROJECT_SPEC.md`](.ai/PROJECT_SPEC.md) | Đặc tả dự án đầy đủ |
| [`.ai/ARCHITECTURE.md`](.ai/ARCHITECTURE.md) | Kiến trúc hệ thống |
| [`.ai/design/SRS.md`](.ai/design/SRS.md) | Software Requirements Specification |
| [`.ai/design/API.md`](.ai/design/API.md) | REST API Design |
| [`.ai/design/ERD.md`](.ai/design/ERD.md) | Entity Relationship Diagram |
| [`.ai/DECISIONS.md`](.ai/DECISIONS.md) | Architecture Decision Records |
| [`docs/Report.md`](docs/Report.md) | Báo cáo tốt nghiệp (outline) |

---

## AI Engineering

Dự án sử dụng AI-assisted development. Context và quy tắc cho coding agent:

- [`·ai/AGENTS.md`](.ai/AGENTS.md) — Quy tắc cho AI agent
- [`.ai/AI_CONTEXT.md`](.ai/AI_CONTEXT.md) — Context phiên làm việc hiện tại
- [`.ai/CODING_RULES.md`](.ai/CODING_RULES.md) — Coding convention

---

## License

[MIT](LICENSE) © 2026 Student-Document-OCR — Đồ án tốt nghiệp

---

## Purpose

Cung cấp thông tin tổng quan cho bất kỳ ai (developer, GVHD, reviewer) về dự án:
mục tiêu, tech stack, cấu trúc thư mục, cách chạy nhanh và các tài liệu liên quan.

## Scope

Toàn bộ hệ thống Student-Document-OCR bao gồm backend, frontend, OCR pipeline,
Elasticsearch search, Docker infrastructure và tài liệu thiết kế.

## TODO

- [ ] Thêm badge: CI/CD status, coverage, license, Python version
- [ ] Thêm screenshot/GIF demo giao diện sau khi có frontend
- [ ] Cập nhật bảng Roadmap khi thay đổi phase status
- [ ] Thêm hướng dẫn Contributing (nếu có collaborator)
- [ ] Thêm link demo video / deployment URL khi có production

## References

- .ai/PROJECT_SPEC.md
- .ai/ARCHITECTURE.md
- .ai/ROADMAP.md
- docs/Proposal.md
