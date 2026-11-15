# TÀI LIỆU HỒ SƠ THÔNG TIN & CHUẨN BỊ BÁO CÁO TIẾN ĐỘ LẦN 2

**Dự án**: Hệ thống số hóa và quản lý tài liệu Công tác sinh viên ứng dụng OCR và Elasticsearch (DocuCTSV)  
**Đơn vị đào tạo**: Trường Đại học Đà Lạt – Khoa Công nghệ Thông tin  
**Lớp**: CTK46-PM  
**Giảng viên hướng dẫn**: ThS. Nguyễn Trọng Hiếu  
**Nhóm sinh viên thực hiện & Phân công nhiệm vụ**:
1. **Ngô Công Thành** – MSSV: 2212461 *(Trưởng nhóm)*: Phụ trách **VietOCR & OCR Pipeline tổng thể** (Thị giác máy tính OpenCV, Tiền xử lý Deskew/khử chấm/lọc dấu đỏ, Cắt dòng, Huấn luyện VietOCR Transformer, Bóc tách cấu trúc Bảng biểu Markdown, Hậu xử lý Unicode NFC & từ điển hành chính).
2. **Phan Thành Phát** – MSSV: 2212436: Phụ trách **Elasticsearch 8.x & Backend CSDL** (Custom Vietnamese Analyzer, Hybrid Search RRF, Phân luồng hồ sơ tự động Percolator, Che mờ PII Masking NĐ 13/2023, Student 360, Geo-Distance NĐ 81, CSDL PostgreSQL 3NF & FastAPI RESTful API).
3. **Lý Gia Bảo** – MSSV: 2213934: Phụ trách **TrOCR-Vi & Frontend Web SPA** (Huấn luyện Vision Transformer TrOCR-Vi, Chẩn đoán lỗi cụt dòng & Thuật toán Horizontal Chunking gối đầu 30%, Tối ưu hóa suy luận FP16 trên GPU RTX 3060, Web SPA React 18 De-AI UI, Side-by-Side Live Editor & Docker Compose).

---

## PHẦN 1: BẢNG MA TRẬN PHÂN CÔNG & TÌNH TRẠNG HỒ SƠ (ĐÃ HOÀN TẤT 100%)

Toàn bộ thông tin phân công chuyên trách và thông số thực tế đã được chuẩn hóa và đồng bộ vào Báo cáo tiến độ lần 2 (`docs/bao_cao_tien_do_lan_2.md` và `docs/bao_cao_tien_do_lan_2.docx`):

| STT | Thành viên phụ trách | Phân hệ chuyên môn đảm nhiệm | Hạng mục công việc kỹ thuật cốt lõi | Trạng thái |
|:---:|---|---|---|:---:|
| 1 | **Ngô Công Thành**<br>*(MSSV: 2212461 - Trưởng nhóm)* | **VietOCR & Image Preprocessing Pipeline** | • Tiền xử lý Deskew, khử đường chấm form `...........`, lọc tem đỏ.<br>• Phân đoạn dòng (Line Segmentation) & loại bỏ dòng rác.<br>• Huấn luyện mô hình VietOCR Transformer (`vgg_transformer`).<br>• Bóc tách cấu trúc lưới Bảng biểu (Table Grid) sang Markdown Table.<br>• Chuẩn hóa Unicode NFC và từ điển hành chính tiếng Việt. | ✅ **Hoàn thành 100%** |
| 2 | **Phan Thành Phát**<br>*(MSSV: 2212436)* | **Elasticsearch 8.x & Backend API / CSDL** | • Thiết lập cụm Elasticsearch 8.x với Custom Vietnamese Analyzer.<br>• Mô hình tìm kiếm lai kết hợp Hybrid Search RRF (BM25 + Dense Vector 768d).<br>• Phân luồng hồ sơ tự động Percolator (7 bộ luật chính sách).<br>• Che mờ dữ liệu nhạy cảm PII Masking theo Nghị định 13/2023/NĐ-CP.<br>• Hồ sơ sinh viên 360°, Đồ thị thực thể Entity Graph, Geo-Distance NĐ 81.<br>• Thiết kế CSDL PostgreSQL 3NF, Celery + Redis 7 & 35+ API FastAPI. | ✅ **Hoàn thành 100%** |
| 3 | **Lý Gia Bảo**<br>*(MSSV: 2213934)* | **TrOCR-Vi Deep Learning & Frontend Web SPA** | • Nghiên cứu & Huấn luyện mô hình Vision Transformer TrOCR-Vi.<br>• Chẩn đoán Phase A Diagnosis: xử lý lỗi cụt đuôi dòng dài (Truncation).<br>• Phát triển giải thuật Horizontal Line Chunking (Tiling gối đầu 30%).<br>• Tối ưu hóa suy luận FP16, Greedy Search tăng tốc 3,5x trên GPU RTX 3060.<br>• Giao diện Web SPA React 18 De-AI UI, Side-by-Side Live Editor, 8 Tab tra cứu.<br>• Xác thực số SHA-256 / QR chống giả mạo & Đóng gói Docker Compose. | ✅ **Hoàn thành 100%** |

