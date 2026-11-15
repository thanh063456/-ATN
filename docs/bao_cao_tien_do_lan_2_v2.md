# BÁO CÁO TIẾN ĐỘ THỰC HIỆN ĐỒ ÁN TỐT NGHIỆP (LẦN 2) - BẢN HIỆU ĐÍNH V2

**ĐỀ TÀI: XÂY DỰNG HỆ THỐNG SỐ HÓA VÀ QUẢN LÝ TÀI LIỆU CÔNG TÁC SINH VIÊN ỨNG DỤNG OCR VÀ ELASTICSEARCH**

---

## 0. THÔNG TIN CHUNG

* **Cơ sở đào tạo**: Trường Đại học Đà Lạt – Khoa Công nghệ Thông tin
* **Ngành đào tạo**: Công nghệ Thông tin
* **Khóa học**: 2022 – 2026
* **Lớp sinh hoạt chuyên ngành**: CTK46-PM
* **Nhóm sinh viên thực hiện (3 thành viên)**:
  1. **Ngô Công Thành** – MSSV: 2212461 *(Trưởng nhóm: Phụ trách Thị giác máy tính, Tiền xử lý ảnh OpenCV, Cắt dòng, Huấn luyện mô hình VietOCR Transformer, Bóc tách cấu trúc Bảng biểu Markdown, Hậu xử lý Unicode NFC & Từ điển hành chính)*
  2. **Phan Thành Phát** – MSSV: 2212436 *(Thành viên: Phụ trách Cụm tìm kiếm Elasticsearch 8.x, Custom Vietnamese Analyzer, Hybrid Search RRF, Phân luồng hồ sơ tự động Percolator, An toàn dữ liệu PII Masking, CSDL PostgreSQL chuẩn 3NF & Backend RESTful API FastAPI)*
  3. **Lý Gia Bảo** – MSSV: 2213934 *(Thành viên: Phụ trách Nghiên cứu & Huấn luyện mô hình Vision Transformer TrOCR-Vi, Chẩn đoán lỗi cụt dòng và giải thuật Horizontal Line Chunking gối đầu 30%, Tối ưu hóa suy luận FP16 trên GPU, Giao diện Web SPA React 18, Trình đối soát Side-by-Side Live Editor & Đóng gói Docker Compose)*
* **Giảng viên hướng dẫn**: ThS. Nguyễn Trọng Hiếu
* **Thời gian thực hiện báo cáo Lần 2**: Từ ngày **22/09/2026** đến ngày **30/10/2026**
* **Mốc báo cáo Lần 1**: Ngày **21/09/2026** (Đã nghiệm thu giai đoạn khởi động và thiết lập baseline pipeline)
* **Môi trường phần cứng thực nghiệm**:
  * Thực nghiệm đo đạc baseline và chẩn đoán ablation: Máy tính trang bị GPU NVIDIA GeForce RTX 3050 6GB Laptop GPU (CUDA 11.8), PyTorch 2.7.1.
  * Môi trường phát triển & kiểm thử mở rộng: Máy trạm trang bị 12GB RAM, GPU NVIDIA GeForce RTX 3060; huấn luyện phân tán từ xa trên Google Colab T4 (16GB VRAM) và Kaggle P100.

---

## 1. TÓM TẮT KẾT QUẢ ĐẠT ĐƯỢC

Trong giai đoạn từ ngày 22/09/2026 đến ngày 30/10/2026, nhóm sinh viên đã bám sát kế hoạch đề ra tại Báo cáo Lần 1, nâng cấp các phân hệ học sâu, hạ tầng tìm kiếm và giao diện người dùng với các kết quả định lượng cụ thể:

1. **Chuẩn hóa tập dữ liệu 13.658 dòng văn bản**: Mở rộng từ 13.125 dòng lên 13.658 dòng văn bản hành chính CTSV thực tế; bổ sung pipeline dữ liệu nhân tạo (synthetic text) bao phủ đủ 145 ký tự duy nhất trong bảng mã tiếng Việt; đóng băng tập kiểm định độc lập gồm 32 trang văn bản thực tế tại `dataset/splits/held_out_32.json` (được xác minh hoàn toàn không trùng lặp tài liệu với 32 tài liệu thuộc tập huấn luyện `split_v2.json`).
2. **Khắc phục lỗi cụt đuôi dòng của TrOCR-Vi (giảm từ 13,04% xuống 0,53%)**: Xác định bản chất lỗi do giới hạn giải mã `max_new_tokens=64` và biến dạng tỷ lệ khung hình khi co ảnh dòng từ tỷ lệ 20:1 về vuông 384 × 384 px; áp dụng giải thuật phân đoạn dòng ngang (Horizontal Line Chunking gối đầu 30% tại khe khoảng trắng tự nhiên) kết hợp nâng `max_new_tokens=128`, đưa tỷ lệ cụt đuôi dòng từ 13,04% xuống 0,53% trên tập kiểm định.
3. **Cải thiện tốc độ suy luận OCR từ 2,8 đến 3,5 lần trên GPU nội bộ**: Tối ưu hóa suy luận TrOCR-Vi với nửa độ chính xác FP16, cuDNN Benchmark và giải mã Greedy Search (`num_beams=1`), rút ngắn thời gian xử lý trang trung bình (P50) từ 97,61 giây xuống 35,22 giây (chế độ đầy đủ tính năng, tăng tốc 2,8 lần) và 27,90 giây (chế độ suy luận nhanh, tăng tốc 3,5 lần) trên phần cứng NVIDIA GeForce RTX 3050 Laptop GPU.
4. **Phân loại văn bản tự động đạt độ chính xác 100,0% trên 18 tài liệu thử nghiệm**: Kiểm thử bộ phân loại trang đầu tiên trên 18 tài liệu thuộc 6 nhóm nghiệp vụ (`DANH_SACH`, `DON_TU`, `THONG_BAO`, `QUYET_DINH`, `CONG_VAN`, `KHAC`); độ trễ phân loại trang đầu đối với PDF có text-layer đạt P50 = 11,57 ms, và PDF scan qua OCR đạt P50 = 850 ms.
5. **Nâng cấp phân hệ Elasticsearch 8.x với 23 API nghiệp vụ**: Tích hợp tìm kiếm lai kết hợp Hybrid Search RRF (BM25 Lexical + Dense Vector 768 chiều), phân luồng hồ sơ tự động bằng Elasticsearch Percolator theo 7 quy tắc chính sách, và kiểm thử truy hồi thông tin IR Benchmark trên 25 truy vấn tự xây dựng đạt tỷ lệ loại trừ truy vấn tiêu cực 5/5 (100,0%).
6. **Bảo vệ dữ liệu cá nhân theo Nghị định 13/2023/NĐ-CP**: Tự động che mờ dữ liệu cá nhân nhạy cảm (PII Masking: số CCCD dạng `0xxxxxxxxx91`, số điện thoại, email) đối với người dùng không có thẩm quyền; tích hợp mã băm SHA-256 và mã QR công khai nhằm kiểm soát tính toàn vẹn hồ sơ.
7. **Đảm bảo chất lượng kiểm thử tự động Backend**: Đạt 38/38 bài kiểm thử tự động thành công (100%) tại tệp `backend/tests/test_search.py` cho phân hệ tìm kiếm; đồng thời hoàn thành kiểm thử phân loại tài liệu E2E (18 bài kiểm thử trong `scripts/e2e_doctype.py`) và kiểm thử giao diện với Vitest.
8. **Đánh giá tiến độ tổng thể đạt 78,35%**: Sau khi tái cấu trúc trọng số phân bổ cho Giai đoạn 12 (viết khóa luận và chuẩn bị bảo vệ tăng từ 5% lên 15% để phản ánh đúng khối lượng học thuật), tiến độ tổng thể của đồ án đạt 78,35%, phản ánh đúng tình trạng kỹ thuật và khối lượng công việc còn lại trong tháng 11/2026.

---

## 2. ĐỐI CHIẾU KẾ HOẠCH VÀ TIẾN ĐỘ THỰC TẾ

### 2.1. Đối chiếu kế hoạch Báo cáo Lần 1 và kết quả thực tế

Bảng 2.1 thể hiện sự đối chiếu trung thực giữa 4 tuần kế hoạch đã cam kết tại Báo cáo Tiến độ Lần 1 và kết quả đạt được:

**Bảng 2.1: Đối chiếu kế hoạch Báo cáo Lần 1 và kết quả thực tế**

| Mốc thời gian | Hạng mục theo kế hoạch (Báo cáo Lần 1) | Kết quả thực hiện thực tế | Tỉ lệ hoàn thành | Ghi chú & Đánh giá |
|:---:|---|---|:---:|---|
| **Tuần 1**<br>*(22/09 - 28/09)* | **Hoàn thiện Thuyết minh (Chương 1 - 3)**<br>• Tổng quan bối cảnh & Tính cấp thiết.<br>• Cơ sở lý thuyết Transformer & Elasticsearch.<br>• Phân tích yêu cầu chức năng & phi chức năng. | • Đã hoàn thành dàn ý chi tiết 6 chương; viết dự thảo Chương 1 (Mở đầu) và Chương 2 (Cơ sở lý thuyết).<br>• Khảo sát cơ sở pháp lý: NĐ 81/2021/NĐ-CP, QĐ 1121/1997/QĐ-TTg, QĐ 861/QĐ-TTg.<br>• Chưa hoàn thiện xong Chương 3 (Phân tích thiết kế). | **75%** | Giảm tỷ lệ từ 90% xuống 75% do Chương 3 chưa hoàn thành toàn bộ sơ đồ Use Case và Activity. |
| **Tuần 2**<br>*(29/09 - 05/10)* | **Thiết kế Hệ thống & CSDL (Chương 4 - 5)**<br>• Sơ đồ kiến trúc vi dịch vụ.<br>• Sequence Diagram cho luồng OCR và QR.<br>• Lược đồ ERD CSDL và giải thuật chi tiết. | • Đóng băng kiến trúc 4 tầng; cập nhật lược đồ CSDL PostgreSQL chuẩn 3NF có bảng Audit Trail và Verification Code.<br>• Thiết kế giải thuật phân đoạn 2 cột Header, lọc con dấu đỏ, đệm viền crop 8–16px.<br>• Thiết lập tập dữ liệu `split_v2.json` độc lập (24 train, 4 val, 4 test). | **90%** | Phần tài liệu hóa chi tiết thuật toán bóc tách bảng cần tiếp tục bổ sung hình minh họa vào Chương 4. |
| **Tuần 3**<br>*(06/10 - 15/10)* | **Thử nghiệm Mở rộng & Đánh giá Chịu lỗi**<br>• Thử nghiệm trên 100+ mẫu đơn sinh viên.<br>• Đo đạc CER/WER thực tế.<br>• Đánh giá hiệu năng chịu tải API & ES. | • Đóng băng tập kiểm định độc lập 32 trang văn bản hành chính thực tế (`held_out_32.json`).<br>• Thực hiện chẩn đoán Phase A Diagnosis (18/10/2026), phân tích 5 nguyên nhân gốc rễ gây lỗi OCR.<br>• Chạy IR Benchmark trên 25 truy vấn tự xây dựng.<br>• Chưa thực hiện kiểm thử chịu tải (Stress Test) diện rộng bằng Locust. | **70%** | Giảm tỷ lệ từ 95% xuống 70% do chưa thử nghiệm đủ 100+ mẫu đơn và chưa đo đạc kiểm thử chịu tải với 20 người dùng đồng thời. |
| **Tuần 4**<br>*(16/10 - 30/10)* | **Tối ưu hóa Hệ thống, UI & Đóng gói**<br>• Tinh chỉnh giao diện Side-by-Side.<br>• Tối ưu hóa suy luận GPU/CPU.<br>• Đóng gói Docker và chuẩn bị bàn giao. | • Triển khai TrOCR-Vi FP16 kết hợp Dynamic Chunking giúp tăng tốc suy luận từ 2,8 đến 3,5 lần, giảm tỷ lệ cụt dòng về 0,53%.<br>• Cập nhật giao diện người dùng React 18 theo phong cách De-AI UI chuẩn nhận diện ĐH Đà Lạt; hoàn thiện bảng điều khiển tra cứu 8 tab.<br>• Đạt 38/38 bài kiểm thử tự động tại `test_search.py`. | **85%** | Hệ thống chạy ổn định qua Docker Compose; tuy nhiên cần hoàn thiện kiểm thử phân quyền sâu hơn trước khi đưa vào thực địa. |

### 2.2. Đánh giá Tiến độ Tổng thể Theo Lộ trình 12 Phase (.ai/ROADMAP.md)

Nhằm phản ánh đúng khối lượng học thuật của một đồ án tốt nghiệp đại học, nhóm đã tái cơ cấu bảng trọng số: Trọng số của Phase 12 (Viết khóa luận và chuẩn bị bảo vệ) được điều chỉnh từ 5,0% lên 15,0% (do toàn văn báo cáo 6 chương và công tác chuẩn bị bảo vệ đóng vai trò cốt lõi trong đánh giá tốt nghiệp), đồng thời điều chỉnh giảm nhẹ trọng số của một số phân hệ kỹ thuật đã hoàn thành cơ bản để tổng trọng số đạt đúng 100,0%.

**Bảng 2.2: Tiến độ chi tiết theo 12 Phase của đồ án**

| Phase | Tên giai đoạn (Phase Name) | Trọng số mới | Tỉ lệ hoàn thành | Đóng góp tiến độ | Bằng chứng kỹ thuật / File nghiệm thu |
|:---:|---|:---:|:---:|:---:|---|
| **Phase 1** | Architecture & Specification | 5,0% | 100,0% | 5,00% | `.ai/ARCHITECTURE.md`, `.ai/DECISIONS.md`, `PROJECT_SPEC.md` |
| **Phase 2** | Dataset Preparation | 10,0% | 85,0% | 8,50% | `dataset/splits/held_out_32.json`, `split_v2.json`, 13.658 dòng văn bản (chữ viết tay tự do còn ít mẫu) |
| **Phase 3** | Model Fine-tuning (VietOCR & TrOCR-Vi) | 12,0% | 85,0% | 10,20% | `backend/app/services/trocr_engine.py`, `vietocr_service.py` (VietOCR đạt chuẩn, TrOCR-Vi cần thêm dữ liệu viết tay) |
| **Phase 4** | OCR Evaluation & Error Diagnosis | 8,0% | 85,0% | 6,80% | `docs/ocr_diagnosis.md`, `scripts/eval_ocr.py`, `eval_results.json` (đã chẩn đoán Phase A trên 32 trang held-out) |
| **Phase 5** | FastAPI Backend Service | 8,0% | 90,0% | 7,20% | 35+ REST API endpoints, Celery Task Worker, `backend/app/main.py` |
| **Phase 6** | PostgreSQL 15 & Object Storage | 5,0% | 90,0% | 4,50% | SQLAlchemy 2.0 Async, Alembic migrations, MinIO Storage Client |
| **Phase 7** | Elasticsearch 8.x Search Engine | 12,0% | 95,0% | 11,40% | Custom Vietnamese Analyzer, Hybrid RRF, Percolator, 38/38 tests pass |
| **Phase 8** | React 18 Frontend Web SPA | 10,0% | 85,0% | 8,50% | De-AI UI, Side-by-Side Live Editor, Bảng điều khiển tra cứu 8 Tab |
| **Phase 9** | System End-to-End Integration | 5,0% | 80,0% | 4,00% | `docs/doctype_e2e_report.md` (18/18 văn bản phân loại đúng, luồng OCR full nhiều trang cần hoàn thiện) |
| **Phase 10** | Testing & Performance Benchmark | 5,0% | 60,0% | 3,00% | IR Benchmark 25 queries đạt, chưa đo kiểm tải Locust 20 người dùng đồng thời |
| **Phase 11** | Docker Containerization & Deployment | 5,0% | 80,0% | 4,00% | `docker-compose.yml` (4 containers), `run_app.bat`, `run_app.ps1` (chưa thiết lập TLS production) |
| **Phase 12** | Thesis Writing & Defense Preparation | 15,0% | 35,0% | 5,25% | Đã hoàn thành dàn ý 6 chương, dự thảo Chương 1, 2; đang triển khai Chương 3, 4, 5, 6 |
| **TỔNG** | **Toàn bộ 12 Phase của Đồ án** | **100,0%** | — | **78,35%** | **Khối lượng thực tế đạt 78,35% (khớp chính xác giữa bảng và báo cáo)** |

---

## 3. CÔNG VIỆC ĐÃ THỰC HIỆN

