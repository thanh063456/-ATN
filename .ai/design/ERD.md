# ERD — Entity Relationship Diagram (Logical Model)

## Purpose

Thiết kế logical data model cho hệ thống Student-Document-OCR.
Định nghĩa tất cả entities, attributes, relationships và constraints.
Đây là logical model — chưa phải physical SQL schema.

## Scope

9 entities: User, Role, Document, DocumentCategory, OCRResult,
DocumentMetadata, ProcessingJob, SearchHistory, AuditLog.

---

## 1. Entity Overview

```
┌─────────────┐     ┌────────────────┐     ┌─────────────────────┐
│    User     │────►│   Document     │────►│     OCRResult       │
│             │     │                │     │  (N per Document)   │
└─────┴───────┘     └───────┴────────┘     └─────────────────────┘
      │                     │
      │             ┌───────▼────────┐     ┌─────────────────────┐
      │             │DocumentCategory│     │  DocumentMetadata   │
      │             └────────────────┘     └─────────────────────┘
      │                     │
      │             ┌───────▼────────┐     ┌─────────────────────┐
      │             │ ProcessingJob  │     │     AuditLog        │
      │             │ (Celery task)  │     └─────────────────────┘
      │             └────────────────┘
      │
      ▼                                   ┌─────────────────────┐
┌─────────────┐                           │    SearchHistory    │
│    Role     │                           └─────────────────────┘
└─────────────┘
```

---

## 2. Entity: User

**Purpose:** Đại diện cho người dùng hệ thống (Administrator và Staff).

| Attribute | Type | Constraint | Mô tả |
|-----------|------|------------|-------|
| `id` | UUID | PK, NOT NULL | Primary key |
| `username` | VARCHAR(50) | UNIQUE, NOT NULL | Tên đăng nhập |
| `email` | VARCHAR(255) | UNIQUE, NOT NULL | Email |
| `hashed_password` | VARCHAR(255) | NOT NULL | bcrypt hash |
| `full_name` | VARCHAR(255) | NOT NULL | Tên đầy đủ |
| `role_id` | UUID | FK → Role.id, NOT NULL | Phân quyền |
| `is_active` | BOOLEAN | DEFAULT TRUE | Tài khoản active/inactive |
| `last_login_at` | TIMESTAMP | NULLABLE | Lần đăng nhập cuối |
| `created_at` | TIMESTAMP | NOT NULL, DEFAULT NOW() | |
| `updated_at` | TIMESTAMP | NOT NULL | |

**Relationships:**
- `User` N:1 `Role` (mỗi user có 1 role)
- `User` 1:N `Document` (user upload nhiều documents)
- `User` 1:N `AuditLog` (user thực hiện nhiều actions)

---

## 3. Entity: Role

**Purpose:** Phân quyền người dùng trong hệ thống.

| Attribute | Type | Constraint | Mô tả |
|-----------|------|------------|-------|
| `id` | UUID | PK, NOT NULL | Primary key |
| `name` | VARCHAR(50) | UNIQUE, NOT NULL | `ADMIN`, `STAFF` |
| `description` | TEXT | NULLABLE | Mô tả quyền hạn |
| `created_at` | TIMESTAMP | NOT NULL | |

**Seed data:**
- `{ name: "ADMIN", description: "Quản trị viên hệ thống" }`
- `{ name: "STAFF", description: "Cán bộ Công tác sinh viên" }`

**Relationships:**
- `Role` 1:N `User`

---

## 4. Entity: DocumentCategory

**Purpose:** Phân loại tài liệu theo nghiệp vụ CTSV.

| Attribute | Type | Constraint | Mô tả |
|-----------|------|------------|-------|
| `id` | UUID | PK, NOT NULL | Primary key |
| `name` | VARCHAR(100) | UNIQUE, NOT NULL | Ví dụ: "Đơn xin nghỉ học", "Biên bản kỷ luật" |
| `code` | VARCHAR(20) | UNIQUE, NOT NULL | Ví dụ: `DON_NGHI_HOC`, `BIEN_BAN_KY_LUAT` |
| `description` | TEXT | NULLABLE | Mô tả loại tài liệu |
| `is_active` | BOOLEAN | DEFAULT TRUE | |
| `created_at` | TIMESTAMP | NOT NULL | |

**Seed data (ví dụ):**
- `DON_NGHI_HOC` — Đơn xin nghỉ học tạm thời
- `DON_BAO_LUU` — Đơn xin bảo lưu kết quả học tập
- `HOC_BONG` — Hồ sơ học bổng
- `KY_LUAT` — Biên bản kỷ luật sinh viên
- `CHUNG_NHAN` — Giấy chứng nhận sinh hoạt
- `OTHER` — Khác

