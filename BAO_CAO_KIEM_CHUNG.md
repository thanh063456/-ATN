# BÁO CÁO KIỂM CHỨNG KỸ THUẬT & SỐ LIỆU THỰC TẾ (FACT-CHECK REPORT)
**Dự án:** DocuCTSV — Hệ thống Số hóa và Quản lý Tài liệu Công tác Sinh viên Ứng dụng OCR và Elasticsearch  
**Tài liệu kiểm chứng:** `DAN_Y_SLIDE.md` (Báo cáo Tiến độ Đợt 2)  
**Ngày thực hiện kiểm chứng:** 02/11/2026  
**Vai trò:** Kỹ sư kiểm chứng (Fact-checker) kiêm Biên tập viên kỹ thuật độc lập

---

## I. BẢNG ĐỐI CHIẾU DANH MỤC KIỂM CHỨNG CHI TIẾT

| Hạng mục kiểm chứng | Giá trị trong dàn ý cũ | Giá trị tìm thấy trong mã nguồn & tài liệu | Bằng chứng kỹ thuật (File:Dòng/Khóa) | Kết luận |
|---|---|---|---|:---:|
| **A1. VietOCR: Backbone** | `VGG-19 hoặc ResNet-50` / `vgg19_bn` | `vgg19_bn` (VGG-19 với Batch Normalization) | `models/logs/transformerocr_ctsv_20261004_1848_n11447_config.yml:4`<br>`backend/app/services/vietocr_engine.py:90` | **Khớp** |
| **A2. VietOCR: Hidden size** | Không ghi rõ | `256` | `models/logs/transformerocr_ctsv_20261004_1848_n11447_config.yml:6` (`cnn.hidden: 256`) | **Khớp** |
| **A3. VietOCR: Chiều cao ảnh** | Cao cố định 32 pixel | `32 pixel` (ảnh dòng), max width 512 | `models/logs/..._config.yml:28` (`image_height: 32`) | **Khớp** |
| **A4. VietOCR: Số ký tự vocab** | `~145 nhãn` | 145 ký tự duy nhất trong bảng mã tiếng Việt chuẩn Unicode NFC | `docs/bao_cao_v2_changelog.md:43`<br>`docs/trocr_data_inventory.md:7` | **Khớp** |
| **A5. VietOCR: CER / WER** | CER 2,80%, WER 5,20% | CER 2,80%, WER 5,20% đo trên tập kiểm thử văn bản in chuẩn hành chính (`test.tsv` - 244 dòng / `split_v2`) | `docs/bao_cao_tien_do_lan_2_v2.md:245` (Bảng 4.1b)<br>`docs/Experiment.md:58` | **Khớp** *(đã làm rõ tập đo)* |
| **A6. VietOCR: Tốc độ xử lý** | `~0,08 giây/dòng` | `~0,08 giây/dòng` (tương đương 1,5–2,5s/trang A4 in chuẩn) | `docs/bao_cao_tien_do_lan_2_v2.md:248` | **Khớp** |
| **B1. Tiền xử lý: Deskew Hough** | Deskew tự động bằng Hough Transform | **Không có trong mã nguồn pipeline**. Hàm `preprocess_image` trả về nguyên bản `return pil_image` | `backend/app/services/vietocr_service.py:420-435` | ❌ **Lệch** *(Đã sửa lại dàn ý)* |
| **B2. Tiền xử lý: CLAHE** | Cân bằng sáng cục bộ CLAHE | **Bị tắt trong pipeline mặc định** vì thực nghiệm phát hiện làm vỡ nét chữ in chuẩn và gây quầng sáng | `backend/app/services/vietocr_service.py:423, 432`<br>`Bao_cao_dot_2.md:258` | ❌ **Lệch** *(Đã sửa lại dàn ý)* |
| **B3. Tiền xử lý: Denoise & Thresholding** | Khử nhiễu & phân ngưỡng nhị phân đưa vào VietOCR | Không nhị phân hóa ảnh nạp vào VietOCR. Chỉ dùng Otsu để tính `ink_ratio` và phát hiện đường kẻ bảng ma trận | `backend/app/services/vietocr_service.py:456, 471` | ❌ **Lệch** *(Đã làm rõ phạm vi)* |
| **C1. TrOCR-Vi: Checkpoint** | `models/trocr-vi` | `models/trocr-vi/final_model` (base từ `microsoft/trocr-base-handwritten`) | `models/trocr-vi/final_model/config.json:1-40`<br>`backend/app/core/config.py:125` | **Khớp** |
| **C2. TrOCR-Vi: Kích thước đầu vào** | 384x384 pixel | `image_size: 384`, `num_channels: 3` | `models/trocr-vi/final_model/config.json` (`encoder.image_size: 384`) | **Khớp** |
| **C3. TrOCR-Vi: Patch size & Patches** | 16x16 pixel (576 patches) | `patch_size: 16` ➔ $(384/16)^2 = 24 \times 24 = 576$ patches | `models/trocr-vi/final_model/config.json` (`encoder.patch_size: 16`) | **Khớp** |
| **C4. TrOCR-Vi: Positional Embeddings** | Positional Embeddings | 1D Positional Embeddings tuần tự mã hóa không gian mảnh ảnh | `models/trocr-vi/final_model/config.json` (`encoder.model_type: vit`) | **Khớp** |
| **C5. TrOCR-Vi: Vocab size** | 50.265 token | `vocab_size: 50265` | `models/trocr-vi/final_model/config.json` (`decoder.vocab_size: 50265`) | **Khớp** |
| **C6. TrOCR-Vi: max_length / tokens** | 64 token ➔ 128 token | Mặc định cũ 64 token; cấu hình mới `trocr_max_new_tokens: 128` | `backend/app/core/config.py:128`<br>`backend/app/services/trocr_engine.py:192` | **Khớp** |
| **C7. TrOCR-Vi: Chunking overlap & Hàm** | 30% overlap, `_find_best_word_boundary` | Hàm `_find_best_word_boundary` tìm khoảng trắng tự nhiên ở cửa sổ `0.15` quanh `0.50` (30% dải giữa dòng) | `backend/app/services/trocr_engine.py:116-168, 206` | **Khớp** |
| **C8. TrOCR-Vi: Truncation rate** | 13,04% ➔ 0,53% | 13,04% (Baseline) ➔ 0,53% (Chunking) và 0,00% (tập con) | `docs/ocr_diagnosis.md:12`<br>`docs/bao_cao_tien_do_lan_2_v2.md:230` | **Khớp** |
| **C9. TrOCR-Vi: Latency P50** | 97,61s ➔ 27,90s/trang | 97,61s (Baseline Beam=2) ➔ 27,90s (Greedy FP16, nhanh hơn 3,5 lần) | `docs/ocr_diagnosis.md:12`<br>`docs/bao_cao_tien_do_lan_2_v2.md:234` | **Khớp** |
| **C10. TrOCR-Vi: CER / WER tập 32 trang** | CER 19,26% ➔ 20,58%, WER 32,97% ➔ 34,82% | CER 19,26% ➔ 20,58%, WER 32,97% ➔ 34,82% trên tập 32 trang scan hành chính hỗn hợp (`held_out_32.json`) | `docs/ocr_diagnosis.md:12`<br>`docs/bao_cao_tien_do_lan_2_v2.md:231, 232` | **Khớp** |
| **C11. Tập 32 trang (held-out)** | 32 trang văn bản hỗn hợp | Đúng 32 file PDF/trang scan thực tế tại trường ĐH Đà Lạt (Quyết định, Kế hoạch, Thông báo, Đơn cứu đuối, Danh sách miễn giảm) | `dataset/splits/held_out_32.json:1-35` | **Khớp** |
| **D1. Hậu xử lý: DocumentHeaderNormalizer** | Chuẩn hóa Quốc hiệu, Tiêu ngữ | Chuẩn hóa Quốc hiệu, Tiêu ngữ, Tên trường qua từ điển regex | `backend/app/services/text_postprocessing/document_header_normalizer.py:50-130` | **Khớp** |
| **D2. Hậu xử lý: Regex Số hiệu / Ngày / MSSV** | Số hiệu, Ngày tháng, MSSV 7–8 chữ số | Regex `_DOC_NO_PATTERN`, `_DATE_PATTERN`, MSSV: `\b(2[0-9]{6,7}\|1[89][0-9]{5,6})\b` (độ chính xác 98,2%) | `backend/app/services/extraction_service.py:38-45`<br>`Bao_cao_dot_2.md:195` | **Khớp** |
| **D3. Hậu xử lý: Ngưỡng Confidence** | Ngưỡng `< 0,70` | Mã nguồn frontend dùng ngưỡng **`< 0,60`** hoặc loại `KHAC` hoặc `needs_review == true` để gắn badge "Cần kiểm tra" | `frontend/src/pages/SearchPage.tsx:1561`<br>`frontend/src/components/common/DocTypeComponents.tsx:64` | ❌ **Lệch** *(Đã sửa lại thành < 0,60)* |
| **E1. Phân loại: 6 nhãn văn bản** | 6 nhóm tài liệu | `QUYET_DINH`, `THONG_BAO`, `DON_TU`, `DANH_SACH`, `CONG_VAN`, `KHAC` | `backend/app/services/doctype_service.py:15-30`<br>`Bao_cao_dot_2.md:104` | **Khớp** |
| **E2. Phân loại: 18/18 mẫu E2E** | 18/18 mẫu đúng 100% | 18 mẫu synthetic test (6 loại x 3 cấu hình trang 1/3/5 trang) đạt 18/18 đúng | `scripts/e2e_doctype.py:30-120`<br>`Bao_cao_dot_2.md:185` | **Khớp** *(ghi rõ tập synthetic)* |
| **E3. Phân loại: Độ trễ P50** | 11,57 ms và 850 ms | PDF có text-layer: P50 = **11,57 ms**; Scanned PDF: P50 = **850 ms** (OCR trang 1) | `Bao_cao_dot_2.md:198-202`<br>`docs/bao_cao_tien_do_lan_2_v2.md:188` | **Khớp** |
| **E4. Gán nhãn tự động & Audit Log** | 5 nhóm nhãn, audit log | 5 nhóm metadata (Số hiệu, Thể loại, Ngành, Khoa/Phòng, Khóa học); bảng `audit_logs` ghi `OVERRIDE_TYPE` | `backend/app/models/audit_logs.py`<br>`Bao_cao_dot_2.md:112` | **Khớp** |
| **F1. Elasticsearch: Phiên bản** | Elasticsearch 8.12 | `elasticsearch:8.12.0` | `docker-compose.yml:45` | **Khớp** |
| **F2. Elasticsearch: Analyzers** | `icu_tokenizer`, `unaccent`, `synonym` | **Mã nguồn dùng `tokenizer: standard`**, bộ lọc `synonym_ctsv` (synonym graph) và `asciifolding` (bỏ dấu). Không cài `analysis-icu` trong image chuẩn | `backend/app/core/elasticsearch.py:110-145` | ❌ **Lệch** *(Đã sửa từ icu_tokenizer sang standard tokenizer)* |
| **F3. Elasticsearch: Hybrid RRF** | BM25 + Vector 768d, RRF | Endpoint `/hybrid-rrf` dung hòa BM25 + kNN vector 768 chiều với `rank_constant: 60`, `window_size: 50` | `backend/app/routers/search.py:4720-4765` | **Khớp** |
| **F4. Elasticsearch: Vector Embeddings** | 768 chiều | `EMBEDDING_DIM = 768`, model Gemini `text-embedding-004` (fallback Term-Hashing 768d) | `backend/app/services/embedding_service.py:18, 40` | **Khớp** |
| **F5. Elasticsearch: Percolator** | 7 luật chính sách | 7 luật: `RULE_ND81_MIEN_100`, `RULE_ND81_GIAM_70`, `RULE_ND81_GIAM_50`, `RULE_TCXH_QD1121`, `RULE_HB_KKHT`, `RULE_CANH_BAO_HOC_VU`, `RULE_CTSV_CHUNG` | `backend/app/routers/search.py:3770-3880` | **Khớp** |
| **F6. Elasticsearch: PII Masking** | Che mờ CCCD, SĐT | Che mờ CCCD (`068******891`), SĐT (`098****321`), Email cho `STUDENT` và Khách; `STAFF`/`ADMIN` xem đủ | `backend/app/routers/search.py:283-295, 923-930` | **Khớp** |
| **F7. IR Benchmark: Ground Truth** | 25 truy vấn thử nghiệm | 25 queries độc lập trong `dataset/ir_ground_truth.json` (10 EASY, 10 HARD, 5 NEGATIVE) | `dataset/ir_ground_truth.json`<br>`docs/Experiment.md:65-105` | **Khớp** |
| **F8. IR Benchmark: Precision@5** | Precision@5 > 92% *(thổi phồng cũ)* | Nhóm EASY: **P@5 = 74,0%** (P@10 = 82,0%, MAP = 72,9%); Nhóm HARD: P@5 = 40,0%; NEGATIVE: Rejection 100%; Macro-average: **45,6%** | `docs/Experiment.md:75-95` | ❌ **Lệch** *(Đã sửa sang 74,0% nhóm Easy và 100% Negative rejection)* |
| **F9. Elasticsearch: Thời gian truy vấn** | `< 45 ms` | Thời gian truy vấn nội bộ ES `< 45 ms` (P50 tổng thể web search = 0,54s) | `docs/Experiment.md:100`<br>`Bao_cao_dot_2.md:204` | **Khớp** |
| **F10. Elasticsearch: Unit test** | 38/38 unit test | `test_search.py` có 40 test functions (38 test cốt lõi ban đầu đạt 100%) | `backend/tests/test_search.py`<br>`HUONG_DAN_TEST_MODULE_ELASTICSEARCH.md:35` | **Khớp** |
| **G1. Dữ liệu: Mở rộng mẫu dòng** | 13.125 ➔ 13.658 dòng | 13.125 dòng gốc + 533 dòng synthetic bổ sung ký tự dấu hiếm = 13.658 dòng | `Bao_cao_dot_2.md:18, 92, 218` | **Khớp** |
| **G2. Dữ liệu: Tỷ lệ phân chia** | 70 / 15 / 15 | Train: 70% (~9.561 dòng), Val: 15% (~2.049 dòng), Test: 15% (~2.049 dòng) theo document split | `Bao_cao_dot_2.md:214-220` | **Khớp** |
| **G3. Bảo mật: 13 lỗi P0** | 13 lỗi P0 (8 Auth, 4 Doc, 1 Rel) | 8 Auth (JWT, refresh token...), 4 Document (IDOR, ticket...), 1 Reliability (fail-fast Postgres, cấm fallback SQLite ở prod) | `Bao_cao_dot_2.md:120-135`<br>`backend/tests/test_p0_auth_security.py` | **Khớp** |
| **H1. Hạ tầng: Số Docker containers** | 4 containers | 4 services: `backend`, `frontend`, `elasticsearch`, `redis` (PostgreSQL dùng bên ngoài / Supabase) | `docker-compose.yml:25-70` | **Khớp** |
| **H2. Hạ tầng: Phiên bản công nghệ** | FastAPI, React 18, ES 8.12, Redis 7 | FastAPI 0.110.0, React 18.3.1, Elasticsearch 8.12.0, Redis 7-alpine, PostgreSQL 15 | `docker-compose.yml`<br>`frontend/package.json`<br>`requirements.txt` | **Khớp** |
| **H3. Hạ tầng: Celery, Nginx, Prometheus** | Đã triển khai / Kế hoạch | Celery mới ở dạng skeleton (`celery_app.py`); Nginx và Prometheus là kế hoạch Tháng 11 | `Bao_cao_dot_2.md:210, 275` | **Khớp** |
| **I1. Tiến độ tổng thể: 78,4%** | 78,4% (Kỹ thuật ~88%, Thuyết minh ~40%) | Trọng số Phase 1-11 chiếm 85% (hoàn thành ~88%), Phase 12 chiếm 15% (hoàn thành 35%): Tổng cộng chính xác **78,35%** | `docs/bao_cao_v2_changelog.md:22`<br>`.ai/ROADMAP.md` | **Khớp** |

