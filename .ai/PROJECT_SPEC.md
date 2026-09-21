# Project Specification — Student-Document-OCR

## Purpose

Tài liệu đặc tả dự án chính thức (Project Specification) cho hệ thống Student-Document-OCR.
Đây là tài liệu gốc (source of truth) cho toàn bộ quá trình phát triển.

## Scope

Bao phủ toàn bộ phạm vi kỹ thuật và nghiên cứu của đề tài tốt nghiệp.

---

## 1. Project Overview

| Mục | Nội dung |
|-----|----------|
| **Tên dự án** | Student-Document-OCR |
| **Tên đề tài** | Xây dựng hệ thống số hóa và quản lý tài liệu Công tác sinh viên ứng dụng OCR và Elasticsearch |
| **Loại dự án** | Đồ án tốt nghiệp (Undergraduate Thesis) |
| **Lĩnh vực** | Computer Vision · Natural Language Processing · Information Retrieval · Web Engineering |
| **Ngôn ngữ xử lý** | Tiếng Việt |
| **Ngôn ngữ lập trình** | Python 3.11 (backend/training) · TypeScript (frontend) |

---

## 2. Business Problem

Phòng Công tác sinh viên (CTSV) tại các trường đại học hiện đang quản lý một khối lượng
lớn tài liệu giấy: đơn xin nghỉ học, đơn xin bảo lưu, biên bản kỷ luật, giấy chứng nhận
sinh hoạt, hồ sơ học bổng, v.v.

**Thực trạng (Pain Points):**

- Tài liệu lưu trữ dạng bản giấy → dễ thất lạc, hư hỏng theo thời gian
- Tra cứu thủ công → mất nhiều thời gian, phụ thuộc vào nhân lực
- Không có khả năng tìm kiếm theo nội dung văn bản
- Khó thống kê, báo cáo tổng hợp
- Không có lịch sử truy cập / audit trail

---

## 3. Problem Statement

> Xây dựng một hệ thống phần mềm có khả năng:
>
> (1) Số hóa tài liệu giấy CTSV thông qua công nghệ OCR nhận dạng chữ viết tiếng Việt,
>
> (2) Lưu trữ và quản lý tài liệu số hóa một cách có cấu trúc,
>
> (3) Hỗ trợ tìm kiếm full-text nội dung tài liệu bằng Elasticsearch,
>
> (4) Cung cấp giao diện web để cán bộ CTSV upload, tra cứu và quản lý tài liệu.

---

## 4. Objectives

### 4.1 Research Objectives

1. Nghiên cứu và đánh giá hiệu suất của VietOCR trên domain tài liệu hành chính tiếng Việt
2. Nghiên cứu phương pháp fine-tuning VietOCR với dữ liệu tài liệu CTSV
3. Nghiên cứu thiết kế Elasticsearch index và search strategy cho văn bản OCR tiếng Việt
4. Đánh giá định lượng chất lượng OCR qua CER (Character Error Rate) và WER (Word Error Rate)

### 4.2 Engineering Objectives

1. Xây dựng OCR pipeline hoàn chỉnh: từ ảnh/PDF đầu vào đến văn bản có cấu trúc
2. Xây dựng REST API backend (FastAPI) tích hợp OCR service, PostgreSQL và Elasticsearch
3. Xây dựng giao diện web (React) cho phép upload, xem OCR result và tìm kiếm tài liệu
4. Containerize toàn bộ hệ thống bằng Docker Compose

---

## 5. Scope

### In Scope

- Số hóa tài liệu tiếng Việt dạng scan (image: JPG, PNG, TIFF) và PDF
- OCR nhận dạng văn bản in (printed text) tiếng Việt
- Fine-tuning VietOCR trên dataset tài liệu CTSV (nếu thu thập được)
- Quản lý tài liệu: upload, lưu trữ (MinIO), phân loại theo category
- Tìm kiếm full-text nội dung OCR bằng Elasticsearch
- Tìm kiếm theo metadata (ngày, loại tài liệu, người upload)
- Giao diện web (React) cho 2 role: Administrator và Staff
- Xác thực người dùng (JWT)
- Audit log cho các thao tác quan trọng
- Triển khai bằng Docker Compose

### Out of Scope

- OCR chữ viết tay (handwriting recognition) — **không trong phạm vi**
- Nhận dạng chữ trên ảnh chụp từ điện thoại chất lượng thấp — **không đảm bảo**
- OCR tài liệu ngôn ngữ khác (tiếng Anh, tiếng Trung) — **không tối ưu**
- Quy trình ký số, xác thực chữ ký — **không trong phạm vi**
- Mobile application (iOS, Android) — **không trong phạm vi**
- Tích hợp với hệ thống quản lý sinh viên hiện có — **không trong phạm vi**
- Tính năng OCR real-time từ camera — **không trong phạm vi**

---

## 6. Target Users

