# BẢNG TỔNG HỢP LỊCH SỬ HIỆU ĐÍNH BÁO CÁO TIẾN ĐỘ LẦN 2 (CHANGELOG V2)

**Dự án**: Hệ thống số hóa và quản lý tài liệu Công tác sinh viên ứng dụng OCR và Elasticsearch (DocuCTSV)  
**Tài liệu gốc**: `docs/bao_cao_tien_do_lan_2.md` / `bao_cao_tien_do_lan_2.docx`  
**Tài liệu hiệu đính v2**: `docs/bao_cao_tien_do_lan_2_v2.md` / `bao_cao_tien_do_lan_2_v2.docx`  
**Ngày thực hiện hiệu đính**: 31/10/2026  
**Đơn vị đào tạo**: Trường Đại học Đà Lạt – Khoa Công nghệ Thông tin  
**Lớp**: CTK46-PM  
**Giảng viên hướng dẫn**: ThS. Nguyễn Trọng Hiếu  
**Nhóm sinh viên thực hiện**: Ngô Công Thành (2212461), Phan Thành Phát (2212436), Lý Gia Bảo (2213934)

---

## 1. BẢNG CHI TIẾT CÁC ĐIỂM HIỆU ĐÍNH (CHANGELOG TABLE)

| Mục trong báo cáo | Nội dung cũ (Bản v1) | Nội dung mới hiệu đính (Bản v2) | Lý do hiệu đính | Nguồn bằng chứng kỹ thuật |
|---|---|---|---|---|
| **Mục 0: Thông tin chung & Phần cứng** | Ghi lẫn lộn GPU RTX 3050 Laptop và RTX 3060; chưa phân định rõ môi trường đo đạc. | Phân định rõ ràng: Thực nghiệm baseline & ablation đo đạc trên **NVIDIA GeForce RTX 3050 6GB Laptop GPU (CUDA 11.8)**; môi trường máy trạm thử nghiệm nội bộ trang bị 12GB RAM, GPU NVIDIA GeForce RTX 3060. | Thống nhất dữ liệu phần cứng trung thực, tránh mâu thuẫn giữa log thử nghiệm và máy trạm demo. | `docs/ocr_diagnosis.md` dòng 3; commit `18f6ab7`. |
| **Mục 1 & Mục 2: Tiến độ tổng thể (Arithmetic)** | Báo cáo nêu tiến độ tổng thể đạt 87,0%, nhưng tổng trọng số trong Bảng 2.2 thực tế cộng lại thành 92,5% (lệch số học). | Tính toán lại chính xác: Điều chỉnh trọng số Phase 12 (viết khóa luận & bảo vệ) từ 5,0% lên 15,0% (do khối lượng toàn văn 6 chương và chuẩn bị bảo vệ chiếm tỷ trọng lớn trong đồ án tốt nghiệp); tiến độ tổng thể đạt đúng **78,35%** (khớp chính xác giữa Mục 1, Mục 2 và Bảng 2.2). | Sửa lỗi sai lệch số học giữa bảng trọng số và số liệu công bố; phản ánh đúng tiến độ thực tế trước khi bảo vệ. | `.ai/ROADMAP.md`; công thức tính trọng số có kiểm chứng script Python. |
| **Bảng 2.1: Đối chiếu kế hoạch tuần** | Tuần 1 ghi 90% (dù Chương 3 chưa xong); Tuần 3 ghi 95% (dù chưa thử nghiệm đủ 100+ mẫu đơn và chưa kiểm thử tải). | Tuần 1 điều chỉnh về **75%** (hoàn thành Chương 1, 2 và dàn ý chi tiết); Tuần 3 điều chỉnh về **70%** (hoàn thành 32 trang held-out, ghi nhận chưa kiểm thử tải Locust 20 người dùng). | Đánh giá trung thực kết quả thực tế so với cam kết kế hoạch tại Báo cáo Lần 1. | `Bao cao.md` Mục 7; `.ai/ROADMAP.md` Phase 10. |
| **Bảng 2.2: Trọng số & Tỷ lệ Phase** | Phase 2 (Dataset) ghi 100% dù chữ viết tay còn thiếu; Phase 10 (Testing) ghi 85% dù chưa test tải; Phase 12 trọng số chỉ 5%. | Tái cơ cấu: Phase 2 điều chỉnh 85% (10% trọng số); Phase 10 điều chỉnh 60% (5% trọng số); Phase 12 nâng lên 15% trọng số (hoàn thành 35%). Tổng trọng số đúng 100,0%, tổng tiến độ đúng **78,35%**. | Đảm bảo tính nhất quán giữa tiến độ các phase với các vấn đề tồn tại nêu tại Mục 5. | `.ai/ROADMAP.md`; `docs/ocr_diagnosis.md`. |
| **Mục 3.1: Dữ liệu ký tự** | Ghi "145 ký tự hiếm". | Đổi thành: "**145 ký tự duy nhất** trong bảng mã tiếng Việt chuẩn Unicode NFC". | Trong bảng mã tiếng Việt chỉ có tổng cộng 145 ký tự duy nhất (bao gồm nguyên âm có dấu, phụ âm, số và dấu câu), không phải có 145 ký tự hiếm. | `docs/trocr_data_inventory.md` dòng 7. |
| **Mục 3.1: Kiểm tra rò rỉ dữ liệu** | Chưa chứng minh tính độc lập giữa tập huấn luyện và tập kiểm định. | Bổ sung kiểm chứng khoa học: Xác nhận 32 tài liệu trong `dataset/splits/held_out_32.json` hoàn toàn **không trùng lặp (0 overlap)** với 32 tài liệu trong `dataset/splits/split_v2.json`. Bổ sung nhận định hạn chế: Tập test của `split_v2` chỉ gồm 4 tài liệu (244 dòng) nên độ bao phủ còn hạn chế. | Đảm bảo nguyên tắc chống rò rỉ dữ liệu (data leakage) trong học máy. | `dataset/splits/split_v2.json`; `dataset/splits/held_out_32.json`. |
| **Mục 3.2: Kiến trúc Decoder TrOCR-Vi** | Ghi `decoder: "vinai/phobert-base-v2"` (Byte-Level BPE, 50.000 vocab). | Sửa lại đúng kiến trúc trong mã nguồn: Khối Decoder Transformer sử dụng từ vựng RoBERTa Byte-Level BPE chuẩn gồm **50.265 tokens** (`microsoft/trocr-base-printed`). | PhoBERT sử dụng từ vựng SentencePiece BPE 64.000 tokens, trong khi mã nguồn `train_trocr_vi.py` nạp `RobertaTokenizer` từ `microsoft/trocr-base-printed` (50.265 tokens). | `training/trocr_vi/train_trocr_vi.py` dòng 214-216. |
| **Mục 3.2: Ví dụ lỗi cụt đuôi dòng** | Dùng ví dụ "BỘ GIÁO DỤC VÀ ĐÀO TẠO" (chỉ 23 ký tự, không thể chạm ngưỡng ngắt 64 tokens). | Thay bằng dòng dài thực tế: `"Căn cứ Kế hoạch số 1153/KH-BGDĐT ngày 05/8/2025 của Bộ Giáo dục và Đào tạo..."` (82 ký tự, sinh ra 85 tokens BPE, bị ngắt cưỡng bức ở token thứ 64). | Ví dụ minh họa phải có độ dài token vượt qua ngưỡng `max_new_tokens=64` mới gây ra lỗi cụt dòng. | `docs/ocr_diagnosis.md` Mục 2 Hạng 1. |
| **Mục 3.2: Quyết định bộ máy OCR mặc định** | Chưa làm rõ engine nào là mặc định khi đưa vào vận hành hệ thống. | Bổ sung tiểu mục 3.2.C: Xác định **VietOCR là engine mặc định** cho văn bản in (CER 2,80%, độ trễ ~0,08s/dòng); **TrOCR-Vi là engine chuyên biệt** cho dòng phức tạp/viết tay hoặc đối soát đa engine. | Làm rõ kiến trúc điều phối nghiệp vụ và lý do kỹ thuật đằng sau việc lựa chọn mô hình. | `backend/app/core/config.py`; `docs/ocr_benchmark.md`. |
| **Mục 3.3: Bảo vệ dữ liệu cá nhân PII** | Dùng chuỗi số `068******891` trông giống tiền tố CCCD thật của tỉnh Lâm Đồng (068). | Thay thế bằng định dạng giả lập an toàn: `0xxxxxxxxx91`. | Tránh rủi ro lộ lọt cấu trúc số định danh cá nhân thật của sinh viên theo Nghị định 13/2023/NĐ-CP. | Nghị định 13/2023/NĐ-CP. |
| **Bảng 4.1: Tính toàn vẹn số liệu thực nghiệm** | Gộp chung VietOCR và TrOCR-Vi vào cùng 1 bảng; ghi nhận CER TrOCR "giảm mạnh"; tỷ lệ cụt dòng ghi lẫn lộn giữa 0,53% và 0,00%; tốc độ ghi chung chung 3,5x. | **Tách thành 2 bảng riêng biệt**: (1) Bảng 4.1a đánh giá TrOCR-Vi trên 32 trang held-out; (2) Bảng 4.1b đánh giá VietOCR trên 244 dòng test in chuẩn. Báo cáo trung thực: CER văn bản hỗn hợp (20,58%) và WER (34,82%) **chưa cải thiện** so với baseline ban đầu (19,26% và 32,97%); Line recall đạt 95,0% (chưa đạt mục tiêu ≥99%). Nêu rõ: Truncation rate đạt 0,53% với Chunking; tốc độ tăng 2,8x (ở P50 = 35,22s) và 3,5x (ở P50 = 27,90s). | Minh bạch học thuật: Không gộp dữ liệu từ các tập kiểm định khác nhau; thừa nhận các chỉ số chưa đạt. | `docs/ocr_diagnosis.md`; `dataset/splits/eval_results.json`. |
| **Mục 4.1: Đánh giá chữ viết tay** | Ghi "100% độ chính xác viết tay với routing". | Ghi nhận chính xác theo số mẫu $n$: Trên tập con đánh giá ($n=2$ trường), ngày tháng đạt 1/1 (100%), số hiệu đạt 0/1 (0% do nhầm nét số 1 thành 4), tính trung bình đạt **50,00% (1/2)**. Làm rõ regex chỉ kiểm tra định dạng cấu trúc, không sửa được giá trị ký tự. | Tránh ngộ nhận về độ chính xác chữ viết tay khi kích thước mẫu đánh giá thực tế còn nhỏ. | `dataset/splits/eval_results.json` run 1, 2, 3; `scripts/eval_ocr.py`. |
| **Mục 4.3: Nhãn tập dữ liệu IR Benchmark** | Ghi "25 truy vấn chuẩn quốc tế". | Sửa thành: "bộ dữ liệu **25 truy vấn thực tế tự xây dựng** (`dataset/ir_ground_truth.json`) gồm 10 Easy, 10 Hard và 5 Negative". Nêu rõ Negative Rejection Rate đạt **5/5 (100,0%)**. | Báo cáo chính xác xuất xứ của tập dữ liệu kiểm thử truy hồi thông tin. | `dataset/ir_ground_truth.json`. |
| **Mục 4.3 & 3.3: Phạm vi kiểm thử tự động** | Khẳng định hệ thống đạt 38/38 tests hoàn hảo. | Nêu rõ: 38/38 tests chỉ bao phủ riêng phân hệ tìm kiếm tại `backend/tests/test_search.py`. Nêu tách bạch kiểm thử E2E phân loại văn bản (18/18 tests trong `scripts/e2e_doctype.py`) và kiểm thử Frontend Vitest. | Minh bạch phạm vi độ phủ kiểm thử của từng phân hệ. | `backend/tests/test_search.py`; `docs/doctype_e2e_report.md`. |
| **Mục 5: Vấn đề tồn tại** | Tuyên bố đã khắc phục triệt để mọi lỗi OCR. | Bổ sung thêm 2 vấn đề mở quan trọng: (1) **Tỷ lệ bắt dòng Line Recall (~95,0%) chưa đạt mục tiêu đề ra (≥99%)** do EasyOCR detector bỏ sót dòng nhỏ; (2) **Chưa thực hiện kiểm thử chịu tải (Locust) với 20 người dùng đồng thời**. | Tinh thần phản biện khoa học, chỉ rõ hạn chế để tiếp tục hoàn thiện trong Phase 10. | `docs/ocr_diagnosis.md` dòng 12; `.ai/ROADMAP.md` Phase 10. |
| **Bảng 6.1: Kế hoạch & Rủi ro tháng 11** | Thiếu đánh giá rủi ro pháp lý về dữ liệu cá nhân khi thử nghiệm thực tế. | Bổ sung rủi ro: Vi phạm an toàn dữ liệu cá nhân khi nạp hồ sơ sinh viên thực tế; Phương án: Ký thỏa thuận bảo mật và làm mờ 100% dữ liệu (anonymization consent) trước khi test tại Phòng CTSV. | Đảm bảo tuân thủ chặt chẽ hành lang pháp lý Nghị định 13/2023/NĐ-CP. | Nghị định 13/2023/NĐ-CP. |
| **Mục 7: Câu hỏi xin ý kiến GVHD** | Các câu hỏi mang tính thủ tục hành chính (xin giấy giới thiệu, lịch nộp bài). | Thay bằng **4 câu hỏi học thuật và kỹ thuật thực chất**: Ngưỡng CER chấp nhận cho chữ viết tay, lựa chọn engine mặc định, giải pháp nâng Line Recall lên ≥98%, thủ tục ẩn danh dữ liệu thực tế. | Nâng cao chất lượng buổi trao đổi học thuật với giảng viên hướng dẫn. | Yêu cầu nghiệp vụ đồ án tốt nghiệp. |
| **Phụ lục A: Cấu hình TrOCR-Vi** | Có dòng comment không hợp lệ cú pháp YAML (`decoder: ... (Byte-Level BPE...)`). | Chuẩn hóa cú pháp YAML hợp lệ, định dạng khối code block đơn cách. | Đảm bảo chuẩn cú pháp định dạng kỹ thuật. | `training/trocr_vi/train_trocr_vi.py`. |
| **Phụ lục B: Danh sách Commit Git** | Thiếu mốc thời gian ngày thực hiện commit; tác giả ghi chưa khớp phân công. | Bổ sung đầy đủ **ngày tháng thực hiện** trích xuất từ `git log` cho 8 commit tiêu biểu trong giai đoạn từ 22/09 đến 30/10/2026. | Minh chứng tiến độ thực tế theo dòng thời gian chuẩn xác của Git. | `git log --since="2026-09-22"`. |
| **Văn phong & Trực quan hóa** | Sử dụng nhiều từ ngữ quảng bá ("triệt để", "kỷ lục", "đột phá", "siêu chính xác", icon emoji 🟢🟡, sơ đồ ASCII). | Lược bỏ toàn bộ từ ngữ chủ quan; loại bỏ emoji trong bảng biểu; **chuyển đổi toàn bộ sơ đồ ASCII sang hình ảnh đồ họa học thuật** (Hình 3.1, Hình 3.2, Hình 4.1, Hình 4.2). | Tuân thủ văn phong học thuật khách quan, chuẩn mực của báo cáo khóa luận tốt nghiệp. | Quy chuẩn viết báo cáo khoa học. |

