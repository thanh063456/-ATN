# 10 CÂU HỎI HỘI ĐỒNG DỄ HỎI NHẤT & KỊCH BẢN TRẢ LỜI NGẮN GỌN
**Dự án:** DocuCTSV — Hệ thống Số hóa và Quản lý Tài liệu Công tác Sinh viên Ứng dụng OCR và Elasticsearch  
**Căn cứ:** Dữ liệu thực nghiệm và mã nguồn đã kiểm chứng 100% tại thư mục dự án  
**Phân công trả lời:** Ngô Công Thành (VietOCR, Xử lý ảnh, Hậu xử lý), Phan Thành Phát (Elasticsearch, CSDL, Bảo mật), Lý Gia Bảo (TrOCR-Vi, Web, Docker)

---

### CÂU 1: Tại sao CER của TrOCR trên tập 32 trang hỗn hợp lại là 20,58% (tăng từ 19,26%), trong khi VietOCR lại đạt 2,80%? Có phải TrOCR bị giảm chất lượng sau khi tối ưu không?
* **Người trả lời:** 👨‍💻 **Lý Gia Bảo** *(TrOCR-Vi)*
* **Dẫn chứng kỹ thuật:** `docs/ocr_diagnosis.md` dòng 12; `docs/bao_cao_tien_do_lan_2_v2.md` dòng 230–232.
* **Đáp án ngắn gọn:**
  > "Kính thưa Thầy/Cô, hai chỉ số này được đo trên hai tập kiểm thử hoàn toàn khác nhau về bản chất:
  > - **VietOCR (CER 2,80%)** được đo trên tập `test.tsv` (244 dòng) gồm toàn bộ là văn bản in chuẩn hành chính rõ nét.
  > - **TrOCR (CER 20,58%)** được đo trên tập kiểm định độc lập `held_out_32.json` gồm 32 trang scan thực tế đầy đủ: chứa nhiều lá đơn sinh viên viết tay tự do, nét bút bi nhạt và đặc biệt là bị con dấu đỏ hành chính đóng đè lên chữ.
  > - Sau khi tối ưu FP16 và Chunking, tỷ lệ cụt dòng giảm kỷ lục từ 13,04% xuống 0,53%. Do các ký tự ở phần đuôi dòng trước đây bị cụt nay được nhận dạng đầy đủ, kết hợp với vùng chữ viết tay mờ và con dấu đỏ ở rìa trang khiến CER tăng nhẹ từ 19,26% lên 20,58%. Đổi lại, hệ thống đọc trọn vẹn văn bản và tốc độ xử lý nhanh hơn 3,5 lần."

---

### CÂU 2: Vì sao trong mã nguồn `vietocr_service.py` hàm `preprocess_image` lại trả về nguyên bản và ghi chú "không áp dụng CLAHE hay GaussianBlur", khác với slide ban đầu?
* **Người trả lời:** 👨‍💻 **Ngô Công Thành** *(Xử lý ảnh & VietOCR)*
* **Dẫn chứng kỹ thuật:** `backend/app/services/vietocr_service.py` dòng 420–435; `Bao_cao_dot_2.md` dòng 258.
* **Đáp án ngắn gọn:**
  > "Kính thưa Thầy/Cô, đây là phát hiện thực nghiệm rất quan trọng của nhóm trong Đợt 2:
  > - Ban đầu nhóm dự kiến áp dụng CLAHE toàn trang để tăng độ tương phản. Tuy nhiên, khi đưa vào thực nghiệm, thuật toán CLAHE toàn cục đã tạo ra các quầng sáng (halo artifacts) bao quanh nét chữ in đậm, làm vỡ các nét chữ nhỏ và đứt đoạn dấu thanh tiếng Việt của văn bản in chuẩn.
  > - Do đó, nhóm đã chủ động tắt CLAHE trên toàn trang để bảo toàn độ nét và màu sắc tự nhiên cho bộ dò EasyOCR và VietOCR. Thay vào đó, nhóm áp dụng kỹ thuật upscale chọn lọc đối với các dòng có chiều cao dưới 32 pixel để nhận diện rõ dấu thanh, giúp duy trì CER 2,80%."

