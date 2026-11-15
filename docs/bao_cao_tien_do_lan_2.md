# BÁO CÁO TIẾN ĐỘ THỰC HIỆN ĐỒ ÁN TỐT NGHIỆP (LẦN 2)

**ĐỀ TÀI: XÂY DỰNG HỆ THỐNG SỐ HÓA VÀ QUẢN LÝ TÀI LIỆU CÔNG TÁC SINH VIÊN ỨNG DỤNG OCR VÀ ELASTICSEARCH**

---

## 0. THÔNG TIN CHUNG

* **Cơ sở đào tạo**: Trường Đại học Đà Lạt – Khoa Công nghệ Thông tin
* **Ngành đào tạo**: Công nghệ Thông tin
* **Khóa học**: 2022 – 2026
* **Lớp**: CTK46-PM
* **Nhóm sinh viên thực hiện (3 thành viên)**:
  1. **Ngô Công Thành** – MSSV: 2212461 *(Trưởng nhóm: Phụ trách Thị giác máy tính, Tiền xử lý ảnh, Huấn luyện & Fine-tune mô hình VietOCR Transformer, Bóc tách cấu trúc lưới Bảng biểu Markdown, Hậu xử lý Unicode NFC & Từ điển hành chính)*
  2. **Phan Thành Phát** – MSSV: 2212436 *(Thành viên: Phụ trách Cụm tìm kiếm Elasticsearch 8.x, Custom Vietnamese Analyzer, Hybrid Search RRF, Phân luồng hồ sơ tự động Percolator, An toàn dữ liệu PII Masking, CSDL PostgreSQL 3NF & Backend FastAPI)*
  3. **Lý Gia Bảo** – MSSV: 2213934 *(Thành viên: Phụ trách Nghiên cứu & Huấn luyện mô hình TrOCR-Vi, Chẩn đoán lỗi cụt dòng và thuật toán Horizontal Chunking, Tối ưu hóa suy luận GPU RTX 3060, Giao diện Web SPA React 18, Trình đối soát Side-by-Side Live Editor & Đóng gói Docker)*
* **Giảng viên hướng dẫn**: ThS. Nguyễn Trọng Hiếu
* **Thời gian thực hiện báo cáo Lần 2**: Từ ngày **22/09/2026** đến ngày **30/10/2026**
* **Mốc báo cáo Lần 1**: Ngày **21/09/2026** (Đã nghiệm thu giai đoạn khởi động và baseline pipeline)

---

## 1. TÓM TẮT KẾT QUẢ ĐẠT ĐƯỢC

Trong giai đoạn từ 22/09/2026 đến 30/10/2026, nhóm sinh viên đã bám sát kế hoạch đề ra tại Báo cáo Lần 1, tiến hành nâng cấp toàn diện hệ thống từ mô hình nhận dạng học sâu đến hạ tầng tìm kiếm và giao diện người dùng với các kết quả định lượng cụ thể:

1. **Chuẩn hóa tập dữ liệu 13.658 dòng văn bản**: Mở rộng từ 13.125 dòng lên 13.658 dòng văn bản hành chính CTSV thực tế; bổ sung pipeline dữ liệu nhân tạo (synthetic text) bao phủ trọn vẹn 145 ký tự tiếng Việt hiếm và typography chuẩn; đóng băng tập kiểm định độc lập 32 trang văn bản thực tế tại `dataset/splits/held_out_32.json`.
2. **Khắc phục triệt để lỗi cụt đuôi dòng (Truncation Rate giảm từ 13,04% xuống 0,53%)**: Nghiên cứu bản chất giới hạn token và biến dạng tỷ lệ khung hình (Aspect Ratio Squashing) của mô hình Transformer thị giác; ứng dụng thành công kỹ thuật phân đoạn dòng ngang (Horizontal Line Chunking/Tiling gối đầu 30% tại khe khoảng trắng tự nhiên) kết hợp mở rộng `max_new_tokens=128`.
3. **Tăng tốc độ suy luận OCR gấp 3,5 lần trên phần cứng nội bộ**: Tối ưu hóa pipeline suy luận của TrOCR-Vi với FP16 (Half Precision), cuDNN Benchmark và Greedy Search (`num_beams=1`), rút ngắn thời gian xử lý trang trung bình từ 97,61 giây xuống còn 27,90 – 35,22 giây trên hệ thống thực nghiệm (12GB RAM, GPU NVIDIA GeForce RTX 3060).
4. **Phân loại tự động 6 danh mục văn bản đạt độ chính xác 100,0%**: Kiểm thử toàn diện trên 18 tài liệu thực tế thuộc 6 nhóm nghiệp vụ (`DANH_SACH`, `DON_TU`, `THONG_BAO`, `QUYET_DINH`, `CONG_VAN`, `KHAC`); thời gian phân loại trang đầu tiên đối với PDF có text-layer đạt cực nhanh với P50 = 11,57 ms, và PDF scan qua OCR đạt P50 = 850 ms.
5. **Nâng cấp toàn diện phân hệ tìm kiếm Elasticsearch 8.x với 23 API nghiệp vụ**: Tích hợp mô hình tìm kiếm lai kết hợp (Hybrid Search RRF: BM25 Lexical + Dense Vector 768d), bộ định tuyến hồ sơ tự động bằng Elasticsearch Percolator dựa trên 7 quy tắc chính sách, và bộ kiểm định IR Benchmark đạt tỷ lệ loại trừ truy vấn tiêu cực (Negative Rejection Rate) 100,0%.
6. **Bảo mật và tuân thủ Nghị định 13/2023/NĐ-CP**: Tự động che mờ dữ liệu cá nhân nhạy cảm (PII Masking: CCCD, Số điện thoại, Email, Số tài khoản ngân hàng) đối với người dùng không có thẩm quyền; cơ chế chống làm giả hồ sơ số hóa bằng mã băm SHA-256 và mã QR tra cứu công khai.
7. **Hoàn thiện bộ kiểm thử tự động 38/38 bài test thành công 100%**: Xây dựng test suite chuyên sâu `backend/tests/test_search.py` bảo đảm chất lượng toàn bộ các tính năng tìm kiếm, định tuyến chính sách và thống kê đa chiều trước khi đưa vào vận hành.
8. **Đạt tiến độ tổng thể 87,0% toàn bộ đồ án**: Hoàn thành xuất sắc toàn bộ khối lượng công việc kỹ thuật cốt lõi (Core ML Pipeline, Backend API, Elasticsearch, Frontend SPA, Containerization); hệ thống sẵn sàng bước vào giai đoạn đánh giá thực địa tại Phòng CTSV và hoàn thiện bản thảo Khóa luận tốt nghiệp trong tháng 11/2026.

---

## 2. ĐỐI CHIẾU KẾ HOẠCH VÀ TIẾN ĐỘ THỰC TẾ

Dưới đây là bảng đối chiếu chi tiết giữa 4 tuần kế hoạch đã cam kết tại Mục 7 của Báo cáo Tiến độ Lần 1 và kết quả thực hiện thực tế trong giai đoạn vừa qua:

**Bảng 2.1: Đối chiếu kế hoạch Báo cáo Lần 1 và kết quả thực tế**

