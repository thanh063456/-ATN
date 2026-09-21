# Backend — FastAPI Service

## Purpose

Backend API service của hệ thống Student-Document-OCR. Cung cấp REST API để:
upload tài liệu, trigger OCR, lưu trữ kết quả, tìm kiếm Elasticsearch và quản lý người dùng.

## Scope

FastAPI application chạy trên port 8000, bao gồm:

| Module | Công nghệ | Mô tả |
|--------|-----------|-------|
| Web Framework | FastAPI + Uvicorn | ASGI, auto OpenAPI docs |
| ORM | SQLAlchemy 2.0 async | Async database access |
| Migrations | Alembic | Schema version control |
| Auth | JWT + bcrypt | Access + Refresh tokens |
| Task Queue | Celery + Redis | Async OCR processing |
| OCR | VietOCR / PaddleOCR | Text recognition engine |
| Search | Elasticsearch 8.x | Full-text search, highlight |
| Storage | MinIO | Document file storage |
| Validation | Pydantic v2 | Request/response schemas |

## Cấu trúc thư mục (planned)

```
backend/
├── app/
│   ├── main.py           # FastAPI app factory
│   ├── config.py         # Settings (pydantic-settings)
│   ├── routers/          # API route handlers
│   │   ├── auth.py
│   │   ├── documents.py
│   │   ├── ocr.py
│   │   └── search.py
│   ├── services/         # Business logic layer
│   ├── repositories/     # Data access layer (Repository pattern)
│   ├── models/           # SQLAlchemy ORM models
│   ├── schemas/          # Pydantic request/response schemas
│   ├── core/             # Auth, security, dependencies
│   └── worker.py         # Celery app & tasks
├── alembic/              # Database migrations
├── tests/                # Backend unit & integration tests
├── Dockerfile
└── .dockerignore
```

## TODO

- [ ] Khởi tạo FastAPI project structure (`app/` folder)
- [ ] Cấu hình `app/config.py` với pydantic-settings
- [ ] Implement database models (SQLAlchemy): User, Document, OCRResult, ProcessingJob
- [ ] Setup Alembic + initial migration
- [ ] Implement JWT authentication router
- [ ] Implement Document upload endpoint (multipart/form-data → MinIO)
- [ ] Implement OCR service (sync + async Celery task)
- [ ] Implement Elasticsearch indexing service
- [ ] Implement Search router với highlight
- [ ] Viết Dockerfile (multi-stage, non-root user)
- [ ] Đạt test coverage >= 80%

## References

- Architecture.md
- FastAPI.md
- Repository.md
- Database.md
- Docker.md
- Testing.md
- .ai/design/API.md
- .ai/design/ERD.md