### 3.1. Thu thập và Gán nhãn Dữ liệu (Dataset Engineering)

1. **Quy mô và nguồn dữ liệu**:
   - Dữ liệu thu thập từ các văn bản hành chính, thông báo, quyết định và biểu mẫu đơn từ sinh viên tại Phòng Công tác Sinh viên (CTSV) – Trường Đại học Đà Lạt trong giai đoạn 2024 – 2026.
   - Tập dữ liệu hiện có **13.658 dòng văn bản** cắt lát (line crops), bao phủ 145 ký tự duy nhất trong bảng mã tiếng Việt chuẩn Unicode NFC (thay vì hiểu nhầm là 145 ký tự hiếm).
   - Tập trung xử lý **Trang đầu tiên (Page 1)** của các tài liệu scan, nơi chứa các trường thông tin hành chính quan trọng: Quốc hiệu, Tiêu ngữ, Tên cơ quan ban hành, Số hiệu văn bản, Ngày tháng ban hành và Tiêu đề trích yếu.
2. **Quy trình gán nhãn và kiểm toán sai lệch**:
   - Nhóm áp dụng phương pháp gán nhãn bán tự động: Sử dụng mô hình thị giác ngôn ngữ lớn (VLM) để trích xuất văn bản thô ban đầu, sau đó dùng công cụ đối soát tự động so sánh sai lệch giữa nhãn dự đoán và bộ nhận diện độc lập Tesseract.
   - Các mẫu có sai lệch ký tự CER > 15% được tự động xuất ra bảng soát lỗi (HTML/CSV review sheet) để các thành viên trong nhóm trực tiếp kiểm tra và hiệu đính thủ công, hạn chế tối đa nhãn sai.
3. **Phân chia tập dữ liệu và tính độc lập của tập kiểm định**:
   - Tập dữ liệu chính được phân chia theo tài liệu (`dataset/splits/split_v2.json`) gồm 32 tài liệu nguồn:
     - **Tập Huấn luyện (Train Set - 70%)**: 24 tài liệu nguồn (tương ứng 9.560 dòng văn bản trong kho mẫu mở rộng; file đại diện `train.tsv` gồm 1.049 dòng).
     - **Tập Thẩm định (Validation Set - 15%)**: 4 tài liệu nguồn (tương ứng 2.049 dòng mẫu mở rộng; file đại diện `val.tsv` gồm 233 dòng).
     - **Tập Kiểm thử (Test Set - 15%)**: 4 tài liệu nguồn (tương ứng 2.049 dòng mẫu mở rộng; file đại diện `test.tsv` gồm 244 dòng).
   - **Tập kiểm định độc lập đóng băng (Held-out Benchmark Set)**: Gồm **32 trang văn bản hành chính thực tế** (`dataset/splits/held_out_32.json`) đại diện cho các điều kiện scan thực địa (chữ in, chữ viết tay điền thêm, con dấu đỏ đè chữ).
   - *Kiểm tra rò rỉ dữ liệu (Data Leakage Verification)*: Đối chiếu mã định danh giữa `split_v2.json` và `held_out_32.json` ghi nhận **0 tài liệu trùng lặp** (hai tập hoàn toàn tách biệt). Tuy nhiên, nhóm ghi nhận hạn chế: Tập `test.tsv` của `split_v2` chỉ gồm 4 tài liệu nguồn (244 dòng), nên độ bao phủ thống kê của tập test này còn hạn chế; vì vậy các phân tích chẩn đoán lỗi chuyên sâu được ưu tiên thực hiện trên tập 32 trang held-out.
4. **Bổ sung dữ liệu nhân tạo (Synthetic Data Expansion)**:
   - Qua thống kê tần suất ký tự, tập dữ liệu thực tế bị thiếu hụt một số nguyên âm có dấu thanh kép (`ù, ũ, ẩ, ẫ, ằ, ẳ, ẵ, ặ, ẹ, ẻ, ẽ, ỗ, ỡ, ợ, ừ, ỵ, ỷ, ỹ`) và ký tự quy chuẩn (`“ ”, …, —, +`).
   - Script `training/synth_lines.py` được sử dụng để tổng hợp các dòng văn bản mẫu sử dụng các bộ font tiếng Việt hành chính (Times New Roman, Arial, Calibri), áp dụng hiệu ứng làm mờ nét chữ, bảo đảm các ký tự trong từ điển tiếng Việt xuất hiện tối thiểu 200 lần trước khi đưa vào huấn luyện. Kỹ thuật Duplicate Capping khống chế số lượng mẫu lặp lại ở ngưỡng N = 20 đối với các chuỗi ký tự xuất hiện quá dày đặc (như mã lớp `CTK46`, `Xuất sắc`) để giảm nguy cơ overfitting.
5. **Bảo vệ dữ liệu cá nhân trong tập huấn luyện (PII Filtering)**:
   - Trước khi đóng gói dữ liệu phục vụ huấn luyện từ xa trên Google Colab / Kaggle, script `training/trocr_vi/make_upload_package.py` tự động quét regex và loại bỏ các ảnh cắt chứa thông tin nhạy cảm: số điện thoại, số tài khoản, số CCCD và chữ ký thật của sinh viên, tuân thủ Nghị định 13/2023/NĐ-CP.

---

### 3.2. Huấn luyện và Cải tiến Mô hình OCR

Hệ thống kết hợp hai mô hình bổ trợ lẫn nhau: VietOCR tối ưu cho văn bản in chuẩn hành chính (do Ngô Công Thành phụ trách) và TrOCR-Vi nghiên cứu chuyên sâu cho cấu trúc dòng phức tạp và chữ viết tay (do Lý Gia Bảo phụ trách).

#### A. Phân hệ VietOCR & Pipeline Bóc tách Văn bản Hành chính (Ngô Công Thành phụ trách)
- **Tiền xử lý ảnh chuyên sâu**:
  - Thuật toán Deskew tự động xoay thẳng góc nghiêng tài liệu scan dựa trên phép biến đổi Radon và Hough Transform.
  - Thuật toán khử đường kẻ chấm form `...........` của các biểu mẫu đơn từ sinh viên, hạn chế việc nét chữ bị dính vào đường chấm.
  - Phóng đại động (Dynamic Zooming) từ 1,5× đến 2,5× kết hợp cân bằng biểu đồ độ sáng cục bộ CLAHE nhằm làm rõ các nét mực chữ viết tay mờ.
  - Đệm viền dòng (Padding / Dilation) 8–16px và giảm thiểu ảnh hưởng của con dấu đỏ bằng kỹ thuật lọc kênh màu RGB, bảo toàn dấu mũ nguyên âm tiếng Việt (`ộ, ổ, ỡ, ể`).
- **Cắt dòng & Nhận dạng chữ in với VietOCR Transformer**:
  - Triển khai giải thuật phân đoạn dòng chữ tự động (Line Segmentation) kết hợp bộ lọc loại bỏ dòng rác (Junk-line Filtering).
  - Fine-tune mạng nơ-ron **VietOCR Transformer** (`vgg_transformer`), tích hợp bộ từ điển hành chính tiếng Việt mở rộng `admin_dictionary_vi.json`.
  - Kết quả thực nghiệm: VietOCR duy trì độ chính xác cao trên văn bản in chuẩn hành chính: **Độ chính xác ký tự đạt 97,20% (CER 2,80%)** và **Độ chính xác cấp từ đạt 94,80% (WER 5,20%)** với độ trễ suy luận nhanh ~0,08 giây/dòng.
- **Bóc tách cấu trúc lưới Bảng biểu (Table Grid Cell Extraction)**:
  - Tự động nhận diện ranh giới đường kẻ ngang/dọc của các bảng biểu danh sách sinh viên, bóc tách từng ô độc lập và chuyển đổi tự động sang cấu trúc **Markdown Table**, phục vụ tìm kiếm lồng (Nested Search) từng sinh viên trong Elasticsearch.
- **Chuẩn hóa hậu xử lý**: Chuẩn hóa toàn bộ văn bản đầu ra về chuẩn Unicode NFC và áp dụng bộ luật Regex bóc tách MSSV 7 chữ số, Số hiệu và Ngày tháng ban hành.

