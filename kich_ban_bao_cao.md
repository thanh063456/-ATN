# KỊCH BẢN THUYẾT TRÌNH BÁO CÁO ĐỒ ÁN TỐT NGHIỆP (10 PHÚT)
*(Bản diễn giải dễ hiểu, tự nhiên, có chú thích tiếng Việt cho mọi thuật ngữ kỹ thuật)*

* **Tên đề tài**: Hệ Thống Số Hóa và Trích Xuất Thông Tin Tài Liệu Công Tác Sinh Viên Bằng Mô Hình OCR và Tìm Kiếm Toàn Văn (DocuCTSV)
* **Giảng viên hướng dẫn**: ThS. Đặng Thế Nguyên
* **Sinh viên thực hiện**:
  * **Ngô Công Thành** (MSSV: 2212461) – *Trưởng nhóm (Phụ trách AI, Xử lý ảnh & Pipeline OCR)*
  * **Phan Thành Phát** (MSSV: 2212463) – *Thành viên (Phụ trách Backend API, CSDL & Máy chủ tìm kiếm Elasticsearch)*
  * **Lý Gia Bảo** (MSSV: 2213934) – *Thành viên (Phụ trách Giao diện Web SPA, Trình đối soát & Đóng gói Docker)*
* **Thời lượng chuẩn**: **10 phút** (+ 5–10 phút hỏi đáp cùng Hội đồng).

---

## ⏱ BẢNG PHÂN BỔ THỜI GIAN THEO TỪNG SLIDE

| Mốc Thời Gian | Slide | Tên Nội Dung Trình Bày | Trọng Tâm Diễn Đạt Dễ Hiểu |
|:---:|:---:|---|---|
| **00:00 – 00:30** | **Slide 1** | Giới thiệu Đề tài & Nhóm tác giả | Chào trang trọng, giới thiệu ngắn gọn tên đề tài và thành viên. |
| **00:30 – 01:15** | **Slide 2** | Đặt vấn đề & Mục tiêu giải pháp | Nêu khó khăn khi gõ tay hồ sơ giấy và thách thức chữ viết tay/bảng. |
| **01:15 – 02:15** | **Slide 3** | Công nghệ & Kiến trúc tổng thể | Giới thiệu 3 tầng: Giao diện Web, Máy chủ xử lý và Tầng CSDL/AI. |
| **02:15 – 03:00** | **Slide 4** | Phân rã 6 Modules & Phân công | Giải thích sơ đồ WBS 2×3, mỗi thành viên đảm nhận 2 phần việc. |
| **03:00 – 04:00** | **Slide 5** | Quy trình Pipeline OCR Đa tầng | Giải thích luồng xử lý từ lúc nạp file đến khi trích xuất thông tin. |
| **04:00 – 05:00** | **Slide 6** | Kỹ thuật Tiền xử lý & Bóc tách Bảng | Cách xoay thẳng ảnh, phóng to chữ mờ và cắt từng ô bảng biểu. |
| **05:00 – 06:15** | **Slide 7** | Mô hình VietOCR & Hậu xử lý | Giải thích cách AI đọc chữ và 3 lớp tự động sửa lỗi chính tả. |
| **06:15 – 07:30** | **Slide 8** | Dữ liệu & Đánh giá chất lượng OCR | Bảng số liệu thực tế (In: 93.8%, Viết tay: 71.2%), giải thích các lỗi còn lại. |
| **07:30 – 08:30** | **Slide 9** | Elasticsearch & Hiệu năng tìm kiếm | Tốc độ tìm 45ms, tìm kiếm mờ khi OCR có sai sót, điểm SUS 82.5. |
| **08:30 – 09:15** | **Slide 10** | Demo Tính năng & Trình đối soát | Giới thiệu màn hình 2 cửa sổ giúp cán bộ vừa nhìn vừa sửa nhanh. |
| **09:15 – 09:45** | **Slide 11** | Bảo mật, SHA-256 & Phân quyền | Mã băm chống sửa file gốc, mã QR an toàn che mờ tên sinh viên. |
| **09:45 – 10:00** | **Slide 12** | Tổng kết, Hạn chế & Lời cảm ơn | Tóm tắt kết quả, nhìn nhận hạn chế thực tế và mời Hội đồng đặt câu hỏi. |