---

## 2. BẢNG KIỂM CÁC HẠNG MỤC CẦN BỔ SUNG & TRẠNG THÁI XÁC MINH

| STT | Hạng mục thông tin | Tình trạng trong Bản v2 | Ghi chú giải trình |
|:---:|---|:---:|---|
| 1 | Lớp sinh hoạt chuyên ngành | **CTK46-PM** (Đã điền) | Khóa 46 ngành Kỹ thuật Phần mềm, Khoa CNTT - ĐH Đà Lạt. |
| 2 | Họ tên & MSSV 3 sinh viên | **Ngô Công Thành (2212461), Phan Thành Phát (2212436), Lý Gia Bảo (2213934)** (Đã điền) | Khớp chính xác với danh sách sinh viên do nhóm cung cấp. |
| 3 | Giảng viên hướng dẫn | **ThS. Nguyễn Trọng Hiếu** (Đã điền) | Giảng viên Bộ môn Công nghệ Phần mềm, Khoa CNTT. |
| 4 | Môi trường phần cứng đo đạc | **NVIDIA GeForce RTX 3050 6GB Laptop GPU (CUDA 11.8)** (Đã chuẩn hóa) | Dùng làm căn cứ đo đạc các mốc thời gian P50 (97,61s -> 27,90s - 35,22s). Máy trạm nội bộ trang bị GPU RTX 3060. |
| 5 | Số hiệu quyết định giao đề tài | *Đã lược bỏ* | Không bắt buộc trong Báo cáo tiến độ lần 2, sẽ cập nhật vào trang bìa toàn văn Khóa luận. |
| 6 | Hạn chót nộp khóa luận đợt 1 | *Đã lược bỏ* | Trao đổi trực tiếp trong buổi họp với GVHD. |