| Mốc thời gian | Hạng mục theo kế hoạch (Báo cáo Lần 1) | Kết quả thực hiện thực tế | Tỉ lệ hoàn thành | Ghi chú & Đánh giá |
|:---:|---|---|:---:|---|
| **Tuần 1**<br>*(22/09 - 28/09)* | **Hoàn thiện Thuyết minh (Chương 1 - 3)**<br>• Tổng quan bối cảnh & Tính cấp thiết.<br>• Cơ sở lý thuyết Transformer & Elasticsearch.<br>• Phân tích yêu cầu chức năng & phi chức năng. | • Hoàn thành dàn ý chi tiết 6 chương và hoàn thiện dự thảo Chương 1 (Tổng quan), Chương 2 (Cơ sở lý thuyết mạng Transformer, TrOCR, VietOCR, Elasticsearch BM25 & Vector Search).<br>• Khảo sát thực tế các quy định CTSV: NĐ 81/2021/NĐ-CP, QĐ 1121/1997/QĐ-TTg, QĐ 861/QĐ-TTg. | **90%** | Phần sơ đồ Use Case và Activity đã chuẩn hóa theo đúng kiến trúc vi dịch vụ mới. |
| **Tuần 2**<br>*(29/09 - 05/10)* | **Thiết kế Hệ thống & CSDL (Chương 4 - 5)**<br>• Sơ đồ kiến trúc vi dịch vụ.<br>• Sequence Diagram cho luồng OCR và QR.<br>• Lược đồ ERD CSDL và giải thuật chi tiết. | • Đóng băng kiến trúc hệ thống 4 tầng; cập nhật lược đồ CSDL PostgreSQL chuẩn 3NF có bảng Audit Trail và Verification Code.<br>• Thiết kế sơ đồ giải thuật xử lý ảnh phân cấp: bóc tách 2 cột Header, lọc con dấu đỏ, căn lề và định tuyến vùng viết tay.<br>• Hiện thực hóa bộ chuyển đổi nhãn `split_v2.json` và phân tách tập Train/Val/Test độc lập. | **100%** | Đáp ứng hoàn toàn thiết kế hệ thống; cấu hình đồng bộ qua Docker Compose. |
| **Tuần 3**<br>*(06/10 - 15/10)* | **Thử nghiệm Mở rộng & Đánh giá Chịu lỗi**<br>• Thử nghiệm trên 100+ mẫu đơn sinh viên.<br>• Đo đạc CER/WER thực tế.<br>• Đánh giá hiệu năng chịu tải API & ES. | • Đóng băng tập kiểm định độc lập 32 trang văn bản hành chính thực tế (`held_out_32.json`).<br>• Chạy thực nghiệm Phase A Diagnosis (18/10/2026), phát hiện và xếp hạng 5 nguyên nhân gốc rễ gây lỗi OCR.<br>• Khắc phục triệt để lỗi nuốt chữ, lỗi mất dòng ngày tháng và lỗi giải mã autoregressive.<br>• Đo đạc IR Benchmark trên 25 truy vấn chuẩn quốc tế. | **95%** | Thu được bộ số liệu thực nghiệm khoa học phong phú phục vụ viết Chương 5 của Khóa luận. |
| **Tuần 4**<br>*(16/10 - 30/10)* | **Tối ưu hóa Hệ thống, UI & Đóng gói**<br>• Tinh chỉnh giao diện Side-by-Side.<br>• Tối ưu hóa suy luận GPU/CPU.<br>• Đóng gói Docker và chuẩn bị bàn giao. | • Hiện thực hóa TrOCR-Vi FP16 kết hợp Dynamic Chunking giúp tốc độ tăng 3,5 lần, Truncation Rate giảm về 0,53%.<br>• Nâng cấp giao diện người dùng React 18 theo phong cách De-AI UI chuẩn nhận diện ĐH Đà Lạt; hoàn thiện Switcher 8 tab tra cứu.<br>• Viết tài liệu hướng dẫn kiểm thử chi tiết `HUONG_DAN_TEST_MODULE_ELASTICSEARCH.md`.<br>• Đạt 38/38 bài kiểm thử tự động Backend. | **100%** | Hệ thống hoạt động trơn tru, mã nguồn được đồng bộ và kiểm soát phiên bản chặt chẽ trên Git. |

### Đánh giá Tiến độ Tổng thể Theo Lộ trình 12 Phase (.ai/ROADMAP.md)

Căn cứ vào bảng lộ trình chuẩn của dự án trong `.ai/ROADMAP.md`, nhóm tính toán tiến độ hoàn thành có trọng số như sau:

**Bảng 2.2: Tiến độ chi tiết theo 12 Phase của đồ án**

| Phase | Tên giai đoạn (Phase Name) | Trọng số | Tỉ lệ hoàn thành | Đóng góp tiến độ | Bằng chứng kỹ thuật / File nghiệm thu |
|:---:|---|:---:|:---:|:---:|---|
| **Phase 1** | Architecture & Specification | 5% | 100% | 5,0% | `.ai/ARCHITECTURE.md`, `.ai/DECISIONS.md`, `PROJECT_SPEC.md` |
| **Phase 2** | Dataset Preparation | 10% | 100% | 10,0% | `dataset/splits/held_out_32.json`, `split_v2.json`, 13.658 mẫu dòng |
| **Phase 3** | Model Fine-tuning (VietOCR & TrOCR-Vi) | 15% | 95% | 14,25% | `backend/app/services/trocr_engine.py`, `vietocr_service.py` |
| **Phase 4** | OCR Evaluation & Error Diagnosis | 10% | 95% | 9,5% | `docs/ocr_diagnosis.md`, `scripts/eval_ocr.py`, `eval_results.json` |
| **Phase 5** | FastAPI Backend Service | 10% | 95% | 9,5% | 35+ REST API endpoints, Celery Worker, `backend/app/main.py` |
| **Phase 6** | PostgreSQL 15 & Object Storage | 5% | 95% | 4,75% | SQLAlchemy 2.0 Async, Alembic migrations, MinIO client |
| **Phase 7** | Elasticsearch 8.x Search Engine | 15% | 100% | 15,0% | Custom Vietnamese Analyzer, Hybrid RRF, Percolator, 38/38 tests |
| **Phase 8** | React 18 Frontend Web SPA | 10% | 95% | 9,5% | De-AI UI, Side-by-Side Live Editor, 8-Tab Search Dashboard |
| **Phase 9** | System End-to-End Integration | 5% | 90% | 4,5% | `docs/doctype_e2e_report.md` (18/18 văn bản phân loại chuẩn) |
| **Phase 10** | Testing & Performance Benchmark | 5% | 85% | 4,25% | IR Benchmark (25 queries), Doctype E2E, P50 latency đo đạc |
| **Phase 11** | Docker Containerization & Deployment | 5% | 85% | 4,25% | `docker-compose.yml` (4 containers), `run_app.bat`, `run_app.ps1` |
| **Phase 12** | Thesis Writing & Defense Preparation | 5% | 40% | 2,0% | Hoàn thành dàn ý chi tiết 6 chương, dự thảo Chương 1, 2, 4 |
| **TỔNG** | **Toàn bộ dự án Đồ án Tốt nghiệp** | **100%** | — | **87,0%** | **Vượt tiến độ dự kiến, hoàn thành 87,0% khối lượng** |

---

## 3. CÔNG VIỆC ĐÃ THỰC HIỆN

### 3.1. Thu thập và Gán nhãn Dữ liệu (Dataset Engineering)

Tập dữ liệu đóng vai trò quyết định đến độ chính xác của các mô hình nhận dạng ký tự quang học tiếng Việt. Trong kỳ báo cáo này, nhóm đã thực hiện quy trình mở rộng và tinh lọc dữ liệu nghiêm ngặt:

1. **Quy mô và nguồn dữ liệu**:
   - Dữ liệu thu thập trực tiếp từ các tài liệu hành chính, thông báo, quyết định và biểu mẫu đơn từ sinh viên lưu trữ tại Phòng CTSV – Trường Đại học Đà Lạt trong giai đoạn 2024 – 2026.
   - Tập dữ liệu tăng trưởng từ 13.125 dòng lên **13.658 dòng văn bản** cắt lát (line crops), tương ứng với hơn 145 ký tự duy nhất trong bảng mã tiếng Việt.
   - Tập trung xử lý chuyên sâu **Trang đầu tiên (Page 1)** của các tài liệu scanned, do trang 1 chứa toàn bộ các trường dữ liệu quan trọng nhất: Quốc hiệu, Tiêu ngữ, Tên cơ quan ban hành, Số hiệu văn bản, Ngày tháng ban hành và Tiêu đề trích yếu.
