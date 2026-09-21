# UI — Thiết kế giao diện người dùng

## Purpose

Mô tả chức năng và layout của 11 màn hình trong hệ thống Student-Document-OCR.
Đây là spec level — chưa phải mockup hoặc code.

## Scope

11 màn hình: Login, Dashboard, Document List, Document Upload, OCR Processing,
OCR Result, Document Detail, Search, Search Result, User Management, Audit Log.

---

## Quy ước UI

| Item | Quy ước |
|------|---------|
| **Layout** | Sidebar cố định bên trái + Content area chính |
| **Sidebar** | Navigation: Dashboard, Documents, Search, (Admin: Users, Audit Log) |
| **Breakpoint** | Desktop-first (min 1280px width) |
| **Color scheme** | [TBD — ADR-008 frontend UI library] |
| **Typography** | [TBD — sau khi chọn UI library] |
| **Locale** | Tiếng Việt |
| **Date format** | `DD/MM/YYYY HH:mm` |

---

## Screen 1 — Login (`/login`)

**Access:** Public (no auth required)  
**Actor:** All users

**Components:**
- Logo và tên hệ thống: "Hệ thống quản lý tài liệu CTSV"
- Form đăng nhập:
  - Input: Tên đăng nhập (autofocus)
  - Input: Mật khẩu (password toggle)
  - Button: "Đăng nhập" (loading state khi submitting)
  - Error message hiển thị dưới form (nếu sai credentials)
- Không có link đăng ký (system-managed accounts)

**UX Notes:**
- Enter key submit form
- Redirect đến Dashboard sau khi đăng nhập thành công
- Nếu đã có token hợp lệ → auto redirect Dashboard (không show Login)

---

## Screen 2 — Dashboard (`/`)

**Access:** ADMIN, STAFF  
**Actor:** All users

**Components:**
- **Header:** Tên user + role + nút Đăng xuất
- **Thống kê nhanh (4 cards):**
  - Tổng số tài liệu
  - Đang chờ OCR (PENDING + PROCESSING)
  - OCR thành công (DONE)
  - OCR thất bại (FAILED)
- **Bảng Tài liệu gần đây (10 items):**
  - Cột: Tiêu đề, Danh mục, Ngày upload, Trạng thái OCR
  - Link: Xem tất cả → Documents List
- **Trạng thái hệ thống (Admin only):**
  - PostgreSQL: OK/Error
  - Elasticsearch: OK/Error
  - MinIO: OK/Error
  - Celery: Active workers count

---

## Screen 3 — Document List (`/documents`)

**Access:** ADMIN, STAFF  
**Actor:** All users

**Components:**
- **Filter bar:**
  - Dropdown: Danh mục (All + categories)
  - Dropdown: Trạng thái OCR (All, PENDING, PROCESSING, DONE, FAILED)
  - Date range picker: Ngày upload từ - đến
  - Button: Áp dụng filter, Reset
- **Action bar:**
  - Button: "+ Upload tài liệu" → navigate /documents/upload
  - Tổng số kết quả: "Hiển thị X / Y tài liệu"
- **Bảng tài liệu:**
  - Cột: Checkbox, Tiêu đề, Loại file (icon), Danh mục, Người upload, Ngày upload, OCR Status (badge), Actions
  - Actions: Xem, Download, (Admin: Xóa)
  - Sort: Tiêu đề, Ngày upload (click header)
- **Pagination:** Page-based, 20 items/page

**OCR Status Badge:**
- PENDING → gray badge
- PROCESSING → blue badge + spinner
- DONE → green badge
- FAILED → red badge

---

## Screen 4 — Document Upload (`/documents/upload`)

**Access:** ADMIN, STAFF  
**Actor:** All users

**Components:**
- **Tiêu đề trang:** "Upload tài liệu mới"
- **Dropzone:**
  - Vùng kéo thả lớn (dashed border)
  - "Kéo thả file vào đây hoặc click để chọn"
  - "Chấp nhận: PDF, JPG, PNG, TIFF. Tối đa 50MB"
  - Preview thumbnail sau khi chọn file
- **Form:**
  - Input: Tiêu đề tài liệu (optional, default: filename)
  - Select: Danh mục (optional)
- **Progress bar:** Hiển thị khi đang upload
- **Button:** "Upload và xử lý OCR" (disabled khi chưa chọn file)
- **Cancel button** → back to Document List

**UX Notes:**
- Sau upload thành công → redirect Document Detail với toast: "Upload thành công. OCR đang được xử lý..."
- Lỗi upload → hiển thị error message, cho phép thử lại

---

## Screen 5 — OCR Processing (Component trong Document Detail)

**Access:** ADMIN, STAFF  
**Actor:** All users

**Hiển thị khi OCR status = PENDING hoặc PROCESSING:**
- Spinner + text: "OCR đang được xử lý..." (PROCESSING)
- text: "Đang chờ OCR..." (PENDING)
- Auto-refresh mỗi 3 giây (polling /api/v1/ocr/{id}/status)
- Progress indicator (nếu có)

---

## Screen 6 — OCR Result (Tab trong Document Detail)

**Access:** ADMIN, STAFF  
**Actor:** All users