---

## 3. DANH SÁCH 5 CÂU HỎI TRỌNG TÂM KHI BÁO CÁO VỚI GIẢNG VIÊN HƯỚNG DẪN

Khi báo cáo tiến độ lần 2 với Giảng viên hướng dẫn (ThS. Nguyễn Trọng Hiếu), nhóm sinh viên cần nắm vững các luận điểm kỹ thuật sau để giải trình:

### Câu 1: Tại sao tỷ lệ lỗi ký tự (CER) của TrOCR-Vi trên văn bản hỗn hợp (20,58%) lại cao hơn rất nhiều so với VietOCR (2,80%)?
- **Trả lời**:
  - *Sự khác biệt về tập dữ liệu đánh giá*: VietOCR được đo đạc trên tập kiểm định chữ in chuẩn (`test.tsv` - 244 dòng văn bản in hành chính độ tương phản cao), nơi mô hình VGG-Transformer thể hiện ưu thế vượt trội (~0,08s/dòng, CER 2,80%).
  - Trong khi đó, TrOCR-Vi được đưa vào thử thách trên **tập kiểm định độc lập 32 trang văn bản thực tế** (`held_out_32.json`) có độ phức tạp rất cao: chứa các dòng chữ viết tay tự do điền thêm vào chỗ trống, nét mực xanh mờ, dấu mộc đỏ đóng đè lên chữ và độ nghiêng ảnh thực địa.
  - Bộ giải mã RoBERTa của TrOCR-Vi khi gặp nét chữ viết tay chưa có trong tập train dễ sinh ra hiện tượng hallucination (lặp từ hoặc đoán sai ký tự). Đây là lý do nhóm quyết định giữ VietOCR làm engine mặc định cho chữ in và tiếp tục fine-tune TrOCR-Vi trong Phase 3.