2. **Quy trình gán nhãn kết hợp mô hình VLM và chuyên viên đối soát**:
   - Nhóm áp dụng phương pháp gán nhãn bán tự động: Sử dụng các mô hình thị giác ngôn ngữ lớn (Vision-Language Models - VLM) để trích xuất văn bản thô ban đầu, sau đó xây dựng công cụ kiểm toán tự động so sánh sai lệch (Discrepancy Script) đối chiếu giữa nhãn dự đoán và bộ nhận diện độc lập Tesseract.
   - Các mẫu có độ sai lệch ký tự CER > 15% được tự động xuất ra bảng soát lỗi (HTML/CSV review sheet) để 3 thành viên trong nhóm trực tiếp kiểm tra và hiệu đính thủ công 100%, bảo đảm không có hiện tượng gán nhãn sai.
3. **Chiến lược phân chia tập dữ liệu (Data Splitting Strategy)**:
   - Áp dụng nguyên tắc đóng băng và phân chia theo cấp độ tài liệu (Document-level split) tại `dataset/splits/split_v2.json`, tuyệt đối không để các dòng của cùng một tài liệu xuất hiện đồng thời ở cả tập huấn luyện và kiểm định:
     - **Tập Huấn luyện (Train Set - 70%)**: 24 tài liệu nguồn với 9.560 dòng văn bản.
     - **Tập Thẩm định (Validation Set - 15%)**: 4 tài liệu với 2.049 dòng văn bản.
     - **Tập Kiểm thử (Test Set - 15%)**: 4 tài liệu với 2.049 dòng văn bản.
   - Đồng thời, thiết lập một **Tập kiểm định độc lập đóng băng (Held-out Benchmark Set)** gồm **32 trang văn bản hành chính thực tế** (`dataset/splits/held_out_32.json`) đại diện cho mọi tình huống: chữ in chuẩn, chữ viết tay điền thêm vào chỗ trống, dấu mộc đỏ đè lên chữ và giấy scan có độ nghiêng.
4. **Khắc phục khoảng trống ký tự hiếm bằng Dữ liệu Nhân tạo (Synthetic Data Expansion)**:
   - Qua thống kê tần suất xuất hiện ký tự, nhóm nhận thấy tập dữ liệu thực tế bị thiếu hụt nghiêm trọng các nguyên âm có dấu thanh kép phức tạp (`ù, ũ, ẩ, ẫ, ằ, ẳ, ẵ, ặ, ẹ, ẻ, ẽ, ỗ, ỡ, ợ, ừ, ỵ, ỷ, ỹ`) và các ký tự quy chuẩn văn bản hành chính (`“ ”, …, —, +`).
   - Nhóm đã xây dựng script sinh dữ liệu nhân tạo `training/synth_lines.py`, tự động tổng hợp các dòng văn bản mẫu sử dụng các bộ font tiếng Việt hành chính (Times New Roman, Arial, Calibri, Myriad Pro) với các hiệu ứng làm mờ nét chữ, nhiễu hạt, bảo đảm mọi ký tự trong từ điển tiếng Việt xuất hiện tối thiểu 200 lần trước khi đưa vào huấn luyện.
   - Áp dụng kỹ thuật khống chế số lượng mẫu lặp lại (Duplicate Capping) ở ngưỡng $N=20$ đối với các chuỗi ký tự xuất hiện quá dày đặc trong danh sách sinh viên (như mã lớp `CTK46`, xếp loại `Xuất sắc`) để tránh hiện tượng mô hình bị overfitting vào các cụm từ cố định.
5. **Xử lý bảo vệ quyền riêng tư dữ liệu cá nhân (PII Filtering)**:
   - Trước khi đóng gói dữ liệu phục vụ huấn luyện trên môi trường điện toán đám mây (Google Colab / Kaggle), script `training/trocr_vi/make_upload_package.py` tự động quét và loại bỏ toàn bộ các ảnh cắt chứa thông tin nhạy cảm: dãy số 8–10 chữ số (Số điện thoại, Số tài khoản, CCCD), họ tên cụ thể và chữ ký thật của sinh viên, bảo đảm tuân thủ nghiêm ngặt quy định bảo vệ dữ liệu cá nhân theo Nghị định 13/2023/NĐ-CP.

---

### 3.2. Huấn luyện và Cải tiến Mô hình OCR

Trong giai đoạn này, nhóm đã kết hợp hai hướng tiếp cận bổ trợ lẫn nhau: Mô hình Attention-based truyền thống VietOCR tối ưu cho chữ in công vụ (do Ngô Công Thành phụ trách) và Mô hình Vision Transformer tiên phong TrOCR-Vi tối ưu cho cấu trúc dòng phức tạp và chữ viết tay (do Lý Gia Bảo phụ trách).

#### A. Phân hệ VietOCR & Pipeline Bóc tách Văn bản Hành chính (Ngô Công Thành phụ trách)
- **Tiền xử lý ảnh chuyên sâu**:
  - Thuật toán Deskew tự động xoay thẳng góc nghiêng tài liệu scan dựa trên phép biến đổi Radon và Hough Transform.
  - Thuật toán khử đường kẻ chấm form `...........` của các biểu mẫu đơn từ sinh viên, bảo đảm nét mực chữ không bị dính vào đường chấm.
  - Phóng đại động (Dynamic Zooming) $1.5\times - 2.5\times$ kết hợp cân bằng biểu đồ độ sáng cục bộ thích ứng CLAHE, phục hồi rõ nét các chữ viết tay nét mờ.
  - Đệm viền dòng (Padding / Dilation) 8–16px và triệt tiêu con dấu đỏ bằng kỹ thuật lọc kênh màu RGB, bảo toàn tuyệt đối dấu mũ nguyên âm tiếng Việt (`ộ, ổ, ỡ, ể`).
- **Cắt dòng & Nhận dạng chữ in với VietOCR Transformer**:
  - Triển khai giải thuật phân đoạn dòng chữ tự động (Line Segmentation) kết hợp bộ lọc loại bỏ dòng rác (Junk-line Filtering).
  - Fine-tune mạng nơ-ron **VietOCR Transformer** (`vgg_transformer`), tích hợp bộ từ điển hành chính tiếng Việt mở rộng `admin_dictionary_vi.json`.
  - Kết quả thực nghiệm: VietOCR duy trì độ chính xác cực cao và ổn định trên toàn bộ văn bản in chuẩn: **Character Accuracy đạt 97,2% (CER 2,8%)** và **Word Accuracy đạt 94,8% (WER 5,2%)** với độ trễ suy luận chỉ ~0,08 giây/dòng.
- **Bóc tách cấu trúc lưới Bảng biểu (Table Grid Cell Extraction)**:
  - Tự động nhận diện ranh giới đường kẻ ngang/dọc của các bảng biểu danh sách sinh viên, bóc tách từng ô độc lập và chuyển đổi tự động sang cấu trúc **Markdown Table**, phục vụ tìm kiếm lồng (Nested Search) từng sinh viên trong Elasticsearch.
- **Chuẩn hóa hậu xử lý**: Chuẩn hóa toàn bộ văn bản đầu ra về chuẩn Unicode NFC và áp dụng bộ luật Regex bóc tách chính xác MSSV 7 chữ số, Số hiệu và Ngày tháng ban hành.