---

### CÂU 3: Bộ phân tích tiếng Việt trong Elasticsearch thực tế sử dụng Tokenizer nào? Có dùng `icu_tokenizer` như tài liệu nghiên cứu đề cập không?
* **Người trả lời:** 👨‍💻 **Phan Thành Phát** *(Elasticsearch)*
* **Dẫn chứng kỹ thuật:** `backend/app/core/elasticsearch.py` dòng 110–145.
* **Đáp án ngắn gọn:**
  > "Kính thưa Thầy/Cô, trong mã nguồn triển khai thực tế trên Docker Compose, nhóm sử dụng **`tokenizer: standard`** kết hợp với bộ lọc từ đồng nghĩa hành chính chuyên biệt **`synonym_ctsv`** và bộ lọc bỏ dấu **`asciifolding`**.
  > - Nhóm đã nghiên cứu `icu_tokenizer` trong giai đoạn thiết kế lý thuyết, nhưng image Docker chuẩn của Elasticsearch 8.12.0 không cài sẵn plugin `analysis-icu`. Để hệ thống có thể triển khai đóng gói nhẹ nhàng và chạy độc lập '1-click' mà không bị lỗi thiếu plugin trên môi trường mới, nhóm đã chuẩn hóa bộ phân tích bằng tokenizer tiêu chuẩn kết hợp từ điển từ đồng nghĩa tiếng Việt viết tắt của trường ĐH Đà Lạt."

---

### CÂU 4: Thuật toán chia nhỏ dòng ngang (Horizontal Line Chunking) trong `trocr_engine.py` cắt ảnh như thế nào để không làm đứt đôi chữ cái hay từ vựng?
* **Người trả lời:** 👨‍💻 **Lý Gia Bảo** *(TrOCR-Vi)*
* **Dẫn chứng kỹ thuật:** `backend/app/services/trocr_engine.py` dòng 116–168 và dòng 200–210.
* **Đáp án ngắn gọn:**
  > "Kính thưa Thầy/Cô, đối với các dòng chữ dài trên 1100 pixel có tỷ lệ khung hình lớn hơn 9:1, nhóm không cắt đôi cố định ở vị trí 50% mà phát triển hàm **`_find_best_word_boundary()`**:
  > - Hàm quét qua vùng giữa dòng (trong cửa sổ tìm kiếm 30% quanh tâm) và tính toán cường độ sáng trung bình theo từng cột dọc.
  > - Thuật toán tự động định vị các dải cột màu trắng liên tục (contiguous white runs) có độ rộng đủ lớn biểu thị khoảng cách giữa hai từ ngữ. Điểm cắt `cut_x` được đặt chính xác vào giữa dải trắng này, bảo đảm không bao giờ cắt ngang thân chữ cái hay âm tiết tiếng Việt, nhờ đó bộ giải mã RoBERTa tiếp nhận trọn vẹn ngữ cảnh của từng từ."

---

### CÂU 5: Tập mẫu kiểm thử phân loại tài liệu (Doctype) gồm 18 mẫu có phải là dữ liệu scan thực tế ngoài đời không?
* **Người trả lời:** 👨‍💻 **Phan Thành Phát** *(Phân loại văn bản)*
* **Dẫn chứng kỹ thuật:** `scripts/e2e_doctype.py` dòng 35–120; `Bao_cao_dot_2.md` dòng 185–190.
* **Đáp án ngắn gọn:**
  > "Kính thưa Thầy/Cô, nhóm xin báo cáo hoàn toàn trung thực: tập 18 mẫu kiểm thử E2E ban đầu được sinh ra tự động từ script `scripts/e2e_doctype.py` gồm 6 loại văn bản nghiệp vụ CTSV nhân với 3 cấu hình trang (1 trang, 3 trang, 5 trang) ở cả dạng PDF có sẵn chữ và PDF scan giả lập.
  > - Mục tiêu của đợt kiểm thử này là xác minh tính đúng đắn của logic phân loại 2 pha: phân loại trong 11,57 ms với file có text-layer và 850 ms trên trang bìa file scan. Nhóm nhận thức rõ 18 mẫu tổng hợp chưa đại diện hết cho thực tế, do đó trong kế hoạch tháng 11, nhóm sẽ mở rộng tập kiểm thử lên 100+ văn bản lưu trữ thực tế tại văn phòng Phòng CTSV."