---

### Câu 2: Bản chất kỹ thuật của hiện tượng cụt đuôi dòng (Truncation) trên mô hình TrOCR là gì và giải thuật Horizontal Chunking giải quyết bài toán này ra sao?
- **Trả lời**:
  - *Nguyên nhân 1 - Giới hạn giải mã*: Dòng văn bản hành chính dài (70–85 ký tự) khi mã hóa bằng Byte-Level BPE sinh ra 75–90 tokens (do nguyên âm tiếng Việt có dấu phân tách thành 2–3 byte tokens). Tham số mặc định `max_new_tokens=64` ngắt cưỡng bức quá trình sinh chuỗi ở token thứ 64, làm mất trắng 15–20 ký tự ở đuôi dòng.
  - *Nguyên nhân 2 - Méo tỷ lệ khung hình*: `ViTImageProcessor` co nén ảnh dòng từ tỷ lệ 20:1 thành hình vuông 384 × 384 px, nén các ký tự ngoài cùng bên phải xuống chỉ còn 3–4 pixel/chữ, làm các patch 16×16 bị lẫn lộn biểu diễn không gian và kích hoạt token kết thúc `</s>` sớm.
  - *Giải pháp*: Nhóm nâng `max_new_tokens=128`, đồng thời xây dựng thuật toán **Horizontal Line Chunking (Tiling)** gối đầu 30%: Hàm `_find_best_word_boundary()` tìm khe khoảng trắng tự nhiên giữa các từ để chia đôi ảnh dòng dài (>900 px), nhận dạng độc lập và ghép nối chuỗi bằng giải thuật LCS. Nhờ đó, tỷ lệ cụt dòng giảm từ **13,04% xuống 0,53%**.