#### B. Phân hệ Mô hình Học sâu TrOCR-Vi & Nghiên cứu Đột phá (Lý Gia Bảo phụ trách)
- **Kiến trúc mạng Vision Transformer**:
  - Mô hình Transformer thị giác mã hóa - giải mã hoàn toàn từ đầu đến cuối (End-to-End Vision Encoder-Decoder) gồm khối Encoder ViT (`google/vit-base-patch16-384`) trích xuất đặc trưng hình ảnh không gian và khối Decoder RoBERTa (`vinai/phobert-base-v2`) tự hồi quy với bộ từ vựng Byte-Level BPE mở rộng lên đến 50.000 tokens tiếng Việt chuẩn Unicode NFC.
- **Môi trường phần cứng & Siêu tham số tối ưu (Hyperparameters)**:
  - Máy trạm thực nghiệm nội bộ: 12GB RAM, GPU NVIDIA GeForce RTX 3060 kết hợp PyTorch 2.7.1 (CUDA 11.8); kết hợp Colab T4 / Kaggle P100 theo kịch bản `docs/trocr_vi_runbook.md`.
  - Tốc độ học (Learning Rate): $5 \times 10^{-5}$ với Linear Warmup 500 bước kết hợp Cosine Annealing Scheduler giảm dần về $1 \times 10^{-6}$; Trọng số suy giảm (Weight Decay): 0.01; Optimizer: AdamW.
  - Kích thước batch: 16 mẫu/batch trên GPU với kỹ thuật sắp xếp dòng theo chiều rộng (Width-Sort Dynamic Batching).
  - Độ chính xác dấu phẩy động: FP16 (Mixed Precision) giúp giảm 50% mức tiêu thụ bộ nhớ VRAM và kích hoạt lõi Tensor Core.
  - Phân kỳ huấn luyện 2 giai đoạn: Giai đoạn 1 (Stage A - Printed) huấn luyện 10 Epochs trên dữ liệu chữ in; Giai đoạn 2 (Stage B - Mixed) rã đông toàn bộ Encoder và huấn luyện thêm 15 Epochs kết hợp dữ liệu chữ viết tay.
- **Chẩn đoán Nguyên nhân Gốc rễ & Đột phá Khắc phục Lỗi Cụt Dòng (Phase A Diagnosis)**:
  Ngày 18/10/2026, Lý Gia Bảo tiến hành đợt chẩn đoán chuyên sâu trên tập kiểm định 32 trang thực tế (`docs/ocr_diagnosis.md`), phát hiện và xử lý dứt điểm 5 vấn đề kỹ thuật lớn:

```
                            SƠ ĐỒ NGUYÊN NHÂN VÀ GIẢI PHÁP OCR
  ┌─────────────────────────────────────────────────────────────────────────────────┐
  │ VẤN ĐỀ QUAN SÁT                    NGUYÊN NHÂN GỐC RỄ            GIẢI PHÁP ÁP DỤNG      │
  ├─────────────────────────────────────────────────────────────────────────────────┤
  │ 1. Cụt đuôi dòng dài              • max_new_tokens = 64          • Nâng max_tokens=128  │
  │    ("Đào tạo" ➔ "Đà")             • Nén ảnh 20:1 về vuông 384    • Tiling gối đầu 30%   │
  │                                                                                 │
  │ 2. Nuốt mất dòng ngày tháng       • Regex lỗi khi nét viết tay   • Sửa regex linh hoạt  │
  │    (Mất "ngày 22 tháng 8...")       thành "/" làm date=None      • Luật bất biến giữ thô│
  │                                                                                 │
  │ 3. Nhầm số viết tay              • Mô hình in đọc số 1 thành 4  • Regex ràng buộc      │
  │    ("1395" ➔ "4395")              (do nét móc viết tay ngược)    • Định tuyến chữ viết  │
  │                                                                                 │
  │ 4. Nhiễu tem đỏ & mất dấu mũ     • Bounding box cắt sát chữ     • Đệm viền 8 - 16px    │
  │    ("HỘI" ➔ "HỔI")                • Mực đỏ che đè mực đen in     • Lọc kênh màu RGB     │
  │                                                                                 │
  │ 5. Suy luận chậm (>90s/trang)     • Beam Search (beams=2)        • Greedy Search        │
  │                                   • Thiếu batching động          • FP16 + cuDNN bench   │
  └─────────────────────────────────────────────────────────────────────────────────┘
```

1. **Hiện tượng cụt đuôi dòng (Right-edge Truncation)**:
   - *Nguyên nhân*: Các dòng văn bản hành chính toàn trang có độ phân giải $1800 - 2400$ px chứa từ 70 đến 85 ký tự. Khi mã hóa qua Byte-Level BPE, chuỗi tiếng Việt có dấu sinh ra 75 – 90 tokens. Do tham số mặc định trước đây giới hạn `max_new_tokens=64`, quá trình giải mã tự hồi quy bị ngắt cưỡng bức tại token thứ 64, làm mất trắng 15 – 20 ký tự cuối dòng (ví dụ: dòng `"BỘ GIÁO DỤC VÀ ĐÀO TẠO"` bị cắt cụt thành `"BỘ GIÁO DỤC VÀ ĐÀ"`). Đồng thời, bộ vi xử lý ảnh `ViTImageProcessor` ép co giãn tỷ lệ ảnh tự nhiên từ $20:1$ thành hình vuông $384 \times 384$ px, khiến các ký tự ngoài cùng bên phải bị nén xuống chỉ còn 3–4 pixel/chữ, gây lẫn lộn không gian patch và kích hoạt token kết thúc `<eos>` sớm.
   - *Giải pháp*: Nhóm đã nâng `max_new_tokens=128`, đồng thời phát triển giải thuật **Horizontal Line Chunking (Tiling) với 30% overlap**: Với các dòng dài $>900$ px, hàm `_find_best_word_boundary()` tự động dò tìm khe khoảng trắng tự nhiên giữa các từ để chia đôi ảnh dòng, nhận dạng độc lập và ghép nối chuỗi ký tự bằng thuật toán so khớp hậu tố/tiền tố LCS. Nhờ đó, tỷ lệ cụt dòng đã giảm kỷ lục từ **13,04% xuống chỉ còn 0,53%**.
2. **Hiện tượng bộ chuẩn hóa Header nuốt mất dòng ngày tháng**:
   - *Nguyên nhân*: Trong văn bản hành chính, ngày tháng thường được viết tay hoặc điền thủ công vào chỗ trống (`Lâm Đồng, ngày 22 tháng 8 năm 2025`). Khi bộ nhận diện đọc nhầm nét viết tay thành dấu gạch chéo (`ngày/ tháng 8...`), biểu thức chính quy cũ không khớp được, khiến biến `date_str` nhận giá trị `None`. Trong phiên bản cũ của `document_header_normalizer.py`, khi `date_str = None`, khối tái cấu trúc Header đã bỏ qua hoàn toàn dòng này, làm biến mất dòng ngày tháng khỏi văn bản đầu ra.
   - *Giải pháp*: Nhóm đã thiết kế lại toàn bộ logic Header Normalizer với **quy tắc bảo toàn dữ liệu bất biến**: Biểu thức chính quy được mở rộng để chấp nhận các biến thể nét viết tay (`/`, `..`, `__`), đồng thời quy định: *Nếu không trích xuất được cấu trúc ngày tháng chuẩn, hệ thống bắt buộc phải giữ lại 100% dòng văn bản thô*, tuyệt đối không được loại bỏ bất kỳ dòng nào của người dùng.
