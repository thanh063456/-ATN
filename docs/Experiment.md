# Báo cáo Thực nghiệm & Đánh giá Hệ thống (Experiment & Evaluation Report)

> **Đề tài:** Hệ thống Quản lý & Số hóa Tài liệu Công tác Sinh viên (DocuCTSV OCR)  
> **Phương pháp đánh giá:** Kiểm thử Chức năng (Functional), Hiệu năng (Performance) và Độ chính xác (Accuracy).

---

## 1. Kiểm thử Chức năng (Functional Testing)

Bộ kiểm thử tự động được xây dựng bằng `pytest` và `pytest-asyncio` tuân thủ nghiêm ngặt **AAA Pattern (Arrange - Act - Assert)** theo quy ước dự án.

### 1.1 Kết quả kiểm thử các Module API chính

| STT | Module kiểm thử | Số test cases | Kết quả | Thời gian chạy | Ghi chú kiểm thử |
|:---:|---|:---:|:---:|:---:|---|
| **1** | **Xác thực & Phân quyền (Auth & RBAC)** | 4 | **100% Pass (4/4)** | 0.82s | Đăng nhập thành công, từ chối sai mật khẩu (401), chặn token rỗng, lấy profile đúng role. |
| **2** | **Quản lý & Upload Tài liệu (Documents)** | 3 | **100% Pass (3/3)** | 1.15s | Upload PDF thành công (202), chặn định dạng không hỗ trợ (.exe -> 400), cán bộ phê duyệt hồ sơ (APPROVED). |
| **3** | **Trích xuất Metadata & OCR Service** | 2 | **100% Pass (2/2)** | 0.05s | Regex trích xuất chính xác MSSV, Họ tên, Ngày tháng, Số hiệu văn bản, tự động phân loại biểu mẫu. |
| **4** | **Tra cứu Toàn văn (Search API)** | 2 | **100% Pass (2/2)** | 0.45s | Tìm kiếm tiếng Việt có dấu, tìm kiếm không dấu (Asciifolding), tìm kiếm mờ (Fuzzy matching). |
| **TỔNG** | **Toàn bộ Test Suite** | **11** | **11 / 11 PASSED** | **2.47s** | **Tỷ lệ thành công: 100%** |

---

## 2. Kiểm thử Hiệu năng & Khả năng Chịu tải (Performance Benchmark)

Thực nghiệm đo lường trên tập dữ liệu gồm **1,000+ tài liệu thực tế và giả lập** được lập chỉ mục trên Elasticsearch 8 và PostgreSQL 15 dưới tải đồng thời (**Concurrency = 10**).

### 2.1 Độ trễ truy vấn Tra cứu Toàn văn (`GET /api/v1/search`)

| Chỉ số đo lường | Mục tiêu cam kết (NFR) | Kết quả thực nghiệm | Đánh giá |
|---|:---:|:---:|:---:|
| **Thời gian đáp ứng trung bình (Avg Latency)** | $< 1000\text{ ms}$ | **$541.82\text{ ms}$** | ✅ Đạt xuất sắc (vượt 45.8%) |
| **Trung vị thời gian đáp ứng (Median - p50)** | $< 800\text{ ms}$ | **$540.52\text{ ms}$** | ✅ Đạt xuất sắc |
| **Phân vị 90% (p90 Latency)** | $< 1000\text{ ms}$ | **$824.88\text{ ms}$** | ✅ Đạt |
| **Phân vị 95% (p95 Latency)** | $< 1200\text{ ms}$ | **$901.03\text{ ms}$** | ✅ Đạt |
| **Thời gian nhanh nhất (Min Latency)** | — | **$134.63\text{ ms}$** | ✅ Phản hồi tức thì |
| **Thông lượng tìm kiếm (Throughput)** | $> 10\text{ QPS}$ | **$18.0\text{ req/s}$** | ✅ Đáp ứng tốt nhu cầu CTSV |
| **Tỷ lệ truy vấn thành công (Success Rate)** | $99.9\%$ | **$100.0\%\ (200/200)$** | ✅ Hoạt động ổn định |

### 2.2 Hiệu năng Pipeline OCR & Xử lý bất đồng bộ

| Thành phần xử lý | Thời gian đo lường (CPU) | Cơ chế tối ưu |
|---|:---:|---|
| **Upload file lên MinIO** | $15 - 35\text{ ms}$ | Đẩy trực tiếp vào MinIO bucket, stream nhị phân độc lập. |
| **Khởi tạo Celery Task qua Redis** | $< 5\text{ ms}$ | Non-blocking dispatch, client nhận mã `202 Accepted` ngay lập tức. |
| **Nhận dạng VietOCR Transformer** | $0.85 - 2.40\text{ s/trang}$ | Mô hình fine-tuned chạy trên CPU, beamsearch tối ưu. |
| **Trích xuất Metadata (Regex NLP)** | $< 2\text{ ms}$ | Pattern matching biên dịch sẵn (compiled regex). |
| **Đánh chỉ mục Elasticsearch** | $12 - 25\text{ ms}$ | Index bất đồng bộ sau khi trích xuất hoàn tất. |

---

## 3. Đánh giá Độ chính xác (Accuracy & Quality Evaluation)

### 3.1 Độ chính xác Nhận dạng Ký tự Quang học (OCR Evaluation)

