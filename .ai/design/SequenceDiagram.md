# Sequence Diagram — Sơ đồ Tuần tự Hệ thống

## Purpose

Mô tả luồng tương tác giữa các thành phần phần mềm (Actor, React Frontend, FastAPI Backend, Celery Worker, Database, MinIO, Elasticsearch) theo thời gian cho các kịch bản quan trọng.

## Scope

3 Sequence Diagrams chính: Upload & Async OCR Flow, Search Document Flow, Human Correction OCR Flow.

---

## 1. Sequence Diagram 1: Upload Tài liệu & Async OCR Pipeline

```mermaid
sequenceDiagram
    autonumber
    actor Staff as Cán bộ (Staff)
    participant FE as React Frontend
    participant BE as FastAPI Backend
    participant Storage as MinIO Storage
    participant DB as PostgreSQL
    participant Queue as Redis Queue
    participant Worker as Celery Worker
    participant ES as Elasticsearch

    Staff->>FE: Kéo thả file PDF/Image & Click Upload
    FE->>BE: POST /api/v1/documents (multipart/form-data)
    BE->>BE: Validate file (type, size <= 50MB)
    BE->>Storage: Save file (uuid_filename)
    Storage-->>BE: Return Object Key
    BE->>DB: INSERT document (ocr_status='PENDING')
    BE->>DB: INSERT processing_job (status='PENDING')
    BE->>Queue: Push Task: process_ocr(document_id)
    BE-->>FE: Return HTTP 202 Accepted (document_id, job_id)
    FE-->>Staff: Hiển thị "Đang xử lý OCR..." (Status: PENDING)

    Note over Queue, Worker: Xử lý Asynchronous OCR
    Queue->>Worker: Pick Task process_ocr(document_id)
    Worker->>DB: UPDATE ocr_status = 'PROCESSING'
    Worker->>Storage: Download File (bytes)
    Worker->>Worker: Run Preprocessing & Text Detection
    Worker->>Worker: Run VietOCR Recognition
    Worker->>Worker: Run Post-processing & Metadata Extraction
    Worker->>DB: INSERT ocr_results (raw_text, confidence)
    Worker->>DB: INSERT document_metadata (student_id, date)
    Worker->>DB: UPDATE document ocr_status = 'DONE'
    Worker->>ES: Index document (title, content, metadata)
    ES-->>Worker: Index OK
    Worker->>DB: UPDATE processing_job (status='DONE')

    loop Frontend Polling Status
        FE->>BE: GET /api/v1/ocr/{document_id}/status
        BE->>DB: Query ocr_status
        DB-->>BE: ocr_status = 'DONE'
        BE-->>FE: Return status 'DONE'
    end
    FE->>BE: GET /api/v1/documents/{document_id}
    BE-->>FE: Return Document Details + OCR Text
    FE-->>Staff: Hiển thị kết quả OCR văn bản hoàn chỉnh
```

---

## 2. Sequence Diagram 2: Tìm kiếm Văn bản (Full-text Search)

```mermaid
sequenceDiagram
    autonumber
    actor Staff as Cán bộ / Admin
    participant FE as React Frontend
    participant BE as FastAPI Backend
    participant ES as Elasticsearch
    participant DB as PostgreSQL

    Staff->>FE: Nhập từ khóa ("đơn xin bảo lưu") & Filter
    FE->>BE: GET /api/v1/search?q=don+xin+bao+luu&category=...
    BE->>BE: Verify JWT Access Token
    BE->>ES: Multi-match Query (fuzziness=AUTO, highlight, filters)
    ES-->>BE: Return Hits (doc_ids, scores, highlights)
    BE->>DB: Query document details for hits
    DB-->>BE: Return titles, uploaders, dates
    BE->>DB: INSERT audit_log (action='SEARCH', detail=query)
    BE-->>FE: Return SearchResultsResponse (items, total, page)
    FE-->>Staff: Hiển thị danh sách kết quả với từ khóa Highlight
```

---

## 3. Sequence Diagram 3: Hiệu chỉnh OCR Thủ công (Human Correction)

```mermaid
sequenceDiagram
    autonumber
    actor Staff as Cán bộ / Admin
    participant FE as React Frontend
    participant BE as FastAPI Backend
    participant DB as PostgreSQL
    participant ES as Elasticsearch

    Staff->>FE: Click "Chỉnh sửa OCR" & Sửa nội dung văn bản
    FE->>BE: PATCH /api/v1/ocr/{document_id}/result (corrected_text)
    BE->>BE: Verify JWT & Staff Role
    BE->>DB: UPDATE ocr_results (corrected_text, is_corrected=true)
    BE->>ES: Update ES Index document content = corrected_text
    ES-->>BE: ES Update OK
    BE->>DB: INSERT audit_log (action='EDIT_OCR')
    BE-->>FE: Return Updated OCRResult
    FE-->>Staff: Hiển thị văn bản đã hiệu chỉnh thành công
```

---

## TODO

- [ ] Bổ sung Sequence Diagram cho luồng Đăng nhập (Auth Flow) và Xóa tài liệu.
- [ ] Export các sơ đồ ra định dạng PNG/SVG nhúng vào báo cáo đồ án.

## References

- Architecture.md
- API.md
- UseCase.md