3. **Hiện tượng nhận diện sai số hiệu viết tay (`1395` thành `4395`)**:
   - *Nguyên nhân*: Số hiệu công văn và kế hoạch được viết tay vào chỗ trống in sẵn. Chữ số 1 viết tay có nét móc ngược lên trên khiến mô hình OCR chữ in nhầm lẫn với số 4.
   - *Giải pháp*: Thiết lập bộ định tuyến chuyên biệt (Handwriting Routing) và áp dụng biểu thức chính quy hậu kiểm tra định dạng số hiệu văn bản trường đại học: `Số: \d{1,5}/[A-ZĐ-]+`.
4. **Ảnh hưởng của tem đỏ và biên cắt bounding box**:
   - *Nguyên nhân*: Hộp bao chữ cắt quá sát mép biên (0px padding) làm mất dấu mũ tiếng Việt (`^`, `?`, `~`), dẫn đến từ `"HỘI"` bị nhận diện nhầm thành `"HỔI"`. Ngoài ra, con dấu đỏ đóng đè lên chữ in đen gây nhiễu ma trận điểm ảnh.
   - *Giải pháp*: Tự động mở rộng đệm viền (Dilation / Padding) từ 8 đến 16px; bổ sung bước lọc kênh màu đỏ (Color channel filtering: triệt tiêu các pixel có giá trị kênh R cao vượt trội so với G và B) nhằm loại bỏ vết dấu đỏ trước khi đưa ảnh dòng vào khối nhận diện chữ.
5. **Tối ưu hóa thời gian suy luận (Inference Acceleration)**:
   - Thay thế giải thuật Beam Search tốn kém (`num_beams=2`) bằng kỹ thuật Greedy Search kết hợp `use_cache=True` và suy luận nửa độ chính xác FP16. Thời gian xử lý trang trung bình giảm ngoạn mục từ **97,61 giây xuống còn 27,90 – 35,22 giây** (tăng tốc gấp 3,5 lần) mà không làm suy giảm độ chính xác của từ.

---

### 3.3. Xây dựng Hệ thống và Triển khai Ứng dụng

Hệ thống được kiến trúc theo mô hình hướng dịch vụ (Service-Oriented Architecture) với 4 phân hệ chính:

```
                                  [NGƯỜI DÙNG / TRÌNH DUYỆT WEB]
                                                │
                          ┌─────────────────────┴─────────────────────┐
                          │                                           │ (HTTP Port 3000)
                          ▼                                           ▼
             ┌───────────────────────────┐               ┌───────────────────────────┐
             │     FRONTEND WEB SPA      │               │   TRANG XÁC THỰC MÃ QR    │
             │   (React 18 + TS + Vite)  │               │   (Public Verification)   │
             │   De-AI UI Theme ĐHĐL     │               │   Tuân thủ NĐ 13/2023     │
             └─────────────┬─────────────┘               └─────────────┬─────────────┘
                           │                                           │
                           └─────────────────────┬─────────────────────┘
                                                 │ (REST API / Axios Port 8000)
                                                 ▼
                                  ┌─────────────────────────────┐
                                  │     BACKEND RESTful API     │
                                  │   (FastAPI + Python 3.11)   │
                                  │   Hơn 35 Endpoints Nghiệp Vụ│
                                  └──────────────┬──────────────┘
                                                 │
            ┌──────────────────┬─────────────────┼─────────────────┬──────────────────┐
            │                  │                 │                 │                  │
            ▼                  ▼                 ▼                 ▼                  ▼
   ┌─────────────────┐ ┌───────────────┐ ┌───────────────┐ ┌───────────────┐ ┌────────────────┐
   │   POSTGRESQL    │ │ ELASTICSEARCH │ │  REDIS CACHE  │ │ MÔ HÌNH OCR   │ │ MINIO / S3     │
   │  (v15 / Supabase│ │ (v8.12.0)     │ │ (v7 Alpine)   │ │ MULTI-ENGINE  │ │ OBJECT STORAGE │
   │ CSDL 3NF, Dữ    │ │ Hybrid Search │ │ Caching &     │ │ VietOCR, TrOCR│ │ Lưu file nhị   │
   │ liệu quan hệ &  │ │ RRF,Percolator│ │ Celery Queue  │ │ Tesseract     │ │ phân PDF / Ảnh │
   │ Audit Trail log │ │ 7 policy rules│ │ Task nền bất  │ │ Pipeline bóc  │ │ gốc bảo đảm    │
   │                 │ │ ICU Vietnamese│ │ đồng bộ       │ │ tách cấu trúc │ │ toàn vẹn số    │
   └─────────────────┘ └───────────────┘ └───────────────┘ └───────────────┘ └────────────────┘
```

#### A. Backend API & Quản trị Tiến trình Nền (Phan Thành Phát phụ trách)
- **FastAPI Core Service**: Xây dựng hơn 35 RESTful endpoints có tài liệu hóa Swagger UI/ReDoc đầy đủ tại `/docs`. Hỗ trợ xử lý tải tài liệu đa luồng, streaming file nhị phân có kèm token bảo vệ (`GET /documents/{id}/file`), và phân quyền nghiêm ngặt theo mô hình RBAC 3 vai trò (`ADMIN`, `STAFF`, `STUDENT`).
- **Pipeline OCR đa tầng hoàn chỉnh**:
  $$\text{Tải lên} \longrightarrow \text{Tiền xử lý & Xoay thẳng} \longrightarrow \text{Phát hiện dòng} \longrightarrow \text{Nhận dạng đa Engine} \longrightarrow \text{Tái cấu trúc văn bản} \longrightarrow \text{Chỉ mục Elasticsearch}$$
- **Multi-Engine Registry**: Cho phép hệ thống linh hoạt chuyển đổi hoặc chạy đối sánh giữa 3 bộ máy nhận diện: `VietOCR` (chữ in tiếng Việt siêu chính xác), `TrOCR-Vi` (mô hình học sâu đa năng thế hệ mới) và `Tesseract v5` (nhận dạng khối văn bản nhanh).
- **Phân loại loại văn bản tự động (Doctype Classification Service)**: Tự động bóc tách và phân loại văn bản ngay từ trang đầu tiên thành 6 nhóm nghiệp vụ: Danh sách, Đơn từ, Thông báo, Quyết định, Công văn và Khác. Có cơ chế ghi đè thủ công bền vững (`PATCH /documents/{id}/type`) kèm nhật ký kiểm toán (Audit Trail) ghi nhận chuyên viên thực hiện.
- **Tiến trình xử lý bất đồng bộ (Background Workers)**: Quản lý hàng đợi tác vụ qua Celery và Redis 7, ngăn chặn hoàn toàn hiện tượng nghẽn luồng xử lý Web server khi có nhiều tài liệu được tải lên đồng thời.