---

## 🎙 LỜI THOẠI CHI TIẾT THEO TỪNG PHÚT (DỄ NÓI, DỄ HIỂU)

---

### 🟢 PHẦN 1: MỞ ĐẦU & ĐẶT VẤN ĐỀ (00:00 – 01:15)

#### 🔹 [00:00 – 00:30] SLIDE 1: TRANG TIÊU ĐỀ
* **Hành động**: Đứng thẳng, tự tin, mắt nhìn bao quát Hội đồng, cúi đầu chào nhẹ.
* **Lời thoại**:
> *"Kính thưa Quý Thầy/Cô trong Hội đồng chấm khóa luận tốt nghiệp, kính thưa Thầy hướng dẫn ThS. Đặng Thế Nguyên cùng toàn thể các bạn sinh viên.*
>
> *Em xin đại diện nhóm sinh viên, gồm 3 thành viên: Ngô Công Thành - Trưởng nhóm, bạn Phan Thành Phát và bạn Lý Gia Bảo, xin phép được trình bày báo cáo đồ án tốt nghiệp với đề tài: **'Hệ thống số hóa và trích xuất thông tin tài liệu Công tác Sinh viên bằng mô hình OCR và tìm kiếm toàn văn'**, tên viết tắt của hệ thống là **DocuCTSV**.*
>
> *Sau đây, em xin phép được bắt đầu phần trình bày của nhóm."*

---

#### 🔹 [00:30 – 01:15] SLIDE 2: ĐẶT VẤN ĐỀ VÀ MỤC TIÊU ĐỀ TÀI
* **Hành động**: [Chuyển sang Slide 2]. Nhấn giọng vào các từ khóa *nhập liệu thủ công*, *chữ viết tay*, *tra cứu mất thời gian*.
* **Lời thoại**:
> *"Kính thưa Hội đồng, hàng năm Phòng Công tác Sinh viên tại Trường Đại học Đà Lạt tiếp nhận hàng chục ngàn hồ sơ giấy như: đơn xin miễn giảm học phí, đơn xin học bổng, giấy xác nhận sinh viên hay các quyết định khen thưởng.*
>
> *Hiện nay, việc quản lý hồ sơ phần lớn vẫn làm **thủ công bằng tay**. Cán bộ phải tự đọc và gõ từng thông tin vào máy tính, rất dễ nhầm lẫn Mã số sinh viên hoặc Họ tên. Mỗi lần cần tìm lại một bộ hồ sơ cũ từ các năm trước, cán bộ phải vào kho lưu trữ lục tìm mất từ nhiều giờ đến nhiều ngày.*
>
> *Bên cạnh đó, tài liệu sinh viên có đặc thù rất phức tạp: vừa có chữ in máy tính, vừa có **chữ viết tay mờ đè lên các dòng chấm**, bảng biểu và con dấu đỏ. Các phần mềm đọc chữ thông thường như Tesseract hay EasyOCR khi đọc tiếng Việt viết tay thường bị sai dấu hoặc làm xáo trộn các cột trong bảng.*
>
> *Vì vậy, mục tiêu của nhóm em là xây dựng hệ thống **DocuCTSV** để tự động hóa trọn vẹn: từ khâu nhận file, làm sạch ảnh, dùng trí tuệ nhân tạo để đọc chữ tiếng Việt, bóc tách bảng biểu, cho đến tìm kiếm siêu tốc và xác thực an toàn."*

---

### 🟢 PHẦN 2: KIẾN TRÚC & PHÂN CÔNG (01:15 – 03:00)