| Role | Mô tả | Quyền hạn |
|------|-------|-----------|
| **Administrator** | Quản trị viên hệ thống | Quản lý user, cấu hình hệ thống, xem audit log, toàn quyền |
| **Staff (Trợ lý CTSV)** | Cán bộ phòng CTSV | Upload tài liệu, kích hoạt OCR, tìm kiếm, xem/sửa OCR result |

---

## 7. Functional Requirements

### FR-AUTH: Authentication

| ID | Requirement |
|----|------------|
| FR-AUTH-01 | Hệ thống hỗ trợ đăng nhập bằng username/password |
| FR-AUTH-02 | Hệ thống phát hành JWT access token (60 phút) và refresh token (7 ngày) |
| FR-AUTH-03 | Hệ thống hỗ trợ đăng xuất (invalidate refresh token) |
| FR-AUTH-04 | Hệ thống kiểm tra phân quyền trên từng API endpoint |

### FR-DOC: Document Management

| ID | Requirement |
|----|------------|
| FR-DOC-01 | User có thể upload file PDF hoặc image (JPG, PNG, TIFF) tối đa 50MB |
| FR-DOC-02 | Hệ thống lưu trữ file gốc trên MinIO |
| FR-DOC-03 | User có thể xem danh sách tài liệu với phân trang |
| FR-DOC-04 | User có thể xem chi tiết tài liệu (metadata + OCR result) |
| FR-DOC-05 | User có thể download file gốc |
| FR-DOC-06 | Admin có thể xóa tài liệu (soft delete) |
| FR-DOC-07 | Tài liệu được phân loại theo DocumentCategory |

### FR-OCR: OCR Processing

| ID | Requirement |
|----|------------|
| FR-OCR-01 | Hệ thống tự động trigger OCR sau khi upload tài liệu thành công |
| FR-OCR-02 | OCR được xử lý bất đồng bộ (async) qua Celery task queue |
| FR-OCR-03 | User có thể theo dõi trạng thái OCR (PENDING / PROCESSING / DONE / FAILED) |
| FR-OCR-04 | User có thể xem kết quả OCR dạng văn bản |
| FR-OCR-05 | User có thể chỉnh sửa kết quả OCR (correction interface) |
| FR-OCR-06 | Hệ thống lưu cả kết quả OCR gốc và phiên bản đã chỉnh sửa |
| FR-OCR-07 | Hệ thống hỗ trợ re-trigger OCR nếu kết quả không đạt |

### FR-SEARCH: Search

| ID | Requirement |
|----|------------|
| FR-SEARCH-01 | User có thể tìm kiếm full-text trên nội dung OCR |
| FR-SEARCH-02 | Kết quả tìm kiếm hiển thị highlight từ khóa trong ngữ cảnh |
| FR-SEARCH-03 | User có thể lọc kết quả theo metadata (ngày upload, category, trạng thái OCR) |
| FR-SEARCH-04 | Hệ thống hỗ trợ fuzzy search để bù đắp lỗi OCR nhỏ |
| FR-SEARCH-05 | Kết quả tìm kiếm được phân trang (page-based) |

### FR-USER: User Management (Admin only)

| ID | Requirement |
|----|------------|
| FR-USER-01 | Admin có thể tạo tài khoản user mới |
| FR-USER-02 | Admin có thể vô hiệu hóa tài khoản user |
| FR-USER-03 | Admin có thể thay đổi role của user |

### FR-AUDIT: Audit Log

| ID | Requirement |
|----|------------|
| FR-AUDIT-01 | Hệ thống ghi nhận audit log cho các thao tác: login, upload, delete, edit OCR |
| FR-AUDIT-02 | Admin có thể xem audit log với filter theo user, action, thời gian |

---

## 8. Non-Functional Requirements

| ID | Category | Requirement | Target |
|----|----------|-------------|--------|
| NFR-01 | Performance | API response time (p95, không tính OCR) | < 300ms |
| NFR-02 | Performance | OCR processing time cho 1 trang A4 (CPU) | < 10 giây |
| NFR-03 | Performance | Elasticsearch search latency (p95) | < 500ms |
| NFR-04 | Scalability | Số concurrent users hỗ trợ | ≥ 20 |
| NFR-05 | Availability | Uptime trong giờ hành chính | ≥ 99% |
| NFR-06 | Security | Tất cả API yêu cầu authentication | Bắt buộc |
| NFR-07 | Security | Mật khẩu được hash bằng bcrypt | Bắt buộc |
| NFR-08 | Security | HTTPS trong môi trường production | Bắt buộc |
| NFR-09 | Maintainability | Test coverage backend | ≥ 70% |
| NFR-10 | Portability | Toàn bộ stack chạy bằng Docker Compose | Bắt buộc |

---

## 9. OCR Requirements