**Relationships:**
- `DocumentCategory` 1:N `Document`

---

## 5. Entity: Document

**Purpose:** Đại diện cho một tài liệu được upload vào hệ thống.

| Attribute | Type | Constraint | Mô tả |
|-----------|------|------------|-------|
| `id` | UUID | PK, NOT NULL | Primary key |
| `title` | VARCHAR(500) | NOT NULL | Tiêu đề tài liệu (user nhập hoặc tự động) |
| `original_filename` | VARCHAR(255) | NOT NULL | Tên file gốc khi upload |
| `file_type` | VARCHAR(10) | NOT NULL | `PDF`, `JPG`, `PNG`, `TIFF` |
| `file_size_bytes` | BIGINT | NOT NULL | Kích thước file |
| `minio_object_key` | VARCHAR(1000) | UNIQUE, NOT NULL | Path trong MinIO bucket |
| `page_count` | INTEGER | NULLABLE | Số trang (điền sau khi xử lý) |
| `category_id` | UUID | FK → DocumentCategory.id, NULLABLE | |
| `uploaded_by` | UUID | FK → User.id, NOT NULL | |
| `ocr_status` | VARCHAR(20) | NOT NULL, DEFAULT 'PENDING' | `PENDING`, `PROCESSING`, `DONE`, `FAILED` |
| `is_deleted` | BOOLEAN | DEFAULT FALSE | Soft delete |
| `deleted_by` | UUID | FK → User.id, NULLABLE | |
| `deleted_at` | TIMESTAMP | NULLABLE | |
| `created_at` | TIMESTAMP | NOT NULL | Thời điểm upload |
| `updated_at` | TIMESTAMP | NOT NULL | |

**Relationships:**
- `Document` N:1 `User` (uploaded_by)
- `Document` N:1 `DocumentCategory`
- `Document` 1:N `OCRResult`
- `Document` 1:1 `DocumentMetadata`
- `Document` 1:N `ProcessingJob`

---

## 6. Entity: OCRResult

**Purpose:** Lưu kết quả OCR của một document. Một document có thể có nhiều OCRResult từ các lần chạy khác nhau.

| Attribute | Type | Constraint | Mô tả |
|-----------|------|------------|-------|
| `id` | UUID | PK, NOT NULL | Primary key |
| `document_id` | UUID | FK → Document.id, NOT NULL | Khóa ngoại N:1 |
| `is_latest` | BOOLEAN | NOT NULL, DEFAULT TRUE | `true` = kết quả OCR mới nhất |
| `raw_text` | TEXT | NULLABLE | Văn bản OCR gốc |
| `corrected_text` | TEXT | NULLABLE | Văn bản đã chỉnh sửa |
| `confidence_score` | FLOAT | NULLABLE | Điểm confidence (0.0–1.0) |
| `ocr_engine` | VARCHAR(50) | NOT NULL | `vietocr`, `paddleocr`, etc |
| `ocr_engine_version` | VARCHAR(20) | NULLABLE | Version |
| `page_texts` | JSONB | NULLABLE | Text theo từng trang |
| `processing_time_ms` | INTEGER | NULLABLE | Thời gian xử lý (ms) |
| `is_corrected` | BOOLEAN | DEFAULT FALSE | |
| `corrected_by` | UUID | FK → User.id, NULLABLE | |
| `corrected_at` | TIMESTAMP | NULLABLE | |
| `created_at` | TIMESTAMP | NOT NULL | |
| `updated_at` | TIMESTAMP | NOT NULL | |

**Relationships:**
- `OCRResult` N:1 `Document`

---

## 7. Entity: DocumentMetadata

**Purpose:** Lưu metadata được extract từ nội dung OCR (rule-based).

| Attribute | Type | Constraint | Mô tả |
|-----------|------|------------|-------|
| `id` | UUID | PK, NOT NULL | Primary key |
| `document_id` | UUID | FK → Document.id, UNIQUE, NOT NULL | 1:1 với Document |
| `student_id` | VARCHAR(20) | NULLABLE | MSSV nếu extract được |
| `student_name` | VARCHAR(255) | NULLABLE | Tên sinh viên |
| `document_date` | DATE | NULLABLE | Ngày trong tài liệu |
| `document_number` | VARCHAR(100) | NULLABLE | Số văn bản |
| `extra` | JSONB | NULLABLE | Các metadata khác (flexible) |
| `created_at` | TIMESTAMP | NOT NULL | |
| `updated_at` | TIMESTAMP | NOT NULL | |