#### 🔹 [01:15 – 02:15] SLIDE 3: CÔNG NGHỆ VÀ KIẾN TRÚC TỔNG THỂ
* **Hành động**: [Chuyển sang Slide 3]. Chỉ tay vào sơ đồ kiến trúc 3 tầng trên màn hình.
* **Lời thoại**:
> *"Để giải quyết bài toán trên, nhóm em xây dựng hệ thống theo kiến trúc 3 tầng hiện đại và rõ ràng:*
>
> *1. **Tầng Giao diện (Client)**: Ứng dụng Web viết bằng **React 18 và TypeScript**, giúp giao diện mượt mà và dễ dùng, kèm theo trang quét mã QR tra cứu an toàn.*
> *2. **Tầng Máy chủ xử lý (Backend)**: Sử dụng **FastAPI** viết trên Python 3.11 để xử lý các nghiệp vụ. Các tác vụ đọc chữ OCR nặng được đưa vào **tiến trình xử lý ngầm (Async Worker)** để không làm đơ hay gián đoạn màn hình của người dùng.*
> *3. **Tầng Dữ liệu và AI**: Sử dụng cơ sở dữ liệu **PostgreSQL** trên Supabase, máy chủ tìm kiếm **Elasticsearch 8.12** chuyên cho tiếng Việt, bộ nhớ tạm **Redis 7** lưu phiên đăng nhập, và file gốc được lưu trữ trên **Supabase Storage**.*
>
> *Toàn bộ hệ thống được đóng gói thành **4 Container Docker** độc lập, giúp dễ dàng cài đặt và vận hành trên bất kỳ máy chủ nào."*

---

#### 🔹 [02:15 – 03:00] SLIDE 4: PHÂN RÃ HỆ THỐNG (WBS) VÀ PHÂN CÔNG NHIỆM VỤ
* **Hành động**: [Chuyển sang Slide 4]. Trình bày ngắn gọn, rõ ràng trách nhiệm của từng bạn.
* **Lời thoại**:
> *"Hệ thống được chia làm **6 phân hệ Module chính** (thể hiện qua bảng lưới 2×3), mỗi bạn trong nhóm phụ trách 2 module đúng theo thế mạnh:*
>
> * *Bạn **Ngô Công Thành** phụ trách **Module 1 và 2**: Thu thập bộ dữ liệu thực tế, lập trình các thuật toán xử lý ảnh, huấn luyện mô hình AI VietOCR và thuật toán bóc tách bảng biểu.*
> * *Bạn **Phan Thành Phát** phụ trách **Module 3 và 4**: Xây dựng bộ luật tự động trích xuất Mã sinh viên, Số hiệu; cấu hình máy chủ tìm kiếm Elasticsearch và lập trình toàn bộ hệ thống máy chủ Backend, CSDL.*
> * *Bạn **Lý Gia Bảo** phụ trách **Module 5 và 6**: Thiết kế giao diện Web với màn hình đối soát 2 cửa sổ Side-by-Side, lập trình tính năng mã băm SHA-256 bảo vệ file gốc, xác thực mã QR và đóng gói Docker.*
>
> *Sự phân chia này giúp các phần việc được phát triển song song và kết nối chặt chẽ với nhau."*

---

### 🟢 PHẦN 3: GIẢI PHÁP AI & QUY TRÌNH OCR (03:00 – 06:15)

