# HƯỚNG DẪN KIỂM THỬ PHÂN HỆ ELASTICSEARCH & SEARCH API (DocuCTSV)
**Thành viên phụ trách**: Phan Thành Phát (MSSV: 2212463)  
**Phân hệ**: Module 3 & Module 4 — Máy chủ tìm kiếm Elasticsearch, CSDL & Backend Search API  
**Mục tiêu**: Hướng dẫn chi tiết cho các thành viên trong nhóm kiểm thử toàn bộ 16 tính năng tìm kiếm, đánh giá IR, chống làm giả số, quản lý SLA và tích hợp Side-by-Side Live Editor.

---

## I. KHỞI ĐỘNG HỆ THỐNG ĐỂ TEST

### Cách 1: Khởi động nhanh bằng 1 cú click
Chạy file script có sẵn tại thư mục gốc:
```cmd
.\run_app.bat
```
*(Hoặc PowerShell: `.\run_app.ps1`)*

### Cách 2: Khởi động thủ công bằng lệnh
```powershell
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

Sau khi server chạy, truy cập tài liệu API trực quan tại:
👉 **Swagger UI**: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)  
👉 **ReDoc**: [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)

---

## II. CHẠY BỘ KIỂM THỬ TỰ ĐỘNG (AUTOMATED TEST SUITE)

Để kiểm chứng toàn bộ mã nguồn hoạt động chính xác 100%, bạn chỉ cần chạy lệnh sau trong thư mục dự án:

```powershell
# 1. Chạy 25 test chuyên sâu cho phân hệ Elasticsearch & Search API
pytest backend/tests/test_search.py -v

