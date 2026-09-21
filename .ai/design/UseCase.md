# Use Case — Đặc tả ca sử dụng

## Purpose

Mô tả đầy đủ các ca sử dụng của hệ thống Student-Document-OCR: actors,
use cases, luồng chính, luồng ngoại lệ và điều kiện tiền/hậu.

## Scope

2 actors: Administrator và Staff. 12 use cases chính.

---

## 1. Actors

### 1.1 Administrator (Admin)

**Mô tả:** Quản trị viên hệ thống. Có toàn quyền trên tất cả chức năng.

**Đặc điểm:**
- Tạo và quản lý tài khoản người dùng
- Xem audit log đầy đủ
- Có thể xóa tài liệu
- Cấu hình danh mục tài liệu

### 1.2 Staff (Trợ lý Công tác sinh viên)

**Mô tả:** Cán bộ phòng CTSV sử dụng hệ thống hàng ngày.

**Đặc điểm:**
- Upload và xử lý tài liệu
- Xem và chỉnh sửa kết quả OCR
- Tìm kiếm tài liệu
- Không thể xóa tài liệu, không xem audit log

---

## 2. Use Case Diagram (Text)

```
┌─────────────────────────────────────────────────────────────┐
│                    Student-Document-OCR                       │
│                                                               │
│   UC-01 Đăng nhập ─────────────────── (Admin, Staff)        │
│   UC-02 Upload tài liệu ───────────── (Admin, Staff)        │
│   UC-03 Kích hoạt OCR ─────────────── (Admin, Staff)        │
│   UC-04 Xem kết quả OCR ───────────── (Admin, Staff)        │
│   UC-05 Chỉnh sửa kết quả OCR ─────── (Admin, Staff)       │
│   UC-06 Tìm kiếm tài liệu ─────────── (Admin, Staff)       │
│   UC-07 Xem chi tiết tài liệu ──────── (Admin, Staff)       │
│   UC-08 Download tài liệu ─────────── (Admin, Staff)        │
│   UC-09 Quản lý metadata ──────────── (Admin, Staff)        │
│   UC-10 Xóa tài liệu ──────────────── (Admin only)         │
│   UC-11 Quản lý người dùng ────────── (Admin only)         │
│   UC-12 Xem audit log ─────────────── (Admin only)         │
│                                                               │
└─────────────────────────────────────────────────────────────┘

Admin ─────── UC-01, 02, 03, 04, 05, 06, 07, 08, 09, 10, 11, 12
Staff ─────── UC-01, 02, 03, 04, 05, 06, 07, 08, 09
```

---

## 3. Use Cases (Chi tiết)

---

### UC-01 — Đăng nhập hệ thống

| Field | Value |
|-------|-------|
| **ID** | UC-01 |
| **Actors** | Administrator, Staff |
| **Precondition** | User có tài khoản, hệ thống đang hoạt động |
| **Postcondition** | User nhận được JWT token, được redirect vào Dashboard |

**Main Flow:**
1. User mở trang Login
2. User nhập username và password
3. Nhấn "Đăng nhập"
4. Hệ thống xác thực credentials (bcrypt)
5. Hệ thống phát hành access_token (60min) + refresh_token (7days)
6. Hệ thống ghi AuditLog: action=LOGIN
7. User được redirect đến Dashboard

**Alternative Flow:**
- 4a. Credentials sai → hiển thị "Tên đăng nhập hoặc mật khẩu không đúng"
- 4b. Tài khoản bị vô hiệu hóa → hiển thị "Tài khoản đã bị khóa"

---

### UC-02 — Upload tài liệu

| Field | Value |
|-------|-------|
| **ID** | UC-02 |
| **Actors** | Administrator, Staff |
| **Precondition** | User đã đăng nhập |
| **Postcondition** | Tài liệu được lưu vào MinIO, OCR task được dispatch |

