# ARCHITECTURE — Kiến trúc hệ thống

## Purpose

Mô tả kiến trúc tổng thể của hệ thống Student-Document-OCR: các layer, component,
luồng dữ liệu và cách các service tương tác. Đây là tài liệu kiến trúc chính thức (frozen).

## Scope

Bao gồm: System Overview, OCR Pipeline, Search Pipeline, Authentication Flow,
Async Processing Flow, Deployment Architecture.

---

## 1. System Overview

```
┌─────────────────────────────────────────────────────────────┐
│                        USER (Browser)                        │
└────────────────────────┬────────────────────────────────────┘
                         │ HTTPS
┌────────────────────────▼────────────────────────────────────┐
│                  React Frontend (Vite)                        │
│         Port 3000 (dev) / Nginx (production)                 │
└────────────────────────┬────────────────────────────────────┘
                         │ REST API (JSON)
┌────────────────────────▼────────────────────────────────────┐
│                   FastAPI Backend                             │
│                      Port 8000                               │
│  ┌─────────────┐  ┌──────────────┐  ┌─────────────────────┐ │
│  │ Auth Router │  │ Doc Router   │  │ Search Router       │ │
│  └─────────────┘  └──────┬───────┘  └──────────┬──────────┘ │
│                          │                      │            │
│  ┌────────────────────────▼──────────────────────▼─────────┐ │
│  │              Service Layer                               │ │
│  │  AuthService  DocumentService  OCRService  SearchService │ │
│  └──────────────────────┬───────────────────────┬──────────┘ │
│                         │                       │            │
│  ┌──────────────────────▼──────┐  ┌─────────────▼──────────┐ │
│  │       Repository Layer      │  │    Elasticsearch Client │ │
│  │  UserRepo  DocumentRepo     │  │    (Search & Indexing)  │ │
│  └──────────────────────┬──────┘  └────────────────────────┘ │
└─────────────────────────┼────────────────────────────────────┘
                          │
        ┌─────────────────┼──────────────────────┐
        │                 │                      │
┌───────▼──────┐ ┌────────▼───────┐ ┌───────────▼──────────┐
│  PostgreSQL  │ │  Elasticsearch  │ │        MinIO         │
│  (Port 5432) │ │  (Port 9200)    │ │     (Port 9000)      │
└──────────────┘ └────────────────┘ └──────────────────────┘

       Async Processing (Celery + Redis):
┌────────────────────────────────────────────┐
│              Celery Worker                  │
│  Nhận task từ Redis Queue                  │
│  → Chạy OCR Pipeline                       │
│  → Lưu kết quả vào PostgreSQL              │
│  → Index vào Elasticsearch                 │
└────────────────────────────────────────────┘
┌─────────────────────┐
│   Redis (Port 6379) │
│   Broker + Results  │
└─────────────────────┘
```

---

## 2. Layer Architecture (Backend)

```
HTTP Request
     │
     ▼
┌─────────────────────────┐
│       Router Layer       │  FastAPI APIRouter
│  (Input Validation)      │  Pydantic Schema validation
└────────────┬────────────┘
             │
             ▼
┌─────────────────────────┐
│      Service Layer       │  Business logic
│  (Orchestration)         │  Không gọi DB trực tiếp
└────────────┬────────────┘
             │
             ▼
┌─────────────────────────┐
│    Repository Layer      │  Data access only
│  (Data Access)           │  SQLAlchemy async queries
└────────────┬────────────┘
             │
             ▼
┌─────────────────────────┐
│      ORM Models          │  SQLAlchemy declarative models
│  + PostgreSQL            │
└─────────────────────────┘
```

---

## 3. OCR Pipeline (Chi tiết)

### 3.1 Input → Pre-processing

```
Input: PDF / Image (JPG, PNG, TIFF)
         │
         ▼
┌─────────────────────────────────┐
│  Step 1: Input Validation        │
│  - File type whitelist check     │
│  - File size check (max 50MB)    │
│  Output: validated file bytes    │
└───────────────┬─────────────────┘
                │
                ▼
┌─────────────────────────────────┐
│  Step 2: Image Conversion        │
│  - PDF → images (pdf2image)      │
│  - Multi-page → list of images   │
│  - Normalize to RGB/Grayscale    │
│  Output: list[np.ndarray]        │
└───────────────┬─────────────────┘
                │
                ▼
┌─────────────────────────────────┐
│  Step 3: Image Preprocessing    │
│  - Deskew (correct rotation)    │
│  - Denoise (if needed)          │
│  - Contrast enhancement         │
│  - Resize for model input       │
│  Output: preprocessed image     │
└───────────────┬─────────────────┘
```

### 3.2 Text Detection → Recognition

```
Preprocessed Image
         │
         ▼
┌─────────────────────────────────┐
│  Step 4: Text Detection          │
│  Engine: [TBD — ADR-002]        │
│  - Detect text regions (boxes)  │
│  Output: list[BoundingBox]       │
└───────────────┬─────────────────┘
                │
                ▼
┌─────────────────────────────────┐
│  Step 5: Text Line Cropping     │
│  - Crop ảnh theo bounding box   │
│  - Sort theo thứ tự đọc (top→  │
│    bottom, left→right)          │
│  Output: list[cropped_image]    │
└───────────────┬─────────────────┘
                │
                ▼
┌─────────────────────────────────┐
│  Step 6: VietOCR Recognition    │
│  - VGG backbone (feature extract│
│  - Transformer Seq2Seq decoder  │
│  - Beam search (beam_width=5)   │
│  Input:  cropped line image     │
│  Output: (text: str, prob: float│
└───────────────┬─────────────────┘
```