---

### Câu 3: Tỷ lệ bắt dòng chữ (Line Recall) hiện tại đạt 95,0%, chưa đạt mục tiêu đề ra (≥99%). Nguyên nhân do đâu và nhóm có kế hoạch xử lý như thế nào?
- **Trả lời**:
  - *Nguyên nhân*: Bộ phát hiện dòng chữ EasyOCR detector sử dụng thuật toán CRAFT. Đối với các trang tài liệu scan ở độ phân giải thấp (150–200 DPI), các dòng in chữ rất nhỏ ở phần chân trang (ghi chú số trang, nơi nhận) hoặc các dòng chữ viết tay nét bút bi quá mảnh thường có điểm tin cậy heatmap thấp hơn ngưỡng phát hiện, dẫn đến bị bỏ sót khoảng 4,5% số dòng.
  - *Kế hoạch xử lý trong tháng 11*:
    1. Tăng độ phân giải render PDF lên chuẩn 300 DPI khi xử lý văn bản scan.
    2. Áp dụng kỹ thuật mở rộng hộp bao (Horizontal Dilation) kết hợp thuật toán phân tích thành phần liên thông (Connected Component Analysis) để gom các cụm chữ nhỏ bị đứt nét.
    3. Thiết lập cơ chế cảnh báo Human-in-the-Loop trên giao diện Side-by-Side để chuyên viên phát hiện và bổ sung bounding box thủ công nếu cần.

