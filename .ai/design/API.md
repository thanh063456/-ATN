# API — REST API Specification

## Purpose

Đặc tả chính thức toàn bộ REST API cho hệ thống Student-Document-OCR.
Đây là spec level — chưa phải implementation.

## Scope

7 nhóm endpoints: Authentication, Documents, OCR, Search, Metadata, Users, Administration.
Base URL: `/api/v1/`

---

## Quy ước chung

| Item | Convention |
|------|-----------|
| **Base URL** | `/api/v1/` |
| **Content-Type** | `application/json` (trừ file upload: `multipart/form-data`) |
| **Authentication** | `Authorization: Bearer <access_token>` |
| **Date format** | ISO 8601: `2026-08-08T07:30:00Z` |
| **ID format** | UUID v4 |
| **Pagination** | Query params: `page=1&page_size=20` |
| **Error format** | `{ "detail": "message", "code": "ERROR_CODE" }` |

### HTTP Status Codes

| Code | Meaning |
|------|---------|
| 200 | OK |
| 201 | Created |
| 202 | Accepted (async task dispatched) |
| 204 | No Content (delete) |
| 400 | Bad Request (validation error) |
| 401 | Unauthorized (no/invalid token) |
| 403 | Forbidden (insufficient role) |
| 404 | Not Found |
| 409 | Conflict (duplicate) |
| 422 | Unprocessable Entity (Pydantic error) |
| 500 | Internal Server Error |

---

## GROUP 1 — Authentication

### POST `/api/v1/auth/login`

| Field | Value |
|-------|-------|
| **Method** | POST |
| **Auth** | None (public) |
| **Purpose** | Đăng nhập, nhận access_token và refresh_token |

**Request Body:**
```json
{
  "username": "string",
  "password": "string"
}
```

**Response 200:**
```json
{
  "access_token": "string (JWT, 60min)",
  "refresh_token": "string (JWT, 7days)",
  "token_type": "bearer",
  "user": {
    "id": "uuid",
    "username": "string",
    "full_name": "string",
    "role": "ADMIN | STAFF"
  }
}
```

**Error cases:**
- `401` — Invalid credentials
- `403` — Account inactive

---

### POST `/api/v1/auth/refresh`

| Field | Value |
|-------|-------|
| **Method** | POST |
| **Auth** | None (uses refresh_token in body) |
| **Purpose** | Làm mới access_token |

**Request Body:**
```json
{ "refresh_token": "string" }
```

**Response 200:**
```json
{ "access_token": "string", "token_type": "bearer" }
```

**Error cases:**
- `401` — Invalid/expired refresh_token

---

### POST `/api/v1/auth/logout`

| Field | Value |
|-------|-------|
| **Method** | POST |
| **Auth** | Bearer token |
| **Purpose** | Đăng xuất, invalidate refresh_token |

**Request Body:**
```json
{ "refresh_token": "string" }
```

**Response 204:** No Content

---

### GET `/api/v1/auth/me`

| Field | Value |
|-------|-------|
| **Method** | GET |
| **Auth** | Bearer token |
| **Purpose** | Lấy thông tin user hiện tại |

**Response 200:**
```json
{
  "id": "uuid",
  "username": "string",
  "email": "string",
  "full_name": "string",
  "role": "ADMIN | STAFF",
  "is_active": true,
  "last_login_at": "datetime | null",
  "created_at": "datetime"
}
```

---

## GROUP 2 — Documents

### POST `/api/v1/documents`

| Field | Value |
|-------|-------|
| **Method** | POST |
| **Auth** | Bearer token (STAFF, ADMIN) |
| **Purpose** | Upload tài liệu mới |
| **Content-Type** | `multipart/form-data` |

**Request Form Data:**
```
file:        File (binary) — required, max 50MB, PDF/JPG/PNG/TIFF
title:       string — optional (default: filename)
category_id: uuid — optional
```

**Response 202 (Accepted):**
```json
{
  "id": "uuid",
  "title": "string",
  "original_filename": "string",
  "file_type": "PDF | JPG | PNG | TIFF",
  "file_size_bytes": 0,
  "ocr_status": "PENDING",
  "created_at": "datetime",
  "processing_job_id": "uuid"
}
```

**Error cases:**
- `400` — File type không hợp lệ
- `413` — File quá lớn (>50MB)
- `422` — Validation error

---

### GET `/api/v1/documents`

| Field | Value |
|-------|-------|
| **Method** | GET |
| **Auth** | Bearer token |
| **Purpose** | Danh sách tài liệu (paginated) |