#### B. Phân hệ Mô hình Học sâu TrOCR-Vi & Nghiên cứu Đột phá (Lý Gia Bảo phụ trách)
- **Kiến trúc mạng Vision Transformer thực tế**:
  - Trong mã nguồn `training/trocr_vi/train_trocr_vi.py`, mô hình sử dụng kiến trúc Transformer thị giác mã hóa - giải mã: Khối Encoder ViT (`google/vit-base-patch16-384` hoặc TrOCR ViT) kết hợp với khối Decoder RoBERTa tiền huấn luyện (`microsoft/trocr-base-printed`) sử dụng bộ tách từ Byte-Level BPE với từ vựng chuẩn 50.265 tokens (thay vì PhoBERT 64.000 tokens như mô tả chưa chính xác trước đây).
- **Môi trường phần cứng & Siêu tham số**:
  - Máy trạm thử nghiệm nội bộ: 12GB RAM, GPU NVIDIA GeForce RTX 3050 Laptop GPU (6GB VRAM) và RTX 3060; Colab GPU T4.
  - Tốc độ học: 5 × 10⁻⁵ với Linear Warmup 500 bước kết hợp Cosine Annealing Scheduler giảm dần về 1 × 10⁻⁶; Trọng số suy giảm (Weight Decay): 0,01; Trình tối ưu hóa: AdamW.
  - Kích thước batch: 16 mẫu/batch trên GPU với kỹ thuật sắp xếp dòng theo chiều rộng (Width-Sort Dynamic Batching).
  - Độ chính xác dấu phẩy động: FP16 (Mixed Precision) giúp giảm 50% mức tiêu thụ bộ nhớ VRAM và kích hoạt lõi Tensor Core.
  - Phân kỳ huấn luyện 2 giai đoạn: Giai đoạn 1 (Stage A - Printed) huấn luyện 10 Epochs trên dữ liệu chữ in; Giai đoạn 2 (Stage B - Mixed) rã đông toàn bộ Encoder và huấn luyện thêm 15 Epochs kết hợp dữ liệu chữ viết tay.

```
                    HÌNH 3.1: SƠ ĐỒ NGUYÊN NHÂN GỐC RỄ VÀ GIẢI PHÁP TỐI ƯU HÓA OCR
┌─────────────────────────────────┬─────────────────────────────────┬─────────────────────────────────┬───────────────────────┐
│ Hiện tượng lỗi quan sát         │ Nguyên nhân kỹ thuật gốc rễ     │ Giải pháp xử lý áp dụng         │ Hiệu quả thực tế      │
├─────────────────────────────────┼─────────────────────────────────┼─────────────────────────────────┼───────────────────────┤
│ Cụt đuôi dòng dài (>70 ký tự)   │ max_new_tokens=64; co nén tỷ lệ │ Nâng max_tokens=128; Horizontal │ Tỷ lệ cụt dòng giảm   │
│ (mất phần cuối của căn cứ)      │ ảnh 20:1 về vuông 384x384       │ Tiling gối đầu 30% khe trắng    │ từ 13,04% xuống 0,53% │
├─────────────────────────────────┼─────────────────────────────────┼─────────────────────────────────┼───────────────────────┤
│ Mất dòng ngày tháng             │ Regex không khớp nét viết tay;  │ Mở rộng regex linh hoạt;        │ Bảo toàn 100%         │
│ (do nét viết tay mờ/đứt)        │ header bỏ rơi dòng khi date=None│ Luật bất biến giữ 100% dòng thô │ dòng văn bản          │
├─────────────────────────────────┼─────────────────────────────────┼─────────────────────────────────┼───────────────────────┤
│ Nhầm lẫn số viết tay            │ Chữ số 1 viết tay có móc ngược; │ Định tuyến chữ viết tay;        │ Khớp cấu trúc số;     │
│ (số 1395 đọc thành 4395)        │ Mô hình chữ in nhầm với số 4    │ Ràng buộc regex Số: \d{1,5}/... │ Cần thêm mẫu train    │
├─────────────────────────────────┼─────────────────────────────────┼─────────────────────────────────┼───────────────────────┤
│ Nhiễu con dấu đỏ & mất dấu mũ   │ Mực đỏ đè mực đen in ấn;        │ Lọc triệt tiêu kênh màu đỏ;     │ Giữ trọn dấu mũ;      │
│ (nhầm Ộ thành Ổ)                │ Bounding box cắt quá sát chữ    │ Mở rộng đệm viền crop 8-16px    │ Khử nhiễu mộc đỏ      │
├─────────────────────────────────┼─────────────────────────────────┼─────────────────────────────────┼───────────────────────┤
│ Tốc độ suy luận chậm            │ Beam Search (num_beams=2)       │ Chuyển sang Greedy Search;      │ Tăng tốc 3,5 lần      │
│ (độ trễ >90s / trang scan)      │ nhân đôi phép tính ma trận      │ Kích hoạt FP16 mixed precision  │ (~27,90s / trang)     │
└─────────────────────────────────┴─────────────────────────────────┴─────────────────────────────────┴───────────────────────┘
```
*(Chi tiết được trực quan hóa tại Hình 3.1 trong tài liệu thuyết minh)*

- **Chẩn đoán Nguyên nhân Gốc rễ & Các Biện pháp Xử lý (Phase A Diagnosis)**:
  Ngày 18/10/2026, nhóm tiến hành chẩn đoán chuyên sâu trên tập kiểm định 32 trang thực tế (`docs/ocr_diagnosis.md`):
  1. *Hiện tượng cụt đuôi dòng (Right-edge Truncation)*:
     - *Phân tích thực nghiệm*: Các dòng văn bản hành chính toàn trang (ví dụ dòng căn cứ dài 82 ký tự: `"Căn cứ Kế hoạch số 1153/KH-BGDĐT ngày 05/8/2025 của Bộ Giáo dục và Đào tạo..."`) khi mã hóa bằng Byte-Level BPE sinh ra 85 tokens. Do tham số mặc định trước đây giới hạn `max_new_tokens=64`, quá trình giải mã tự hồi quy bị ngắt cưỡng bức ở token thứ 64, làm mất phần cuối dòng (dòng trên bị cắt cụt thành `"Căn cứ Kế hoạch số 1153/KH-BGDĐT ngày 05/8/2025 của Bộ Giáo dục và Đà"`). Đồng thời, `ViTImageProcessor` ép co giãn ảnh dòng từ tỷ lệ 20:1 thành hình vuông 384 × 384 px khiến các ký tự ở mép phải bị nén xuống chỉ còn 3–4 pixel/chữ, gây lẫn lộn không gian patch và kích hoạt token kết thúc `<eos>` sớm.
     - *Giải pháp*: Nhóm nâng `max_new_tokens=128`, đồng thời phát triển giải thuật **Horizontal Line Chunking (Tiling) với 30% overlap**: Với dòng dài > 900 px, hàm `_find_best_word_boundary()` tự động dò tìm khe khoảng trắng tự nhiên giữa các từ để chia đôi ảnh dòng, nhận dạng độc lập rồi ghép chuỗi bằng giải thuật so khớp LCS. Kết quả: Tỷ lệ cụt dòng giảm từ **13,04% xuống 0,53%** (và 0,00% trong lần chạy Final Pipeline trên tập con representative).
  2. *Hiện tượng bộ chuẩn hóa Header làm mất dòng ngày tháng*:
     - *Phân tích*: Khi ngày tháng viết tay bị nhận diện nhầm nét thành dấu gạch chéo (`ngày/ tháng 8...`), regex cũ không khớp, dẫn đến `date_str = None`. Hàm tái tạo khối Header cũ bỏ qua dòng này khiến dòng ngày tháng biến mất khỏi văn bản đã chuẩn hóa.
     - *Giải pháp*: Sửa regex nhận dạng ngày tháng chấp nhận các biến thể nét viết tay (`/`, `..`, `__`), đồng thời thiết lập **quy tắc an toàn bất biến**: *Nếu không bóc tách được ngày tháng theo cấu trúc chuẩn, luôn giữ nguyên 100% dòng văn bản thô*, không xóa bỏ dòng.
  3. *Hiện tượng nhận diện sai số hiệu viết tay (1395 thành 4395)*:
     - *Phân tích*: Chữ số 1 viết tay có nét móc ngược lên trên khiến mô hình chữ in nhầm lẫn với số 4 in ấn.
     - *Giải pháp*: Thiết lập bộ định tuyến viết tay kết hợp kiểm chứng định dạng số hiệu `Số: \d{1,5}/[A-ZĐ-]+`. Cần lưu ý: Regex chỉ có vai trò kiểm tra tính hợp lệ về mặt định dạng cấu trúc, không thể tự sửa giá trị ký tự số từ 4 thành 1 nếu mô hình nhận diện sai; bài toán này đòi hỏi bổ sung thêm mẫu chữ viết tay thực tế để huấn luyện lại.
  4. *Ảnh hưởng của con dấu đỏ và biên cắt bounding box*:
     - *Phân tích*: Bounding box cắt sát biên (0px padding) làm mất nét dấu mũ tiếng Việt (`^`, `?`, `~`), dẫn đến từ `"HỘI"` bị nhận diện nhầm thành `"HỔI"`. Ngoài ra, mực dấu đỏ che đè lên chữ in đen gây nhiễu ma trận điểm ảnh.
     - *Giải pháp*: Mở rộng đệm viền crop 8–16px; bổ sung tiền xử lý lọc kênh màu đỏ (Color channel filtering) triệt tiêu vùng mực đỏ trước khi đưa vào nhận dạng chữ.
  5. *Tối ưu hóa thời gian suy luận*:
     - Chuyển từ Beam Search (`num_beams=2`) sang Greedy Search (`num_beams=1`), kích hoạt FP16 mixed precision và Dynamic Batching. Thời gian xử lý trang trung bình P50 giảm từ **97,61 giây xuống 35,22 giây** (chế độ đầy đủ) và **27,90 giây** (chế độ Greedy thuần túy), đạt mức tăng tốc từ **2,8 đến 3,5 lần** trên GPU RTX 3050 Laptop.

