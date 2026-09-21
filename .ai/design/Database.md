# Database — Chi tiết Schema & Mapping Vật lý

## Purpose

Tài liệu mô tả chi tiết thiết kế Cơ sở dữ liệu Vật lý (Physical Data Schema) trên PostgreSQL 15 cho hệ thống Student-Document-OCR, chuyển đổi từ ERD Logical Model sang các câu lệnh DDL / SQLAlchemy Models.

## Scope

Tất cả 9 bảng: `roles`, `users`, `document_categories`, `documents`, `ocr_results`, `document_metadata`, `processing_jobs`, `search_history`, `audit_logs`.

---

## 1. Quy ước Thiết kế Database

- **Database Engine**: PostgreSQL 15+
- **Naming Convention**: Tên bảng dùng số nhiều, chữ thường, gạch dưới (snake_case) (vd: `documents`, `ocr_results`).
- **Primary Keys**: Dùng kiểu dữ liệu `UUID` (`uuid_generate_v4()`) để tránh suy đoán ID ngẫu nhiên.
- **Timestamps**: Tất cả các bảng đều có `created_at` (TIMESTAMP WITH TIME ZONE, default `NOW()`). Các bảng hỗ trợ sửa đổi có `updated_at`.
- **Foreign Keys**: Luôn có ràng buộc FK rõ ràng với On Delete action phù hợp (`RESTRICT` hoặc `CASCADE`).
- **Indexes**: Đánh Index trên các cột thường xuyên query/filter: `username`, `email`, `uploaded_by`, `category_id`, `ocr_status`, `is_deleted`, `created_at`.

---

## 2. Chi tiết Định nghĩa các Bảng (Physical DDL Spec)

### 2.1 Bảng `roles`

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | UUID | PK, DEFAULT uuid_generate_v4() | Khóa chính |
| `name` | VARCHAR(50) | UNIQUE, NOT NULL | Tên vai trò (`ADMIN`, `STAFF`) |
| `description` | TEXT | NULLABLE | Mô tả quyền hạn |
| `created_at` | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | Ngày tạo |

### 2.2 Bảng `users`

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | UUID | PK, DEFAULT uuid_generate_v4() | Khóa chính |
| `username` | VARCHAR(50) | UNIQUE, NOT NULL, INDEX | Tên đăng nhập |
| `email` | VARCHAR(255) | UNIQUE, NOT NULL, INDEX | Email |
| `hashed_password` | VARCHAR(255) | NOT NULL | Mật khẩu mã hóa bcrypt |
| `full_name` | VARCHAR(255) | NOT NULL | Tên đầy đủ |
| `role_id` | UUID | FK -> roles(id), NOT NULL | Khóa ngoại vai trò |
| `is_active` | BOOLEAN | NOT NULL, DEFAULT TRUE | Trạng thái tài khoản |
| `last_login_at` | TIMESTAMPTZ | NULLABLE | Lần đăng nhập gần nhất |
| `created_at` | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | ngày tạo |
| `updated_at` | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | Ngày cập nhật |

### 2.3 Bảng `document_categories`

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | UUID | PK, DEFAULT uuid_generate_v4() | Khóa chính |
| `name` | VARCHAR(100) | UNIQUE, NOT NULL | Tên hiển thị danh mục |
| `code` | VARCHAR(50) | UNIQUE, NOT NULL | Mã code (vd: `DON_NGHI_HOC`) |
| `description` | TEXT | NULLABLE | Mô tả chi tiết |
| `is_active` | BOOLEAN | NOT NULL, DEFAULT TRUE | Trạng thái hiển thị |
| `created_at` | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | Ngày tạo |

### 2.4 Bảng `documents`

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | UUID | PK, DEFAULT uuid_generate_v4() | Khóa chính |
| `title` | VARCHAR(500) | NOT NULL | Tiêu đề văn bản |
| `original_filename` | VARCHAR(255) | NOT NULL | Tên file gốc khi upload |
| `file_type` | VARCHAR(10) | NOT NULL | Định dạng (`PDF`, `JPG`, `PNG`, `TIFF`) |
| `file_size_bytes` | BIGINT | NOT NULL | Dung lượng file (Bytes) |
| `minio_object_key` | VARCHAR(1000) | UNIQUE, NOT NULL | Đường dẫn object trên MinIO |
| `page_count` | INTEGER | NULLABLE | Số trang của tài liệu |
| `category_id` | UUID | FK -> document_categories(id), NULLABLE | Danh mục tài liệu |
| `uploaded_by` | UUID | FK -> users(id), NOT NULL, INDEX | Người upload |
| `ocr_status` | VARCHAR(20) | NOT NULL, DEFAULT 'PENDING', INDEX | Trạng thái OCR |
| `is_deleted` | BOOLEAN | NOT NULL, DEFAULT FALSE, INDEX | Đánh dấu xóa mềm |
| `deleted_by` | UUID | FK -> users(id), NULLABLE | Người thực hiện xóa |
| `deleted_at` | TIMESTAMPTZ | NULLABLE | Thời điểm xóa |
| `created_at` | TIMESTAMPTZ | NOT NULL, DEFAULT NOW(), INDEX | Thời điểm upload |
| `updated_at` | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | Thời điểm cập nhật |