#### 🔹 [03:00 – 04:00] SLIDE 5: QUY TRÌNH XỬ LÝ OCR ĐA TẦNG (PIPELINE)
* **Hành động**: [Chuyển sang Slide 5]. Giải thích từng bước trong sơ đồ Pipeline.
* **Lời thoại**:
> *"Trọng tâm kỹ thuật của đồ án nằm ở **Quy trình OCR đa tầng** được thiết kế riêng cho văn bản hành chính và tài liệu sinh viên:*
>
> * *Đầu tiên, file PDF hoặc ảnh chụp khi tải lên sẽ được tạo ảnh với **độ phân giải linh hoạt (Adaptive DPI)**: Mặc định dùng 300 DPI để chạy nhanh, nhưng khi thấy có bảng biểu hoặc chữ viết tay, máy tự tăng lên 450 DPI để giữ nét rõ ràng.*
> * *Tiếp theo là bước tiền xử lý: Tự động xoay thẳng ảnh nếu bị chụp nghiêng, và cân bằng ánh sáng để làm đậm nét mực.*
> * *Sau đó hệ thống kiểm tra cấu trúc: Nếu có bảng biểu, máy sẽ cắt từng ô lưới để ghép thành bảng Markdown; nếu là văn bản thường, máy sẽ cắt rời từng dòng chữ.*
> * *Các dòng chữ được gom lại và đưa qua mô hình **VietOCR** nhận dạng theo lô (Batch) để tăng tốc độ. Cuối cùng, văn bản được chạy qua **3 lớp hậu xử lý** để tự sửa lỗi chính tả và trích xuất thông tin trước khi lưu trữ."*

---

#### 🔹 [04:00 – 05:00] SLIDE 6: KỸ THUẬT TIỀN XỬ LÝ ẢNH VÀ BÓC TÁCH BẢNG BIỂU
* **Hành động**: [Chuyển sang Slide 6]. Nêu 4 kỹ thuật chính giúp đọc được chữ viết tay và bảng.
* **Lời thoại**:
> *"Để xử lý tốt chữ viết tay và bảng biểu, nhóm em áp dụng 4 kỹ thuật xử lý ảnh quan trọng:*
>
> *1. **Tự động xoay thẳng ảnh (Deskew)**: Dùng thuật toán tìm góc xiên của trang giấy và xoay phẳng về 0 độ, giúp chữ không bị méo nghiêng.*
> *2. **Khử đường chấm biểu mẫu**: Nhận diện và làm mờ dải chấm in sẵn `...........` để không bị dính vào nét chữ của sinh viên.*
> *3. **Tự động phóng to chữ nhỏ (Dynamic Zooming)**: Nếu dòng chữ viết tay có chiều cao quá nhỏ dưới 48 pixel, hệ thống tự động phóng to lên trên 56 pixel để mô hình AI nhìn rõ nét.*
> *4. **Bóc tách Bảng biểu (Table Grid)**: Thuật toán quét các đường kẻ ngang và dọc để bắt chính xác các ô trong bảng, cắt từng ô ra đọc chữ rồi ghép lại thành **Bảng Markdown** giữ nguyên hàng cột chuẩn xác."*

---

#### 🔹 [05:00 – 06:15] SLIDE 7: MÔ HÌNH NHẬN DẠNG AI VÀ HẬU XỬ LÝ VĂN BẢN
* **Hành động**: [Chuyển sang Slide 7]. Giải thích mô hình Transformer và 3 lớp sửa lỗi.
* **Lời thoại**:
> *"Về phần nhận dạng chữ, nhóm em sử dụng mô hình **VietOCR Transformer**:*
> * *Mạng **VGG-19** đóng vai trò như mắt nhìn, trích xuất hình ảnh của dòng chữ.*
> * *Mạng **Transformer với cơ chế chú ý (Self-Attention)** đóng vai trò như bộ não, hiểu được ngữ cảnh tiếng Việt cả phía trước và phía sau để đoán đúng từ ngữ và dấu thanh.*
>
> *Sau khi đọc xong, văn bản đi qua **Gói hậu xử lý 3 lớp** do nhóm tự phát triển:*
> * * **Lớp 1 - Sửa lỗi quang học**: Tự sửa các chữ hay nhìn nhầm, ví dụ chữ `l` thường nhầm thành số `1`, chữ `O` hoa nhầm thành số `0`, hay `tháng 40)` sửa thành `tháng 4`.*
> * * **Lớp 2 - Tra từ điển hành chính**: Tự sửa các từ vựng đặc thù của Trường Đại học Đà Lạt, ví dụ sửa `Điêu` thành `Điều`, `Quyét` thành `Quyết`, mã văn bản `QD-DHDL` thành `QĐ-ĐHĐL`.*
> * * **Lớp 3 - Chuẩn hóa tiêu đề**: Tự động dựng lại Quốc hiệu, Tiêu ngữ, Số hiệu, Ngày tháng chuẩn đẹp, và xóa sạch các tiêu đề bị lặp lại ở thân bài.*
>
> *Nhờ đó, hệ thống tự động lấy ra chính xác **Mã sinh viên, Họ tên, Ngày tháng** và tự phân loại đúng biểu mẫu như Đơn xin nghỉ học, Đơn học bổng hay Kế hoạch."*

