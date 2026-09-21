# Functional Requirement — Yêu cầu Chức năng Chi tiết

## Purpose

Tài liệu mô tả chi tiết tất cả các yêu cầu chức năng (Functional Requirements) cho các phân hệ trong phần mềm Student-Document-OCR.

## Scope

7 Phân hệ chức năng chính: Authentication, Document Management, OCR Service, Metadata Extraction, Search Engine, User Management, Audit Log.

---

## 1. Danh sách Phân hệ Chức năng

```
┌─────────────────────────────────────────────────────────────────┐
│                    STUDENT-DOCUMENT-OCR                         │
├─────────────────┬─────────────────┬─────────────────────────────┤
│ 1. AUTHENTICATE │ 2. DOCUMENT MGT │ 3. OCR PROCESSING           │
├─────────────────┼─────────────────┼─────────────────────────────┤
│ 4. METADATA EXT │ 5. FULLTEXT SRCH│ 6. USER MGT & 7. AUDIT LOG  │
└─────────────────┴─────────────────┴─────────────────────────────┘
```

---

## 2. Chi tiết Yêu cầu Chức năng theo Phân hệ

### Module 1: Xác thực & Phân quyền (Authentication & RBAC)

- **FR-AUTH-01 (Đăng nhập)**: User nhập `username` và `password`. Hệ thống kiểm tra và trả về cặp `access_token` (JWT) và `refresh_token`.
- **AUTH-02 (Đăng xuất)**: Thêm refresh token vào blacklist/redis để vô hiệu hóa phiên làm việc.
- **AUTH-03 (Làm mới phiên)**: Cấp `access_token` mới khi gửi `refresh_token` hợp lệ.
- **AUTH-04 (Kiểm tra Phân quyền)**:
  - Role `ADMIN`: Có full quyền xem, tạo, sửa, xóa, quản lý user, xem audit log.
  - Role `STAFF`: Có quyền upload, xem tài liệu, xem/chỉnh sửa kết quả OCR, tìm kiếm, sửa metadata. Không có quyền xóa tài liệu hay xem audit log.

### Module 2: Quản lý Tài liệu (Document Management)

- **FR-DOC-01 (Upload Tài liệu)**: Hỗ trợ kéo thả/chọn file formats `.pdf`, `.jpg`, `.jpeg`, `.png`, `.tiff`. Dung lượng tối đa 50MB/file.
- **FR-DOC-02 (Lưu trữ File)**: Tự động tải file gốc lên MinIO Bucket `student-documents` với đường dẫn dạng `YYYY/MM/DD/{uuid}_{filename}`.
- **FR-DOC-03 (Danh sách Tài liệu)**: Hiển thị dạng bảng có phân trang, hỗ trợ sắp xếp theo ngày upload, tên file, danh mục, trạng thái OCR.
- **FR-DOC-04 (Xem Chi tiết)**: Hiển thị Preview ảnh/PDF song song với thông tin OCR và Metadata.
- **FR-DOC-05 (Download File)**: Tạo đường dẫn tải xuống an toàn (Presigned URL có thời hạn).
- **FR-DOC-06 (Xóa Tài liệu)**: Thực hiện Soft Delete (`is_deleted = true`) chỉ dành cho Admin.

### Module 3: Xử lý OCR (OCR Processing Engine)

- **FR-OCR-01 (Khởi tạo Async Task)**: Sau khi upload thành công, gửi Celery task `process_ocr_document` với `document_id`.
- **FR-OCR-02 (Xử lý Tiền xử lý & Recognition)**:
  - Nếu là PDF: Convert từng trang ra ảnh (pdf2image DPI 200).
  - Crop dòng chữ (Text Detection/Line cropping).
  - Nhận dạng dòng chữ với VietOCR model.
  - Ghép các câu văn bản theo thứ tự từ trên xuống dưới, từ trái sang phải.
- **FR-OCR-03 (Quản lý Trạng thái)**: Cập nhật trạng thái `PENDING` -> `PROCESSING` -> `DONE` (hoặc `FAILED`).
- **FR-OCR-04 (Chỉnh sửa Kết quả)**: Người dùng có thể hiệu chỉnh văn bản OCR sai sót. Lưu vết `is_corrected = true`, `corrected_by`, `corrected_at`.
- **FR-OCR-05 (Re-trigger OCR)**: Cho phép chạy lại OCR với tham số hoặc engine khác nếu cần.

### Module 4: Trích xuất Metadata (Metadata Extraction)

- **FR-META-01 (Trích xuất Tự động)**: Áp dụng Regex & Rule-based NLP để bóc tách:
  - Mã số sinh viên (MSSV): Pattern 8-10 chữ số.
  - Họ và tên sinh viên.
  - Ngày tháng năm ghi trên đơn (DD/MM/YYYY).
  - Số công văn / Số hiệu đơn từ.
- **FR-META-02 (Cập nhật Metadata)**: Cán bộ có thể chủ động sửa lại thông tin metadata bị bóc tách sai.

### Module 5: Tìm kiếm Toàn văn (Search Engine)

- **FR-SRCH-01 (Full-text Search)**: Tìm kiếm theo từ khóa trên trường `content` (văn bản OCR) và `title`.
- **FR-SRCH-02 (Xử lý Tiếng Việt)**: Tự động hỗ trợ tìm kiếm không dấu (vd: tìm "xin nghi hoc" vẫn ra "xin nghỉ học").
- **FR-SRCH-03 (Fuzzy Search)**: Tìm kiếm chấp nhận lỗi gõ/lỗi OCR nhỏ (fuzziness=AUTO/edit distance ≤ 2).
- **FR-SRCH-04 (Highlighting)**: Trả về các mẩu văn bản chứa từ khóa được highlight tag `<em>kw</em>`.
- **FR-SRCH-05 (Filter & Sort)**: Lọc kết quả theo Khoảng ngày, Danh mục, Trạng thái.

### Module 6: Quản lý Người dùng (User Management - Admin)

- **FR-USR-01 (Tạo mới User)**: Thêm cán bộ mới với các thông tin: username, email, full_name, role, default password.
- **FR-USR-02 (Quản lý Trạng thái)**: Khóa/Mở khóa tài khoản (`is_active = false/true`).
- **FR-USR-03 (Đổi Mật khẩu/Role)**: Đổi quyền hoặc reset mật khẩu người dùng.

### Module 7: Nhật ký Hệ thống (Audit Log - Admin)

- **FR-LOG-01 (Ghi Log Tự động)**: Tự động ghi lại log với thông tin: `user_id`, `action`, `resource_type`, `resource_id`, `ip_address`, `timestamp`.
- **FR-LOG-02 (Tra cứu Audit Log)**: Admin lọc log theo loại hành động, người thực hiện hoặc khoảng thời gian.

---

## TODO

- [ ] Hoàn thiện sơ đồ Use Case chi tiết cho từng Module.
- [ ] Xây dựng bảng ma trận phân quyền Chi tiết (Matrix Permission).

## References

- SRS.md
- UseCase.md
- API.md
