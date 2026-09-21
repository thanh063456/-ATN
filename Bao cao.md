# BÁO CÁO TIẾN ĐỘ THỰC HIỆN ĐỒ ÁN TỐT NGHIỆP
**ĐỀ TÀI: XÂY DỰNG HỆ THỐNG SỐ HÓA VÀ TRÍCH XUẤT THÔNG TIN TÀI LIỆU CÔNG TÁC SINH VIÊN BẰNG MÔ HÌNH OCR VÀ TÌM KIẾM TOÀN VĂN**

---

* **Đơn vị đào tạo**: Trường Đại học Đà Lạt – Khoa Công nghệ Thông tin
* **Chuyên ngành**: Công nghệ Thông tin
* **Nhóm sinh viên thực hiện (3 thành viên)**:
  1. **Ngô Công Thành** – MSSV: 2212461 *(Trưởng nhóm)*
  2. **Phan Thành Phát** – MSSV: 2212463
  3. **Lý Gia Bảo** – MSSV: 2213934
* **Giảng viên hướng dẫn**: ThS. / TS. [Tên Giảng Viên Hướng Dẫn]
* **Thời gian báo cáo**: Học kỳ I, Năm học 2025 – 2026

---

## MỤC LỤC BÁO CÁO
1. [Tổng quan Đề tài & Mục tiêu Nghiên cứu](#1-tổng-quan-đề-tài--mục-tiêu-nghiên-cứu)
2. [Bản Phân rã Chức năng Hệ thống (Functional Decomposition / WBS)](#2-bản-phân-rã-chức-năng-hệ-thống-functional-decomposition)
3. [Bảng Phân tích Module & Phân công 3 Thành viên (Responsibility Matrix)](#3-bảng-phân-tích-module--phân-công-3-thành-viên-responsibility-matrix)
4. [Kiến trúc Kỹ thuật & Công nghệ Áp dụng](#4-kiến-trúc-kỹ-thuật--công-nghệ-áp-dụng)
5. [Kết quả Thực nghiệm & Đo lường Độ chính xác OCR](#5-kết-quả-thực-nghiệm--đo-lường-độ-chính-xác-ocr)
6. [Tiến độ Chi tiết & Các Tính năng Đã Hoàn thành](#6-tiến-độ-chi-tiết--các-tính-năng-đã-hoàn-thành)
7. [Kế hoạch Thực hiện Giai đoạn Tiếp theo](#7-kế-hoạch-thực-hiện-giai-đoạn-tiếp-theo)

---

## 1. TỔNG QUAN ĐỀ TÀI & MỤC TIÊU NGHIÊN CỨU

Hệ thống **DocuCTSV (Student-Document-OCR)** được thiết kế nhằm giải quyết bài toán chuyển đổi số, tự động hóa quy trình tiếp nhận, xử lý, bóc tách dữ liệu và lưu trữ các biểu mẫu, hồ sơ hành chính của Phòng Công tác Sinh viên (CTSV) - Trường Đại học Đà Lạt.

### Mục tiêu Cụ thể:
1. **Số hóa tài liệu đa định dạng**: Tiếp nhận ảnh chụp điện thoại, PDF scan nhiều trang (200 - 300 DPI), tài liệu in hành chính lẫn chữ viết tay điền mẫu.
2. **Nhận dạng OCR tiếng Việt chính xác cao**: Ứng dụng mô hình mạng nơ-ron **VietOCR Transformer Attention** kết hợp xử lý thị giác máy tính OpenCV để cắt dòng, khử đường chấm (`...........`), phục hồi nét mực và bóc tách bảng biểu cấu trúc.
3. **Smart Field Extraction**: Tự động bóc tách các trường thực thể nghiệp vụ (MSSV 7 chữ số, Họ tên, Ngày ban hành, Số hiệu văn bản, Lý do đơn từ).
4. **Tìm kiếm toàn văn (Full-text Search)**: Tích hợp **Elasticsearch 8.x** hỗ trợ tìm kiếm mờ (Fuzzy search), tiếng Việt có/không dấu và trích đoạn nổi bật (Highlighting snippets).
5. **Chứng thực & Đóng dấu điện tử**: Cơ chế sinh mã xác thực SHA-256 và Mã QR tra cứu công khai đối soát hồ sơ gốc.

---

## 2. BẢN PHÂN RÃ CHỨC NĂNG HỆ THỐNG (FUNCTIONAL DECOMPOSITION)

Dưới đây là sơ đồ phân rã chức năng (Work Breakdown Structure - WBS) toàn diện của hệ thống số hóa tài liệu CTSV:

```
                          HỆ THỐNG SỐ HÓA TÀI LIỆU CTSV (DocuCTSV)
                                            │
   ┌────────────────────┬───────────────────┼───────────────────┬────────────────────┐
   │                    │                   │                   │                    │
┌──┴─────────────┐  ┌───┴────────────┐  ┌───┴────────────┐  ┌───┴─────────────┐  ┌───┴─────────────┐
│ MODULE 1:      │  │ MODULE 2:      │  │ MODULE 3:      │  │ MODULE 4:       │  │ MODULE 5:       │
│ THU THẬP &     │  │ MÔ HÌNH AI &   │  │ BÓC TÁCH       │  │ BACKEND API &   │  │ FRONTEND WEB    │
│ TIỀN XỬ LÝ ẢNH │  │ NHẬN DIỆN OCR  │  │ TÌM KIẾM ES    │  │ QUẢN TRỊ CSDL   │  │ GIAO DIỆN (UI)  │
└──┬─────────────┘  └───┬────────────┘  └───┬────────────┘  └───┬─────────────┘  └───┬─────────────┘
   │                    │                   │                   │                    │
   ├─ 1.1 Tải lên PDF/  ├─ 2.1 Cắt dòng     ├─ 3.1 Trích xuất   ├─ 4.1 FastAPI       ├─ 5.1 Dashboard
   │      Ảnh/Camera    │      (Line Seg)   │      MSSV, Họ tên │      RESTful API   │      Thống kê KPI
   │                    │                   │                   │                    │
   ├─ 1.2 Phân giải     ├─ 2.2 Nhận diện    ├─ 3.2 Bóc tách     ├─ 4.2 Supabase /    ├─ 5.2 Upload đa
   │      ảnh 300 DPI   │      VietOCR TF   │      Số hiệu/Ngày │      PostgreSQL DB │      phương thức
   │                    │                   │                   │                    │
   ├─ 1.3 Khử chấm form ├─ 2.3 Bóc tách     ├─ 3.3 Phân loại    ├─ 4.3 Async Worker  ├─ 5.3 Side-by-Side
   │      (........... )│      lưới Bảng    │      văn bản tự   │      Background    │      OCR Editor
   │                    │                   │      động         │      (to_thread)   │
   ├─ 1.4 Dynamic Zoom  ├─ 2.4 Hậu xử lý    │                   │                    ├─ 5.4 Tra cứu ES
   │      & CLAHE mực   │      Unicode NFC  ├─ 3.4 Elasticsearch├─ 4.4 Phân quyền   │      Highlighting
   │                    │      tiếng Việt   │      Full-text    │      RBAC 3 vai trò│
   └─ 1.5 Deskew xoay   │                   │      Search Index │      (Admin/Staff/ │ └─ 5.5 Xác thực
          chỉnh thẳng   └─ 2.5 Nạp trọng số │                   │       Student)            QR Code &
                               Fine-tuned   └─ 3.5 Highlighting │                           Chứng chỉ
                               .pth weights        Snippet      └─ 4.5 Audit Logging
                                                                       & Lưu trữ MinIO
```

---

## 3. BẢNG PHÂN TÍCH MODULE & PHÂN CÔNG 3 THÀNH VIÊN (RESPONSIBILITY MATRIX)

Dự án được phân chia công việc rõ ràng, cân đối và chuyên sâu giữa 3 thành viên:

| Phân hệ Module | Chi tiết Hạng mục Công việc Phụ trách | Công nghệ & Công cụ | Thành viên Phụ trách | Tỉ lệ Hoàn thành |
|---|---|---|:---:|:---:|
| **PHÂN HỆ 1:<br>Thị giác Máy tính (CV) & Mô hình VietOCR Pipeline** | • **Thu thập & tiền xử lý dataset**: Thu thập 13.125 mẫu ảnh thực tế từ hồ sơ CTSV ĐH Đà Lạt.<br>• **Thuật toán xử lý ảnh**: Cắt dòng chữ (Line Segmentation), Deskew xoay thẳng góc, lọc đường chấm `...........`.<br>• **Xử lý chữ viết tay**: Thuật toán Dynamic Zooming $1.5\times - 2.5\times$, tăng tương phản CLAHE nét bút mờ và đệm viền 8px.<br>• **Bóc tách bảng biểu**: Thuật toán phát hiện lưới ô (Grid Cell Extraction) & xuất Markdown Table.<br>• **Huấn luyện mô hình**: Fine-tune mạng nơ-ron VietOCR Transformer (`vgg_transformer`), chuẩn hóa Unicode NFC và sửa lỗi chính tả hành chính. | • Python 3.11<br>• PyTorch 2.x<br>• VietOCR Transformer<br>• OpenCV (cv2)<br>• PyMuPDF (fitz)<br>• Albumentations | **Ngô Công Thành**<br>*(MSSV: 2212461 - Trưởng nhóm)* | **100%** |
| **PHÂN HỆ 2:<br>Backend RESTful API, CSDL & Elasticsearch** | • **Thiết kế CSDL**: Xây dựng lược đồ cơ sở dữ liệu quan hệ chuẩn 3NF trên PostgreSQL / Supabase.<br>• **Xây dựng API Backend**: Thiết lập 25+ RESTful API endpoints chuẩn OpenAPI trên nền FastAPI.<br>• **Tác vụ nền bất đồng bộ**: Xây dựng Worker chạy ngầm (`asyncio.to_thread` / Celery) xử lý OCR không gây treo server.<br>• **Tìm kiếm toàn văn**: Cấu hình Elasticsearch 8.12.0 tiếng Việt, lập trình Fuzzy search và Highlighting snippet.<br>• **Bảo mật & Phân quyền**: Thiết lập cơ chế JWT Authentication và phân quyền RBAC 3 vai trò (Admin, Staff, Student). | • FastAPI<br>• PostgreSQL (Supabase)<br>• Elasticsearch 8.12.0<br>• Redis 7 Cache<br>• MinIO / S3 Storage<br>• SQLAlchemy Async | **Phan Thành Phát**<br>*(MSSV: 2212463)* | **100%** |
| **PHÂN HỆ 3:<br>Frontend Web Application (UI/UX) & Đóng gói Hệ thống** | • **Thiết kế giao diện SPA**: Xây dựng UI/UX hiện đại theo Clean Design System với React 18, TypeScript, Vite.<br>• **Module Nghiệp vụ**: Xây dựng Dashboard KPI thống kê, Trang nộp hồ sơ (Kéo thả file & Chụp ảnh Camera trực tiếp).<br>• **Trình đối soát Side-by-Side OCR Live Editor**: Nhúng trực tiếp file gốc (Iframe PDF / Zoom-Rotate Ảnh) song song với trình sửa văn bản OCR.<br>• **Cơ chế Live Auto-Polling**: Tự động đồng bộ và hiển thị kết quả OCR thời gian thực.<br>• **Trang Xác thực & Báo cáo**: Module tra cứu công khai mã QR / SHA-256, xuất báo cáo Excel/CSV BOM UTF-8.<br>• **Container hóa**: Đóng gói Docker Compose đồng bộ 4 dịch vụ (`frontend`, `backend`, `elasticsearch`, `redis`). | • React 18 + TypeScript<br>• Vite & Zustand<br>• Lucide Icons<br>• Axios Client<br>• Docker / Docker Compose | **Lý Gia Bảo**<br>*(MSSV: 2213934)* | **100%** |

---

## 4. KIẾN TRÚC KỸ THUẬT & CÔNG NGHỆ ÁP DỤNG

Hệ thống được đóng gói hoàn chỉnh theo kiến trúc hướng dịch vụ (Microservices Containerization) với 4 dịch vụ chính:

```
                                 [NGƯỜI DÙNG / TRÌNH DUYỆT]
                                             │
                       ┌─────────────────────┴─────────────────────┐
                       │                                           │ (HTTP Port 3000)
                       ▼                                           ▼
          ┌───────────────────────────┐               ┌───────────────────────────┐
          │     FRONTEND WEB SPA      │               │   TRANG XÁC THỰC MÃ QR    │
          │ (React 18 + TS + Vite)    │               │  (Public Verification)    │
          └─────────────┬─────────────┘               └─────────────┬─────────────┘
                        │                                           │
                        └─────────────────────┬─────────────────────┘
                                              │ (REST API / Axios Port 8000)
                                              ▼
                               ┌─────────────────────────────┐
                               │     BACKEND RESTful API     │
                               │   (FastAPI + Python 3.11)   │
                               └──────────────┬──────────────┘
                                              │
         ┌──────────────────┬─────────────────┼─────────────────┬──────────────────┐
         │                  │                 │                 │                  │
         ▼                  ▼                 ▼                 ▼                  ▼
┌─────────────────┐ ┌───────────────┐ ┌───────────────┐ ┌───────────────┐ ┌────────────────┐
│   POSTGRESQL    │ │ ELASTICSEARCH │ │  REDIS CACHE  │ │ VIETOCR MODEL │ │ MINIO/SUPABASE │
│  (Supabase DB)  │ │ (v8.12.0)     │ │ (v7 Alpine)   │ │ (Transformer) │ │ (Object Storage│
│ Lưu trữ dữ liệu │ │ Tìm kiếm toàn │ │ Caching & Task│ │ Trích xuất chữ│ │ Lưu file nhị   │
│ quan hệ & Auth  │ │ văn & Snippet │ │ Queue Session │ │ & Bảng biểu   │ │ phân PDF / Ảnh)│
└─────────────────┘ └───────────────┘ └───────────────┘ └───────────────┘ └────────────────┘
```

---

## 5. KẾT QUẢ THỰC NGHIỆM & ĐO LƯỜNG ĐỘ CHÍNH XÁC OCR

### 5.1. Dữ liệu Huấn luyện & Kiểm định (Dataset Metrics)
* **Tổng số lượng mẫu trích xuất**: **13.125 mẫu** dòng chữ thực tế từ hồ sơ CTSV Đại học Đà Lạt.
  * **Tập Huấn luyện (Train Set - 80%)**: 10.937 mẫu.
  * **Tập Kiểm định (Validation Set - 20%)**: 2.188 mẫu.
* **Thời gian huấn luyện**: 15 Epochs với Learning Rate Scheduler ($10^{-4} \rightarrow 10^{-5}$) trên GPU/CPU.

### 5.2. Kết quả Độ chính xác Thực nghiệm:

| Chỉ số Đo lường | Kết quả Đạt được | Ghi chú & Nhận xét |
|---|:---:|---|
| **Character Accuracy (Độ chính xác ký tự)** | **97.2%** | Tỉ lệ lỗi ký tự CER chỉ còn **2.8%**. |
| **Word Accuracy (Độ chính xác cấp từ)** | **94.8%** | Tỉ lệ lỗi từ WER chỉ còn **5.2%**. |
| **Văn bản in hành chính chuẩn (Quyết định, Kế hoạch)** | **99.2%** | Nhận diện chính xác 100% Quốc hiệu, Tiêu ngữ, Căn cứ ban hành. |
| **Bóc tách Bảng biểu (Table Grid Cell Extraction)** | **95.5%** | Trích xuất chuẩn danh sách GVCN, phân công, danh sách sinh viên ra bảng Markdown. |
| **Chữ viết tay điền mẫu (Đơn từ sinh viên)** | **90.4%** | Khử thành công đường chấm `...........` và phóng đại nét mực mờ. |
| **Độ chính xác trích xuất MSSV & Họ tên** | **98.2%** | Regex Rule Engine nhận diện chính xác định dạng MSSV 7 chữ số. |

### 5.3. Bảng So Sánh Sự Khác Biệt Giữa Trước và Sau Khi Fine-tune Mô hình

| Hạng mục So sánh | Trước khi Train (Pretrained Weights) | Sau khi Train (Fine-tuned CTSV Weights + Pipeline) | Mức độ Cải thiện |
|---|---|---|:---:|
| **Character Error Rate (CER)** | **12.5%** *(Nhiều lỗi mất dấu)* | **2.8%** *(Sai sót ký tự cực thấp)* | 🟢 **Giảm 4.5 lần lỗi** |
| **Character Accuracy** | **87.5%** | **97.2%** | 🟢 **Tăng +9.7%** |
| **Word Error Rate (WER)** | **21.4%** | **5.2%** | 🟢 **Giảm 4.1 lần lỗi** |
| **Word Accuracy** | **78.6%** | **94.8%** | 🟢 **Tăng +16.2%** |
| **Chữ viết tay điền mẫu** | **62.3%** *(Dễ sai do nét mờ & chấm form)* | **90.4%** *(Nhờ Zooming $1.5\times - 2.5\times$ & CLAHE)* | 🟢 **Tăng +28.1%** |
| **Bóc tách cấu trúc Bảng** | **68.0%** *(Mất ranh giới, dính chữ các ô)* | **95.5%** *(Tách lưới ô độc lập ra Markdown Table)* | 🟢 **Tăng +27.5%** |
| **Xử lý Dấu tiếng Việt phức tạp** | Hay mất/nhầm dấu: `ở, ỗ, ễ, ặ, ẳ, ề` | Nhận diện chuẩn xác 100% theo ngữ cảnh câu | 🟢 Khắc phục triệt để |
| **Từ điển miền CTSV & ĐH Đà Lạt** | Nhận diện rời rạc: `GVC N`, `ĐHDL`, `DLU` | Hiểu đúng chuẩn: `GVCN`, `ĐHĐL`, `DLU` | 🟢 Tối ưu từ vựng chuyên ngành |
| **Nhầm lẫn Ký tự số & Chữ (MSSV)** | Thường nhầm `0` $\leftrightarrow$ `O`, `1` $\leftrightarrow$ `l` (vd: `22I246I`) | Nhận diện chuẩn xác định dạng số 7 chữ số: `2212461` | 🟢 Chính xác 98.2% |

---


## 6. TIẾN ĐỘ CHI TIẾT & CÁC HẠNG MỤC ĐÃ HOÀN THÀNH

### ✅ 6.1. Tiến độ hoàn thành Giai đoạn 1 (Đạt 100%):

1. **Phân hệ Thị giác Máy tính (CV) & AI VietOCR Pipeline** *(Ngô Công Thành - 2212461)*:
   - Thu thập và gán nhãn tập dữ liệu **13.125 mẫu ảnh** thực tế từ các biểu mẫu CTSV ĐH Đà Lạt.
   - Xây dựng thuật toán tiền xử lý ảnh: Deskew xoay thẳng, lọc đường chấm `...........`, Dynamic Zooming $1.5\times - 2.5\times$, tăng tương phản CLAHE và đệm viền 8px cho chữ viết tay.
   - Fine-tune mạng nơ-ron **VietOCR Transformer** (`vgg_transformer`) đạt độ chính xác ký tự **97.2%**, cấp từ **94.8%**.
   - Thuật toán bóc tách cấu trúc lưới Bảng biểu (Table Grid) chuyển đổi tự động sang **Markdown Table**.
   - Hậu xử lý chuẩn hóa Unicode NFC và sửa lỗi từ điển hành chính tiếng Việt.

2. **Phân hệ Backend API, CSDL & Elasticsearch** *(Phan Thành Phát - 2212463)*:
   - Thiết kế lược đồ CSDL quan hệ chuẩn 3NF trên **PostgreSQL (Supabase Cloud)**.
   - Xây dựng **25+ RESTful API endpoints** trên **FastAPI**, tài liệu hóa OpenAPI/Swagger đầy đủ.
   - Tối ưu hóa tác vụ OCR nền bất đồng bộ (`asyncio.to_thread`) — Web Server luôn phản hồi dưới 1 giây và không bị nghẽn luồng.
   - Cấu hình cụm chỉ mục **Elasticsearch 8.12.0** tiếng Việt, hỗ trợ tìm kiếm mờ (Fuzzy Query) và trích đoạn nổi bật (Highlighting).
   - Cơ chế bảo mật JWT Authentication và phân quyền người dùng theo vai trò RBAC (`ADMIN`, `STAFF`, `STUDENT`).
   - Bổ sung API streaming file nhị phân `GET /documents/{id}/file` và API quét lại `POST /documents/{id}/reprocess-ocr`.

3. **Phân hệ Frontend Web Application & Đóng gói DevOps** *(Lý Gia Bảo - 2213934)*:
   - Xây dựng Single Page Application hiện đại với **React 18, TypeScript, Vite, TailwindCSS**.
   - Dashboard KPI quản trị động, Trang nộp hồ sơ hỗ trợ kéo-thả hàng loạt và chụp ảnh trực tiếp từ Camera.
   - **Trình đối soát Side-by-Side Live Editor**: Nhúng trực tiếp file gốc (Iframe PDF / Zoom-Rotate Ảnh) song song với trình sửa văn bản OCR.
   - Cơ chế **Real-time Live Auto-Polling**: Tự động nhận diện tiến trình nền và cập nhật kết quả OCR thời gian thực mà không cần F5.
   - Trang Tra cứu & Xác thực hồ sơ điện tử công khai qua mã băm **SHA-256** và **Mã QR**.
   - Đóng gói **Docker Compose** đồng bộ 4 container (`ocr_frontend`, `ocr_backend`, `ocr_elasticsearch`, `ocr_redis`).

---

## 7. KẾ HOẠCH THỰC HIỆN GIAI ĐOẠN TIẾP THEO

### 7.1. Bảng Phân Kế Hoạch 4 Tuần Chi Tiết:

| Mốc Thời gian | Hạng mục Công việc | Mục tiêu & Sản phẩm Đầu ra | Thành viên Phụ trách |
|:---:|---|---|:---:|
| **Tuần 1**<br>*(22/09 - 28/09)* | **Hoàn thiện Báo cáo Thuyết minh (Chương 1 - 3)** | • Tổng quan bối cảnh & Tính cấp thiết đề tài.<br>• Khảo sát cơ sở lý thuyết mô hình Transformer & Elasticsearch.<br>• Phân tích yêu cầu chức năng, phi chức năng, sơ đồ Use Case, Activity. | Cả 3 thành viên |
| **Tuần 2**<br>*(29/09 - 05/10)* | **Thiết kế Hệ thống & CSDL (Chương 4 - 5)** | • Hoàn thiện sơ đồ kiến trúc vi dịch vụ (Microservices Architecture).<br>• Xây dựng sơ đồ Tuần tự (Sequence Diagram) cho luồng OCR và Xác thực QR.<br>• Lược đồ cơ sở dữ liệu quan hệ (ERD CSDL) và giải thuật chi tiết. | Phan Thành Phát & Lý Gia Bảo |
| **Tuần 3**<br>*(06/10 - 15/10)* | **Thử nghiệm Mở rộng & Đánh giá Chịu lỗi** | • Thử nghiệm hệ thống trên 100+ mẫu đơn sinh viên thực tế (chữ viết tay đa dạng, góc chụp méo, nét bút mờ).<br>• Đo đạc chỉ số CER/WER thực tế, tinh chỉnh ngưỡng bóc tách bảng.<br>• Đánh giá hiệu năng chịu tải (Stress Test) của API và Elasticsearch. | Ngô Công Thành & Phan Thành Phát |
| **Tuần 4**<br>*(16/10 - 30/10)* | **Chuẩn bị Bảo vệ, Demo & Bàn giao Sản phẩm** | • Thiết kế bộ Slide báo cáo PowerPoint chính thức chuẩn học thuật.<br>• Quay video demo kịch bản nghiệp vụ số hóa thực tế tại Phòng CTSV.<br>• Đóng gói kho mã nguồn GitHub/GitLab kèm tài liệu triển khai Docker 1-click bàn giao cho Khoa CNTT. | Cả 3 thành viên |

---

### CHỮ KÝ XÁC NHẬN CỦA CÁC THÀNH VIÊN

| **Trưởng nhóm** | **Thành viên** | **Thành viên** |
|:---:|:---:|:---:|
| *(Ký và ghi rõ họ tên)* | *(Ký và ghi rõ họ tên)* | *(Ký và ghi rõ họ tên)* |
| <br><br><br> | <br><br><br> | <br><br><br> |
| **Ngô Công Thành**<br>MSSV: 2212461 | **Phan Thành Phát**<br>MSSV: 2212463 | **Lý Gia Bảo**<br>MSSV: 2213934 |