---

## PHẦN 2: 5 CÂU HỎI TRỌNG TÂM CẦN CHUẨN BỊ KHI BÁO CÁO VỚI GVHD

Dưới đây là 5 câu hỏi học thuật và kỹ thuật mà Giảng viên hướng dẫn (ThS. Nguyễn Trọng Hiếu) và Hội đồng thường chất vấn nhóm sinh viên kèm gợi ý trả lời ngắn gọn, chuẩn xác:

### Câu hỏi 1: Tại sao nhóm lại nghiên cứu tích hợp song song cả VietOCR và TrOCR-Vi thay vì chỉ chọn một mô hình duy nhất?
- **Gợi ý trả lời**:
  - *Bản chất kỹ thuật*: **VietOCR** (kiến trúc CNN VGG + Transformer Seq2Seq) đã được huấn luyện rất sâu trên kho ngữ liệu tiếng Việt, cho độ chính xác cực cao trên văn bản in chuẩn hành chính (CER đạt **2,80%**, WER **5,20%**) và tốc độ suy luận nhanh (~0,08s/dòng). Tuy nhiên, VietOCR rất dễ gặp ảo giác (hallucination) khi gặp nét chữ viết tay tự do hoặc góc nghiêng lớn.
  - Ngược lại, **TrOCR-Vi** (kiến trúc Vision Transformer ViT hoàn toàn từ đầu đến cuối) có khả năng trích xuất đặc trưng không gian vượt trội của chữ viết tay và biểu mẫu phức tạp.
  - *Ý nghĩa thực tiễn*: Nhóm xây dựng cơ chế **Multi-Engine Registry** để kết hợp ưu thế của cả hai: Văn bản in chuẩn sử dụng VietOCR để đạt tốc độ tối đa; các vùng biểu mẫu có chữ viết tay điền thêm (Số hiệu, Ngày tháng, Họ tên) được định tuyến linh hoạt sang TrOCR-Vi.

---

### Câu hỏi 2: Nguyên nhân kỹ thuật nào khiến mô hình TrOCR bị cụt chữ ở cuối dòng (Truncation), và giải pháp Horizontal Chunking giải quyết bài toán này ra sao?
- **Gợi ý trả lời**:
  - *Nguyên nhân 1*: Bộ giải mã tự hồi quy (Autoregressive Decoder) bị giới hạn cứng bởi tham số `max_new_tokens=64`. Dòng văn bản hành chính dài (70–85 ký tự) khi mã hóa bằng Byte-Level BPE sinh ra 75–90 tokens, dẫn đến việc bị ngắt cưỡng bức ở token thứ 64 làm mất 15–20 ký tự cuối.
  - *Nguyên nhân 2*: Khối `ViTImageProcessor` ép co giãn ảnh dòng dài từ tỷ lệ tự nhiên $20:1$ thành hình vuông $384 \times 384$ px, khiến các ký tự ở mép phải bị nén xuống chỉ còn 3–4 pixel/chữ, làm các patch 16x16 bị lẫn lộn biểu diễn và kích hoạt sớm token kết thúc `<eos>`.
  - *Giải pháp*: Nhóm nâng `max_new_tokens=128` và xây dựng thuật toán **Horizontal Line Chunking (Tiling)** gối đầu 30%: Tự động dò tìm khe khoảng trắng tự nhiên giữa các từ (`_find_best_word_boundary`) để chia đôi dòng dài mà không bao giờ cắt đôi từ, sau đó ghép nối lại bằng so khớp chuỗi LCS. Nhờ đó, tỷ lệ cụt dòng giảm từ **13,04% xuống 0,53%**.

---

### Câu hỏi 3: Làm thế nào hệ thống bảo đảm an toàn dữ liệu cá nhân theo Nghị định 13/2023/NĐ-CP khi lưu trữ và tìm kiếm hồ sơ sinh viên?
- **Gợi ý trả lời**:
  - *Tại tầng dữ liệu huấn luyện*: Script `make_upload_package.py` tự động quét regex và loại bỏ các ảnh cắt chứa chuỗi số 8–10 chữ số (CCCD, SĐT, STK) và chữ ký trước khi đưa lên Colab/Kaggle.
  - *Tại tầng tìm kiếm & hiển thị*: Tích hợp cơ chế **PII Masking** theo vai trò (RBAC):
    - Tài khoản `STUDENT` hoặc khách vãng lai khi tra cứu chỉ nhìn thấy thông tin đã che mờ (ví dụ: CCCD `068******891`, SĐT `098****321`).
    - Chỉ tài khoản Cán bộ (`STAFF`) hoặc Quản trị (`ADMIN`) mới được giải mã để đối soát nghiệp vụ.
  - *Tính toàn vẹn*: Mọi tài liệu số hóa đều được băm SHA-256 để chống can thiệp hoặc làm giả hồ sơ.