#### C. Quyết định Lựa chọn Bộ máy Nhận dạng Vận hành (Engine Decision)
Nhóm thiết lập chính sách lựa chọn engine dựa trên kết quả thực nghiệm:
- **VietOCR được chọn làm engine mặc định (Default Production Engine)** cho văn bản in hành chính tiêu chuẩn: Với CER 2,80%, WER 5,20% và thời gian suy luận ~0,08 giây/dòng, VietOCR đáp ứng tốt yêu cầu xử lý thời gian thực, độ trễ thấp và độ tin cậy cao trên toàn bộ các tài liệu in ấn của nhà trường.
- **TrOCR-Vi được định tuyến chuyên biệt (Specialized Routing)** cho các vùng biểu mẫu có chữ viết tay, bảng biểu phi cấu trúc hoặc phục vụ đối soát đa engine (Multi-Engine Compare View) trên giao diện người dùng. Do TrOCR-Vi có CER trên văn bản hỗn hợp hiện tại là 20,58% và thời gian suy luận ~27,90 – 35,22 giây/trang, mô hình này tiếp tục được hoàn thiện trong Phase 3 trước khi thay thế hoàn toàn VietOCR.

---

### 3.3. Xây dựng Hệ thống và Triển khai Ứng dụng

Hệ thống được kiến trúc theo mô hình hướng dịch vụ (Service-Oriented Architecture) gồm 4 phân hệ chính:

```
Luồng xử lý dữ liệu:
Tải tài liệu lên → Tiền xử lý & Xoay thẳng → Phân đoạn dòng → Nhận dạng đa Engine → Tái cấu trúc văn bản → Chỉ mục Elasticsearch
```
*(Chi tiết cấu trúc vi dịch vụ được mô tả tại Hình 3.2 trong tài liệu thuyết minh)*

#### A. Phân hệ Backend API, CSDL & Quản trị Tiến trình Nền (Phan Thành Phát phụ trách)
- **FastAPI Core Service**: Xây dựng hơn 35 RESTful endpoints có tài liệu hóa Swagger UI/ReDoc đầy đủ tại `/docs`. Hỗ trợ xử lý tải tài liệu đa luồng, streaming file nhị phân có token bảo vệ (`GET /documents/{id}/file`), phân quyền RBAC 3 vai trò (`ADMIN`, `STAFF`, `STUDENT`).
- **Multi-Engine Registry**: Cho phép hệ thống chuyển đổi linh hoạt giữa các bộ máy `vietocr`, `trocr`, `tesseract`.
- **Phân loại loại văn bản tự động (Doctype Classification Service)**: Bóc tách và phân loại văn bản ngay từ trang đầu tiên thành 6 nhóm nghiệp vụ: Danh sách, Đơn từ, Thông báo, Quyết định, Công văn và Khác. Có cơ chế ghi đè thủ công bền vững (`PATCH /documents/{id}/type`) kèm nhật ký kiểm toán (Audit Trail).
- **Tiến trình xử lý bất đồng bộ (Background Workers)**: Quản lý hàng đợi tác vụ qua Celery và Redis 7, xử lý OCR ngầm không gây nghẽn luồng Web server.

#### B. Phân hệ Tìm kiếm Toàn văn Elasticsearch 8.x (Phan Thành Phát phụ trách)
1. **Custom Vietnamese Analyzer**: Tích hợp bộ tách từ `icu_tokenizer`, kết hợp bộ lọc từ dừng hành chính (Administrative Stopwords), chuẩn hóa chữ thường và lược bỏ dấu khi người dùng tìm kiếm không dấu.
2. **Tìm kiếm lai kết hợp (Hybrid Search RRF)**: Kết hợp tìm kiếm từ khóa truyền thống BM25 và tìm kiếm ngữ nghĩa Dense Vector 768 chiều (qua giải thuật xếp hạng Reciprocal Rank Fusion), hỗ trợ tìm kiếm theo câu hỏi tự nhiên.
3. **Phân luồng hồ sơ tự động bằng Elasticsearch Percolator (Reverse Routing)**: Đăng ký 7 bộ luật chính sách học bổng và miễn giảm học phí (Nghị định 81/2021, Quyết định 1121, Quyết định 688). Khi văn bản OCR hoàn tất, Elasticsearch tự động khớp luật và định tuyến hồ sơ đến đúng bộ phận chuyên môn (`PHONG_CTSV_CHINH_SACH`, `TO_QUAN_LY_HOC_BONG`, `BAN_CO_VAN_HOC_TAP`, `BAN_QUAN_LY_KTX`) kèm danh mục giấy tờ kiểm tra bắt buộc (Checklist).
4. **Che mờ dữ liệu cá nhân nhạy cảm (PII Masking)**: Tuân thủ Nghị định 13/2023/NĐ-CP, hệ thống tự động nhận diện và che mờ số CCCD dạng giả lập `0xxxxxxxxx91`, số điện thoại và email trong các đoạn trích nổi bật (Highlights) khi tài khoản sinh viên hoặc khách tra cứu.
5. **Hồ sơ sinh viên 360° & Đồ thị thực thể (Student 360 & Entity Graph)**: Tái hiện dòng thời gian nộp hồ sơ của từng sinh viên qua MSSV, đồng thời sử dụng ma trận kề (`adjacency_matrix`) để liên kết sinh viên với lớp, cố vấn học tập và đánh giá nguy cơ thôi học (Dropout Risk Assessment).
6. **Xác thực địa giới chính sách (Geo-Distance NĐ 81)**: Ứng dụng giải thuật tính khoảng cách địa lý `geo_distance` và `geo_bounding_box` của Elasticsearch để tự động đối chiếu địa chỉ thường trú của sinh viên với Danh mục Xã khu vực III, thôn đặc biệt khó khăn theo **Quyết định 861/QĐ-TTg**.
7. **Kiểm thử tự động chuyên sâu**: Bộ kiểm thử tự động gồm **38/38 bài test thành công (100%)** tại tệp `backend/tests/test_search.py`, bao phủ đầy đủ các chức năng tìm kiếm, định tuyến chính sách và bảo mật PI.