# 2. Chạy toàn bộ 124 test của cả hệ thống Backend
pytest backend/tests -v
```
> **Kết quả chuẩn**: `25/25 PASSED (100%)` cho test_search.py và `124/124 PASSED (100%)` cho toàn bộ Backend.

---

## III. HƯỚNG DẪN TEST CHI TIẾT TỪNG TÍNH NĂNG (SWAGGER UI & CURL)

Tất cả các API dưới đây đều nằm trong nhóm thẻ **`search`** trên giao diện [Swagger UI](http://127.0.0.1:8000/docs). Bạn chỉ việc bấm **"Try it out"**, nhập tham số và bấm **"Execute"**.

---

### 1. Đánh giá Thực nghiệm Khoa học Chất lượng Tìm kiếm (IR Benchmark)
- **Endpoint**: `GET /api/v1/search/evaluation/benchmark` (hoặc `POST`)
- **Mô tả**: Tự động chạy 25 truy vấn độc lập từ file `dataset/ir_ground_truth.json` (EASY, HARD, NEGATIVE) và tính toán các chỉ số Information Retrieval chuẩn quốc tế.
- **Tham số Swagger**:
  - `include_details`: `true`
  - `max_queries`: `10` (hoặc `25` để chạy toàn bộ)
- **Kiểm thử bằng cURL**:
  ```bash
  curl -X GET "http://127.0.0.1:8000/api/v1/search/evaluation/benchmark?include_details=true&max_queries=10"
  ```
- **Kết quả kỳ vọng**: Trả về `precision_at_5`, `precision_at_10`, `recall_at_10`, `mean_average_precision_map`, `mean_reciprocal_rank_mrr`, `negative_rejection_rate = 100.0%`, và `avg_latency_ms < 50ms`.

---

### 2. Xác thực Tính toàn vẹn Số & Chống Làm giả Hồ sơ (QR & SHA-256 Anti-Tamper)
- **Endpoint**: `GET /api/v1/search/verify/{code_or_hash}`
- **Mô tả**: Dùng để quét mã QR hoặc nhập mã số văn bản / SHA-256 nhằm phát hiện hồ sơ bị chỉnh sửa hoặc làm giả (Slide 11 kịch bản báo cáo).
- **Kiểm thử trường hợp Hợp lệ**:
  ```bash
  # Tra cứu theo Document ID hợp lệ trong hệ thống
  curl -X GET "http://127.0.0.1:8000/api/v1/search/verify/41fd8ae61c594624b4da0ee3d024e904"
  ```
  *Kỳ vọng*: `status: "VALID"`, `tamper_check_passed: true`, `file_hash` (chuỗi 64 ký tự SHA-256), cơ quan cấp: *"Phòng Công tác Sinh viên - Trường Đại học Đà Lạt"*.
- **Kiểm thử trường hợp Giả mạo**:
  ```bash
  curl -X GET "http://127.0.0.1:8000/api/v1/search/verify/CTSV-DLU-FAKE9999"
  ```
  *Kỳ vọng*: `status: "NOT_FOUND"`, `is_valid: false`, `tamper_check_passed: false` kèm cảnh báo có dấu hiệu giả mạo.

---

### 3. Tìm kiếm Chịu lỗi OCR Chữ viết tay & Lỗi Chính tả (OCR Error-Tolerant)
- **Endpoint**: `POST /api/v1/search/ocr-tolerant`
- **Mô tả**: Tự động phát hiện nhầm lẫn ký tự OCR thường gặp trên chữ viết tay (0/O trong năm học, 1/l) và mở rộng từ viết tắt hồ sơ CTSV (`hb` -> học bổng, `nvqs` -> nghĩa vụ quân sự, `nckh` -> nghiên cứu khoa học, `kkht` -> khuyến khích học tập).
- **Kiểm thử bằng cURL**:
  ```bash
  curl -X POST "http://127.0.0.1:8000/api/v1/search/ocr-tolerant" \
    -H "Content-Type: application/json" \
    -d '{"query": "don xin hb kkht sv 2O21", "page": 1, "page_size": 5}'
  ```
- **Kết quả kỳ vọng**:
  - `normalized_query`: tự động đổi thành *"don xin học bổng khuyến khích học tập sinh viên 2021"*.
  - `suggested_corrections`: liệt kê chi tiết các từ đã được tự động nắn chỉnh.
  - `results`: danh sách tài liệu tìm thấy tương ứng.

---

### 4. Trích xuất Tọa độ Bounding Box cho Side-by-Side Live Editor
- **Endpoint**: `GET /api/v1/search/documents/{document_id}/spatial-highlights`
- **Mô tả**: Trả về số trang và tọa độ khung hình chữ nhật `[ymin, xmin, ymax, xmax]` của từ khóa để Frontend tự động cuộn đến trang và vẽ hộp highlight màu vàng nổi bật ngay trên file PDF scan gốc (Slide 10 kịch bản báo cáo).
- **Kiểm thử bằng cURL**:
  ```bash
  curl -X GET "http://127.0.0.1:8000/api/v1/search/documents/41fd8ae61c594624b4da0ee3d024e904/spatial-highlights?q=sinh%20vi%C3%AAn"
  ```
- **Kết quả kỳ vọng**:
  - `highlights`: Danh sách các vị trí xuất hiện của từ khóa kèm `page`, `box: [ymin, xmin, ymax, xmax]`, `matched_text` và `confidence`.

---

### 5. Che mờ Dữ liệu Cá nhân Nhạy cảm (PII Masking theo Nghị định 13/2023/NĐ-CP)
- **Endpoint**: `GET /api/v1/search?q=sinh%20viên`
- **Mô tả**:
  - Khi người dùng là **Sinh viên** hoặc **Chưa đăng nhập**: Toàn bộ số CCCD, CMND, Số điện thoại VN, Email cá nhân, và STK ngân hàng trong `content_snippet` và `highlights` sẽ **tự động bị che mờ** (ví dụ: `068******891`, `098****321`, `n***t@gmail.com`).
  - Khi đăng nhập bằng tài khoản **Cán bộ (STAFF)** hoặc **Admin (ADMIN)**: Dữ liệu hiển thị đầy đủ phục vụ đối soát nghiệp vụ.

---

### 6. Quản lý Hạn chót & Theo dõi Tiến độ Hồ sơ (SLA Tracking)
- **Endpoint**: `GET /api/v1/search/sla/summary`
- **Mô tả**: Bảng tổng hợp tiến độ xử lý hồ sơ của phòng CTSV:
  - `OVERDUE`: Hồ sơ chờ duyệt > 5 ngày (ưu tiên cảnh báo đỏ).
  - `EXPIRING_SOON`: Hồ sơ chờ duyệt 3 - 5 ngày (cảnh báo vàng).
  - `ON_TRACK`: Hồ sơ mới tiếp nhận < 3 ngày.
  - `compliance_rate`: Tỷ lệ hồ sơ giải quyết đúng hạn (%).
- **Kiểm thử bằng cURL**:
  ```bash
  curl -X GET "http://127.0.0.1:8000/api/v1/search/sla/summary"
  ```

---

### 7. Phát hiện Trùng lặp Hồ sơ & Gian lận Chính sách (Duplicate Check)
- **Endpoint**: `GET /api/v1/search/documents/{document_id}/duplicate-check`
- **Mô tả**: Quét nhanh trong kho tài liệu để phát hiện xem sinh viên có nộp trùng đơn xin miễn giảm học phí hoặc học bổng hay không.
- **Kết quả kỳ vọng**: Trả về `risk_level` (`SAFE`, `WARNING`, `CRITICAL`), điểm tương đồng `lexical_similarity_score`, danh sách tài liệu nghi vấn trùng lặp và khuyến nghị xử lý cho cán bộ.

---

### 8. Hồ sơ Sinh viên 360° & Dòng thời gian Giấy tờ (Student 360 Profile)
- **Endpoint**: `GET /api/v1/search/student-profile/{student_id}`
- **Kiểm thử**: Nhập MSSV (ví dụ: `20210678`):
  ```bash
  curl -X GET "http://127.0.0.1:8000/api/v1/search/student-profile/20210678"
  ```
- **Kết quả kỳ vọng**: Tái hiện toàn bộ vòng đời sinh viên: tổng đơn đã nộp, đơn đã duyệt, đơn chờ xử lý, biểu đồ phân loại đơn theo danh mục và danh sách mốc sự kiện theo dòng thời gian từ năm nhất đến năm tư.

---

### 9. Cảnh báo Biểu mẫu Cũ & Theo dõi Hiệu lực Pháp lý (Validity Tracker)
- **Endpoint**: `GET /api/v1/search/documents/{document_id}/validity`
- **Mô tả**: Kiểm tra biểu mẫu có còn hiệu lực hay đã hết hạn. Nếu hết hạn, hệ thống trả về nhãn `HẾT HIỆU LỰC (ĐÃ THAY THẾ)` kèm link trỏ ngay đến biểu mẫu mới nhất do nhà trường ban hành.

---

### 10. Phân tích Điểm nóng Dư luận Sinh viên (Trending Topics)
- **Endpoint**: `GET /api/v1/search/analytics/trending-topics`
- **Yêu cầu quyền**: `STAFF` hoặc `ADMIN`.
- **Mô tả**: Ứng dụng thuật toán phân tích tần suất đột biến (Significant Terms) để chỉ ra các chủ đề sinh viên đang quan tâm hoặc phản ánh nhiều nhất trong tháng (Học phí Nghị định 81, Nội trú KTX, Học bổng Hessen, Tạm hoãn NVQS) kèm tỷ lệ tăng trưởng `%`.

---

### 11. Đánh giá Hiệu suất Cán bộ CTSV (Staff Performance Analytics)
- **Endpoint**: `GET /api/v1/search/analytics/staff-performance`
- **Yêu cầu quyền**: `STAFF` hoặc `ADMIN`.
- **Mô tả**: Báo cáo tổng số hồ sơ đã duyệt/từ chối, thời gian xử lý trung bình và tính điểm KPI năng suất (`performance_score`) cho từng cán bộ.

---

### 12. Gợi ý Từ khóa Thời gian thực (Autocomplete / Search-As-You-Type)
- **Endpoint**: `GET /api/v1/search/suggest?q=miễn`
- **Mô tả**: Trả về ngay danh sách các tiêu đề gợi ý và thẻ nhãn liên quan với độ trễ < 15ms.

---

### 13. Tìm kiếm Tài liệu Tương đồng (More Like This)
- **Endpoint**: `GET /api/v1/search/documents/{document_id}/similar`
- **Mô tả**: Tự động gợi ý các hồ sơ, biểu mẫu có nội dung hoặc quy cách tương tự với tài liệu đang mở.

---

### 14. Bảng điều khiển Thống kê Đa chiều (Search Dashboard Analytics)
- **Endpoint**: `GET /api/v1/search/analytics/dashboard`
- **Mô tả**: Trả về dữ liệu vẽ biểu đồ:
  - Thống kê theo dòng thời gian 30 ngày gần nhất (`timeline`).
  - Phân bổ theo danh mục hồ sơ (`categories`).
  - Trạng thái xử lý hồ sơ (`status`).
  - Thống kê chất lượng nhận dạng OCR (`confidence_stats`: min, max, avg, số hồ sơ < 80%).

---

## IV. TỔNG HỢP DANH SÁCH FILE ĐƯỢC CẬP NHẬT TRONG MODULE 3 & 4

Toàn bộ các thay đổi được gói gọn trong phân hệ Module 3 & 4 mà **không làm ảnh hưởng hay xung đột với code OCR hoặc Frontend**:
1. `backend/app/core/elasticsearch.py`: Cấu hình kết nối ES 8.x, Custom Vietnamese Analyzer, ICU Tokenizer, Stopwords & Synonym Graph.
2. `backend/app/routers/search.py`: Toàn bộ 16 endpoint nghiệp vụ và tìm kiếm toàn văn.
3. `backend/app/schemas/search.py`: Tất cả Pydantic response/request models chuẩn hóa.
4. `backend/app/models/documents.py`: Bổ sung mapping trường `is_verified`, `verification_code`, `qr_code_url`.
5. `backend/app/services/search_index_service.py`: Dịch vụ lập chỉ mục và Partial Update tài liệu.
6. `backend/app/services/embedding_service.py`: Dịch vụ Dense Vector Embedding cho Hybrid Search.
7. `backend/app/worker/tasks.py`: Celery Task đồng bộ chỉ mục sau khi OCR hoàn tất.
8. `backend/tests/test_search.py`: Bộ 25 bài test tự động bao phủ 100% chức năng.
9. `scripts/sync_es_index.py`: Script quét và đồng bộ dữ liệu PostgreSQL sang Elasticsearch.
10. `scripts/backup_restore_es.py`: Script sao lưu snapshot và phục hồi chỉ mục.
11. `run_app.bat` & `run_app.ps1`: Script chạy nhanh một cú click cho Windows.
12. `update_module_elasticsearch_phat.zip`: Gói nén sạch (66.5 KB) để chia sẻ nhanh.

---
*Tài liệu được soạn thảo và kiểm thử bởi Phan Thành Phát (MSSV: 2212463) phục vụ dự án DocuCTSV.*