### 2.5 Bảng `ocr_results`

> **Quan hệ: 1 Document → NHIỀU OCRResult** (không phải 1:1).
> Một tài liệu có thể được chạy OCR nhiều lần (fine-tune model mới, thử engine khác).
> Dùng cột `is_latest = true` để backend lấy kết quả mới nhất mà không cần quét toàn bộ lịch sử.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | UUID | PK, DEFAULT uuid_generate_v4() | Khóa chính |
| `document_id` | UUID | FK -> documents(id) ON DELETE CASCADE, NOT NULL, INDEX | Khóa ngoại N:1 với Document (**không UNIQUE**) |
| `is_latest` | BOOLEAN | NOT NULL, DEFAULT TRUE, INDEX | Đánh dấu kết quả OCR mới nhất của document này. Khi insert kết quả mới, backend phải set `is_latest=false` cho tất cả bản ghi cũ cùng `document_id`. |
| `raw_text` | TEXT | NULLABLE | Văn bản OCR gốc chưa sửa |
| `corrected_text` | TEXT | NULLABLE | Văn bản sau khi người dùng sửa |
| `confidence_score` | FLOAT | NULLABLE | Điểm độ tin cậy OCR (0.0 - 1.0) |
| `ocr_engine` | VARCHAR(50) | NOT NULL | Engine OCR (vd: `vietocr`) |
| `ocr_engine_version` | VARCHAR(20) | NULLABLE | Phiên bản engine |
| `page_texts` | JSONB | NULLABLE | Mảng text từng trang `[{"page":1,"text":"..."}]` |
| `processing_time_ms` | INTEGER | NULLABLE | Thời gian xử lý OCR (ms) |
| `is_corrected` | BOOLEAN | NOT NULL, DEFAULT FALSE | Đã chỉnh sửa thủ công chưa |
| `corrected_by` | UUID | FK -> users(id), NULLABLE | Người sửa |
| `corrected_at` | TIMESTAMPTZ | NULLABLE | Thời điểm sửa |
| `created_at` | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | Ngày tạo |
| `updated_at` | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | Ngày cập nhật |

### 2.6 Bảng `document_metadata`

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | UUID | PK, DEFAULT uuid_generate_v4() | Khóa chính |
| `document_id` | UUID | FK -> documents(id) ON DELETE CASCADE, UNIQUE, NOT NULL | Khóa ngoại 1:1 với Document |
| `student_id` | VARCHAR(20) | NULLABLE, INDEX | Mã số sinh viên (MSSV) |
| `student_name` | VARCHAR(255) | NULLABLE | Họ tên sinh viên |
| `document_date` | DATE | NULLABLE | Ngày ghi trên đơn |
| `document_number` | VARCHAR(100) | NULLABLE | Số hiệu văn bản |
| `extra` | JSONB | NULLABLE | Dữ liệu metadata bổ sung |
| `created_at` | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | Ngày tạo |
| `updated_at` | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | Ngày cập nhật |

### 2.7 Bảng `processing_jobs`

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | UUID | PK, DEFAULT uuid_generate_v4() | Khóa chính |
| `document_id` | UUID | FK -> documents(id) ON DELETE CASCADE, NOT NULL | Tài liệu đang xử lý |
| `celery_task_id` | VARCHAR(255) | UNIQUE, NULLABLE | Task ID từ Celery Worker |
| `status` | VARCHAR(20) | NOT NULL, DEFAULT 'PENDING' | Trạng thái Job |
| `error_message` | TEXT | NULLABLE | Thông báo lỗi khi FAILED |
| `retry_count` | INTEGER | NOT NULL, DEFAULT 0 | Số lần đã retry |
| `started_at` | TIMESTAMPTZ | NULLABLE | Thời điểm bắt đầu chạy |
| `completed_at` | TIMESTAMPTZ | NULLABLE | Thời điểm hoàn thành |
| `created_at` | TIMESTAMPTZ | NOT NULL, DEFAULT NOW() | Ngày tạo |