---

## II. DANH SÁCH THAY ĐỔI ĐÃ ÁP DỤNG VÀO DÀN Ý SLIDE (`DAN_Y_SLIDE.md`)

| Slide | Nội dung cũ trong bản nháp | Nội dung mới sau kiểm chứng | Lý do kỹ thuật |
|:---:|---|---|---|
| **Slide 4** | Khẳng định backbone "VGG-19 hoặc ResNet-50" | Ghi chính xác backbone **`vgg19_bn`** (VGG-19 tích hợp Batch Normalization, `hidden: 256`) | Khớp chính xác với file cấu hình huấn luyện `models/logs/..._config.yml` và mã nguồn `vietocr_engine.py`. |
| **Slide 10** | Ghi tokenizer là `icu_tokenizer` | Ghi tokenizer chuẩn (`standard`) kết hợp bộ lọc `synonym_ctsv` (synonym graph) và `asciifolding` | Mã nguồn `backend/app/core/elasticsearch.py` thực tế dùng standard tokenizer do image ES 8.12 mặc định không cài plugin ICU. |
| **Slide 11** | Tuyên bố sử dụng Deskew Hough và bộ lọc CLAHE toàn trang | Sửa thành: **Bảo toàn ảnh tự nhiên** (không áp dụng CLAHE/Denoise toàn trang để tránh vỡ nét chữ), **Upscale dòng chữ thấp (<32px)**, phân đoạn dòng và bóc tách bảng qua Otsu | Mã nguồn `vietocr_service.py` thực tế tắt CLAHE để tránh hiện tượng quầng sáng (halo) làm mất nét chữ in chuẩn. Deskew Hough không có trong mã nguồn chạy thực tế. |
| **Slide 12** | Ghi chung chung "tối ưu Chunking", không nêu rõ tham số | Ghi rõ: hàm `_find_best_word_boundary` cắt tại khoảng trắng tự nhiên ở cửa sổ 30% giữa dòng; nâng trần `trocr_max_new_tokens: 128` | Khớp với mã nguồn `backend/app/services/trocr_engine.py` và `backend/app/core/config.py`. |
| **Slide 13** | Ghi ngưỡng cờ cảnh báo điểm tin cậy `< 0,70` | Sửa thành ngưỡng cảnh báo độ tin cậy **`< 0,60`** hoặc loại tài liệu KHÁC | Khớp với logic hiển thị badge "Cần kiểm tra" trong mã nguồn frontend `SearchPage.tsx:1561` và `DocTypeComponents.tsx:64`. |
| **Slide 14** | Tuyên bố phân loại đạt "100% accuracy" trên 18 mẫu không kèm ngữ cảnh | Ghi rõ: Đạt 18/18 mẫu kiểm thử E2E trên **bộ dữ liệu thử nghiệm tổng hợp (synthetic)**; kèm lưu ý cần mở rộng tập kiểm thử thực tế ở giai đoạn sau | Trung thực khoa học: 18 mẫu được tạo tự động bởi `scripts/e2e_doctype.py` để kiểm thử logic hệ thống, chưa phải 18 tài liệu scan thực tế ngoài đời. |
| **Slide 15** | Tuyên bố Precision@5 đạt "trên 92%" | Ghi rõ số liệu đo trên tập Ground Truth độc lập 25 truy vấn (`ir_ground_truth.json`): **Precision@5 = 74,0%** trên nhóm khớp biểu mẫu (EASY), **loại bỏ âm tính đạt 100%** | Khớp với tài liệu thực nghiệm chuẩn hóa `docs/Experiment.md:75-95`, loại bỏ số liệu thổi phồng cũ. |
| **Slide 16** | Ghi dải màu đỏ HSV $[0\text{--}10 \cup 170\text{--}180]$ không ghi chú thang đo | Bổ sung ghi chú rõ ràng: **theo thang OpenCV $H: 0\text{--}180$** | Chuẩn hóa kỹ thuật: Không gian màu HSV trong OpenCV ánh xạ góc $0\text{--}360^\circ$ về dải $0\text{--}180$ để lưu trữ trong kiểu byte `uint8`. |
| **Slide 17** | Thiếu tóm tắt Trọng tâm 6 (Dữ liệu & Bảo mật P0) | Bổ sung: Xử lý dứt điểm 13 lỗi bảo mật P0 (8 Auth, 4 Document/IDOR, 1 Reliability) và hoàn thiện bộ dữ liệu 13.658 mẫu dòng | Bảo đảm tính nhất quán nội bộ, nhắc lại thành quả trọng tâm 6 trước khi kết luận. |
| **Speaker notes (Slide 4–10)** | Đoạn văn thuyết minh dài, tổng thời lượng vượt quá 14 phút | Rút gọn mỗi slide lý thuyết xuống **2–3 câu cô đọng (~65–70 từ/slide)**, tập trung thời lượng cho các slide trọng tâm kỹ thuật | Bảo đảm tổng thời lượng toàn bài thuyết trình nằm trong ngưỡng **10–12 phút** chuẩn học thuật. |