---

### CÂU 6: Chỉ số Precision@5 của Elasticsearch trong tài liệu `Experiment.md` ghi nhận 74,0% trên nhóm Easy và trung bình là 45,6%, tại sao trước đây từng có báo cáo 100% hoặc 92%?
* **Người trả lời:** 👨‍💻 **Phan Thành Phát** *(Elasticsearch & IR Benchmark)*
* **Dẫn chứng kỹ thuật:** `docs/Experiment.md` dòng 65–105; `dataset/ir_ground_truth.json`.
* **Đáp án ngắn gọn:**
  > "Kính thưa Thầy/Cô, con số 100% trước đây là do phương pháp đo cũ bị lỗi vòng lặp (circular keyword-match): hệ thống lấy chính từ khóa trong kết quả tìm kiếm để tự kiểm tra lại nên kết quả bị thổi phồng.
  > - Trong Đợt 2, nhóm đã chuẩn hóa lại hoàn toàn theo phương pháp khoa học quốc tế với bộ Ground Truth độc lập gồm **25 truy vấn** (`ir_ground_truth.json`).
  > - Kết quả đo lường khách quan cho thấy: với nhóm truy vấn khớp biểu mẫu (EASY), Precision@5 đạt **74,0%** và Precision@10 đạt **82,0%**; với nhóm truy vấn âm tính ngoài phạm vi trường học (NEGATIVE), tỷ lệ nhận diện và loại bỏ chính xác đạt **100%**. Con số trung bình toàn tập là 45,6% vì bao gồm cả các truy vấn viết tắt không dấu rất khó."

---

### CÂU 7: Cơ chế Percolator phân luồng tự động hoạt động thế nào trên 7 bộ luật chính sách, và có gì ưu việt hơn chuỗi câu lệnh if-else trong code Python?
* **Người trả lời:** 👨‍💻 **Phan Thành Phát** *(Elasticsearch)*
* **Dẫn chứng kỹ thuật:** `backend/app/routers/search.py` dòng 3750–3880.
* **Đáp án ngắn gọn:**
  > "Kính thưa Thầy/Cô, Percolator là cơ chế tìm kiếm ngược (Reverse Search):
  > - Thay vì người dùng nhập từ khóa tìm tài liệu, hệ thống lưu sẵn 7 bộ luật chính sách (như Nghị định 81 miễn 100%, giảm 70%, 50%, Quyết định 1121 trợ cấp xã hội, Học bổng KKHT) vào chỉ mục. Khi có hồ sơ sinh viên mới được nạp vào, Elasticsearch tự động khớp toàn văn tài liệu với các bộ luật trong bộ nhớ chỉ mất dưới 10 mili-giây.
  > - Điểm ưu việt là tách biệt hoàn toàn nghiệp vụ khỏi mã nguồn: khi nhà trường ban hành quy chế học bổng mới, cán bộ chỉ cần thêm một tài liệu luật vào chỉ mục qua giao diện API mà không cần sửa code Python backend, không cần deploy lại hệ thống và tận dụng được toàn bộ khả năng tìm kiếm từ đồng nghĩa tiếng Việt của Elasticsearch."

---

