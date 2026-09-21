# Security — Kiến trúc & Chính sách Bảo mật

## Purpose

Tài liệu thiết kế các chính sách, cơ chế và kiến trúc bảo mật cho toàn bộ hệ thống Student-Document-OCR nhằm bảo vệ dữ liệu sinh viên và an toàn vận hành.

## Scope

Xác thực (Authentication), Phân quyền (Authorization), Bảo mật Dữ liệu (Data Security), Bảo mật API, Bảo mật Lưu trữ File và Audit Logging.

---

## 1. Nguyên tắc Bảo mật Trung tâm

1. **Least Privilege (Quyền tối thiểu)**: Người dùng và dịch vụ chỉ có đúng các quyền cần thiết để hoàn thành công việc.
2. **Defense in Depth (Bảo vệ nhiều lớp)**: Bảo vệ ở mọi tầng: Network -> Container -> API -> Database -> File Storage.
3. **Never Trust User Input**: Validate nghiêm ngặt mọi dữ liệu đầu vào tại Pydantic Schemas.
4. **Immutability of Audit Trail**: Log kiểm toán không thể bị xóa hoặc sửa đổi bởi người dùng thông thường.

---

## 2. Xác thực & Phân quyền (Authentication & Authorization)

### 2.1 Mã hóa Mật khẩu
- Tất cả mật khẩu người dùng **KHÔNG BAO GIỜ** lưu dưới dạng plaintext.
- Mật khẩu được mã hóa bằng chuẩn `bcrypt` với muối tự động (Salt factor = 12).

### 2.2 JWT (JSON Web Token) Policy
- **Access Token**: Thời hạn ngắn (60 phút). Chứa `user_id`, `role`, `exp`. Ký bằng thuật toán `HS256` với Secret Key mạnh từ môi trường (`SECRET_KEY`).
- **Refresh Token**: Thời hạn dài (7 ngày). Dùng để lấy Access Token mới mà không cần nhập lại mật khẩu.
- **Token Invalidation**: Khi người dùng Đăng xuất (Logout), Refresh Token được thêm vào Redis Blacklist.

### 2.3 Phân quyền Dựa trên Vai trò (RBAC)
- Hệ thống áp dụng 2 vai trò: `ADMIN` và `STAFF`.
- Phân quyền được kiểm tra trực tiếp tại lớp Middleware / Dependency Injection của FastAPI (dùng `Security(get_current_active_user)`).

---

## 3. Bảo mật File Storage & Tải lên (File Upload Security)

1. **Validation định dạng file**:
   - Kiểm tra MIME Type thực tế của file qua thư viện `python-magic` (không chỉ dựa vào phần mở rộng `.pdf`/`.jpg`).
   - Danh sách định dạng cho phép (Whitelist): `application/pdf`, `image/jpeg`, `image/png`, `image/tiff`.
2. **Kích thước tối đa**: Giới hạn tối đa 50MB per file tại FastAPI Router level.
3. **Đổi tên File khi Lưu trữ**: File gốc khi lưu lên MinIO sẽ được sinh tên ngẫu nhiên UUIDv4 để tránh tấn công Path Traversal hoặc trùng tên (`bucket/2026/08/08/a1b2c3d4-xxxx.pdf`).
4. **Truy cập File An toàn**: Không công khai trực tiếp đường dẫn MinIO. Mọi thao tác tải/xem file đều qua **Presigned URL** có thời gian hết hạn (5 phút).

---

## 4. Bảo mật Dữ liệu & Tìm kiếm (Database & Search Security)

- **PostgreSQL**:
  - Kết nối DB sử dụng tài khoản có quyền hạn giới hạn (không dùng superuser `postgres` cho app).
  - Sử dụng ORM (SQLAlchemy) với Parameterized Queries để chống hoàn toàn tấn công **SQL Injection**.
- **Elasticsearch**:
  - Không mở public port 9200 ra ngoài Internet trong môi trường production.
  - Elasticsearch chỉ giao tiếp nội bộ trong mạng Docker Network (`ocr_net`).

---

## 5. Bảo mật API & Mạng (Network & API Security)

- **CORS Policy**: Chỉ cho phép tên miền/origin chính thức của Frontend truy cập API.
- **HTTPS Enforcement**: Trong môi trường Production, Nginx Reverse Proxy bắt buộc bật TLS/SSL (HTTPS) với chuẩn mã hóa TLS 1.2/1.3.
- **Rate Limiting**: Cấu hình giới hạn số lượng request per minute để chống Tấn công Từ chối Dịch vụ (DoS/Brute-force Login).

---

## 6. Nhật ký Kiểm toán (Audit Logging)

- Mọi thao tác quan trọng (`LOGIN`, `UPLOAD`, `DELETE`, `EDIT_OCR`, `SEARCH`) đều tự động lưu vào bảng `AuditLog`.
- Bảng AuditLog **chỉ cho phép hành động INSERT** (Append-only). Không có API hay giao diện nào hỗ trợ UPDATE hoặc DELETE AuditLog.

---

## TODO

- [ ] Sinh chuỗi `SECRET_KEY` ngẫu nhiên 64 ký tự an toàn cho file `.env`.
- [ ] Cấu hình Nginx SSL Certificate (Let's Encrypt / Self-signed dev).

## References

- SRS.md
- NonFunctionalRequirement.md
- API.md
- .ai/design/ERD.md