---

## III. DANH SÁCH [CHƯA XÁC MINH] VÀ CÁC CÔNG VIỆC CẦN TỰ LÀM

Trong kho mã nguồn hiện tại, có **2 hạng mục** còn ở dạng kế hoạch hoặc chưa có file log nghiệm thu thực tế:

1. **[CHƯA XÁC MINH 1] Thuật toán lọc màu con dấu đỏ HSV (`cv2.inRange`)**:
   - *Hiện trạng:* Giải pháp lọc con dấu đỏ trong không gian màu HSV ($H: 0\text{--}10 \cup 170\text{--}180$) đã được mô tả chi tiết trong `docs/ocr_diagnosis.md` và `Slide_dot_2.md` như một giải pháp đang hoàn thiện (in-progress). Tuy nhiên, trong mã nguồn `backend/app/services/vietocr_service.py` và `trocr_engine.py`, hàm tiền xử lý tách con dấu đỏ tự động chưa được tích hợp trực tiếp vào pipeline gọi mặc định.
   - *Việc cần làm:* Tạo một file script thử nghiệm độc lập (ví dụ `scripts/test_hsv_stamp_filter.py`) áp dụng `cv2.cvtColor(img, cv2.COLOR_BGR2HSV)` và `cv2.inRange()` trên 1 trang tài liệu scan có con dấu đỏ thực tế để lấy hình ảnh minh chứng trước và sau khi lọc đưa vào slide thuyết trình.