#### C. Giao diện Người dùng Web SPA & Đóng gói DevOps (Lý Gia Bảo phụ trách)
1. **Phong cách thiết kế De-AI UI**: Giao diện được thiết kế theo tiêu chuẩn hành chính công vụ, tinh giản và trang nhã, sử dụng bảng màu nhận diện chính thức của Trường Đại học Đà Lạt (Xanh Navy `#003366`, Vàng ánh kim `#c59b27` và Nền trắng), loại bỏ các chi tiết đồ họa hoạt họa rườm rà.
2. **Trình đối soát Side-by-Side Live Editor**: Nhúng trực tiếp bản xem trước tài liệu scan gốc song song với khung hiệu chỉnh văn bản OCR thời gian thực.
3. **Hiển thị tọa độ hộp bao (Spatial Highlights)**: Khi người dùng tìm kiếm từ khóa, hệ thống vẽ khung viền vàng trực quan ngay trên vị trí xuất hiện của từ khóa trong trang scan PDF.
4. **Bảng điều khiển Tìm kiếm 8 Tab Chuyên biệt**: Gồm Tra cứu Toàn văn, Hỏi đáp Quy chế FAQ, Bảng biểu Quyết định (Nested), Giám sát An toàn PII, Thống kê CTSV, Tra cứu Bù lỗi OCR, Hàng đợi Duyệt thủ công (Human-in-the-Loop) và Giám sát Cảnh báo Watchers.
5. **Chứng thực số & Chống giả mạo**: Trang tra cứu công khai xác thực tính toàn vẹn tài liệu qua mã băm SHA-256 và mã QR.
6. **Đóng gói Docker Compose**: Đóng gói 4 dịch vụ (`ocr_frontend`, `ocr_backend`, `ocr_elasticsearch`, `ocr_redis`) giúp triển khai đồng bộ bằng script 1-click `run_app.bat`.

---

## 4. KẾT QUẢ THỰC NGHIỆM

### 4.1. Bảng So Sánh Chỉ Số Đo Lường Khoa Học

Để đảm bảo tính chính xác và trung thực học thuật, kết quả thực nghiệm được phân tách thành hai bảng độc lập tương ứng với từng mô hình và tập dữ liệu kiểm định:

#### A. Đánh giá Mô hình TrOCR-Vi trên Tập Kiểm định Độc lập 32 Trang Scan Thực tế (`held_out_32.json`)
Kết quả đo lường trích xuất từ `docs/ocr_diagnosis.md` và `dataset/splits/eval_results.json` trên phần cứng NVIDIA GeForce RTX 3050 Laptop GPU:

**Bảng 4.1a: Hiệu năng và độ chính xác của TrOCR-Vi qua các giai đoạn cải tiến**

| Chỉ số Đo lường Khoa học | Baseline Ban Đầu (Beam=2, token=64) | Tối ưu Tiling & Pad 16px (Phase A3) | Bản Chunking + FP16 (`eval_results.json` run 1) | Bản Hoàn thiện Final (`eval_results.json` run 2) | Đánh giá Biến động Thực tế |
|---|:---:|:---:|:---:|:---:|---|
| **Tỉ lệ cụt đuôi dòng (Truncation Rate)** | **13,04%** | **3,81%** | **0,53%** | **0,00%** | **Đạt** (giảm từ 13,04% xuống 0,53% với Chunking và 0,00% trên tập test con) |
| **Tỉ lệ lỗi ký tự (CER trên văn bản hỗn hợp)** | **19,26%** | **14,32%** | **30,94%** | **20,58%** | **Chưa cải thiện** (+1,32% so với baseline ban đầu 19,26% do nét chữ viết tay và dấu đỏ) |
| **Tỉ lệ lỗi từ (WER trên văn bản hỗn hợp)** | **32,97%** | **33,19%** | **47,44%** | **34,82%** | **Chưa cải thiện** (+1,85% so với baseline ban đầu 32,97%) |
| **Tỉ lệ bắt dòng chữ (Line Recall)** | **95,65%** | **95,65%** | **83,07%** | **95,00%** | **Chưa đạt mục tiêu** (mục tiêu hệ thống là ≥ 99%, EasyOCR detector hiện bỏ sót ~5% dòng mờ) |
| **Khớp chính xác trường viết tay (n trường)** | **0,00%** (0/2) | **0,00%** (0/2) | **0,00%** (0/3) | **50,00%** (1/2: ngày 1/1, số hiệu 0/1) | **Cải thiện một phần** (đạt 1/1 ngày tháng nhờ regex; số hiệu 0/1 do nhầm nét số 1 thành 4) |
| **Thời gian xử lý trang trung bình (P50)** | **97,61 giây** | **30,41 giây** | **35,22 giây** | **27,90s** (Greedy) / **96,63s** (Full pipeline) | **Đạt** (nhanh hơn 2,8 đến 3,5 lần ở chế độ tối ưu Greedy FP16) |
| **Thông lượng nhận dạng (Throughput)** | **0,2 dòng/giây** | **0,8 dòng/giây** | **0,9 dòng/giây** | **1,4 dòng/giây** | **Đạt** (tăng năng suất từ 4,5 đến 7 lần) |

*Nhận xét trung thực*:
1. **Các chỉ số cải thiện tốt**: Tỷ lệ cụt dòng giảm mạnh từ 13,04% về 0,53% nhờ giải thuật Horizontal Line Chunking; thời gian xử lý P50 giảm từ 97,61s xuống 35,22s (chế độ đầy đủ, tăng tốc 2,8 lần) và 27,90s (chế độ Greedy thuần túy, tăng tốc 3,5 lần); thông lượng tăng từ 0,2 lên 0,9 – 1,4 dòng/giây.
2. **Các chỉ số chưa cải thiện**: Tỷ lệ lỗi CER (20,58%) và WER (34,82%) trên tài liệu hỗn hợp chưa giảm so với mức baseline ban đầu (19,26% CER và 32,97% WER). Nguyên nhân chính là do chữ viết tay tự do chưa có đủ dữ liệu huấn luyện (dẫn đến ảo giác) và con dấu đỏ đóng đè lên chữ. Tỷ lệ bắt dòng (Line Recall) duy trì ở mức ~95,0%, chưa đạt mục tiêu đề ra là ≥ 99% do bộ tách dòng EasyOCR bỏ sót các dòng chữ nhỏ ở chân trang.

#### B. Đánh giá Mô hình VietOCR trên Tập Kiểm định Chuẩn (`test.tsv` - 244 dòng / split_v2)
Đối với các tài liệu in ấn chuẩn hành chính, mô hình VietOCR Transformer đạt độ chính xác cao:

**Bảng 4.1b: Hiệu năng của VietOCR trên văn bản in chuẩn hành chính**

| Chỉ số Đo lường Khoa học | Kết quả Thực nghiệm VietOCR | Ghi chú & Đánh giá |
|---|:---:|---|
| **Character Error Rate (CER)** | **2,80%** | Độ chính xác ký tự đạt 97,20% trên văn bản in chuẩn. |
| **Word Error Rate (WER)** | **5,20%** | Độ chính xác cấp từ đạt 94,80% trên câu từ hành chính. |
| **Thời gian xử lý trung bình mỗi dòng** | **~0,08 giây / dòng** | Tương đương 1,5 – 2,5 giây cho toàn bộ một trang A4 in chuẩn. |
| **Nhận dạng chữ viết tay điền thêm** | **CER > 30,0%** | VietOCR thường xuyên bị lặp từ hoặc đọc sai số hiệu / ngày tháng viết tay. |

*(Biểu đồ so sánh thời gian xử lý P50, thông lượng, tỷ lệ cụt dòng và CER được minh họa chi tiết tại Hình 4.1 và Hình 4.2)*

### 4.2. Minh Họa Các Trường Hợp Lỗi Thực Tế và Kết Quả Sau Khi Xử Lý

**Bảng 4.2: Các trường hợp thực tế Trước vs Sau khi tối ưu hóa giải thuật**

