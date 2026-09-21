# Tests — Chiến lược kiểm thử

## Purpose

Tổng quan và hướng dẫn toàn bộ chiến lược testing của dự án Student-Document-OCR:
test pyramid, conventions, cách chạy, tools và coverage targets.

## Scope

Theo **Test Pyramid**:

```
        [E2E / Performance]  10%  → tests/PerformanceTest.md
       [Integration Tests]   20%  → tests/IntegrationTest.md
      [Unit Tests]           70%  → tests/UnitTest.md
     ─────────────────────────
     Target coverage: >= 80%
```

| File | Loại test | Tool |
|------|-----------|------|
| `UnitTest.md` | Unit tests (service, repo, schema) | pytest + pytest-mock |
| `IntegrationTest.md` | API endpoint tests | httpx.AsyncClient |
| `PerformanceTest.md` | Load test, latency benchmark | Locust |
| `OCRTest.md` | OCR accuracy tests (CER/WER) | pytest + custom metrics |

## Cấu trúc thư mục tests/ (planned)

```
tests/
├── conftest.py           # Shared fixtures: db session, async client, test user
├── unit/
│   ├── test_auth_service.py
│   ├── test_document_service.py
│   ├── test_ocr_service.py
│   └── test_search_service.py
├── integration/
│   ├── test_auth_api.py
│   ├── test_documents_api.py
│   └── test_search_api.py
├── performance/
│   └── locustfile.py
└── ocr/
    ├── test_ocr_accuracy.py
    └── test_data/        # Ground truth samples
```

## Chạy tests

```bash
# Tất cả tests
make test

# Unit tests only
make test-unit

# Integration tests (cần Docker stack running)
make test-integration

# OCR accuracy tests
make test-ocr

# Coverage report
pytest --cov=backend/app --cov-report=html
open htmlcov/index.html
```

## TODO

- [ ] Viết `conftest.py` với fixtures: `db_session`, `async_client`, `test_user`, `auth_headers`
- [ ] Implement test database strategy (PostgreSQL test DB, teardown sau mỗi test)
- [ ] Viết unit tests cho AuthService, DocumentService, OCRService
- [ ] Viết integration tests cho tất cả API endpoints
- [ ] Viết OCR accuracy tests với ground truth samples
- [ ] Setup CI: pytest chạy tự động trên GitHub Actions
- [ ] Đạt coverage >= 80% cho `backend/app/services/`

## References

- UnitTest.md
- IntegrationTest.md
- PerformanceTest.md
- OCRTest.md
- backend/Testing.md
- pyproject.toml (pytest config)