---

### Câu 4: Việc phân luồng hồ sơ tự động bằng Elasticsearch Percolator mang lại lợi ích cụ thể gì so với việc viết các hàm `if/else` trong mã nguồn Python?
- **Trả lời**:
  - *Nguyên lý Reverse Search*: Percolator đảo ngược quy trình tìm kiếm: Đăng ký trước 7 bộ luật chính sách (Nghị định 81/2021, Quyết định 1121, Quyết định 688) vào chỉ mục. Khi có văn bản OCR mới, Elasticsearch tự động đối soát xem văn bản đó khớp với những luật nào trong bộ nhớ chỉ mất < 10 ms.
  - *Lợi ích thực tiễn*:
    1. **Tách biệt nghiệp vụ khỏi mã nguồn**: Khi nhà trường cập nhật chính sách học bổng mới, chuyên viên chỉ cần thêm một tài liệu query vào chỉ mục `percolator_policies` qua Swagger UI mà không cần can thiệp vào code Python backend và không cần restart hệ thống.
    2. **Khớp từ khóa linh hoạt**: Percolator tận dụng toàn bộ sức mạnh của Custom Vietnamese Analyzer (ICU tokenizer, từ đồng nghĩa, tìm kiếm mờ), giúp khớp chính xác ngay cả khi văn bản OCR bị sai chính tả nhẹ.

---

### Câu 5: Hệ thống đảm bảo an toàn thông tin sinh viên như thế nào khi triển khai thử nghiệm thực tế tại Phòng Công tác Sinh viên?
- **Trả lời**:
  - *Kiểm soát rủi ro tuân thủ Nghị định 13/2023/NĐ-CP*:
    1. **Làm mờ thông tin cá nhân (PII Masking)**: Hệ thống tự động nhận diện regex và che mờ các trường nhạy cảm (số CCCD `0xxxxxxxxx91`, số điện thoại, email) trên giao diện tìm kiếm đối với người dùng không phải Cán bộ quản lý (`STAFF`/`ADMIN`).
    2. **Môi trường cục bộ On-Premise**: Hệ thống được đóng gói hoàn chỉnh bằng Docker Compose, chạy offline nội bộ tại phòng máy của Trường Đại học Đà Lạt, tuyệt đối không gửi dữ liệu hồ sơ sinh viên lên bất kỳ dịch vụ đám mây bên thứ ba nào.
    3. **Thủ tục ẩn danh hóa**: Trước khi chạy thử nghiệm trên dữ liệu hồ sơ thực tế của kỳ học này, nhóm sẽ xin ý kiến GVHD và phối hợp với Phòng CTSV thực hiện quy trình ký thỏa thuận bảo vệ dữ liệu và làm mờ thông tin định danh sinh viên.