Đo lường trên tập dữ liệu thử nghiệm biểu mẫu sinh viên (500 dòng văn bản scan thực tế):

| Mô hình thử nghiệm | Character Error Rate (CER) ↓ | Word Error Rate (WER) ↓ | Độ tin cậy trung bình (Confidence) |
|---|:---:|:---:|:---:|
| **VietOCR Pretrained (Gốc)** | $8.42\%$ | $14.65\%$ | $89.2\%$ |
| **VietOCR Fine-tuned (Đề xuất)** | **$2.15\%$** | **$4.80\%$** | **$96.4\%$** |
| **Mức độ cải thiện** | **Giảm 74.5% lỗi ký tự** | **Giảm 67.2% lỗi từ** | **Tăng +7.2%** |

---

### 3.2 Đánh giá Độ chính xác Tìm kiếm (Information Retrieval - IR Metrics)

Bộ đánh giá đã được xây dựng lại hoàn chỉnh với **Ground Truth độc lập (`dataset/ir_ground_truth.json`)** trên **25 truy vấn thử nghiệm** phân chia thành 3 mức độ khó (10 Easy, 10 Hard, 5 Negative).

#### Bảng đối chiếu: Phương pháp đo lường CŨ (Bị lỗi) vs MỚI (Ground Truth Độc lập)

| Chỉ số đo lường | Phương pháp CŨ (Bị lỗi) | Phương pháp MỚI (Chuẩn hóa) | Nhận xét phân tích |
|---|:---:|:---:|---|
| **Số lượng truy vấn** | 5 queries | **25 queries** | Mở rộng quy mô mẫu, bao phủ các trường hợp khó/âm tính. |
| **Cơ chế xác định Relevance** | Circular keyword-match | **Ground Truth ID độc lập** | Loại bỏ logic vòng lặp tự so khớp từ khóa. |
| **Precision@5 (Mẫu cố định = 5)** | $100.0\%$ (thổi phồng) | **$45.6\%$** | Trung thực với truy vấn phức tạp và truy vấn âm tính. |
| **Precision@10 (Mẫu cố định = 10)** | $100.0\%$ (thổi phồng) | **$50.8\%$** | Mẫu số luôn cố định bằng 10 theo đúng chuẩn IR. |
| **Recall@10 (Công thức thật)** | $94.0\%$ (gán cứng) | **$6.22\%$** | Tính trên tập dữ liệu 1,000+ tài liệu ($\text{Top-10}/\text{Total}$). |
| **F1-Score (P@10 & R@10)** | $96.91\%$ (tính từ số bịa) | **$4.23\%$** | F1 thực tế khi giới hạn Top-10 trên kho dữ liệu lớn. |
| **Mean Average Precision (MAP)** | $100.0\%$ | **$44.70\%$** | Đánh giá chính xác chất lượng thứ hạng trả về. |
| **Mean Reciprocal Rank (MRR)** | $1.000$ | **$0.4180$** | Vị trí trung bình của kết quả đúng đầu tiên. |

#### Chi tiết Đánh giá theo Nhóm Độ khó

| Nhóm độ khó | Số lượng Query | Precision@5 (%) | Precision@10 (%) | Recall@10 (%) | MAP (%) | MRR |
|---|:---:|:---:|:---:|:---:|:---:|:---:|
| **EASY (Dễ: Khớp trực tiếp biểu mẫu)** | 10 | **$74.0\%$** | **$82.0\%$** | **$13.7\%$** | **$72.9\%$** | **$0.6867$** |
| **HARD (Khó: Viết tắt, đồng nghĩa, không dấu)** | 10 | **$40.0\%$** | **$45.0\%$** | **$1.85\%$** | **$38.85\%$** | **$0.3583$** |
| **NEGATIVE (Âm tính: Ngoài phạm vi CTSV)** | 5 | **$0.0\%$** | **$0.0\%$** | **$0.0\%$** | **$0.0\%$** | **$0.0000$** |
| **Macro-Average (Toàn bộ 25 Queries)** | **25** | **$45.6\%$** | **$50.8\%$** | **$6.22\%$** | **$44.70\%$** | **$0.4180$** |

---

## 4. Bảng Tổng hợp Đối chiếu Yêu cầu Phi chức năng (NFR Compliance)

| Yêu cầu Phi chức năng | Chỉ số yêu cầu | Kết quả Đạt được | Kết luận |
|---|---|---|:---:|
| **Thời gian phản hồi tìm kiếm** | $< 1.0\text{ giây}$ | $0.54\text{ giây}$ (Median) | **ĐẠT** |
| **Thời gian xử lý OCR mỗi trang** | $< 5.0\text{ giây}$ | $1.60\text{ giây}$ (Trung bình) | **ĐẠT** |
| **Độ chính xác nhận dạng OCR** | $\text{CER} < 5\%$ | $\text{CER} = 2.15\%$ | **ĐẠT** |
| **Bảo mật truy cập & Phân quyền** | JWT + RBAC 3 vai trò | Đã xác thực trên toàn bộ Endpoints | **ĐẠT** |
| **Tính toàn vẹn & Truy vết** | Ghi nhận Audit Log | Bảng `audit_logs` lưu trữ mọi thay đổi trạng thái | **ĐẠT** |
| **Khả năng mở rộng lưu trữ** | Tách biệt Storage & Compute | MinIO S3 + Celery Worker Worker Pool | **ĐẠT** |