### 2.8 Bảng `search_history`

> Lưu lịch sử truy vấn tìm kiếm của người dùng — dùng cho thống kê từ khóa phổ biến và gợi ý tìm kiếm.
> Đây là bảng **append-only**, không có UPDATE, không có soft-delete.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | UUID | PK, DEFAULT uuid_generate_v4() | Khóa chính |
| `user_id` | UUID | FK -> users(id) ON DELETE SET NULL, NULLABLE, INDEX | Người thực hiện tìm kiếm (NULL nếu anonymous) |
| `keyword` | TEXT | NOT NULL | Từ khóa tìm kiếm |
| `filter` | JSONB | NULLABLE | Bộ lọc đi kèm (category, date range, v.v.) |
| `result_count` | INTEGER | NULLABLE | Số kết quả trả về (để phân tích zero-result queries) |
| `created_at` | TIMESTAMPTZ | NOT NULL, DEFAULT NOW(), INDEX | Thời điểm tìm kiếm |

### 2.9 Bảng `audit_logs`

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | UUID | PK, DEFAULT uuid_generate_v4() | Khóa chính |
| `user_id` | UUID | FK -> users(id), NULLABLE, INDEX | Người thực hiện hành động |
| `action` | VARCHAR(50) | NOT NULL, INDEX | Hành động (`LOGIN`, `UPLOAD`, `DELETE`,...) |
| `resource_type` | VARCHAR(50) | NULLABLE | Tên loại tài nguyên |
| `resource_id` | UUID | NULLABLE | ID tài nguyên tác động |
| `detail` | JSONB | NULLABLE | Dữ liệu chi tiết bổ sung |
| `ip_address` | VARCHAR(45) | NULLABLE | Địa chỉ IP người dùng |
| `user_agent` | TEXT | NULLABLE | Trình duyệt/Thiết bị |
| `created_at` | TIMESTAMPTZ | NOT NULL, DEFAULT NOW(), INDEX | Thời điểm thực hiện |

---

## 3. Database Indexing Strategy (Tối ưu Query)

```sql
-- Indexes cho tìm kiếm và sắp xếp danh sách tài liệu
CREATE INDEX idx_documents_uploaded_by ON documents(uploaded_by);
CREATE INDEX idx_documents_category_id ON documents(category_id);
CREATE INDEX idx_documents_ocr_status ON documents(ocr_status);
CREATE INDEX idx_documents_created_at ON documents(created_at DESC);
CREATE INDEX idx_documents_is_deleted ON documents(is_deleted);

-- Index tra cứu MSSV nhanh
CREATE INDEX idx_document_metadata_student_id ON document_metadata(student_id);

-- Index ocr_results: lấy kết quả mới nhất theo document
CREATE INDEX idx_ocr_results_document_id ON ocr_results(document_id);
CREATE INDEX idx_ocr_results_is_latest ON ocr_results(document_id, is_latest) WHERE is_latest = true;

-- Index search_history
CREATE INDEX idx_search_history_user_id ON search_history(user_id);
CREATE INDEX idx_search_history_created_at ON search_history(created_at DESC);

-- Index lọc Audit Log
CREATE INDEX idx_audit_logs_user_action ON audit_logs(user_id, action);
CREATE INDEX idx_audit_logs_created_at ON audit_logs(created_at DESC);
```

---

## 4. Lưu ý Alembic — Driver URL

> **QUAN TRỌNG khi viết `alembic/env.py`:**
>
> - `DATABASE_URL` trong `.env` dùng scheme `postgresql+asyncpg://` cho FastAPI async engine.
> - Alembic mặc định chạy **sync** — cần URL riêng dùng driver `psycopg2`:
>   ```
>   ALEMBIC_DATABASE_URL=postgresql+psycopg2://ocr_user:CHANGE_ME@localhost:5432/ocr_db
>   ```
> - Trong `alembic/env.py`, dùng `ALEMBIC_DATABASE_URL` (nếu có) thay vì `DATABASE_URL`.
> - Hoặc dùng cách `run_sync` với async engine — nhưng URL riêng là đơn giản hơn.

## TODO

- [ ] Tạo file migration gốc bằng Alembic trong Phase 6 (`alembic revision --autogenerate -m "init_db"`).
- [ ] Viết script Seed Data dữ liệu mẫu cho danh mục và tài khoản Admin mặc định.
- [ ] Khi viết `alembic/env.py`, thêm `ALEMBIC_DATABASE_URL` vào `.env` dùng driver `psycopg2`.

## References

- ERD.md
- Architecture.md
- backend/Database.md