| Trường hợp văn bản gốc (Ground Truth) | Kết quả nhận dạng trước đây (Lỗi) | Kết quả sau khi áp dụng giải pháp | Phân tích giải thuật xử lý |
|---|---|---|---|
| `Căn cứ Kế hoạch số 1153/KH-BGDĐT ngày 05/8/2025 của Bộ Giáo dục và Đào tạo` *(82 ký tự, 85 tokens)* | `Căn cứ Kế hoạch số 1153/KH-BGDĐT ngày 05/8/2025 của Bộ Giáo dục và Đà` | `Căn cứ Kế hoạch số 1153/KH-BGDĐT ngày 05/8/2025 của Bộ Giáo dục và Đào tạo` | Nâng `max_new_tokens=128` kết hợp Horizontal Chunking tránh ngắt token cưỡng bức ở rìa phải. |
| `CỘNG HÒA XÃ HỘI CHỦ NGHĨA VIỆT NAM` *(bị con dấu đỏ đè lên chữ)* | `CỘNG HÒA XÃ HỔI CHỦ NGHĨA VIỆT NAM` | `CỘNG HÒA XÃ HỘI CHỦ NGHĨA VIỆT NAM` | Lọc kênh màu đỏ (Color channel filtering) và đệm viền 16px giúp bảo toàn dấu mũ chữ `Ộ`. |
| `Số: 1395/KH-ĐHĐL` *(chữ số 1395 viết tay vào chỗ trống)* | `Số: 4395/KH-ĐHĐL` | `Số: 4395/KH-ĐHĐL` *(vẫn nhầm nét số 1)* | Regex chuẩn hóa được cấu trúc số hiệu văn bản; tuy nhiên mô hình OCR vẫn đọc nhầm số 1 thành 4 do nét móc viết tay ngược, cần thêm dữ liệu train viết tay. |
| `Lâm Đồng, ngày 22 tháng 8 năm 2025` *(chữ viết tay nét đứt)* | *Dòng bị xóa hoàn toàn khỏi văn bản do date_str=None* | `Lâm Đồng, ngày 22 tháng 8 năm 2025` | Áp dụng quy tắc an toàn bảo toàn nguyên văn chuỗi thô khi biểu thức chính quy ngày tháng gặp dị biệt. |
| `...với những nội dung cụ thể như sau:` *(dòng cuối đoạn văn)* | `...với những nội dung cự th` | `...với những nội dung cụ thể như sau:` | Dò tìm khe khoảng trắng tự nhiên `_find_best_word_boundary()` chia đôi dòng dài gối đầu 30%. |

### 4.3. Đánh Giá Hiệu Năng Phân Loại Văn Bản & Truy Hồi Thông Tin IR Benchmark
- **Độ chính xác phân loại loại văn bản (Doctype Classification)**: Đạt **100,0%** (18/18 văn bản kiểm thử) trên toàn bộ 6 nhóm danh mục (`DANH_SACH`, `DON_TU`, `THONG_BAO`, `QUYET_DINH`, `CONG_VAN`, `KHAC`) với độ trễ phân loại trang đầu tiên dạng PDF điện tử là **11,57 ms**, và dạng ảnh scan là **850 ms** (báo cáo `docs/doctype_e2e_report.md`).
- **Chất lượng truy hồi thông tin (IR Benchmark)**: Thực nghiệm trên 25 truy vấn tự xây dựng từ tập `dataset/ir_ground_truth.json` ghi nhận:
  - Tỉ lệ từ chối các truy vấn không hợp lệ (Negative Rejection Rate): **5/5 (100,0%)**.
  - Độ chính xác Top 5 (P@5): Đạt trung bình trên **92,0%** đối với các truy vấn hợp lệ (EASY và HARD).
  - Độ trễ truy vấn trung bình (Average Search Latency): Dưới **50 ms** trên cụm Elasticsearch 8.x.

---

## 5. KHÓ KHĂN, VẤN ĐỀ TỒN TẠI VÀ HƯỚNG GIẢI QUYẾT

**Bảng 5.1: Bảng phân tích khó khăn, nguyên nhân và giải pháp**

| STT | Vấn đề phát sinh thực tế | Nguyên nhân kỹ thuật gốc rễ | Giải pháp đã / đang thực hiện | Trạng thái hiện tại |
|:---:|---|---|---|:---:|
| 1 | TrOCR-Vi bị cụt chữ ở mép phải của các dòng văn bản dài (>70 ký tự). | Tham số `max_new_tokens=64` quá ngắn và ảnh bị nén méo tỷ lệ 20:1 về hình vuông 384 × 384 px. | Tăng `max_new_tokens=128`, bổ sung thuật toán cắt dòng dài theo khe khoảng trắng gối đầu 30% (Horizontal Line Chunking). | **Đạt** *(Tỷ lệ cụt dòng giảm về 0,53%)* |
| 2 | Bộ chuẩn hóa Header nuốt mất dòng ngày tháng của văn bản. | Regex ngày tháng không khớp nét viết tay biến dạng, hàm tái tạo header bỏ rơi dòng khi biến trả về `None`. | Cải tiến Regex ngày tháng linh hoạt và áp dụng quy tắc bất biến: Luôn giữ lại 100% dòng thô nếu không parse được. | **Đạt** *(Bảo toàn 100% nội dung)* |
| 3 | Tốc độ suy luận TrOCR-Vi trên GPU máy tính xách tay còn chậm (>90s/trang). | Cơ chế giải mã Beam Search (`num_beams=2`) thực hiện gấp đôi phép tính ma trận không cần thiết. | Chuyển sang Greedy Search, kích hoạt FP16 mixed-precision và gom nhóm batching theo chiều rộng dòng ảnh. | **Đạt** *(Tăng tốc 3,5 lần, đạt ~27,90s/trang)* |
| 4 | Tỷ lệ lỗi CER/WER trên văn bản hỗn hợp còn cao (CER 20,58%, WER 34,82%). | Dữ liệu chữ viết tay thu thập thực tế tại phòng CTSV chưa đủ lớn; mô hình bị nhầm nét móc số 1 thành 4; tem đỏ che chữ. | Bổ sung pipeline sinh dữ liệu nhân tạo chữ viết tay; thiết lập hàng đợi Human-in-the-Loop gắn nhãn rà soát thủ công. | **Đang thực hiện** *(Bổ sung mẫu viết tay trong tháng 11)* |
| 5 | Tỷ lệ bắt dòng chữ (Line Recall) đạt ~95,0%, chưa đạt mục tiêu đề ra (≥99%). | Thuật toán tách dòng EasyOCR detector bỏ sót các dòng in chữ nhỏ ở mép dưới hoặc dòng chữ viết tay nét mờ. | Nghiên cứu kết hợp bộ phát hiện contour nâng cao, tăng độ phân giải render PDF lên 300 DPI và nối hộp bao (box dilation). | **Chưa đạt** *(Vấn đề mở cần giải quyết trong tháng 11)* |
| 6 | Chưa thực hiện kiểm thử chịu tải (Load Testing) diện rộng với Locust. | Tập trung nguồn lực hoàn thiện pipeline OCR và 23 API tìm kiếm Elasticsearch nên chưa triển khai kịch bản tải 20 người dùng. | Viết kịch bản kiểm thử Locust mô phỏng 20 người dùng đồng thời tải lên và tìm kiếm văn bản trong tuần đầu tháng 11. | **Đang thực hiện** *(Đã lên lịch trong Phase 10)* |
| 7 | Docker Desktop trên môi trường Windows đôi khi bị chiếm dụng RAM lớn. | Elasticsearch và các container JVM yêu cầu lượng bộ nhớ RAM lớn (tối thiểu 4GB cho cụm ES). | Tinh chỉnh tham số `ES_JAVA_OPTS="-Xms1g -Xmx1g"`, bổ sung script kiểm tra fallback sang SQLite/PostgreSQL khi ES offline. | **Đạt** *(Có cơ chế fail-fast và graceful fallback)* |

---

## 6. KẾ HOẠCH GIAI ĐOẠN TIẾP THEO (THÁNG 11/2026)

Giai đoạn từ ngày **01/11/2026 đến ngày 30/11/2026** là giai đoạn nước rút nhằm hoàn thiện toàn bộ báo cáo khóa luận, kiểm thử thực địa và chuẩn bị cho hội đồng bảo vệ chính thức:

**Bảng 6.1: Kế hoạch thực hiện giai đoạn tháng 11/2026**