**Relationships:**
- `DocumentMetadata` 1:1 `Document`

---

## 8. Entity: SearchHistory

**Purpose:** Lưu lịch sử truy vấn tìm kiếm của người dùng.

| Attribute | Type | Constraint | Mô tả |
|-----------|------|------------|-------|
| `id` | UUID | PK, NOT NULL | Primary key |
| `user_id` | UUID | FK → User.id, NULLABLE | NULL nếu anonymous |
| `keyword` | TEXT | NOT NULL | Từ khóa tìm kiếm |
| `filter` | JSONB | NULLABLE | Bộ lọc đi kèm |
| `result_count` | INTEGER | NULLABLE | Số kết quả trả về |
| `created_at` | TIMESTAMP | NOT NULL | Thời điểm tìm kiếm |

**Relationships:**
- `SearchHistory` N:1 `User`

---

## 9. Entity: ProcessingJob

**Purpose:** Tracking Celery task cho OCR processing.

| Attribute | Type | Constraint | Mô tả |
|-----------|------|------------|-------|
| `id` | UUID | PK, NOT NULL | Primary key |
| `document_id` | UUID | FK → Document.id, NOT NULL | |
| `celery_task_id` | VARCHAR(255) | UNIQUE, NULLABLE | Celery task UUID |
| `status` | VARCHAR(20) | NOT NULL | `PENDING`, `PROCESSING`, `DONE`, `FAILED` |
| `error_message` | TEXT | NULLABLE | Nếu FAILED |
| `retry_count` | INTEGER | DEFAULT 0 | Số lần retry |
| `started_at` | TIMESTAMP | NULLABLE | |
| `completed_at` | TIMESTAMP | NULLABLE | |
| `created_at` | TIMESTAMP | NOT NULL | |

**Relationships:**
- `ProcessingJob` N:1 `Document`

---

## 9. Entity: AuditLog

**Purpose:** Ghi lại lịch sử thao tác của người dùng (immutable).

| Attribute | Type | Constraint | Mô tả |
|-----------|------|------------|-------|
| `id` | UUID | PK, NOT NULL | Primary key |
| `user_id` | UUID | FK → User.id, NULLABLE | NULL nếu system action |
| `action` | VARCHAR(50) | NOT NULL | `LOGIN`, `LOGOUT`, `UPLOAD`, `DELETE`, `EDIT_OCR`, `SEARCH` |
| `resource_type` | VARCHAR(50) | NULLABLE | `Document`, `User`, `OCRResult` |
| `resource_id` | UUID | NULLABLE | ID của resource bị tác động |
| `detail` | JSONB | NULLABLE | Chi tiết thêm |
| `ip_address` | VARCHAR(45) | NULLABLE | IPv4 hoặc IPv6 |
| `user_agent` | TEXT | NULLABLE | |
| `created_at` | TIMESTAMP | NOT NULL | |

**Relationships:**
- `AuditLog` N:1 `User`

**Note:** AuditLog là **append-only** — không có UPDATE, không có soft delete.

---

## 10. Relationships Summary

```
Role ──◄ User >──────── Document >──── OCRResult (1:N, is_latest flag)
                  │                    Document >──── DocumentMetadata (1:1)
                  │                    Document >──── ProcessingJob (1:N)
                  │
User >────────────────────────────── AuditLog (1:N)
User >────────────────────────────── SearchHistory (1:N)

DocumentCategory ──◄ Document
```

---

## 11. Elasticsearch Document Schema

*(Không phải SQL — đây là ES index mapping, lưu ở đây để tham chiếu)*

```json
{
  "document_id": "uuid",
  "title": "text (analyzed)",
  "content": "text (analyzed, Vietnamese)",
  "category": "keyword",
  "student_id": "keyword",
  "student_name": "text",
  "document_date": "date",
  "uploader_id": "keyword",
  "ocr_status": "keyword",
  "created_at": "date",
  "is_deleted": "boolean"
}
```

---

## TODO

- [ ] Review ERD với GVHD
- [ ] Xác nhận DocumentMetadata fields với Phòng CTSV (field nào thực tế cần)
- [ ] Quyết định JSONB vs normalized table cho page_texts
- [ ] Vẽ ERD diagram bằng dbdiagram.io (export PNG nhúng vào đây)
- [ ] Chuyển sang design/Database.md cho mapping chi tiết từng field
- [ ] Tạo Alembic migrations trong Phase 6

## References

- .ai/design/Database.md
- .ai/design/Architecture.md
- .ai/DECISIONS.md
- backend/Database.md