| ID | Requirement |
|----|------------|
| OCR-01 | Engine chính: VietOCR (VGG + Transformer) cho text recognition |
| OCR-02 | Text detection: [TBD — xem DECISIONS.md ADR-002] |
| OCR-03 | Input: ảnh grayscale hoặc màu, độ phân giải khuyến nghị ≥ 150 DPI |
| OCR-04 | Input: PDF (convert sang ảnh trước khi OCR) |
| OCR-05 | Output: UTF-8 text, confidence score (nếu engine hỗ trợ) |
| OCR-06 | Target CER: < 5% trên tài liệu in chuẩn, scan chất lượng tốt |
| OCR-07 | Target WER: < 10% trên cùng điều kiện |
| OCR-08 | Xử lý bất đồng bộ (không block HTTP request) |

---

## 10. Search Requirements

| ID | Requirement |
|----|------------|
| SEARCH-01 | Full-text search trên nội dung OCR |
| SEARCH-02 | Hỗ trợ tiếng Việt với dấu (có/không dấu) |
| SEARCH-03 | Fuzzy search (edit distance ≤ 2) cho lỗi OCR |
| SEARCH-04 | Highlight kết quả trong đoạn văn |
| SEARCH-05 | Filter theo metadata fields |
| SEARCH-06 | Pagination: page-based, mặc định 20 kết quả/trang |
| SEARCH-07 | Vietnamese analyzer: [TBD — benchmark cần thiết] |

---

## 11. Security Requirements

| ID | Requirement |
|----|------------|
| SEC-01 | JWT authentication cho tất cả protected endpoints |
| SEC-02 | Role-based access control: Administrator / Staff |
| SEC-03 | Mật khẩu lưu dạng bcrypt hash, salt tự động |
| SEC-04 | File upload: whitelist type (PDF, JPG, PNG, TIFF), max 50MB |
| SEC-05 | Audit log không thể xóa bởi Staff |
| SEC-06 | Rate limiting: [TBD — cấu hình sau khi benchmark] |
| SEC-07 | CORS: chỉ cho phép origin của frontend |

---

## 12. Performance Requirements

| Metric | Target | Điều kiện |
|--------|--------|-----------|
| API latency p95 | < 300ms | Không tính OCR, 20 concurrent users |
| OCR latency | < 10s/trang | CPU-only, ảnh 150–300 DPI |
| Search latency p95 | < 500ms | Elasticsearch, 10k documents |
| Upload response | < 2s | Chỉ upload + lưu, chưa tính OCR |
| CER | < 5% | Tài liệu in, scan ≥ 150 DPI |
| WER | < 10% | Cùng điều kiện |

---

## 13. System Constraints

| Constraint | Mô tả |
|-----------|-------|
| **Ngôn ngữ** | Tiếng Việt là ngôn ngữ chính của tài liệu |
| **Runtime** | Python 3.11, Node.js 20 |
| **Deployment** | Docker Compose (không có K8s trong phạm vi đề tài) |
| **GPU** | Inference chạy được trên CPU (GPU optional, tăng tốc) |
| **OS** | Linux (production), Windows/macOS (development) |
| **Dataset** | Phụ thuộc vào khả năng thu thập từ thực tế |
| **Thời gian** | Giới hạn bởi timeline đề tài tốt nghiệp |

---

## 14. Expected Outputs

1. **Trained Model**: VietOCR model đã fine-tune trên dataset CTSV (nếu dataset đủ lượng)
2. **Backend API**: FastAPI service hoàn chỉnh với tất cả endpoints
3. **Frontend UI**: React application với đầy đủ chức năng cho 2 role
4. **Docker Compose**: Stack triển khai hoàn chỉnh
5. **Dataset**: Tập dữ liệu tài liệu CTSV đã annotate (nếu thu thập được)
6. **Evaluation Report**: Báo cáo CER/WER và system performance benchmark
7. **Thesis**: Báo cáo tốt nghiệp theo format trường

---

## 15. Research Contributions

1. **Đánh giá VietOCR** trên domain tài liệu hành chính tiếng Việt — đóng góp benchmark mới
2. **Tích hợp OCR + Elasticsearch** cho hệ thống quản lý tài liệu tiếng Việt — hệ thống end-to-end
3. **Quy trình fine-tuning VietOCR** cho domain-specific document — tài liệu hướng dẫn thực tế

---

## 16. Future Work

- Mở rộng hỗ trợ chữ viết tay (handwriting recognition)
- Tích hợp với hệ thống quản lý sinh viên (ERP/SIS)
- Mobile application cho tra cứu
- OCR real-time từ camera
- Layout analysis để hiểu cấu trúc tài liệu phức tạp
- Vector search (semantic search) với embedding

---

## TODO

- [ ] Xác nhận tên đề tài chính thức với GVHD
- [ ] Xác nhận GVHD chính thức
- [ ] Xác nhận timeline với GVHD
- [ ] Quyết định text detection engine (xem ADR-002 trong DECISIONS.md)
- [ ] Xác nhận dataset có thể thu thập từ Phòng CTSV
- [ ] Xác nhận target CER/WER với GVHD

## References

- .ai/ARCHITECTURE.md
- .ai/TECH_STACK.md
- .ai/DECISIONS.md
- .ai/design/SRS.md
- .ai/design/FunctionalRequirement.md
- .ai/design/NonFunctionalRequirement.md
