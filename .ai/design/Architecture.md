# Architecture Design — Thiết kế Kiến trúc Chi tiết

## Purpose

Tài liệu thiết kế chi tiết kiến trúc tầng phần mềm, phân chia module và nguyên lý giao tiếp giữa các thành phần của hệ thống Student-Document-OCR.

## Scope

Tài liệu tham chiếu chi tiết hơn của `ARCHITECTURE.md` (gốc), tập trung vào thiết kế từng tầng: Presentation Layer, Application API Layer, Domain & OCR Worker Layer, Data Access Layer & Infrastructure.

---

## 1. Mẫu Thiết kế Kiến trúc (Architectural Patterns)

Hệ thống được thiết kế dựa trên sự kết hợp của 3 mẫu kiến trúc hiện đại:

1. **Layered Architecture (Kiến trúc Phân tầng)**:
   - Tách biệt rõ ràng trách nhiệm giữa UI -> API Router -> Service -> Repository -> Data Model.
2. **Event-Driven / Asynchronous Task Pattern (Kiến trúc Bất đồng bộ)**:
   - Sử dụng Message Broker (Redis) và Celery Task Queue để giải phóng HTTP Thread khi thực hiện các tác vụ nặng (OCR Engine).
3. **Repository Pattern**:
   - Tách biệt hoàn toàn logic truy vấn CSDL khỏi Service Layer, giúp dễ dàng kiểm thử (Mock Unit Test).

---

## 2. Chi tiết Các Tầng Kiến trúc (Layer Details)

```
┌─────────────────────────────────────────────────────────────┐
│                 1. PRESENTATION LAYER (React)               │
│   - UI Components (Vite, TypeScript, Tailwind/Shadcn)       │
│   - State Management (TanStack Query, Zustand)              │
└──────────────────────────────┬──────────────────────────────┘
                               │ HTTP REST API (JSON)
┌──────────────────────────────▼──────────────────────────────┐
│                2. API ROUTER LAYER (FastAPI)                │
│   - Routers (/auth, /documents, /ocr, /search, /users)      │
│   - Pydantic Validation & JWT Authentication Middleware     │
└──────────────────────────────┬──────────────────────────────┘
                               │ Async Internal Calls
┌──────────────────────────────▼──────────────────────────────┐
│              3. SERVICE LAYER (Business Logic)              │
│   - AuthService, DocumentService, OCRService, SearchService │
└──────────────┬───────────────────────────────┬──────────────┘
               │                               │
               ▼                               ▼
┌──────────────────────────────┐  ┌───────────────────────────┐
│ 4. REPOSITORY LAYER          │  │ 5. ASYNC WORKER LAYER     │
│  - UserRepo, DocumentRepo,   │  │  - Celery Worker Tasks    │
│    OCRResultRepo             │  │  - VietOCR Pipeline       │
└──────────────┬───────────────┘  └────────────┬──────────────┘
               │                               │
               ▼                               ▼
┌─────────────────────────────────────────────────────────────┐
│               6. INFRASTRUCTURE & DATA LAYER                │
│   - PostgreSQL 15 | Elasticsearch 8.x | MinIO | Redis 7     │
└─────────────────────────────────────────────────────────────┘
```

---

## 3. Trách nhiệm & Hợp đồng giữa các Tầng

### 3.1 Presentation Layer (Frontend)
- **Nhiệm vụ**: Đảm nhận hiển thị giao diện, quản lý Form State, lưu trữ JWT Token và Render màn hình kết quả.
- **Không thực hiện**: Không chứa logic tính toán nghiệp vụ hay trực tiếp gọi CSDL.

### 3.2 API Router Layer (FastAPI)
- **Nhiệm vụ**: Tiếp nhận HTTP Request, Validate dữ liệu đầu vào bằng Pydantic Schemas, kiểm tra Token/RBAC, gọi Service tương ứng và trả về HTTP Response.

### 3.3 Service Layer (Business Logic)
- **Nhiệm vụ**: Thực thi các quy tắc nghiệp vụ (Business Rules), phối hợp giữa Repository, MinIO Client, Celery Task Dispatcher và Elasticsearch Client.

### 3.4 Repository Layer (Data Access)
- **Nhiệm vụ**: Thực thi các truy vấn CSDL PostgreSQL thông qua SQLAlchemy Async Session (`select`, `insert`, `update`, `delete`).

### 3.5 Async Worker Layer (Celery OCR Engine)
- **Nhiệm vụ**: Lắng nghe Task từ Redis Queue, tải ảnh từ MinIO, thực thi OCR Pipeline (Preprocessing -> Detection -> VietOCR Recognition -> Post-processing -> Extract Metadata), lưu kết quả vào DB và Index lên Elasticsearch.

---

## TODO

- [ ] Cập nhật C4 Diagram Level 1, 2, 3 bằng C4-PlantUML.
- [ ] Xây dựng hướng dẫn viết Unit Test độc lập cho từng tầng kiến trúc.

## References

- .ai/ARCHITECTURE.md
- TECH_STACK.md
- API.md
- Database.md