**Query Params:**
```
page:        int = 1
page_size:   int = 20 (max 100)
category_id: uuid — filter
ocr_status:  PENDING | PROCESSING | DONE | FAILED — filter
sort_by:     created_at | title (default: created_at)
sort_order:  asc | desc (default: desc)
```

**Response 200:**
```json
{
  "items": [
    {
      "id": "uuid",
      "title": "string",
      "original_filename": "string",
      "file_type": "string",
      "file_size_bytes": 0,
      "ocr_status": "string",
      "category": { "id": "uuid", "name": "string", "code": "string" },
      "uploaded_by": { "id": "uuid", "full_name": "string" },
      "created_at": "datetime"
    }
  ],
  "total": 0,
  "page": 1,
  "page_size": 20,
  "pages": 0
}
```

---

### GET `/api/v1/documents/{document_id}`

| Field | Value |
|-------|-------|
| **Method** | GET |
| **Auth** | Bearer token |
| **Purpose** | Chi tiết một tài liệu |

**Response 200:**
```json
{
  "id": "uuid",
  "title": "string",
  "original_filename": "string",
  "file_type": "string",
  "file_size_bytes": 0,
  "page_count": 0,
  "ocr_status": "string",
  "category": { "id": "uuid", "name": "string" },
  "uploaded_by": { "id": "uuid", "full_name": "string" },
  "ocr_result": {
    "id": "uuid",
    "raw_text": "string | null",
    "corrected_text": "string | null",
    "confidence_score": 0.95,
    "ocr_engine": "vietocr",
    "is_corrected": false,
    "processing_time_ms": 0
  },
  "metadata": {
    "student_id": "string | null",
    "student_name": "string | null",
    "document_date": "date | null",
    "document_number": "string | null"
  },
  "created_at": "datetime",
  "updated_at": "datetime"
}
```

**Error cases:**
- `404` — Document not found
- `403` — Không có quyền (nếu deleted và là STAFF)

---

### GET `/api/v1/documents/{document_id}/download`

| Field | Value |
|-------|-------|
| **Method** | GET |
| **Auth** | Bearer token |
| **Purpose** | Download file gốc (presigned URL hoặc stream) |

**Response 200:** File stream hoặc redirect tới presigned URL MinIO

---

### DELETE `/api/v1/documents/{document_id}`

| Field | Value |
|-------|-------|
| **Method** | DELETE |
| **Auth** | Bearer token (ADMIN only) |
| **Purpose** | Soft delete tài liệu |

**Response 204:** No Content

**Error cases:**
- `403` — Chỉ ADMIN được xóa
- `404` — Not found

---

## GROUP 3 — OCR

### POST `/api/v1/ocr/{document_id}/trigger`

| Field | Value |
|-------|-------|
| **Method** | POST |
| **Auth** | Bearer token (STAFF, ADMIN) |
| **Purpose** | Re-trigger OCR cho document (nếu muốn chạy lại) |

**Response 202:**
```json
{
  "document_id": "uuid",
  "processing_job_id": "uuid",
  "status": "PENDING",
  "message": "OCR task queued"
}
```

**Error cases:**
- `409` — OCR đang PROCESSING
- `404` — Document not found

---

### GET `/api/v1/ocr/{document_id}/status`

| Field | Value |
|-------|-------|
| **Method** | GET |
| **Auth** | Bearer token |
| **Purpose** | Kiểm tra trạng thái OCR |

**Response 200:**
```json
{
  "document_id": "uuid",
  "ocr_status": "PENDING | PROCESSING | DONE | FAILED",
  "processing_job_id": "uuid",
  "started_at": "datetime | null",
  "completed_at": "datetime | null",
  "error_message": "string | null"
}
```

---

### PATCH `/api/v1/ocr/{document_id}/result`

| Field | Value |
|-------|-------|
| **Method** | PATCH |
| **Auth** | Bearer token (STAFF, ADMIN) |
| **Purpose** | Chỉnh sửa kết quả OCR (human correction) |

**Request Body:**
```json
{ "corrected_text": "string" }
```

**Response 200:**
```json
{
  "id": "uuid",
  "document_id": "uuid",
  "corrected_text": "string",
  "is_corrected": true,
  "corrected_by": { "id": "uuid", "full_name": "string" },
  "corrected_at": "datetime"
}
```

---

## GROUP 4 — Search

### GET `/api/v1/search`

