# SRS — Software Requirements Specification

## Purpose

Tài liệu Đặc tả Yêu cầu Phần mềm (Software Requirements Specification - SRS) cho hệ thống Student-Document-OCR theo chuẩn IEEE 830.

## Scope

Toàn bộ các yêu cầu chức năng, phi chức năng, giao diện, lưu trữ, bảo mật và ràng buộc hệ thống.

---

## 1. Introduction

### 1.1 Purpose
Tài liệu này xác định chi tiết các yêu cầu kỹ thuật cho hệ thống **Student-Document-OCR** nhằm mục đích số hóa, quản lý và tìm kiếm văn bản Công tác sinh viên (CTSV).

### 1.2 Document Conventions
- **MUST / SHALL**: Yêu cầu bắt buộc phải có.
- **SHOULD**: Yêu cầu khuyến nghị.
- **MAY**: Yêu cầu tùy chọn.

### 1.3 Intended Audience
- Giảng viên hướng dẫn & Hội đồng bảo vệ đồ án tốt nghiệp.
- Developers, System Architects, Testers.

---

## 2. Overall Description

### 2.1 Product Perspective
Hệ thống là một giải pháp độc lập (Standalone Web Application) dựa trên kiến trúc Microservices-inspired Monorepo:
- **Client**: Single Page Application (React + Vite).
- **Backend Service**: RESTful API Service (FastAPI).
- **OCR Engine Worker**: Asynchronous Task Worker (Celery + Redis + VietOCR).
- **Storage Layer**: PostgreSQL 15 (Metadata & DB), MinIO (File Object Storage), Elasticsearch 8.x (Search Engine).

### 2.2 Product Functions
1. **Xác thực & Phân quyền**: Đăng nhập JWT, 2 Roles (ADMIN, STAFF).
2. **Quản lý Tài liệu số**: Upload (PDF, JPG, PNG, TIFF), phân loại danh mục, lưu trữ an toàn.
3. **Xử lý OCR Tự động**: Nhận dạng chữ viết tiếng Việt từ ảnh/PDF scan bất đồng bộ.
4. **Hiệu chỉnh Kết quả OCR**: Cho phép người dùng chỉnh sửa và cập nhật văn bản OCR.
5. **Trích xuất Metadata**: Tự động nhận diện MSSV, ngày tháng, loại đơn.
6. **Tìm kiếm Full-text**: Tìm kiếm toàn văn trên Elasticsearch với tiếng Việt có/không dấu, fuzzy search, highlight.
7. **Audit Log & Quản trị**: Ghi vết mọi thao tác người dùng, quản lý tài khoản và danh mục.

---

## 3. Specific Requirements

### 3.1 External Interface Requirements
- **User Interfaces**: Giao diện Web trực quan, tuân thủ spec trong `design/UI.md`.
- **Hardware Interfaces**: Khuyến nghị Server 4 Cores CPU, 8GB RAM, Disk SSD 50GB.
- **Software Interfaces**: Docker Engine v25+, Linux OS / Windows Server.
- **Communications Interfaces**: HTTPS / RESTful API (JSON), WebSocket/Polling cho async status.

### 3.2 Functional Requirements

#### 3.2.1 Authentication & Security (AUTH)
- **AUTH-01**: Hệ thống MUST yêu cầu đăng nhập bằng username/password.
- **AUTH-02**: Mật khẩu MUST được mã hóa bcrypt trước khi lưu database.
- **AUTH-03**: Hệ thống SHALL phát hành JWT Access Token (hạn 60p) và Refresh Token (hạn 7 ngày).

#### 3.2.2 Document Management (DOC)
- **DOC-01**: Hệ thống MUST hỗ trợ upload các định dạng PDF, JPG, PNG, TIFF với dung lượng ≤ 50MB.
- **DOC-02**: File tải lên MUST được lưu trữ an toàn trong MinIO Bucket `student-documents`.
- **DOC-03**: Cán bộ MUST có thể phân loại tài liệu theo danh mục (Đơn xin nghỉ học, Bảo lưu, Kỷ luật, Học bổng,...).

#### 3.2.3 OCR Processing (OCR)
- **OCR-01**: Xử lý OCR MUST chạy dạng bất đồng bộ (Asynchronous Worker) qua Celery Queue.
- **OCR-02**: Trạng thái OCR MUST bao gồm: `PENDING`, `PROCESSING`, `DONE`, `FAILED`.
- **OCR-03**: Hệ thống MUST lưu cả văn bản OCR gốc (`raw_text`) và văn bản hiệu chỉnh (`corrected_text`).
- **OCR-04**: Hệ thống MUST hỗ trợ Re-trigger OCR khi người dùng yêu cầu.

#### 3.2.4 Search Engine (SRCH)
- **SRCH-01**: Hệ thống MUST hỗ trợ tìm kiếm toàn văn (Full-text Search) trên nội dung OCR.
- **SRCH-02**: Tìm kiếm MUST hỗ trợ tiếng Việt có dấu và không dấu (Diacritic folding).
- **SRCH-03**: Hệ thống MUST làm nổi bật (Highlight) từ khóa khớp trong ngữ cảnh kết quả.
- **SRCH-04**: Hệ thống SHALL hỗ trợ lọc (Filter) theo Ngày upload, Danh mục, Trạng thái OCR.

### 3.3 Non-Functional Requirements

- **Performance**: Latency API p95 < 300ms (không tính thời gian OCR). Thời gian OCR < 10s/trang A4 trên CPU.
- **Reliability**: Hệ thống đạt Uptime ≥ 99% trong giờ hành chính. Data persistence 100% (PostgreSQL + MinIO).
- **Security**: RBAC 2 cấp (ADMIN, STAFF). Không lưu plaintext password. Audit Log bất biến (Immutable).
- **Maintainability**: Test Coverage backend ≥ 70%. Source code tuân thủ PEP8 (Ruff).

---

## TODO

- [ ] Lấy xác nhận chính thức tài liệu SRS từ GVHD.
- [ ] Bổ sung các sơ đồ Usecase & Sequence Diagram tương ứng.

## References

- PROJECT_SPEC.md
- FunctionalRequirement.md
- NonFunctionalRequirement.md
- Architecture.md
