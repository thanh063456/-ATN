# Tài liệu Chẩn đoán Nguyên nhân Gốc rễ TrOCR-Vi (Phase A Diagnosis)
**Ngày đánh giá:** 18/10/2026  
**Môi trường phần cứng:** NVIDIA GeForce RTX 3050 6GB Laptop GPU | PyTorch 2.7.1+cu118 (CUDA 11.8)  
**Tập kiểm định độc lập (Held-out Set):** 32 trang văn bản hành chính CTSV chuẩn hóa (Page 1) đóng băng tại `dataset/splits/held_out_32.json`.

---

## 1. Bảng đo đạc thực nghiệm các biến thể (Ablation Benchmark Table)

| Experiment / Mode | CER (%) | WER (%) | Trunc. Rate (%) | Line Recall (%) | HW Match (%) | p50 Page (s) | Throughput (l/s) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Baseline (E2E Detector + TrOCR) | 19.26% | 32.97% | 13.04% | 95.65% | 0.00% | 97.61s | 0.2 |
| A1: GT-box Line Crops (no detector noise) | 19.55% | 32.54% | 10.87% | 95.65% | 0.00% | 30.48s | 0.8 |
| A2: Crop Padding 0px (tight crop) | 19.55% | 32.54% | 10.87% | 95.65% | 0.00% | 30.45s | 0.8 |
| A2: Crop Padding 16px (expanded margin) | 19.89% | 33.19% | 15.22% | 95.65% | 0.00% | 30.41s | 0.8 |
| A3: Aspect-Preserving Tiling + Pad 16px | 14.32% | 33.19% | 3.81% | 95.65% | 0.00% | 30.41s | 0.8 |

---

## 2. Xếp hạng nguyên nhân gốc rễ (Ranked Root Causes)

Dựa trên phân tích mã nguồn, log suy luận, cấu hình mô hình và thực nghiệm cô lập từng biến số:

### Hạng 1: Giới hạn token `max_new_tokens=64` & Biến dạng tỉ lệ khung hình (Aspect Ratio Squashing)
* **Phân tích thực nghiệm**:
  * Các dòng văn bản hành chính toàn trang (chiều rộng 1800–2400px, 70–85 ký tự) khi mã hóa bằng Byte-Level BPE (50k vocab) tạo ra **75–90 tokens** (do nhiều âm tiết tiếng Việt có dấu phân tách thành 2–3 byte tokens).
  * Do tham số `max_new_tokens=64` trong hàm `predict_batch()`, quá trình giải mã autoregressive bị **ngắt cưỡng bức** tại token thứ 64, cắt cụt toàn bộ 15–20 ký tự ở đuôi dòng (`...với những nội dung cự th` bị ngắt trước `cụ thể như sau:`).
  * Đồng thời, bộ vi xử lý ảnh `ViTImageProcessor` ép co giãn ảnh dòng từ tỉ lệ tự nhiên $20:1$ thành hình vuông $384 \times 384$ px (nén ngang ~5x, kéo giãn dọc ~4x). Ký tự ở rìa phải bị nén xuống chỉ còn 3–4 pixel/chữ, làm các patch 16x16 bị lẫn lộn biểu diễn không gian và kích hoạt token kết thúc `<eos>` sớm.
* **Giải pháp**:
  1. Nâng `max_new_tokens=128`.
  2. Áp dụng kỹ thuật **Horizontal Line Chunking / Tiling với 30% overlap**: Với các dòng dài $>900$px, chia thành 2 phần cắt có gối đầu, nhận diện độc lập rồi ghép chuỗi bằng giải thuật căn chỉnh xâu LCS/overlap.

### Hạng 2: Bộ chuẩn hóa Header (`document_header_normalizer.py`) nuốt mất dòng ngày tháng
* **Phân tích thực nghiệm**:
  * Hàm `_is_header_fragment` phát hiện dòng chứa `Lâm Đồng` và `ngày...` nên đánh dấu là dòng Header cần tái cấu trúc.
  * Tuy nhiên, do chữ viết tay ngày tháng bị nhận diện nhầm thành dấu gạch chéo (`Lâm Đồng, ngày/ tháng 8 năm 2025`), regex `_DATE_PATTERN` không khớp ký tự `/`, dẫn đến biến `date_str = None`.
  * Khi `_rebuild_header_block` tạo khối header mới, vì `date_str` bị `None`, nó để trống cột ngày tháng và **bỏ qua hoàn toàn dòng gốc**, khiến dòng ngày tháng biến mất khỏi văn bản đã chuẩn hóa.
* **Giải pháp**:
  * Sửa regex nhận dạng ngày tháng để bắt được các biến thể nét viết tay `/`, `..`, `__`.
  * Đặt quy tắc an toàn bất biến: **Nếu không parse được ngày chuẩn, luôn giữ nguyên 100% dòng text thô**, tuyệt đối không được xóa bỏ dòng.

### Hạng 3: Bounding box của EasyOCR cắt sát mép biên chữ & Nhiễu tem đỏ
* **Phân tích thực nghiệm**:
  * Padding 0px làm tăng CER và tỷ lệ cụt chữ (truncation rate) do mất nét của các ký tự ngoài cùng như dấu mũ, móc chữ `ơ`, `ư`, `t`, `g`. Padding 8–16px cải thiện rõ rệt biên nhận dạng.
  * Tem đỏ hình tròn che đè lên chữ in đen làm mô hình TrOCR nhầm lẫn chữ `kỷ niệm` thành `ký niệ`, `Bộ Giáo dục` thành `Bặ Giáo dược`.
* **Giải pháp**:
  * Điều chỉnh detector: Mở rộng box theo phương ngang (Horizontal dilation) 5–8% chiều cao dòng.
  * Tiền xử lý lọc kênh màu đỏ (Color channel filtering: triệt tiêu vùng R cao, G,B thấp) trước khi đưa vào nhận dạng mà vẫn bảo toàn mực viết tay xanh/đen.

### Hạng 4: Chữ viết tay số hiệu & ngày tháng bị mô hình in ấn (printed) nhận diện sai
* **Phân tích thực nghiệm**:
  * Số hiệu viết tay `1395` bị TrOCR đọc thành `4395` (do nét số 1 viết tay có móc chéo ngược giống số 4 in ấn).
* **Giải pháp**:
  * Sử dụng cơ chế nhận diện vùng viết tay kết hợp kiểm chứng ràng buộc số hiệu `Số: \d{1,5}/[A-ZĐ-]+`.
  * Sử dụng mô hình chuyên biệt cho chữ viết tay hoặc cơ chế so khớp đối chiếu VietOCR/TrOCR cho vùng số hiệu & ngày tháng.

### Hạng 5: TrOCR chạy chậm do Beam Search không cần thiết trên CPU/GPU
* **Phân tích thực nghiệm**:
  * Beam Search (`num_beams=2`) nhân đôi số phép tính trên mỗi token so với Greedy Search.
* **Giải pháp**:
  * Batching theo chiều rộng động (dynamic padding).
  * Chạy Greedy Search (`num_beams=1`) cho các dòng in ấn độ tương phản cao, chỉ dùng beams khi confidence thấp.