**Main Flow:**
1. User vào trang Document Upload
2. User kéo thả file (hoặc click chọn file)
3. User nhập tiêu đề (optional) và chọn danh mục (optional)
4. Nhấn "Upload"
5. Hệ thống validate: file type (PDF/JPG/PNG/TIFF), size ≤ 50MB
6. Hệ thống upload file lên MinIO
7. Hệ thống tạo Document record (ocr_status=PENDING)
8. Hệ thống dispatch Celery task: process_ocr
9. Hệ thống ghi AuditLog: action=UPLOAD
10. UI hiển thị thông báo thành công + document status

**Alternative Flow:**
- 5a. File type không hợp lệ → báo lỗi "Chỉ chấp nhận PDF, JPG, PNG, TIFF"
- 5b. File > 50MB → báo lỗi "File không được vượt quá 50MB"
- 6a. Upload MinIO thất bại → báo lỗi, không tạo Document record

---

### UC-03 — Kích hoạt OCR (Re-trigger)

| Field | Value |
|-------|-------|
| **ID** | UC-03 |
| **Actors** | Administrator, Staff |
| **Precondition** | Document đã upload, trạng thái DONE hoặc FAILED |
| **Postcondition** | OCR task mới được dispatch |

**Main Flow:**
1. User vào trang Document Detail
2. User nhấn "Chạy lại OCR"
3. Hệ thống kiểm tra trạng thái: không phải PROCESSING
4. Hệ thống dispatch Celery task mới
5. Document status → PENDING
6. UI cập nhật trạng thái real-time (polling hoặc refresh)

**Alternative Flow:**
- 3a. Document đang PROCESSING → báo lỗi "OCR đang được xử lý"

---

### UC-04 — Xem kết quả OCR

| Field | Value |
|-------|-------|
| **ID** | UC-04 |
| **Actors** | Administrator, Staff |
| **Precondition** | Document tồn tại, OCR status = DONE |
| **Postcondition** | User xem được nội dung văn bản OCR |

**Main Flow:**
1. User vào Document Detail
2. Tab "OCR Result" hiển thị raw_text hoặc corrected_text
3. UI hiển thị confidence score (nếu có)
4. UI phân biệt text gốc và text đã chỉnh sửa (nếu is_corrected=true)

**Alternative Flow:**
- 2a. OCR status = FAILED → hiển thị thông báo lỗi + nút "Chạy lại"
- 2b. OCR status = PROCESSING → hiển thị spinner + "Đang xử lý..."
- 2c. OCR status = PENDING → hiển thị "Đang chờ xử lý..."

---

### UC-05 — Chỉnh sửa kết quả OCR

| Field | Value |
|-------|-------|
| **ID** | UC-05 |
| **Actors** | Administrator, Staff |
| **Precondition** | Document tồn tại, OCR status = DONE |
| **Postcondition** | corrected_text được lưu, Elasticsearch index được cập nhật |

**Main Flow:**
1. User xem OCR result (UC-04)
2. User nhấn "Chỉnh sửa"
3. UI hiển thị text editor với nội dung OCR
4. User chỉnh sửa văn bản
5. User nhấn "Lưu"
6. Hệ thống lưu corrected_text, cập nhật is_corrected=true
7. Hệ thống re-index document trong Elasticsearch với corrected_text
8. Hệ thống ghi AuditLog: action=EDIT_OCR

---

### UC-06 — Tìm kiếm tài liệu

| Field | Value |
|-------|-------|
| **ID** | UC-06 |
| **Actors** | Administrator, Staff |
| **Precondition** | User đã đăng nhập |
| **Postcondition** | Kết quả tìm kiếm được hiển thị với highlight |

**Main Flow:**
1. User vào trang Search
2. User nhập từ khóa vào ô tìm kiếm
3. User có thể chọn filter: danh mục, ngày, trạng thái OCR
4. Nhấn "Tìm kiếm" hoặc Enter
5. Hệ thống thực hiện Elasticsearch query
6. Kết quả hiển thị: tiêu đề, đoạn highlight, metadata
7. User có thể click vào kết quả → Document Detail
8. Hệ thống ghi AuditLog: action=SEARCH

**Alternative Flow:**
- 2a. Từ khóa trống → không thực hiện search
- 5a. Không có kết quả → hiển thị "Không tìm thấy tài liệu phù hợp"

---

### UC-07 — Xem chi tiết tài liệu