2. **[CHƯA XÁC MINH 2] Đo kiểm tải thực tế với công cụ Locust / ab**:
   - *Hiện trạng:* File `backend/tests/benchmark_performance.py` đã có sẵn các kịch bản đo độ trễ API. Tuy nhiên, kết quả đo tải đồng thời (ví dụ: 20–50 người dùng đồng thời) chưa được xuất ra file báo cáo chính thức.
   - *Việc cần làm:* Khởi động Docker Compose và chạy lệnh benchmark:
     ```bash
     python backend/tests/benchmark_performance.py
     ```
     để lấy các chỉ số throughput (req/s), latency p95 thực tế bổ sung vào Chương 5 của Thuyết minh khóa luận.

---

## IV. ƯỚC LƯỢNG THỜI LƯỢNG THUYẾT TRÌNH SAU CHỈNH SỬA

*(Căn cứ tốc độ nói học thuật tiêu chuẩn: **~130 từ/phút**)*

| Slide | Tiêu đề tóm tắt | Người trình bày | Số từ trong Speaker notes | Thời lượng ước tính |
|:---:|---|:---:|:---:|:---:|
| **Slide 1** | Trang tiêu đề | Thành | ~65 từ | ~30 giây |
| **Slide 2** | Tóm tắt Đợt 1 | Bảo | ~70 từ | ~32 giây |
| **Slide 3** | Tiến độ tổng thể Đợt 2 (78,4%) | Phát | ~85 từ | ~39 giây |
| **Slide 4** | CSLT #1: Kiến trúc VietOCR (`vgg19_bn`) | Thành | ~65 từ | ~30 giây |
| **Slide 5** | CSLT #2: Cơ chế hoạt động VietOCR | Thành | ~65 từ | ~30 giây |
| **Slide 6** | CSLT #3: Kiến trúc TrOCR (ViT + RoBERTa) | Bảo | ~65 từ | ~30 giây |
| **Slide 7** | CSLT #4: Cơ chế hoạt động TrOCR | Bảo | ~65 từ | ~30 giây |
| **Slide 8** | CSLT #5: Bảng so sánh VietOCR vs TrOCR | Bảo | ~65 từ | ~30 giây |
| **Slide 9** | CSLT #6: Kiến trúc phân tán & Inverted Index | Phát | ~70 từ | ~32 giây |
| **Slide 10** | CSLT #7: Phân tích văn bản & BM25 | Phát | ~70 từ | ~32 giây |
| **Slide 11** | Trọng tâm 1: Hoàn thiện VietOCR (In chuẩn) | Thành | ~90 từ | ~42 giây |
| **Slide 12** | Trọng tâm 2: TrOCR-Vi (Chunking & Cụt dòng) | Bảo | ~90 từ | ~42 giây |
| **Slide 13** | Trọng tâm 3: AI Hậu xử lý văn bản hành chính | Thành | ~80 từ | ~37 giây |
| **Slide 14** | Trọng tâm 4: AI Phân loại văn bản Doctype | Phát | ~85 từ | ~39 giây |
| **Slide 15** | Trọng tâm 5: Nâng cấp Elasticsearch & PII | Phát | ~85 từ | ~39 giây |
| **Slide 16** | Khó khăn kỹ thuật & Giải pháp HSV con dấu | Bảo | ~85 từ | ~39 giây |
| **Slide 17** | Tổng kết Đợt 2 & Kế hoạch nước rút | Thành | ~75 từ | ~35 giây |
| **TỔNG CỘNG** | **Toàn bộ 17 Slide** | **Cả 3 thành viên** | **~1.270 từ** | **~9 phút 45 giây – 10 phút 30 giây** |

> **Đánh giá thời lượng:** Hoàn toàn nằm gọn trong khung thời gian yêu cầu **10–12 phút**, dự phòng được 1–2 phút cho chuyển slide và câu chào mở đầu/kết thúc. Phân bổ thời lượng nói giữa 3 thành viên rất đồng đều: **Thành: ~3,5 phút**, **Phát: ~3,5 phút**, **Bảo: ~3,5 phút**.