**Hiển thị khi OCR status = DONE:**
- **Header:**
  - Badge: "OCR hoàn thành" (green)
  - Confidence score (nếu có): "Độ chính xác: 92%"
  - Thời gian xử lý: "Xử lý trong 3.2 giây"
  - Button: "Chỉnh sửa" | Button: "Chạy lại OCR"
- **Text viewer:**
  - Hiển thị corrected_text (nếu có) hoặc raw_text
  - Indicator "Đã chỉnh sửa thủ công" nếu is_corrected=true
  - Monospace font, scrollable
- **Edit mode** (sau khi click "Chỉnh sửa"):
  - Textarea thay thế text viewer
  - Button: "Lưu" | Button: "Hủy"

**Hiển thị khi OCR status = FAILED:**
- Alert đỏ: "OCR thất bại. Lỗi: {error_message}"
- Button: "Thử lại OCR"

---

## Screen 7 — Document Detail (`/documents/{id}`)

**Access:** ADMIN, STAFF  
**Actor:** All users

**Layout:**
- **Left panel (40%):** File preview (ảnh hoặc PDF viewer)
- **Right panel (60%):** Thông tin + tabs

**Right panel — Info section:**
- Tiêu đề tài liệu (editable inline cho Admin/Staff)
- Danh mục (dropdown, editable)
- Ngày upload, người upload
- Kích thước file, số trang
- OCR Status badge

**Right panel — Tabs:**
- **Tab 1: OCR Result** → Screen 6 content
- **Tab 2: Metadata**
  - MSSV, Tên sinh viên (input fields)
  - Ngày trong tài liệu (date picker)
  - Số văn bản (input)
  - Button: "Lưu metadata"
- **Tab 3: Lịch sử**
  - Timeline: Upload → OCR Started → OCR Done → Edited (nếu có)

**Action bar (trên cùng):**
- Button: "Download" | Button: (Admin) "Xóa"
- Breadcrumb: Documents > {title}

---

## Screen 8 — Search (`/search`)

**Access:** ADMIN, STAFF  
**Actor:** All users

**Components:**
- **Search bar:** Input text lớn + Button "Tìm kiếm"
- **Advanced filter (collapsible):**
  - Danh mục
  - Ngày từ / đến
  - Trạng thái OCR
  - Fuzzy search toggle (bật mặc định)
- **Search tips:** "Tip: Bạn có thể tìm không dấu, hệ thống sẽ tự nhận diện."

**Initial state:** Không có kết quả (chờ user search)

---

## Screen 9 — Search Result (Tích hợp trong Search screen)

**Access:** ADMIN, STAFF  
**Actor:** All users

**Components:**
- Tiêu đề: "X kết quả cho '{query}'"
- **Result list:**
  - Mỗi item:
    - Tiêu đề tài liệu (clickable → Document Detail)
    - Danh mục + Ngày upload
    - Đoạn highlight: "...văn bản **từ khóa** trong ngữ cảnh..."
    - Badge: OCR status
    - MSSV / Tên sinh viên (nếu có metadata)
- **Pagination:** trang 1/N
- **No result state:** "Không tìm thấy kết quả. Thử từ khóa khác hoặc bỏ filter."

**Highlight style:**
- Từ khóa được wrap trong `<em>` → bold + highlight màu vàng

---

## Screen 10 — User Management (`/admin/users`) — Admin only

**Access:** ADMIN only  
**Actor:** Administrator

**Components:**
- **Table:**
  - Cột: Username, Họ tên, Email, Role (badge), Trạng thái, Lần đăng nhập cuối, Actions
  - Actions: Sửa thông tin, Toggle active/inactive
- **Button:** "+ Thêm người dùng" → Modal

**Add/Edit User Modal:**
- Input: Username (readonly khi edit)
- Input: Họ tên đầy đủ
- Input: Email
- Input: Mật khẩu (chỉ khi tạo mới)
- Select: Role (ADMIN / STAFF)
- Button: "Lưu"

---

## Screen 11 — Audit Log (`/admin/audit-logs`) — Admin only

**Access:** ADMIN only  
**Actor:** Administrator

**Components:**
- **Filter bar:**
  - Select: Người dùng
  - Select: Hành động (LOGIN, UPLOAD, DELETE, EDIT_OCR, SEARCH...)
  - Date range: Từ - đến
  - Button: Lọc, Reset
- **Table:**
  - Cột: Thời gian, Người dùng, Hành động, Đối tượng, IP, Chi tiết
  - Click row → expand để xem detail JSON
- **Pagination:** 50 items/page

---

## TODO

- [ ] Tạo wireframe/mockup cho Screen 4 (Upload) và Screen 7 (Detail)
- [ ] Quyết định ADR-008 (UI library) → xác định design system
- [ ] Thiết kế responsive cho màn hình nhỏ hơn
- [ ] Xác nhận ngôn ngữ UI với GVHD (tiếng Việt toàn bộ)
- [ ] Thiết kế empty states và error states cho tất cả screens
- [ ] Thiết kế loading skeletons cho danh sách

## References

- .ai/design/UseCase.md
- .ai/design/API.md
- frontend/README.md
- frontend/ComponentGuide.md
- .ai/DECISIONS.md (ADR-008)