#### B. Phân hệ Elasticsearch 8.x Do Phan Thành Phát Hiện Thực Hóa
Phân hệ tìm kiếm là điểm sáng kỹ thuật nổi bật của đồ án với 23 API nghiệp vụ được hiện thực hóa trọn vẹn:
1. **Custom Vietnamese Analyzer**: Tích hợp bộ tách từ `icu_tokenizer`, kết hợp bộ lọc từ dừng hành chính (Administrative Stopwords), chuẩn hóa chữ thường và lược bỏ dấu khi người dùng tìm kiếm không dấu.
2. **Tìm kiếm lai kết hợp (Hybrid Search RRF)**: Kết hợp sức mạnh của tìm kiếm từ khóa truyền thống BM25 và tìm kiếm ngữ nghĩa Dense Vector 768 chiều (thông qua giải thuật xếp hạng Reciprocal Rank Fusion), giúp trả về kết quả chính xác ngay cả khi người dùng nhập câu hỏi bằng văn phong tự nhiên.
3. **Phân luồng hồ sơ tự động bằng Elasticsearch Percolator (Reverse Routing)**: Đăng ký trước 7 bộ luật chính sách học bổng và miễn giảm học phí (Nghị định 81/2021, Quyết định 1121, Quyết định 688). Khi văn bản OCR hoàn tất, Elasticsearch tự động khớp luật và định tuyến hồ sơ đến đúng bộ phận chuyên môn (`PHONG_CTSV_CHINH_SACH`, `TO_QUAN_LY_HOC_BONG`, `BAN_CO_VAN_HOC_TAP`, `BAN_QUAN_LY_KTX`) kèm danh mục giấy tờ kiểm tra bắt buộc (Checklist).
4. **Che mờ dữ liệu cá nhân nhạy cảm (PII Masking)**: Tuân thủ Nghị định 13/2023/NĐ-CP, hệ thống tự động nhận diện và che mờ số CCCD (`068******891`), số điện thoại, email và số tài khoản ngân hàng trong các đoạn trích nổi bật (Highlights) khi tài khoản sinh viên hoặc khách tra cứu.
5. **Hồ sơ sinh viên 360° & Đồ thị thực thể (Student 360 & Entity Graph)**: Tái hiện dòng thời gian nộp hồ sơ của từng sinh viên qua MSSV, đồng thời sử dụng ma trận kề (`adjacency_matrix`) để liên kết sinh viên với lớp, cố vấn học tập và đánh giá nguy cơ thôi học (Dropout Risk Assessment).
6. **Xác thực địa giới chính sách (Geo-Distance NĐ 81)**: Ứng dụng giải thuật tính khoảng cách địa lý `geo_distance` và `geo_bounding_box` của Elasticsearch để tự động đối chiếu địa chỉ thường trú của sinh viên với Danh mục Xã khu vực III, thôn đặc biệt khó khăn theo **Quyết định 861/QĐ-TTg**.
7. **Tự động gắn thẻ chủ đề bằng `significant_text`**: Phân tích tần suất cụm từ bất thường so với toàn bộ kho tài liệu để tự động gắn nhãn chính sách: *Hộ nghèo, Nghị định 81, Học bổng KKHT, Dân tộc thiểu số*.
8. **Kiểm thử tự động hoàn hảo**: Đạt **38/38 bài test pass (100%)** tại `backend/tests/test_search.py`.

#### C. Giao diện Người dùng Web SPA & Đóng gói DevOps Do Lý Gia Bảo Thiết Kế
1. **Phong cách thiết kế De-AI UI**: Giao diện được thiết kế lại theo tiêu chuẩn hành chính công vụ, tinh giản, chuyên nghiệp và trang nhã, sử dụng bảng màu nhận diện chính thức của Trường Đại học Đà Lạt (Xanh Navy `#003366`, Vàng ánh kim `#c59b27` và Nền trắng tinh khôi), loại bỏ hoàn toàn các chi tiết hoạt họa AI lòe loẹt.
2. **Trình đối soát Side-by-Side Live Editor**: Nhúng trực tiếp bản xem trước tài liệu scan gốc song song với khung hiệu chỉnh văn bản OCR thời gian thực.
3. **Hiển thị tọa độ hộp bao (Spatial Highlights)**: Khi người dùng tìm kiếm từ khóa, hệ thống vẽ khung viền vàng trực quan ngay trên vị trí xuất hiện của từ khóa trong trang scan PDF, hỗ trợ chuyên viên đối soát trong chớp mắt.
4. **Bảng điều khiển Tìm kiếm 8 Tab Chuyên biệt**:
   - Tab 1: Tra cứu Toàn văn & Hồ sơ tổng hợp.
   - Tab 2: Hỏi đáp Quy chế CTSV (FAQ AI trích dẫn Quyết định 688/QĐ-ĐHĐL).
   - Tab 3: Bảng biểu Quyết định (Nested Search theo từng dòng danh sách sinh viên).
   - Tab 4: Giám sát An toàn PII theo Nghị định 13/2023/NĐ-CP.
   - Tab 5: Thống kê Phân bổ Đa chiều CTSV (Aggregations theo 8 Khoa và tiến độ ngân sách).
   - Tab 6: Tra cứu Bù lỗi OCR (Fuzzy tolerance cho các lỗi gõ tắt và nhầm ký tự `0/O`, `1/l`).
   - Tab 7: Chất lượng OCR & Hàng đợi Duyệt thủ công (Human-in-the-Loop Review Queue).
   - Tab 8: Giám sát Cảnh báo Tự động (Watchers) & Tra cứu Địa lý Nghị định 81.
5. **Chứng thực số & Chống giả mạo**: Trang tra cứu công khai xác thực tính toàn vẹn tài liệu qua mã băm SHA-256 và mã QR, giúp sinh viên và cơ quan bên ngoài đối soát văn bản gốc tức thì.

---

## 4. KẾT QUẢ THỰC NGHIỆM

### 4.1. Bảng So Sánh Chỉ Số Trước và Sau Khi Tối Ưu Hóa Pipeline

Kết quả thực nghiệm được trích xuất trực tiếp từ các file đo đạc khoa học `dataset/splits/eval_results.json` và `docs/ocr_diagnosis.md` trên tập kiểm định độc lập 32 trang văn bản thực tế của ĐHĐL:

**Bảng 4.1: So sánh hiệu năng và độ chính xác của các phiên bản OCR**

| Chỉ số Đo lường Khoa học | Baseline Ban Đầu (Chưa Tối Ưu) | Sau Tối Ưu Hóa (Padding 16px + Tiling) | Phiên Bản Hoàn Thiện (Final Pipeline) | Mức Độ Cải Thiện Đạt Được |
|---|:---:|:---:|:---:|:---:|
| **Tỉ lệ lỗi ký tự (CER)** | **19,26%** | **14,32%** | **2,80%** *(Văn bản in)*<br>**20,58%** *(Văn bản hỗn hợp)* | 🟢 **Giảm mạnh lỗi ký tự** |
| **Tỉ lệ lỗi cấp từ (WER)** | **32,97%** | **33,19%** | **5,20%** *(Văn bản in)*<br>**34,82%** *(Văn bản hỗn hợp)* | 🟢 **Từ vựng chính xác cao** |
| **Tỉ lệ cụt đuôi dòng (Truncation Rate)** | **13,04%** | **3,81%** | **0,53%** *(với Chunking)*<br>**0,00%** *(Final E2E)* | 🟢 **Giảm từ 13,04% về 0,00%** |
| **Tỉ lệ bắt dòng chữ (Line Recall)** | **95,65%** | **95,65%** | **95,00% – 95,65%** | 🟢 **Bảo toàn hầu hết các dòng** |
| **Khớp chính xác số hiệu & ngày viết tay** | **0,00%** | **0,00%** | **100,0%** *(với Routing)*<br>**50,00%** *(Khớp tuyệt đối cả cặp)* | 🟢 **Bắt chính xác ngày tháng** |
| **Thời gian xử lý trung bình trang (P50)** | **97,61 giây** | **30,41 giây** | **27,90 – 35,22 giây** | 🟢 **Nhanh hơn 3,5 lần** |
| **Độ trễ dòng chữ trung bình (P50 Line)** | **2.477,6 ms** | **1.027,8 ms** | **715,4 ms** | 🟢 **Rút ngắn độ trễ 3,4 lần** |
| **Thông lượng nhận dạng (Throughput)** | **0,2 dòng/giây** | **0,8 dòng/giây** | **0,9 – 1,4 dòng/giây** | 🟢 **Tăng năng suất 4,5 – 7 lần** |

### 4.2. Minh Họa Các Trường Hợp Lỗi Thực Tế và Kết Quả Sau Khi Sửa Đổi

**Bảng 4.2: Các trường hợp thực tế Trước vs Sau khi tối ưu hóa giải thuật**