---

### 🟢 PHẦN 4: KẾT QUẢ THỰC TẾ, TÌM KIẾM & DEMO (06:15 – 09:15)

#### 🔹 [06:15 – 07:30] SLIDE 8: TẬP DỮ LIỆU THỰC TẾ VÀ ĐÁNH GIÁ CHẤT LƯỢNG OCR
* **Hành động**: [Chuyển sang Slide 8]. Hướng mắt về bảng số liệu, giọng khách quan, khoa học.
* **Lời thoại**:
> *"Kính thưa Hội đồng, nhóm em đã xây dựng bộ dữ liệu thực nghiệm gồm **13.125 dòng chữ từ 425 trang tài liệu thực tế** tại Phòng CTSV. Dữ liệu được chia theo từng trang gốc độc lập để việc kiểm tra hoàn toàn khách quan.*
>
> *Bảng đo lường thực tế trên màn hình cho thấy sự tiến bộ rõ rệt:*
> * *Mô hình gốc ban đầu (Baseline) gặp rất nhiều lỗi với tỷ lệ lỗi ký tự lên đến **24.8%**.*
> * *Khi thêm các bước tiền xử lý ảnh, độ chính xác tăng lên **81.5%**.*
> * *Khi huấn luyện mô hình trên dữ liệu CTSV, độ chính xác đạt **85.8%**.*
> * *Và khi áp dụng **toàn bộ hệ thống cùng 3 lớp hậu xử lý**, độ chính xác ký tự toàn hệ thống đạt **89.6%** (tỷ lệ lỗi ký tự giảm xuống chỉ còn **10.4%**), và độ chính xác cấp từ đạt **82.4%**.*
>
> *Đi vào thực tế từng loại tài liệu:*
> * * **Văn bản in hành chính**: Đạt độ chính xác rất cao **93.8%**, đọc tốt các quyết định, kế hoạch.*
> * * **Chữ viết tay sinh viên**: Đạt **71.2%** (tăng mạnh từ mức 42.5% ban đầu). Tuy nhiên, nhóm em thẳng thắn nhận định chữ viết tay trong thực tế vẫn còn nhiều sai sót do nét chữ sinh viên quá nguệch ngoạc, nét mực mờ hoặc bị con dấu đỏ đè lên.*
>
> *Chính vì nhận thức rõ OCR không thể đúng 100%, nhóm em đã thiết kế giải pháp thực tế: **AI tự động hóa 80% khâu nhập liệu thô**, kết hợp màn hình **Side-by-Side Live Editor** để con người kiểm tra nhanh và tính năng **Tìm kiếm mờ** để không bị mất tài liệu."*

---