---

### Câu hỏi 4: Tính năng Phân luồng hồ sơ tự động bằng Elasticsearch Percolator có ưu thế gì vượt trội so với viết các câu lệnh `if/else` hoặc query SQL truyền thống?
- **Gợi ý trả lời**:
  - *Khái niệm đảo ngược (Reverse Search)*: Tìm kiếm thông thường là "người dùng nhập từ khóa tìm tài liệu"; còn Percolator là **"đăng ký trước các bộ luật chính sách vào chỉ mục, khi có tài liệu OCR mới nạp vào, Elasticsearch tự động tìm xem tài liệu đó khớp với những luật nào"**.
  - *Ưu thế*:
    - **Tốc độ cực nhanh**: Elasticsearch biên dịch các câu query luật thành bộ lọc bộ nhớ (In-memory Inverted Index), khớp hàng chục điều luật cùng lúc trong thời gian < 10ms mà không làm tải chậm Web server.
    - **Mở rộng linh hoạt (Dynamic Rules)**: Khi nhà trường ban hành quy chế mới hoặc sửa đổi định mức miễn giảm, chuyên viên chỉ cần thêm một document luật mới vào index `percolator_policies` mà không cần phải sửa code, không cần deploy lại backend và không cần viết lại chuỗi câu lệnh `if/else` phức tạp.

---

### Câu hỏi 5: Khi nhận dạng bảng danh sách sinh viên nhiều trang, hệ thống giải quyết vấn đề hiệu năng và nối trang như thế nào?
- **Gợi ý trả lời**:
  - *Chiến lược 2 giai đoạn (Two-stage Scope Policy)*:
    - Nếu là PDF có sẵn text-layer: Hệ thống trích xuất toàn bộ trang ngay lập tức qua PyMuPDF (độ trễ P50 chỉ 11,57 ms).
    - Nếu là PDF scan: Mặc định hệ thống chỉ OCR sâu **Trang 1** (P50 = 850 ms) để phân loại loại văn bản và trích xuất số hiệu/ngày tháng ban hành.
    - Với các trang danh sách tiếp theo: Hệ thống cho phép kích hoạt tác vụ nền bất đồng bộ (`POST /documents/{id}/ocr-full`) qua Celery Worker, nối kết quả các trang rõ ràng bằng cú pháp `--- Trang N ---`.
  - *Cấu trúc bảng*: Bóc tách tự động ma trận ô bảng sang định dạng **Markdown Table**, cho phép tìm kiếm lồng (Nested Search) từng sinh viên trong bảng danh sách.

---

## PHẦN 3: TÓM TẮT 1 SLIDE (TỐI ĐA 10 DÒNG) CHO PHẦN THUYẾT TRÌNH BẢO CÁO

```text
======================= TÓM TẮT TIẾN ĐỘ ĐỒ ÁN LẦN 2 (1 SLIDE) =======================
1. ĐỀ TÀI: Số hóa & Quản lý tài liệu Công tác sinh viên bằng OCR và Elasticsearch.
2. PHÂN CÔNG: Thành (VietOCR & Tiền xử lý), Phát (Elasticsearch & Backend), Bảo (TrOCR-Vi & Frontend) - CTK46-PM.
3. CÁN BỘ HƯỚNG DẪN: ThS. Nguyễn Trọng Hiếu - Khoa Công nghệ Thông tin, Trường Đại học Đà Lạt.
4. TIẾN ĐỘ TỔNG THỂ: Đạt 87,0% khối lượng toàn bộ 12 Phase của đồ án (vượt kế hoạch).
5. DỮ LIỆU: Mở rộng 13.658 dòng văn bản CTSV, bổ sung synthetic data bao phủ 145 ký tự tiếng Việt.
6. ĐỘT PHÁ OCR: Khắc phục lỗi cụt đuôi dòng TrOCR (giảm từ 13,04% xuống 0,53%), tăng tốc GPU 3,5x.
7. PHÂN LOẠI VĂN BẢN: Đạt 100% độ chính xác trên 6 nhóm tài liệu (P50 từ 11,57 ms đến 850 ms).
8. ELASTICSEARCH 8.x: Hoàn thiện 23 API, Hybrid RRF, Percolator 7 luật, PII Masking, 38/38 tests pass.
9. GIAO DIỆN REACT 18: De-AI UI chuẩn ĐH Đà Lạt, Side-by-Side Live Editor, tra cứu 8 tab chuyên biệt.
10. KẾ HOẠCH THÁNG 11: Hoàn thiện toàn văn Khóa luận (Chương 1-6), thử nghiệm tại Phòng CTSV & bảo vệ.
======================================================================================
```