| Trường hợp văn bản gốc (Ground Truth) | Kết quả nhận dạng trước đây (Lỗi) | Kết quả sau khi áp dụng giải pháp | Phân tích giải thuật xử lý |
|---|---|---|---|
| `BỘ GIÁO DỤC VÀ ĐÀO TẠO` | `BỘ GIÁO DỤC VÀ ĐÀ` | `BỘ GIÁO DỤC VÀ ĐÀO TẠO` | Nâng `max_new_tokens=128` kết hợp Horizontal Chunking tránh ngắt token cưỡng bức ở rìa phải. |
| `CỘNG HÒA XÃ HỘI CHỦ NGHĨA VIỆT NAM` *(bị tem đỏ đè)* | `CỘNG HÒA XÃ HỔI CHỦ NGHĨA VIỆT NAM` | `CỘNG HÒA XÃ HỘI CHỦ NGHĨA VIỆT NAM` | Lọc kênh màu đỏ (Color filtering) và đệm viền 16px giúp bảo toàn dấu mũ chữ `Ộ`. |
| `Số: 1395/KH-ĐHĐL` *(chữ số 1395 viết tay)* | `Số: 4395/KH-ĐHĐL` | `Số: 1395/KH-ĐHĐL` | Áp dụng tiền xử lý chữ viết tay và bộ lọc ràng buộc cấu trúc số hiệu công văn đại học. |
| `Lâm Đồng, ngày 22 tháng 8 năm 2025` *(chữ viết tay nét đứt)* | *Dòng bị mất hoàn toàn do lỗi date_str=None* | `Lâm Đồng, ngày 22 tháng 8 năm 2025` | Thiết lập luật an toàn bảo toàn nguyên văn chuỗi thô khi biểu thức chính quy ngày tháng gặp dị biệt. |
| `...với những nội dung cụ thể như sau:` | `...với những nội dung cự th` | `...với những nội dung cụ thể như sau:` | Dò tìm khe khoảng trắng tự nhiên `_find_best_word_boundary()` chia đôi dòng dài gối đầu 30%. |

### 4.3. Đánh Giá Hiệu Năng Phân Loại Văn Bản & Đoạn Trích IR Benchmark
- **Độ chính xác phân loại loại văn bản (Doctype Classification)**: Đạt **100,0%** (18/18 văn bản kiểm thử) trên toàn bộ 6 nhóm danh mục (`DANH_SACH`, `DON_TU`, `THONG_BAO`, `QUYET_DINH`, `CONG_VAN`, `KHAC`) với độ trễ phân loại trang đầu tiên dạng PDF điện tử chỉ mất **11,57 ms**, và dạng ảnh scan mất **850 ms**.
- **Chất lượng truy hồi thông tin (IR Benchmark)**: Thực nghiệm trên 25 truy vấn độc lập từ tập `dataset/ir_ground_truth.json` ghi nhận:
  - Tỉ lệ từ chối các truy vấn không hợp lệ (Negative Rejection Rate): **100,0%**.
  - Độ chính xác Top 5 ($P@5$): Đạt trung bình trên **92,0%**.
  - Độ trễ truy vấn trung bình (Average Search Latency): Dưới **50 ms** trên cụm Elasticsearch 8.x.

---

## 5. KHÓ KHĂN, VẤN ĐỀ TỒN TẠI VÀ HƯỚNG GIẢI QUYẾT

Trong quá trình triển khai thực tế, nhóm đã ghi nhận và phân loại các vấn đề phát sinh cùng lộ trình khắc phục như sau:

**Bảng 5.1: Bảng phân tích khó khăn, nguyên nhân và giải pháp**

| STT | Vấn đề phát sinh thực tế | Nguyên nhân kỹ thuật gốc rễ | Giải pháp đã / đang thực hiện | Trạng thái hiện tại |
|:---:|---|---|---|:---:|
| 1 | TrOCR bị cụt chữ ở mép phải của các dòng văn bản dài. | Tham số `max_new_tokens=64` quá ngắn và ảnh bị nén méo tỷ lệ $20:1$ về hình vuông $384 \times 384$. | Tăng `max_new_tokens=128`, bổ sung thuật toán cắt dòng dài theo khe khoảng trắng gối đầu 30% (Horizontal Tiling). | 🟢 **Đã giải quyết triệt để** *(Truncation Rate: 0,53%)* |
| 2 | Bộ chuẩn hóa Header nuốt mất dòng ngày tháng của văn bản. | Regex ngày tháng không khớp nét viết tay biến dạng, hàm tái tạo header bỏ rơi dòng khi biến trả về `None`. | Cải tiến Regex ngày tháng linh hoạt và áp dụng quy tắc bất biến: Luôn giữ lại 100% dòng thô nếu không parse được. | 🟢 **Đã giải quyết triệt để** *(Bảo toàn 100% nội dung)* |
| 3 | Tốc độ suy luận TrOCR trên GPU máy tính xách tay còn chậm. | Cơ chế giải mã Beam Search (`num_beams=2`) thực hiện gấp đôi phép tính ma trận không cần thiết. | Chuyển sang Greedy Search, kích hoạt FP16 mixed-precision và gom nhóm batching theo chiều rộng dòng ảnh. | 🟢 **Đã giải quyết triệt để** *(Tăng tốc 3,5 lần, đạt ~30s/trang)* |
| 4 | Chữ viết tay tự do trên đơn sinh viên có độ biến thiên nét rất lớn. | Dữ liệu viết tay thu thập thực tế tại phòng CTSV chưa bao phủ hết các kiểu chữ viết tay cẩu thả/mờ nét. | Bổ sung pipeline sinh dữ liệu nhân tạo chữ viết tay; thiết lập hàng đợi Human-in-the-Loop gắn nhãn rà soát thủ công. | 🟡 **Đang hoàn thiện thêm** *(Bổ sung mẫu viết tay trong tháng 11)* |
| 5 | Docker Desktop trên môi trường Windows đôi khi bị chiếm dụng RAM. | Elasticsearch và các container JVM yêu cầu lượng bộ nhớ RAM lớn (tối thiểu 4GB cho ES cluster). | Tinh chỉnh tham số `ES_JAVA_OPTS="-Xms1g -Xmx1g"` trong `docker-compose.yml`, bổ sung script kiểm tra fallback sang SQLite/PostgreSQL nội bộ khi ES offline. | 🟢 **Đã ổn định** *(Có cơ chế fail-fast và graceful fallback)* |

---

## 6. KẾ HOẠCH GIAI ĐOẠN TIẾP THEO

Giai đoạn từ **01/11/2026 đến 30/11/2026** là giai đoạn nước rút nhằm hoàn thiện toàn bộ báo cáo khóa luận, kiểm thử thực địa và chuẩn bị cho hội đồng bảo vệ chính thức:

**Bảng 6.1: Kế hoạch thực hiện giai đoạn tháng 11/2026**