#### 🔹 [07:30 – 08:30] SLIDE 9: TÌM KIẾM ELASTICSEARCH VÀ HIỆU NĂNG HỆ THỐNG
* **Hành động**: [Chuyển sang Slide 9]. Nhấn mạnh tốc độ 45 mili-giây và khả năng tìm kiếm thông minh.
* **Lời thoại**:
> *"Để bù đắp cho những chữ có thể bị OCR đọc sai, nhóm em đã tích hợp máy chủ tìm kiếm **Elasticsearch 8.12** chuyên xử lý tiếng Việt, hỗ trợ **Tìm kiếm mờ (Fuzzy Search)** và tìm kiếm không dấu.*
>
> *Thực nghiệm trên 1.000 tài liệu với 50 câu tìm kiếm mẫu cho kết quả rất ấn tượng:*
> * * **Tốc độ tìm kiếm**: Cực nhanh, chỉ mất **45 mili-giây** (0.045 giây), mang lại phản hồi tức thì cho người dùng.*
> * * **Độ chuẩn xác**: Đạt **92.4%**, tức là trong 10 kết quả đầu tiên thì có hơn 9 kết quả trả về đúng nhu cầu.*
> * * **Khả năng chịu lỗi**: Kể cả khi người dùng gõ từ khóa không dấu, hoặc bản OCR bị sai 1–2 chữ cái do mực mờ, máy chủ tìm kiếm vẫn tìm ra chính xác tài liệu cần tìm.*
>
> *Khảo sát độ hài lòng của người dùng theo thang đo chuẩn **SUS** trên cán bộ và sinh viên đạt **82.5 / 100 điểm** – xếp hạng Mức độ sử dụng Xuất sắc."*

---

#### 🔹 [08:30 – 09:15] SLIDE 10: GIAO DIỆN VÀ TÍNH NĂNG NỔI BẬT (DEMO)
* **Hành động**: [Chuyển sang Slide 10]. Trình bày màn hình Dashboard và Live Editor 2 cửa sổ.
* **Lời thoại**:
> *"Về mặt ứng dụng thực tế, điểm tiện lợi nhất của DocuCTSV nằm ở giao diện quản lý trực quan và màn hình **đối soát 2 cửa sổ (Side-by-Side Live Editor)**:*
> * *Trên Bảng điều khiển, trạng thái hồ sơ được phân loại rõ ràng qua các thẻ tóm tắt và bảng dữ liệu trạng thái tiến độ.*
> * *Khi đối soát, màn hình chia làm đôi: bên trái là file gốc PDF hoặc ảnh chụp có thể phóng to thu nhỏ; bên phải là văn bản chữ do AI bóc tách.*
> * *Cán bộ chỉ cần quan sát đối chiếu và thao tác sửa lỗi trong vài giây; khi bấm Lưu, máy chủ tìm kiếm sẽ đồng bộ dữ liệu ngay lập tức.*
> * *Ngoài ra, khi tải lên lượng lớn hồ sơ, **thanh tiến độ tải hiển thị phần trăm theo thời gian thực** giúp người dùng dễ dàng theo dõi hệ thống đang xử lý đến đâu."*

---

### 🟢 PHẦN 5: BẢO MẬT, TỔNG KẾT & KẾT THÚC (09:15 – 10:00)

#### 🔹 [09:15 – 09:45] SLIDE 11: BẢO MẬT, TÍNH TOÀN VẸN VÀ PHÂN QUYỀN RBAC
* **Hành động**: [Chuyển sang Slide 11]. Nói dứt khoát về tính an toàn dữ liệu và tuân thủ quy định.
* **Lời thoại**:
> *"Về bảo mật và an toàn dữ liệu, hệ thống được trang bị 3 lớp bảo vệ:*
> * *1. **Mã băm SHA-256**: Mỗi file tải lên được gắn một 'dấu vân tay số'. Nếu file lưu trữ bị ai đó vào chỉnh sửa trái phép dù chỉ 1 chữ, hệ thống sẽ phát hiện và cảnh báo ngay.*
> * *2. **Xác thực Mã QR An toàn**: Tuân thủ Nghị định 13/2023 về bảo vệ dữ liệu cá nhân, trang web quét mã QR công khai chỉ hiển thị trạng thái hợp lệ và thông tin đã được che mờ (ví dụ `Nguyễn V*** A`), không làm lộ thông tin nhạy cảm của sinh viên ra ngoài.*
> * *3. **Phân quyền 3 vai trò (RBAC)**: Tách biệt rõ ràng quyền hạn giữa Quản trị viên (Admin), Cán bộ phòng ban (Staff) và Sinh viên (Student)."*

---