| Field | Value |
|-------|-------|
| **Method** | GET |
| **Auth** | Bearer token |
| **Purpose** | Full-text search tài liệu |

**Query Params:**
```
q:           string — từ khóa tìm kiếm (required)
page:        int = 1
page_size:   int = 20
category_id: uuid — filter
date_from:   date — filter
date_to:     date — filter
ocr_status:  string — filter
fuzzy:       bool = true — bật/tắt fuzzy
```

**Response 200:**
```json
{
  "query": "string",
  "total": 0,
  "page": 1,
  "page_size": 20,
  "pages": 0,
  "items": [
    {
      "document_id": "uuid",
      "title": "string",
      "category": "string",
      "score": 0.95,
      "highlights": [
        "... văn bản <em>từ khóa</em> trong ngữ cảnh ..."
      ],
      "metadata": {
        "student_id": "string | null",
        "document_date": "date | null"
      },
      "created_at": "datetime"
    }
  ]
}
```

---

## GROUP 5 — Metadata

### PATCH `/api/v1/documents/{document_id}/metadata`

| Field | Value |
|-------|-------|
| **Method** | PATCH |
| **Auth** | Bearer token (STAFF, ADMIN) |
| **Purpose** | Chỉnh sửa metadata của tài liệu |

**Request Body:**
```json
{
  "student_id": "string | null",
  "student_name": "string | null",
  "document_date": "date | null",
  "document_number": "string | null",
  "category_id": "uuid | null"
}
```

**Response 200:** Updated document metadata object

---

## GROUP 6 — Users (Admin only)

### GET `/api/v1/users`

| Field | Value |
|-------|-------|
| **Method** | GET |
| **Auth** | Bearer token (ADMIN only) |
| **Purpose** | Danh sách người dùng |

**Response 200:** Paginated list of User objects

---

### POST `/api/v1/users`

| Field | Value |
|-------|-------|
| **Method** | POST |
| **Auth** | Bearer token (ADMIN only) |
| **Purpose** | Tạo người dùng mới |

**Request Body:**
```json
{
  "username": "string",
  "email": "string",
  "password": "string (min 8 chars)",
  "full_name": "string",
  "role": "ADMIN | STAFF"
}
```

**Response 201:** Created User object

**Error cases:**
- `409` — username hoặc email đã tồn tại

---

### PATCH `/api/v1/users/{user_id}`

| Field | Value |
|-------|-------|
| **Method** | PATCH |
| **Auth** | Bearer token (ADMIN only) |
| **Purpose** | Cập nhật thông tin / trạng thái user |

**Request Body:**
```json
{
  "full_name": "string | null",
  "role": "ADMIN | STAFF | null",
  "is_active": "bool | null"
}
```

**Response 200:** Updated User object

---

## GROUP 7 — Administration (Admin only)

### GET `/api/v1/admin/audit-logs`

| Field | Value |
|-------|-------|
| **Method** | GET |
| **Auth** | Bearer token (ADMIN only) |
| **Purpose** | Xem audit log |

**Query Params:**
```
user_id:   uuid — filter
action:    LOGIN | LOGOUT | UPLOAD | DELETE | EDIT_OCR | SEARCH
date_from: datetime
date_to:   datetime
page:      int = 1
page_size: int = 50
```

**Response 200:** Paginated AuditLog list

---

### GET `/api/v1/admin/categories`

| Field | Value |
|-------|-------|
| **Method** | GET |
| **Auth** | Bearer token (ADMIN only) |
| **Purpose** | Quản lý danh mục tài liệu |

**Response 200:** List of DocumentCategory

---

### POST `/api/v1/admin/categories`

| Field | Value |
|-------|-------|
| **Method** | POST |
| **Auth** | Bearer token (ADMIN only) |
| **Purpose** | Tạo danh mục tài liệu mới |

**Request Body:**
```json
{ "name": "string", "code": "string", "description": "string | null" }
```

**Response 201:** Created DocumentCategory

---

## TODO

- [ ] Thêm PATCH /api/v1/documents/{id} (update title, category)
- [ ] Thêm GET /api/v1/admin/stats (thống kê tổng quan)
- [ ] Xem xét thêm WebSocket hoặc SSE cho OCR status real-time
- [ ] Xác nhận pagination strategy (page-based vs cursor-based)
- [ ] Tạo OpenAPI YAML spec sau khi implement
- [ ] Review với GVHD

## References

- .ai/design/ERD.md
- .ai/ARCHITECTURE.md
- .ai/design/UseCase.md
- backend/FastAPI.md