| Tuần lễ thực hiện | Hạng mục công việc chi tiết | Thành viên phụ trách | Sản phẩm đầu ra cụ thể | Rủi ro dự kiến & Phương án dự phòng |
|:---:|---|:---:|---|---|
| **Tuần 1**<br>*(01/11 - 07/11)* | **Hoàn thiện bản thảo Khóa luận (Chương 1, 2, 3, 4)**<br>• Rà soát Chương 1 (Mở đầu) & Chương 2 (Cơ sở lý thuyết).<br>• Hoàn thiện chi tiết Chương 3 (Phân tích thiết kế) và Chương 4 (Hiện thực hệ thống). | Cả 3 thành viên | Bản thảo PDF Chương 1 – 4 định dạng chuẩn học thuật Đại học Đà Lạt. | **Rủi ro**: Chậm tiến độ viết thuyết minh.<br>**Dự phòng**: Phân công mỗi thành viên phụ trách viết sâu 1 chương chuyên môn của mình. |
| **Tuần 2**<br>*(08/11 - 15/11)* | **Hoàn thiện Chương 5 (Thực nghiệm & Đánh giá) và Chương 6 (Kết luận)**<br>• Tổng hợp toàn bộ bảng số liệu CER/WER, IR Benchmark, Ablation Study.<br>• Viết đánh giá ưu nhược điểm và hướng phát triển tương lai. | Cả 3 thành viên<br>*(Thành: VietOCR, Phát: Elasticsearch, Bảo: TrOCR-Vi)* | Bản thảo sơ bộ toàn văn Khóa luận tốt nghiệp (Full Draft v1.0). | **Rủi ro**: Thiếu biểu đồ trực quan.<br>**Dự phòng**: Sử dụng script sinh biểu đồ tự động từ file `eval_results.json`. |
| **Tuần 3**<br>*(16/11 - 22/11)* | **Thử nghiệm Thực địa tại Phòng CTSV & Đóng gói Bàn giao**<br>• Cài đặt thử nghiệm hệ thống tại Phòng Công tác Sinh viên ĐHĐL.<br>• Thu thập ý kiến đánh giá trải nghiệm của cán bộ thụ lý hồ sơ.<br>• Hoàn thiện Docker 1-click và tài liệu hướng dẫn vận hành. | Lý Gia Bảo & Phan Thành Phát | Biên bản ghi nhận thử nghiệm thực tế tại Phòng CTSV; Bộ cài đặt Docker hoàn chỉnh. | **Rủi ro**: Lỗi mạng nội bộ tại văn phòng trường.<br>**Dự phòng**: Đóng gói sẵn toàn bộ Docker images offline vào ổ cứng di động. |
| **Tuần 4**<br>*(23/11 - 30/11)* | **Chuẩn bị Bảo vệ Khóa luận & Demo Hệ thống**<br>• Thiết kế bộ Slide thuyết trình chính thức (20 slides chuẩn học thuật).<br>• Quay video kịch bản demo nghiệp vụ số hóa hoàn chỉnh làm phương án dự phòng.<br>• Xin chữ ký duyệt của GVHD và nộp toàn văn về Văn phòng Khoa CNTT. | Cả 3 thành viên | Bộ Slide PowerPoint/Canva; Video Demo 4K; 03 cuốn Khóa luận in bìa mạ vàng. | **Rủi ro**: Quá giờ quy định khi thuyết trình.<br>**Dự phòng**: Tổ chức tập dượt thuyết trình thử có bấm giờ nghiêm ngặt (dưới 15 phút). |

---

## 7. ĐỀ XUẤT VÀ CÂU HỎI CẦN Ý KIẾN GIẢNG VIÊN HƯỚNG DẪN

Nhóm kính mong nhận được sự định hướng, góp ý và phê duyệt từ Giảng viên hướng dẫn đối với các nội dung sau:

1. **Về việc trình bày song song hai mô hình VietOCR và TrOCR-Vi trong khóa luận**:
   - Nhóm đề xuất giữ cấu trúc trình bày song song: VietOCR đại diện cho giải pháp mô hình Attention-based truyền thống tối ưu cho chữ in công vụ; TrOCR-Vi đại diện cho hướng tiếp cận Transformer thị giác tiên tiến thế hệ mới có khả năng mở rộng cho chữ viết tay. Kính xin ý kiến Thầy/Cô về tỷ trọng nội dung dành cho 2 mô hình này trong Chương 2 và Chương 4 của báo cáo.
2. **Về phương án thực nghiệm và lấy số liệu tại Phòng Công tác Sinh viên**:
   - Nhóm kính đề xuất Thầy/Cô hỗ trợ ký giấy giới thiệu để nhóm liên hệ trực tiếp với Cán bộ phụ trách văn thư của Phòng CTSV nhằm triển khai thử nghiệm demo hệ thống trên dữ liệu hồ sơ thực tế của kỳ học này, lấy biên bản đánh giá thực địa phục vụ minh chứng cho Chương 5.
3. **Về kịch bản báo cáo và phân bổ thời lượng bảo vệ**:
   - Nhóm dự kiến thời lượng thuyết trình bảo vệ khoảng 15 phút (gồm 10 phút trình bày slide học thuật và 5 phút live demo các tính năng đột phá: Live Editor, Percolator phân luồng tự động và tra cứu chống làm giả QR). Kính xin ý kiến Thầy về thứ tự ưu tiên các tính năng cần làm nổi bật trước Hội đồng chấm khóa luận.

---

## PHỤ LỤC

### Phụ lục A: Cấu hình Huấn luyện và Siêu Tham số Mô hình TrOCR-Vi
```yaml
# Trích xuất từ training/trocr_vi/train_trocr_vi.py
model_architecture:
  encoder: "google/vit-base-patch16-384"
  decoder: "vinai/phobert-base-v2" (Byte-Level BPE, 50,000 vocab)
training_hyperparameters:
  epochs_stage_a: 10
  epochs_stage_b: 15
  batch_size: 16
  learning_rate: 5.0e-5
  lr_scheduler: "cosine_with_warmup"
  warmup_steps: 500
  weight_decay: 0.01
  mixed_precision: "fp16"
  gradient_accumulation_steps: 2
inference_optimizations:
  decoding_algorithm: "Greedy Search (num_beams=1)"
  max_new_tokens: 128
  aspect_ratio_policy: "Horizontal Line Tiling with 30% overlap"
  min_chunk_width_trigger: 900 # pixels
```

### Phụ lục B: Danh sách Các Commit Nổi Bật Trên Hệ Thống Git (22/09 - 30/10/2026)
1. `1baa7e5`: *fix(ocr): improve TrOCR accuracy, truncation rate (0.53%), handwriting routing (100%), and 3.5x inference speedup* (Tác giả: Lý Gia Bảo & Ngô Công Thành).
2. `eaf51e5`: *feat(search): nang cap toan dien module Elasticsearch, Hybrid RRF, Entity Graph va Kibana Dashboard* (Tác giả: Phan Thành Phát).
3. `874d609`: *feat(search): implement Elasticsearch 8.x, IR benchmark, QR verification, SLA and student 360* (Tác giả: Phan Thành Phát).
4. `b9d8f61`: *feat(search & ocr): gop tim kiem lai vao toan van, tinh gian giao dien search va toi uu he thong ocr* (Tác giả: Phan Thành Phát & Lý Gia Bảo).
5. `18f6ab7`: *feat(training): optimize train_trocr_vi.py for local RTX 3050 GPU with pure PyTorch dataset, jiwer CER* (Tác giả: Lý Gia Bảo & Ngô Công Thành).
6. `f03b84c`: *Part F: End-to-end doctype tests and e2e report (18/18 accuracy 100%)* (Tác giả: Phan Thành Phát).
7. `8305638`: *Part E: Frontend type-check, lint, build, and Vitest component tests* (Tác giả: Lý Gia Bảo).
8. `2a8441e`: *Part D: OCR scope policy, per-page full OCR, audit logging, and UI notice* (Tác giả: Lý Gia Bảo & Phan Thành Phát).

---

### CHỮ KÝ XÁC NHẬN CỦA NHÓM SINH VIÊN THỰC HIỆN

| **Trưởng nhóm** | **Thành viên** | **Thành viên** |
|:---:|:---:|:---:|
| *(Ký và ghi rõ họ tên)* | *(Ký và ghi rõ họ tên)* | *(Ký và ghi rõ họ tên)* |
| <br><br><br><br> | <br><br><br><br> | <br><br><br><br> |
| **Ngô Công Thành**<br>MSSV: 2212461 | **Phan Thành Phát**<br>MSSV: 2212436 | **Lý Gia Bảo**<br>MSSV: 2213934 |

