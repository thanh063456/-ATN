# AGENTS.md — Hướng dẫn cho AI Coding Agent

## Purpose

Quy tắc và hướng dẫn cho AI coding agent khi làm việc trong dự án này.
Giúp agent hiểu context, convention và tránh lỗi phổ biến giữa các phiên làm việc.

## Scope

Áp dụng cho toàn bộ quá trình viết code, review, refactor và documentation
trong project Student-Document-OCR.

---

## 1. Đọc trước khi code

**LUÔN đọc các file sau trước khi tạo file mới liên quan đến kiến trúc hoặc schema:**

| File | Đọc khi nào |
|------|------------|
| `.ai/ARCHITECTURE.md` | Tạo service mới, thêm endpoint, thay đổi luồng dữ liệu |
| `.ai/design/Database.md` | Tạo model, schema, migration, query |
| `.ai/design/ERD.md` | Thiết kế quan hệ giữa các bảng |
| `.ai/DECISIONS.md` | Trước khi đề xuất thay đổi tech stack hoặc kiến trúc |
| `.ai/CODING_RULES.md` | Trước khi viết bất kỳ code Python/JS nào |

---

## 2. Nguyên tắc kiến trúc cốt lõi — KHÔNG được vi phạm

### (a) OCR luôn đọc file từ MinIO

```
✅ ĐÚNG:  Client upload → Backend lưu vào MinIO → OCR Worker lấy file từ MinIO → OCR
❌ SAI:   Client upload → OCR đọc file từ request body trực tiếp
❌ SAI:   Client upload → Backend pass file stream sang OCR service
```

OCR service (Celery task) nhận `minio_object_key`, tự lấy file từ MinIO.
Không bao giờ truyền file binary qua message queue hoặc HTTP call.

### (b) Backend chủ động index sang Elasticsearch

```
✅ ĐÚNG:  Backend gọi ES client → index document sau khi OCR xong
❌ SAI:   PostgreSQL trigger tự đẩy dữ liệu sang ES
❌ SAI:   Celery worker trực tiếp index ES (phải qua backend service)
```

Elasticsearch **không phải** bản sao tự động của PostgreSQL.
Chỉ backend (qua `SearchService` hoặc `DocumentService`) mới được gọi ES client để index/update/delete.

### (c) Luồng upload chuẩn

```
1. Client POST /documents/upload (multipart/form-data)
2. Backend validate file (type, size, checksum)
3. Backend upload file lên MinIO → nhận minio_object_key
4. Backend tạo Document record trong PostgreSQL (status=PENDING)
5. Backend enqueue Celery task (ocr_task) với document_id
6. Backend trả về 202 Accepted + document_id cho client
7. [Async] Celery worker lấy file từ MinIO → chạy OCR
8. [Async] Celery worker lưu OCRResult vào PostgreSQL (is_latest=true)
9. [Async] Celery worker update Document.ocr_status = DONE
10. [Async] Backend index document sang ES (trigger từ Celery task result)
```

---

## 3. Quy tắc đồng bộ Schema

**Sau khi thêm bảng mới hoặc sửa schema:**

- [ ] Cập nhật `.ai/design/Database.md` (physical schema)
- [ ] Cập nhật `.ai/design/ERD.md` (logical model + relationships summary)
- [ ] Tạo hoặc cập nhật SQLAlchemy model trong `backend/app/models/`
- [ ] Tạo Alembic migration: `alembic revision --autogenerate -m "describe_change"`
- [ ] Cập nhật Pydantic schemas trong `backend/app/schemas/` nếu có thay đổi API

---

## 4. OCRResult — Quy tắc is_latest

Khi insert OCRResult mới cho một document:

```python
# SAI — không làm thế này:
new_result = OCRResult(document_id=doc_id, is_latest=True, ...)
db.add(new_result)

# ĐÚNG — phải reset is_latest trước:
await db.execute(
    update(OCRResult)
    .where(OCRResult.document_id == doc_id)
    .values(is_latest=False)
)
new_result = OCRResult(document_id=doc_id, is_latest=True, ...)
db.add(new_result)
await db.commit()
```

Khi query OCRResult của một document, luôn filter `is_latest=True` trừ khi cần lịch sử:

```python
# Lấy kết quả mới nhất
result = await db.scalar(
    select(OCRResult)
    .where(OCRResult.document_id == doc_id, OCRResult.is_latest == True)
)
```

---

## 5. Lưu ý Alembic — Hai URL khác nhau

- `DATABASE_URL` (asyncpg) → dùng cho FastAPI async engine
- `ALEMBIC_DATABASE_URL` (psycopg2) → dùng trong `alembic/env.py` cho migration sync

Trong `alembic/env.py`:
```python
import os
from app.core.config import settings

# Dùng ALEMBIC_DATABASE_URL nếu có, fallback sang DATABASE_URL với psycopg2
alembic_url = os.getenv("ALEMBIC_DATABASE_URL") or settings.database_url.replace(
    "postgresql+asyncpg://", "postgresql+psycopg2://"
)
config.set_main_option("sqlalchemy.url", alembic_url)
```

---

## 6. Cấu trúc thư mục Backend

```
backend/
├── app/
│   ├── core/
│   │   ├── config.py         # Settings (pydantic-settings)
│   │   ├── database.py       # Async engine + session
│   │   ├── security.py       # JWT encode/decode
│   │   ├── exceptions.py     # AppException hierarchy
│   │   └── dependencies.py   # FastAPI Depends factories
│   ├── models/               # SQLAlchemy ORM models (1 file = 1 bảng)
│   ├── schemas/              # Pydantic schemas (Create/Update/Response)
│   ├── routers/              # FastAPI routers (1 file = 1 resource)
│   ├── services/             # Business logic (không import trực tiếp từ router)
│   ├── repositories/         # DB queries (optional layer, dùng nếu service phức tạp)
│   ├── worker/               # Celery app + tasks
│   └── main.py               # FastAPI app init, middleware, routers
├── alembic/
│   ├── versions/
│   └── env.py
├── tests/
│   ├── unit/
│   └── integration/
└── Dockerfile
```

---

## 7. Không làm

- ❌ Không import model trực tiếp vào router — đi qua service layer.
- ❌ Không hardcode URL, secret, credential trong code — dùng `settings`.
- ❌ Không dùng `SELECT *` trong raw SQL — luôn select cột cụ thể.
- ❌ Không commit code chưa có unit test cho service layer mới.
- ❌ Không thêm dependency mới vào `requirements.txt` mà không ghi ADR hoặc comment lý do.

---

## References

- `.ai/CODING_RULES.md`
- `.ai/TECH_STACK.md`
- `.ai/ARCHITECTURE.md`
- `.ai/design/Database.md`
- `.ai/DECISIONS.md`