#### 🔹 [09:45 – 10:00] SLIDE 12 & TRANG CUỐI: TỔNG KẾT, HẠN CHẾ VÀ HƯỚNG PHÁT TRIỂN
* **Hành động**: [Chuyển sang Slide 12]. Nhìn thẳng Hội đồng, giọng khiêm tốn, tự tin và trang trọng.
* **Lời thoại**:
> *"Kính thưa Hội đồng, đề tài đã hoàn thành tốt các mục tiêu đề ra: Xây dựng trọn vẹn hệ thống số hóa DocuCTSV giúp tự động hóa 80% công việc nhập liệu văn bản in (93.8%), hỗ trợ đọc chữ viết tay (71.2%), tra cứu siêu tốc 45 mili-giây, có giao diện đối soát tiện lợi và đóng gói Docker sẵn sàng đưa vào sử dụng.*
>
> *Dù vậy, nhóm em thẳng thắn nhận định một số **hạn chế thực tế**:*
> * *Chữ viết tay quá nguệch ngoạc, mực mờ đứt đoạn hoặc bị con dấu đè lên vẫn còn tỷ lệ lỗi.*
> * *Bảng biểu không có đường kẻ khung viền cần thuật toán phân tích bố cục sâu hơn.*
>
> *Trong tương lai, nhóm sẽ nghiên cứu ứng dụng các mô hình **AI hiểu bố cục tài liệu (Document AI)**, tăng tốc độ xử lý trên máy tính thông thường và tích hợp chữ ký số.*
>
> *Nhóm chúng em xin gửi lời cảm ơn chân thành và sâu sắc nhất đến Thầy hướng dẫn ThS. Đặng Thế Nguyên cùng Quý Thầy/Cô trong Hội đồng đã lắng nghe. Kính mời Quý Thầy/Cô đặt câu hỏi và đóng góp ý kiến cho nhóm. Em xin trân trọng cảm ơn!"*

---

## 🎯 TOP 7 CÂU HỎI PHẢN BIỆN THƯỜNG GẶP & CÁCH TRẢ LỜI DỄ HIỂU

### ❓ Câu 1: *"Tại sao nhóm chọn VietOCR Transformer mà không dùng Tesseract, EasyOCR hay dịch vụ Cloud như Google Vision API?"*
* **Trả lời dễ hiểu**:
  > *"Dạ thưa Thầy/Cô, nhóm em đã thử nghiệm: Tesseract và EasyOCR đọc chữ tiếng Việt viết tay rất yếu (lỗi hơn 25%), hay bị sai dấu hỏi, ngã. Còn Google Vision API tuy đọc tốt nhưng phải có Internet, tốn tiền trả theo từng trang và có nguy cơ lộ thông tin hồ sơ nội bộ của trường.
  > VietOCR chạy offline hoàn toàn trên máy chủ của trường, không tốn thêm chi phí, hiểu ngữ cảnh tiếng Việt rất tốt và có thể huấn luyện thêm theo các mẫu đơn riêng của Trường Đại học Đà Lạt ạ."*

---

### ❓ Câu 2: *"Mô hình xử lý như thế nào khi gặp chữ viết tay bị dòng chấm `...........` đè lên hoặc nét bút bi bị mờ?"*
* **Trả lời dễ hiểu**:
  > *"Dạ thưa Thầy/Cô, nhóm em giải quyết bằng 2 bước xử lý ảnh:
  > 1. Dùng thuật toán lọc ảnh để xóa mờ các dải chấm in sẵn `...........` để không dính vào chữ.
  > 2. Dùng thuật toán CLAHE để tăng độ tương phản, làm đậm nét mực bút bi bị mờ, sau đó tự động phóng to dòng chữ lên trên 56 pixel để mô hình AI nhìn rõ nét chữ hơn ạ."*

---

