# TECH_STACK — Công nghệ sử dụng

## Purpose

Xác định chính thức (freeze) toàn bộ công nghệ, framework và thư viện được sử dụng trong dự án.
Không thay đổi tech stack mà không có ADR trong DECISIONS.md.

## Scope

Bao gồm tất cả layer: AI/OCR, Backend, Frontend, Database, Search, Storage, Infrastructure, Testing.

---

## 1. AI / OCR Layer

| Thành phần | Công nghệ | Version | Ghi chú |
|-----------|-----------|---------|---------|
| **Deep Learning Framework** | PyTorch | ≥ 2.3.0 | CPU + GPU (optional) |
| **OCR Recognition Engine** | VietOCR | ≥ 0.3.0 | VGG + Transformer Seq2Seq |
| **OCR Text Detection** | [TBD] | — | Xem ADR-002 trong DECISIONS.md |
| **Image Processing** | OpenCV (cv2) | ≥ 4.9.0 | Preprocessing pipeline |
| **Image Processing** | Pillow | ≥ 10.3.0 | Format conversion |
| **PDF → Image** | pdf2image | ≥ 1.17.0 | Dùng poppler |
| **Training — Augmentation** | albumentations | ≥ 1.4.0 | Data augmentation |
| **Training — Monitoring** | TensorBoard | ≥ 2.17.0 | Loss/metric visualization |
| **Evaluation — Metrics** | python-Levenshtein | ≥ 0.25.0 | CER/WER calculation |

> **Quyết định cốt lõi**: VietOCR được chọn làm text recognition engine chính.
> VietOCR **KHÔNG** làm text detection. Text detection là bước riêng biệt (xem ADR-002).

---

## 2. Backend Layer

| Thành phần | Công nghệ | Version | Ghi chú |
|-----------|-----------|---------|---------|
| **Ngôn ngữ** | Python | 3.11 | |
| **Web Framework** | FastAPI | ≥ 0.111.0 | ASGI, async |
| **ASGI Server** | Uvicorn | ≥ 0.30.0 | Production: gunicorn + uvicorn workers |
| **Data Validation** | Pydantic v2 | ≥ 2.7.0 | Request/response schemas |
| **Config** | pydantic-settings | ≥ 2.3.0 | .env-based config |
| **ORM** | SQLAlchemy | ≥ 2.0.0 | Async (asyncpg driver) |
| **Migrations** | Alembic | ≥ 1.13.0 | Schema versioning |
| **DB Driver** | asyncpg | ≥ 0.29.0 | Async PostgreSQL |
| **Task Queue** | Celery | ≥ 5.4.0 | Async OCR processing |
| **Message Broker** | Redis | ≥ 7.0 | Celery broker + result backend |
| **HTTP Client** | httpx | ≥ 0.27.0 | Async HTTP client |
| **Auth** | python-jose | ≥ 3.3.0 | JWT encode/decode |
| **Password Hashing** | passlib[bcrypt] | ≥ 1.7.4 | bcrypt |
| **File Upload** | python-multipart | ≥ 0.0.9 | FastAPI file upload |
| **Object Storage Client** | minio | ≥ 7.2.0 | MinIO Python SDK |
| **ES Client** | elasticsearch[async] | ≥ 8.12.0 | Elasticsearch 8.x Python client |
| **Logging** | loguru | ≥ 0.7.0 | Structured logging |
| **Utilities** | tenacity | ≥ 8.3.0 | Retry logic |

---

## 3. Frontend Layer

| Thành phần | Công nghệ | Version | Ghi chú |
|-----------|-----------|---------|---------|
| **Ngôn ngữ** | TypeScript | ≥ 5.4 | |
| **Framework** | React | ≥ 18.3 | |
| **Build Tool** | Vite | ≥ 5.2 | HMR, ESM |
| **Routing** | React Router | v6 | |
| **Server State** | TanStack Query | ≥ 5.0 | API cache, pagination |
| **Client State** | Zustand | ≥ 4.5 | Auth store, UI state |
| **Forms** | React Hook Form | ≥ 7.51 | |
| **Validation** | Zod | ≥ 3.23 | Schema validation |
| **HTTP Client** | Axios | ≥ 1.7 | JWT interceptor |
| **UI Library** | [TBD] | — | Xem ADR-008 trong DECISIONS.md |
| **Frontend Testing** | [TBD] | — | Xem ADR-009 trong DECISIONS.md |

---

## 4. Database Layer

| Thành phần | Công nghệ | Version | Ghi chú |
|-----------|-----------|---------|---------|
| **Relational DB** | PostgreSQL | 15 | Primary data store |
| **Search Engine** | Elasticsearch | 8.12.0 | Full-text search |
| **Cache / Queue** | Redis | 7-alpine | Celery broker + cache |
| **Object Storage** | MinIO | latest | S3-compatible, file storage |

---

## 5. Infrastructure Layer

| Thành phần | Công nghệ | Version | Ghi chú |
|-----------|-----------|---------|---------|
| **Containerization** | Docker | ≥ 25.0 | |
| **Orchestration** | Docker Compose | v2 | Development + Production |
| **Reverse Proxy** | Nginx | 1.25-alpine | Production only |
| **CI/CD** | [TBD] | — | Xem ADR-010 |

---

## 6. Testing Layer

| Thành phần | Công nghệ | Version | Ghi chú |
|-----------|-----------|---------|---------|
| **Backend Test Runner** | pytest | ≥ 8.2.0 | |
| **Async Test Support** | pytest-asyncio | ≥ 0.23.0 | |
| **Coverage** | pytest-cov | ≥ 5.0.0 | Target: ≥ 70% |
| **API Test Client** | httpx (AsyncClient) | ≥ 0.27.0 | FastAPI test client |
| **Mocking** | pytest-mock | ≥ 3.14.0 | |
| **Load Testing** | Locust | ≥ 2.29.0 | Performance benchmark |
| **Frontend Testing** | [TBD] | — | Xem ADR-009 |

---

## 7. Code Quality

| Thành phần | Công nghệ | Ghi chú |
|-----------|-----------|---------|
| **Linter + Formatter** | Ruff | Thay thế flake8, black, isort |
| **Type Checker** | mypy | Dần kích hoạt strict mode |
| **Pre-commit** | pre-commit | Chạy ruff + mypy trước commit |
| **Editor Config** | .editorconfig | UTF-8, LF, 4-space indent |

---

## 8. Version Lock Policy

- **Python packages**: Được pin trong `pyproject.toml` và `requirements.txt`
- **Docker images**: Dùng digest hoặc minor version tag (không dùng `latest` trong production)
- **Frontend packages**: Được lock bởi `package-lock.json` hoặc `pnpm-lock.yaml`
- **Thay đổi tech stack**: Bắt buộc tạo ADR trong `DECISIONS.md`

---

## TODO

- [ ] Quyết định text detection engine (ADR-002)
- [ ] Quyết định frontend UI library (ADR-008)
- [ ] Quyết định frontend testing framework (ADR-009)
- [ ] Quyết định CI/CD platform (ADR-010)
- [ ] Pin exact versions sau khi setup môi trường lần đầu
- [ ] Kiểm tra compatibility PyTorch ↔ VietOCR trên Python 3.11

## References

- .ai/DECISIONS.md
- pyproject.toml
- requirements.txt
- .ai/PROJECT_SPEC.md