| Field | Value |
|-------|-------|
| **ID** | UC-07 |
| **Actors** | Administrator, Staff |
| **Precondition** | Document tồn tại và chưa bị xóa (hoặc là Admin) |
| **Postcondition** | User xem đầy đủ thông tin tài liệu |

**Main Flow:**
1. User click vào tài liệu từ danh sách hoặc search result
2. Hệ thống load Document Detail
3. UI hiển thị: tiêu đề, thông tin upload, danh mục, metadata, OCR status
4. Tab "Preview": xem ảnh/PDF preview
5. Tab "OCR Result": xem nội dung OCR
6. Tab "Metadata": xem metadata extract

---

### UC-08 — Download tài liệu

| Field | Value |
|-------|-------|
| **ID** | UC-08 |
| **Actors** | Administrator, Staff |
| **Precondition** | Document tồn tại |
| **Postcondition** | File gốc được tải về |

**Main Flow:**
1. User ở trang Document Detail
2. User nhấn nút "Download"
3. Hệ thống generate presigned URL từ MinIO (valid 5 phút)
4. Browser tải file

---

### UC-09 — Quản lý metadata

| Field | Value |
|-------|-------|
| **ID** | UC-09 |
| **Actors** | Administrator, Staff |
| **Precondition** | Document tồn tại |
| **Postcondition** | Metadata được cập nhật, ES index được sync |

**Main Flow:**
1. User vào tab "Metadata" trong Document Detail
2. User chỉnh sửa: student_id, student_name, document_date, category
3. Nhấn "Lưu metadata"
4. Hệ thống cập nhật DocumentMetadata
5. Hệ thống sync metadata vào Elasticsearch index

---

### UC-10 — Xóa tài liệu (Admin only)

| Field | Value |
|-------|-------|
| **ID** | UC-10 |
| **Actors** | Administrator |
| **Precondition** | Document tồn tại, user là Admin |
| **Postcondition** | Document bị soft delete, không hiện trong danh sách Staff |

**Main Flow:**
1. Admin ở Document Detail
2. Nhấn "Xóa tài liệu"
3. Hiển thị confirmation dialog
4. Admin confirm
5. Hệ thống set is_deleted=true, deleted_by=admin_id
6. Hệ thống xóa document khỏi Elasticsearch index
7. Hệ thống ghi AuditLog: action=DELETE

**Alternative Flow:**
- 4a. Admin hủy → không xóa

---

### UC-11 — Quản lý người dùng (Admin only)

| Field | Value |
|-------|-------|
| **ID** | UC-11 |
| **Actors** | Administrator |
| **Precondition** | User là Admin |
| **Postcondition** | User được tạo/cập nhật/vô hiệu hóa |

**Main Flow (Tạo user):**
1. Admin vào User Management
2. Nhấn "Thêm người dùng"
3. Điền form: username, email, full_name, password, role
4. Nhấn "Tạo"
5. Hệ thống tạo User, hash password bằng bcrypt

**Main Flow (Vô hiệu hóa):**
1. Admin chọn user từ danh sách
2. Toggle "Trạng thái hoạt động" → OFF
3. Hệ thống set is_active=false

---

### UC-12 — Xem audit log (Admin only)

| Field | Value |
|-------|-------|
| **ID** | UC-12 |
| **Actors** | Administrator |
| **Precondition** | User là Admin |
| **Postcondition** | Admin xem được lịch sử thao tác |

**Main Flow:**
1. Admin vào trang Audit Log
2. Filter theo: user, action, khoảng thời gian
3. Nhấn "Lọc"
4. Danh sách audit log hiển thị với: thời gian, user, action, resource

---

## TODO

- [ ] Vẽ Use Case Diagram bằng PlantUML
- [ ] Bổ sung Sequence Diagram cho UC-02 (upload + async OCR)
- [ ] Xác nhận với Phòng CTSV về quy trình thực tế
- [ ] Xem xét thêm UC: Export search results

## References

- .ai/design/API.md
- .ai/design/SRS.md
- .ai/design/SequenceDiagram.md
- .ai/PROJECT_SPEC.md