### ❓ Câu 3: *"Khi OCR đọc chữ bị sai một vài từ, làm sao máy chủ tìm kiếm vẫn tìm ra được tài liệu?"*
* **Trả lời dễ hiểu**:
  > *"Dạ thưa Thầy/Cô, nhóm em giải quyết ở 2 tầng:
  > 1. Tầng OCR có 3 lớp tự động sửa lỗi chính tả và sửa các từ vựng hành chính quen thuộc.
  > 2. Tầng tìm kiếm Elasticsearch có tính năng 'Tìm kiếm mờ (Fuzzy Search)'. Khi người dùng tìm một từ, máy chủ cho phép sai lệch 1–2 ký tự gần giống. Nhờ vậy, kể cả khi bản OCR bị sai 1–2 chữ cái hoặc người dùng gõ không dấu, máy vẫn tìm đúng tài liệu trong 45 mili-giây ạ."*

---

### ❓ Câu 4: *"Làm thế nào để biết file PDF gốc lưu trong máy chủ có bị ai đó sửa đổi trộm hay không?"*
* **Trả lời dễ hiểu**:
  > *"Dạ thưa Thầy/Cô, khi nhận file tải lên, hệ thống tự động tạo ra một 'dấu vân tay số' (mã băm SHA-256) và lưu vào cơ sở dữ liệu. Mỗi khi ai đó tải file về hoặc quét mã QR xác thực, hệ thống sẽ kiểm tra lại dấu vân tay này. Nếu file bị chèn thêm trang, sửa chữ hay đổi dù chỉ 1 ký tự, dấu vân tay sẽ bị sai và hệ thống lập tức báo động ạ."*

---

### ❓ Câu 5: *"Phần trăm tiến độ OCR được tính toán như thế nào theo thời gian thực?"*
* **Trả lời dễ hiểu**:
  > *"Dạ thưa Thầy/Cô, trong lúc xử lý, máy chủ đếm tổng số trang và số dòng thực tế. Cứ mỗi khi làm xong một trang, chạy xong một lô dòng chữ hoặc bóc tách xong bảng, hệ thống sẽ tự cộng phần trăm từ 0% lên 100%. Giao diện Web tự động hỏi máy chủ mỗi 1–2 giây một lần để hiển thị thanh tiến độ chạy mượt mà cho người dùng thấy ạ."*

---

### ❓ Câu 6: *"Nếu trường tuyển sinh khóa mới (ví dụ K50, K51 với MSSV 24xxxxx, 25xxxxx), hệ thống có phải viết lại code không?"*
* **Trả lời dễ hiểu**:
  > *"Dạ thưa Thầy/Cô, hoàn toàn không cần sửa code ạ. Toàn bộ quy tắc nhận diện Mã sinh viên, tiền tố năm học đều được nhóm cấu hình trong file cài đặt môi trường (`.env`). Khi có khóa mới, quản trị viên chỉ cần gõ thêm số năm vào file cài đặt mà không cần lập trình lại hệ thống ạ."*

---

### ❓ Câu 7: *"Trong thực tế, tại sao OCR vẫn còn đọc sai một số từ và chữ viết tay? Hệ thống giải quyết bài toán ứng dụng thực tế ra sao?"*
* **Trả lời dễ hiểu**:
  > *"Dạ thưa Thầy/Cô, trong thực tế, chữ viết tay của mỗi người mỗi khác (có bạn viết đẹp, có bạn viết xấu, bút mờ đứt nét) và con dấu đỏ đè lên chữ là bài toán rất khó với mọi phần mềm đọc chữ hiện nay.
  > Nhóm em tiếp cận theo mô hình 'AI hỗ trợ con người':
  > 1. AI tự động làm 80% công việc nặng nhọc: đọc khung thô và lấy sẵn thông tin.
  > 2. Giao diện 2 cửa sổ Side-by-Side giúp cán bộ chỉ mất 5–10 giây nhìn và sửa lại những chữ AI đọc chưa đúng trước khi lưu.
  > 3. Máy chủ tìm kiếm có tính năng tìm kiếm mờ để không làm mất tài liệu.
  > Nhờ đó, hệ thống thực tế vẫn giúp giảm hơn 75% thời gian làm việc so với việc phải ngồi gõ tay toàn bộ ạ."*