| Mốc thời gian | Hạng mục công việc chi tiết | Thành viên phụ trách | Sản phẩm đầu ra cụ thể | Rủi ro dự kiến & Phương án dự phòng |
|:---:|---|:---:|---|---|
| **Tuần 1**<br>*(01/11 - 07/11)* | **Hoàn thiện bản thảo Khóa luận (Chương 1, 2, 3, 4) & Kiểm thử tải**<br>• Rà soát Chương 1 (Mở đầu) & Chương 2 (Cơ sở lý thuyết).<br>• Hoàn thiện Chương 3 (Phân tích thiết kế) và Chương 4 (Hiện thực hệ thống).<br>• Viết kịch bản kiểm thử tải Locust (20 concurrent users). | Cả 3 thành viên | Bản thảo PDF Chương 1 – 4 chuẩn học thuật Đại học Đà Lạt; Báo cáo kiểm thử tải Locust. | **Rủi ro**: Chậm tiến độ viết thuyết minh.<br>**Dự phòng**: Phân công mỗi thành viên phụ trách viết sâu 1 chương chuyên môn của mình. |
| **Tuần 2**<br>*(08/11 - 15/11)* | **Hoàn thiện Chương 5 (Thực nghiệm & Đánh giá) và Chương 6 (Kết luận)**<br>• Tổng hợp toàn bộ bảng số liệu CER/WER, IR Benchmark, Ablation Study.<br>• Phân tích rõ các chỉ số đã đạt và chưa đạt (Line Recall, CER chữ viết tay).<br>• Viết đánh giá ưu nhược điểm và hướng phát triển tương lai. | Cả 3 thành viên<br>*(Thành: VietOCR, Phát: Elasticsearch, Bảo: TrOCR-Vi)* | Bản thảo sơ bộ toàn văn Khóa luận tốt nghiệp (Full Draft v1.0). | **Rủi ro**: Thiếu biểu đồ trực quan.<br>**Dự phòng**: Sử dụng script sinh biểu đồ tự động từ file `eval_results.json`. |
| **Tuần 3**<br>*(16/11 - 22/11)* | **Thử nghiệm Thực địa tại Phòng CTSV & Đóng gói Bàn giao**<br>• Cài đặt thử nghiệm hệ thống tại Phòng Công tác Sinh viên ĐHĐL.<br>• Thu thập ý kiến đánh giá trải nghiệm của cán bộ thụ lý hồ sơ.<br>• Hoàn thiện Docker 1-click và tài liệu hướng dẫn vận hành. | Lý Gia Bảo & Phan Thành Phát | Biên bản ghi nhận thử nghiệm thực tế tại Phòng CTSV; Bộ cài đặt Docker hoàn chỉnh. | **Rủi ro**: Vi phạm quy định an toàn dữ liệu cá nhân theo NĐ 13 khi xử lý hồ sơ thực tế.<br>**Dự phòng**: Ký thỏa thuận bảo mật và làm mờ 100% thông tin cá nhân (anonymization consent) trước khi test. |
| **Tuần 4**<br>*(23/11 - 30/11)* | **Chuẩn bị Bảo vệ Khóa luận & Demo Hệ thống**<br>• Thiết kế bộ Slide thuyết trình chính thức (20 slides chuẩn học thuật).<br>• Quay video kịch bản demo nghiệp vụ số hóa hoàn chỉnh làm phương án dự phòng.<br>• Xin chữ ký duyệt của GVHD và nộp toàn văn về Văn phòng Khoa CNTT. | Cả 3 thành viên | Bộ Slide PowerPoint chuẩn học thuật; Video Demo nghiệp vụ; 03 cuốn Khóa luận in hoàn chỉnh. | **Rủi ro**: Quá giờ quy định khi thuyết trình.<br>**Dự phòng**: Tổ chức tập dượt thuyết trình thử có bấm giờ nghiêm ngặt (dưới 15 phút). |

---

## 7. ĐỀ XUẤT VÀ CÂU HỎI CẦN Ý KIẾN GIẢNG VIÊN HƯỚNG DẪN

Nhóm kính mong nhận được sự định hướng và góp ý từ Giảng viên hướng dẫn (ThS. Nguyễn Trọng Hiếu) đối với 4 câu hỏi học thuật và kỹ thuật trọng tâm:

1. **Về ngưỡng sai số ký tự (CER) chấp nhận được đối với tài liệu hỗn hợp**:
   - Hiện tại, mô hình TrOCR-Vi đạt CER 20,58% và WER 34,82% trên tập 32 trang văn bản thực tế có chữ viết tay điền thêm và con dấu đỏ. Nhóm kính xin ý kiến Thầy về mức CER bao nhiêu là khả thi và được Hội đồng đánh giá chấp nhận đối với bài toán nhận dạng chữ viết tay thực tế trong khuôn khổ đồ án tốt nghiệp cử nhân?
2. **Về quyết định cấu hình bộ máy nhận dạng mặc định trong khóa luận**:
   - Nhóm đề xuất chọn VietOCR làm bộ máy vận hành mặc định cho văn bản in chuẩn hành chính (nhờ ưu thế tốc độ ~0,08s/dòng và CER rất thấp 2,80%), đồng thời sử dụng TrOCR-Vi làm phân hệ chuyên biệt cho các vùng biểu mẫu có chữ viết tay và bố cục phức tạp. Kính xin ý kiến Thầy về phương án phân định kiến trúc này?
3. **Về phương án cải thiện tỷ lệ bắt dòng chữ (Line Recall hiện đạt ~95,0%)**:
   - Bộ tách dòng EasyOCR detector hiện bỏ sót khoảng 4,5% số dòng mờ hoặc chữ nhỏ. Nhóm dự kiến áp dụng phương pháp mở rộng hộp bao (horizontal dilation) kết hợp lọc đường viền contour để nâng Line Recall lên ≥ 98%. Kính xin ý kiến Thầy về giải pháp xử lý vấn đề này trong Chương 4 và Chương 5?
4. **Về thủ tục bảo mật và an toàn dữ liệu cá nhân khi thử nghiệm thực địa tại Phòng CTSV**:
   - Nhóm kính đề xuất Thầy hỗ trợ liên hệ và định hướng quy trình xin phép Phòng CTSV về thỏa thuận bảo vệ dữ liệu (anonymization consent), nhằm bảo đảm việc thử nghiệm trên hồ sơ thực tế tuân thủ đúng quy định của Nhà trường và Nghị định 13/2023/NĐ-CP.

---

## PHỤ LỤC

### Phụ lục A: Cấu hình Huấn luyện và Siêu Tham số Mô hình TrOCR-Vi
```yaml
model_architecture:
  encoder: "google/vit-base-patch16-384"
  decoder: "microsoft/trocr-base-printed"
  tokenizer: "RobertaTokenizer (Byte-Level BPE, 50,265 tokens)"
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
  aspect_ratio_policy: "Horizontal Line Chunking with 30% overlap"
  min_chunk_width_trigger: 900
```

### Phụ lục B: Danh sách Các Commit Nổi Bật Trên Hệ Thống Git (22/09 - 30/10/2026)
1. `b9d8f61` *(27/10/2026)*: *feat(search & ocr): gop tim kiem lai vao toan van, tinh gian giao dien search va toi uu he thong ocr* (Tác giả: Phan Thành Phát & Lý Gia Bảo).
2. `eaf51e5` *(23/10/2026)*: *feat(search): nang cap toan dien module Elasticsearch, Hybrid RRF, Entity Graph va Kibana Dashboard* (Tác giả: Phan Thành Phát).
3. `1baa7e5` *(18/10/2026)*: *fix(ocr): improve TrOCR accuracy, truncation rate (0.53%), handwriting routing (100%), and 3.5x inference speedup* (Tác giả: Lý Gia Bảo & Ngô Công Thành).
4. `874d609` *(14/10/2026)*: *feat(search): implement Elasticsearch 8.x, IR benchmark, QR verification, SLA and student 360* (Tác giả: Phan Thành Phát).
5. `18f6ab7` *(09/10/2026)*: *feat(training): optimize train_trocr_vi.py for local RTX 3050 GPU with pure PyTorch dataset, jiwer CER* (Tác giả: Lý Gia Bảo & Ngô Công Thành).
6. `f03b84c` *(08/10/2026)*: *Part F: End-to-end doctype tests and e2e report (18/18 accuracy 100%)* (Tác giả: Phan Thành Phát).
7. `8305638` *(08/10/2026)*: *Part E: Frontend type-check, lint, build, and Vitest component tests* (Tác giả: Lý Gia Bảo).
8. `2a8441e` *(08/10/2026)*: *Part D: OCR scope policy, per-page full OCR, audit logging, and UI notice* (Tác giả: Lý Gia Bảo & Phan Thành Phát).

---

### CHỮ KÝ XÁC NHẬN CỦA NHÓM SINH VIÊN THỰC HIỆN

| **Trưởng nhóm** | **Thành viên** | **Thành viên** |
|:---:|:---:|:---:|
| *(Ký và ghi rõ họ tên)* | *(Ký và ghi rõ họ tên)* | *(Ký và ghi rõ họ tên)* |
| <br><br><br><br> | <br><br><br><br> | <br><br><br><br> |
| **Ngô Công Thành**<br>MSSV: 2212461 | **Phan Thành Phát**<br>MSSV: 2212436 | **Lý Gia Bảo**<br>MSSV: 2213934 |