### CÂU 8: Phương pháp lọc con dấu đỏ bằng không gian màu HSV theo thang OpenCV (H: 0–10 và 170–180) có nguy cơ làm mất nét chữ đen bị con dấu đè lên không?
* **Người trả lời:** 👨‍💻 **Ngô Công Thành** *(Xử lý ảnh)*
* **Dẫn chứng kỹ thuật:** `docs/ocr_diagnosis.md` dòng 55–65; `Slide_dot_2.md` Slide 16.
* **Đáp án ngắn gọn:**
  > "Kính thưa Thầy/Cô, trong không gian màu HSV theo thang chuẩn OpenCV ($H: 0\text{--}180$), sắc độ màu đỏ phân bố ở hai đầu biên: từ 0 đến 10 và từ 170 đến 180.
  > - Khi con dấu đỏ đóng đè lên chữ in đen, tại các điểm ảnh giao nhau, mực đen làm giảm mạnh giá trị độ sáng V (Value) và độ bão hòa S (Saturation) so với vùng chỉ có mực đỏ của con dấu.
  > - Thuật toán của nhóm sử dụng phân ngưỡng thích nghi kết hợp hai điều kiện: chỉ loại bỏ các điểm ảnh có sắc độ đỏ kèm độ sáng cao (vùng con dấu thuần), đồng thời bảo lưu các điểm ảnh có độ tối sâu (nét chữ đen). Nhờ đó, lớp mực đỏ của con dấu bị triệt tiêu mà khung xương nét chữ đen bên dưới vẫn được phục hồi để mô hình OCR đọc chính xác."

---

### CÂU 9: Tỷ lệ tiến độ toàn đồ án đạt 78,4% được tính toán như thế nào, và vì sao khối lượng kỹ thuật đạt ~88% trong khi phần thuyết minh mới đạt 40%? Liệu nhóm có kịp nộp khóa luận trong tháng 11?
* **Người trả lời:** 👨‍💻 **Ngô Công Thành** *(Trưởng nhóm)*
* **Dẫn chứng kỹ thuật:** `docs/bao_cao_v2_changelog.md` dòng 22; `.ai/ROADMAP.md`.
* **Đáp án ngắn gọn:**
  > "Kính thưa Thầy/Cô, đồ án được chia thành 12 Phase với bảng trọng số khoa học:
  > - 11 Phase kỹ thuật (từ khảo sát, xây dựng dữ liệu, mô hình OCR đến Docker backend/frontend) chiếm 85% tổng trọng số, hiện đã hoàn thành khoảng 88%.
  > - Phase 12 (Viết toàn văn Khóa luận và bảo vệ) chiếm 15% trọng số, hiện đạt khoảng 35–40% (đã hoàn thiện đề cương chi tiết và 2 chương đầu). Tổng tiến độ tích lũy đạt đúng **78,35%**, nhóm làm tròn thành 78,4%.
  > - Nhóm ưu tiên hoàn thiện phần kỹ thuật trước để có số liệu thực nghiệm chính xác tuyệt đối. Vì mã nguồn, kết quả thực nghiệm và sơ đồ hệ thống đều đã hoàn chỉnh, trong 2 tuần đầu tháng 11 nhóm sẽ tập trung toàn bộ thời gian để hoàn thành các chương 3, 4, 5 và chắc chắn kịp tiến độ nộp quyển vào tuần thứ 4."

---

### CÂU 10: Hệ thống bảo vệ dữ liệu cá nhân (PII Masking) theo Nghị định 13/2023/NĐ-CP được triển khai ở tầng nào, che mờ những thông tin gì và đối với những đối tượng nào?
* **Người trả lời:** 👨‍💻 **Phan Thành Phát** *(Bảo mật & Backend)*
* **Dẫn chứng kỹ thuật:** `backend/app/routers/search.py` dòng 283–295 và dòng 923–930.
* **Đáp án ngắn gọn:**
  > "Kính thưa Thầy/Cô, tính năng PII Masking được triển khai tại tầng API Gateway của Backend trước khi trả dữ liệu về giao diện:
  > - **Quy tắc che mờ:** Tự động nhận diện regex và che mờ số Căn cước công dân (chỉ hiển thị 3 số đầu và 3 số cuối, ví dụ `068******891`), số điện thoại di động (ví dụ `098****321`) và địa chỉ email cá nhân của sinh viên.
  > - **Phân quyền theo vai trò (RBAC):** Khi người dùng chưa đăng nhập hoặc đăng nhập bằng tài khoản Sinh viên (`STUDENT`), hệ thống tự động che mờ các trường dữ liệu trên. Chỉ tài khoản Cán bộ Phòng CTSV (`STAFF`) hoặc Quản trị viên (`ADMIN`) mới có quyền xem thông tin định danh đầy đủ để phục vụ nghiệp vụ đối soát hồ sơ."