> **QUAN TRỌNG**: VietOCR chỉ làm **Text Recognition** (nhận dạng văn bản trong ảnh đã crop).
> VietOCR **KHÔNG** làm Text Detection (định vị vùng chữ trên trang).

### 3.3 Post-processing → Storage

```
OCR Raw Results
         │
         ▼
┌─────────────────────────────────┐
│  Step 7: Post-processing        │
│  - Join text lines              │
│  - Unicode normalization (NFC)  │
│  - Remove control characters    │
│  - Reconstruct paragraph        │
│  Output: clean_text: str        │
└───────────────┬─────────────────┘
                │
                ▼
┌─────────────────────────────────┐
│  Step 8: Metadata Extraction    │
│  - Document type detection      │
│  - Date extraction (regex)      │
│  - Student ID extraction        │
│  - Entity recognition (rule)   │
│  Output: DocumentMetadata       │
└───────────────┬─────────────────┘
                │
         ┌──────┴──────┐
         │             │
         ▼             ▼
┌────────────┐  ┌──────────────────┐
│ PostgreSQL │  │  Elasticsearch   │
│ OCRResult  │  │  Document Index  │
│ (text +    │  │  (full-text +    │
│  metadata) │  │   metadata)      │
└────────────┘  └──────────────────┘
```

---

## 4. Search Pipeline

```
User Search Query
         │
         ▼
┌─────────────────────────────────┐
│  Query Builder (SearchService)  │
│  - Parse query string           │
│  - Apply filters (metadata)     │
│  - Build ES query DSL           │
└───────────────┬─────────────────┘
                │
                ▼
┌─────────────────────────────────┐
│  Elasticsearch Query            │
│  - Full-text search on content  │
│  - Fuzzy match (edit_distance≤2)│
│  - Metadata filters             │
│  - Highlight fragment           │
└───────────────┬─────────────────┘
                │
                ▼
┌─────────────────────────────────┐
│  Result Mapping                 │
│  - Map ES hits → SearchResult   │
│  - Inject highlights            │
│  - Pagination metadata          │
└───────────────┬─────────────────┘
                │
                ▼
           HTTP Response
      (SearchResultResponse)
```

---

## 5. Async Processing Flow (Celery)

```
HTTP POST /api/v1/documents (upload)
         │
         ▼
FastAPI: save file → MinIO
         │
         ▼
Create Document record (status=PENDING)
         │
         ▼
Dispatch Celery Task: process_ocr(document_id)
         │
         ▼
FastAPI trả về HTTP 202 Accepted
         │
    (background)
         ▼
Celery Worker picks up task
         │
         ▼
Update status: PROCESSING
         │
         ▼
Run OCR Pipeline (steps 1-8)
         │
         ▼
Save OCRResult → PostgreSQL
         │
         ▼
Index → Elasticsearch
         │
         ▼
Update status: DONE (hoặc FAILED)
```

---

## 6. Authentication Flow

```
POST /api/v1/auth/login
  { username, password }
         │
         ▼
Verify credentials (bcrypt)
         │
         ▼
Issue: access_token (60min) + refresh_token (7days)
         │
         ▼
Client stores tokens

Subsequent Requests:
  Header: Authorization: Bearer <access_token>
         │
         ▼
FastAPI Security Dependency: verify JWT
         │
         ▼
Extract user_id + role
         │
         ▼
RBAC check: có đủ quyền không?
         │
         ▼
Proceed to handler / 401 / 403
```

---

## 7. Deployment Architecture (Docker Compose)

```
┌──────────────────────────────────────────────────────────┐
│                  Docker Compose Stack                     │
│                                                           │
│  ┌─────────────┐  ┌──────────────┐  ┌─────────────────┐  │
│  │   frontend  │  │   backend    │  │  celery_worker  │  │
│  │ nginx:3000  │  │ uvicorn:8000 │  │   (OCR tasks)   │  │
│  └─────────────┘  └──────────────┘  └─────────────────┘  │
│                                                           │
│  ┌─────────────┐  ┌──────────────┐  ┌─────────────────┐  │
│  │  postgres   │  │elasticsearch │  │      minio      │  │
│  │   :5432     │  │    :9200     │  │      :9000      │  │
│  └─────────────┘  └──────────────┘  └─────────────────┘  │
│                                                           │
│  ┌─────────────┐  ┌──────────────┐                        │
│  │    redis    │  │    flower    │                        │
│  │    :6379    │  │    :5555     │                        │
│  └─────────────┘  └──────────────┘                        │
│                                                           │
│  Network: ocr_net (bridge)                               │
└──────────────────────────────────────────────────────────┘
```

---

## 8. Key Architecture Decisions

| Decision | Choice | Lý do |
|----------|--------|-------|
| OCR Recognition | VietOCR | Tối ưu tiếng Việt, có pre-trained |
| OCR Detection | [TBD — ADR-002] | Cần benchmark |
| Async Processing | Celery + Redis | OCR nặng, không block HTTP |
| Search | Elasticsearch | Full-text, fuzzy, highlight tốt |
| Storage | MinIO | S3-compatible, self-hosted |
| DB | PostgreSQL | Mature, async support tốt |
| Infra | Docker Compose | Đơn giản cho thesis scope |

---

## TODO

- [ ] Quyết định text detection engine (ADR-002) → hoàn thiện Step 4
- [ ] Vẽ C4 Level 1-3 diagram (PlantUML/draw.io)
- [ ] Vẽ Sequence Diagram cho OCR async flow
- [ ] Benchmark: ước lượng OCR latency trên CPU

## References

- .ai/TECH_STACK.md
- .ai/DECISIONS.md
- .ai/design/Architecture.md
- .ai/design/DeploymentDiagram.md
- .ai/design/SequenceDiagram.md
