# Non-Functional Requirement — Yêu cầu Phi chức năng

## Purpose

Tài liệu xác định các tiêu chuẩn và chỉ số kỹ thuật về hiệu năng, độ tin cậy, an toàn, khả năng mở rộng và bảo trì của hệ thống Student-Document-OCR.

## Scope

Hiệu năng (Performance), Độ tin cậy (Reliability), Bảo mật (Security), Khả năng mở rộng (Scalability), Tính tương thích (Portability) và Bảo trì (Maintainability).

---

## 1. Yêu cầu Hiệu năng (Performance Requirements)

| Tiêu chí | Mục tiêu Kỹ thuật | Điều kiện / Môi trường |
|----------|-------------------|------------------------|
| **API Response Latency (p95)** | < 300 ms | Áp dụng cho các API CRUD, Authentication, List. Không tính thời gian xử lý OCR. |
| **Search Response Latency (p95)** | < 500 ms | Thực hiện query Elasticsearch trên tập dữ liệu 10.000 tài liệu. |
| **OCR Processing Speed** | < 10 giây / trang A4 | Chạy trên môi trường CPU-only (4 Cores CPU). |
| **File Upload Speed** | < 2 giây / file 10MB | Chỉ tính thời gian ghi file lên MinIO và tạo bản ghi DB. |
| **Concurrent Users** | ≥ 20 phiên làm việc đồng thời | Hệ thống không bị treo hoặc rò rỉ bộ nhớ. |

---

## 2. Yêu cầu Độ tin cậy & Sẵn sàng (Reliability & Availability)

- **Uptime**: Đạt tỷ lệ sẵn sàng ≥ 99% trong giờ làm việc hành chính (8h00 - 17h00).
- **Data Integrity (Tính nguyên vẹn dữ liệu)**:
  - 100% tài liệu số được lưu trữ song song bản gốc trên MinIO và bản ghi cơ sở dữ liệu PostgreSQL.
  - Sử dụng Database Transactions cho các thao tác ghi dữ liệu liên quan đến nhiều bảng.
- **Fault Tolerance (Khả năng chịu lỗi)**:
  - Nếu Worker OCR bị ngắt đột ngột (crash/restart), Celery task sẽ tự động retry tối đa 3 lần.
  - Nếu Elasticsearch dừng hoạt động, các chức năng upload và quản lý văn bản trên PostgreSQL vẫn hoạt động bình thường (Graceful Degradation).

---

## 3. Yêu cầu Khả năng Mở rộng (Scalability)

- **Storage Scalability**: MinIO Object Storage có khả năng mở rộng dung lượng ổ đĩa dễ dàng (support up to Terabytes).
- **Worker Scalability**: Celery Workers có thể scale horizontal (tăng số lượng container worker) khi số lượng file upload lớn.
- **Search Indexing**: Elasticsearch được thiết kế index sẵn sàng cho việc phân cụm (Sharding & Replication) khi mở rộng.

---

## 4. Khả năng Tương thích & Thích ứng (Portability & Compatibility)

- **Cross-browser Compatibility**: Giao diện React SPA hoạt động hoàn hảo trên các trình duyệt hiện đại: Chrome (v100+), Firefox (v100+), Edge (v100+), Safari (v15+).
- **Containerization**: Toàn bộ hệ thống chạy nhất quán trên Docker Compose trên cả Linux (Ubuntu 22.04 LTS), macOS và Windows 11.
- **Resolution Support**: Giao diện hỗ trợ chuẩn màn hình Desktop từ 1280x720 đến 1920x1080.

---

## 5. Quy chuẩn Mã nguồn & Bảo trì (Maintainability)

- **Test Coverage**: Backend đạt mức bao phủ kiểm thử (Test Coverage) ≥ 70%.
- **Code Quality**:
  - Tuân thủ quy chuẩn PEP8 (Python) bằng công cụ `ruff`.
  - Type Hinting đầy đủ với Python 3.11 (`mypy`).
  - TypeScript Strict Mode cho Frontend.
- **Documentation**: Tất cả API Endpoints tự động xuất bản tài liệu OpenAPI (Swagger UI) tại `/docs`.

---

## TODO

- [ ] Lập kế hoạch kiểm thử tải (Load Testing) bằng Locust để đo đạc các chỉ số thực tế.
- [ ] Thiết lập Prometheus + Grafana dashboard để giám sát tài nguyên CPU/RAM.

## References

- SRS.md
- Architecture.md
- TECH_STACK.md
