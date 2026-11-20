# KỊCH BẢN QUAY VIDEO DEMO HỆ THỐNG DOCUCTSV (4 – 5 PHÚT)
**Đồ án tốt nghiệp**: Hệ thống Số hóa và Trích xuất Thông tin Tài liệu Công tác Sinh viên bằng Mô hình OCR và Tìm kiếm Toàn văn (DocuCTSV)  
**Nhóm sinh viên thực hiện**: Ngô Công Thành – Phan Thành Phát – Lý Gia Bảo  
**Giảng viên hướng dẫn**: ThS. Đặng Thế Nguyên — Đại học Đà Lạt

---

## 🎬 TỔNG QUAN KỊCH BẢN QUAY

* **Thời lượng đề xuất**: **4 phút 30 giây – 5 phút** (chuẩn khung chiếu Hội đồng và nộp lưu trữ).
* **Độ phân giải quay**: Full HD (1920 × 1080) hoặc 2K, tỷ lệ 16:9, 60fps.
* **Chuẩn bị trước khi bấm máy**:
  1. Mở sẵn 2 trình duyệt hoặc 2 profile:
     - Profile 1 (Admin/Cán bộ): Đã đăng nhập tài khoản Cán bộ CTSV (`ctsv@dlu.edu.vn`).
     - Profile 2 (Sinh viên/Guest): Trình duyệt ẩn danh để test quét mã QR và phân quyền.
  2. Chuẩn bị sẵn 2 file mẫu trong thư mục màn hình:
     - File 1: *Đơn xin miễn giảm học phí / Đơn học bổng* có chữ viết tay và bảng biểu (ví dụ: `TB Hoc bong TA. Development 2026.pdf`).
     - File 2: *Thông báo / Kế hoạch hành chính* (nhiều trang, có số hiệu và ngày tháng).
  3. Đảm bảo Backend, Frontend, PostgreSQL, Supabase Storage và Elasticsearch đang chạy ổn định.

---

## ⏱️ BẢNG PHÂN BỔ THỜI GIAN THEO PHÂN CẢNH

| Phân cảnh | Mốc thời gian | Tên nội dung | Điểm nhấn kỹ thuật |
| :---: | :---: | :--- | :--- |
| **Cảnh 1** | `00:00 – 00:30` | Mở đầu & Đăng nhập phân quyền (RBAC) | Giới thiệu hệ thống, bảo mật JWT, 3 vai trò phân quyền. |
| **Cảnh 2** | `00:30 – 01:30` | Tải tài liệu & Giám sát tiến độ OCR nền | Upload kéo thả, thanh tiến độ Real-time, pipeline tiền xử lý ảnh. |
| **Cảnh 3** | `01:30 – 02:45` | Đối soát Side-by-Side & Bóc tách thực thể | Giao diện 2 cửa sổ, bóc tách bảng Markdown, chuẩn hóa Header Nghị định 30, Smart Fields. |
| **Cảnh 4** | `02:45 – 03:45` | Hệ sinh thái Tìm kiếm thông minh Elasticsearch | Full-text Search 45ms, Tìm kiếm mờ (Fuzzy), Lọc Facets, RRF Hybrid. |
| **Cảnh 5** | `03:45 – 04:30` | Trợ lý Hỏi đáp Quy chế CTSV (NLP FAQ) | Phân giải từ viết tắt `mghp`, `kkht`, trích xuất Điều/Khoản & Biểu mẫu. |
| **Cảnh 6** | `04:30 – 05:00` | Xác thực toàn vẹn SHA-256, Mã QR & Kết thúc | Chống giả mạo file gốc, che mờ PII Nghị định 13, lời chào kết. |

---

## 🎙️ KỊCH BẢN CHI TIẾT TỪNG PHÂN CẢNH (THAO TÁC + LỜI THOẠI)

---

### 🔹 PHÂN CẢNH 1: MỞ ĐẦU & ĐĂNG NHẬP PHÂN QUYỀN (00:00 – 00:30)

* **Thao tác màn hình**:
  - `00:00`: Quay màn hình Trang chủ / Trang Đăng nhập (`/login`) với giao diện thương hiệu ĐH Đà Lạt hiện đại.
  - `00:10`: Nhập tài khoản Cán bộ Phòng CTSV (`ctsv@dlu.edu.vn`), bấm **Đăng nhập**.
  - `00:20`: Chuyển mượt mà vào **Bảng điều khiển (Dashboard)**: Lướt chuột qua các thẻ thống kê tổng số văn bản, tỷ lệ hoàn tất OCR, biểu đồ phân loại hồ sơ.
* **Lời thoại thuyết minh (Voice-over)**:
  > *"Xin chào Quý Thầy/Cô và các bạn. Đây là video demo thực tế hệ thống số hóa và trích xuất thông tin tài liệu Công tác Sinh viên — DocuCTSV.*
  >
  > *Hệ thống áp dụng kiến trúc phân quyền RBAC 3 vai trò: Quản trị viên, Cán bộ CTSV và Sinh viên. Sau khi Cán bộ đăng nhập, bảng điều khiển trung tâm lập tức hiển thị bức tranh toàn cảnh về tiến độ số hóa, biểu đồ chất lượng hồ sơ và tình trạng phê duyệt theo thời gian thực."*

---

### 🔹 PHÂN CẢNH 2: TẢI TÀI LIỆU & GIÁM SÁT TIẾN ĐỘ OCR REAL-TIME (00:30 – 01:30)

* **Thao tác màn hình**:
  - `00:30`: Bấm vào menu **Tải lên văn bản** (`/upload`).
  - `00:40`: Kéo thả file PDF văn bản hành chính thực tế (ví dụ: `TB Hoc bong TA. Development 2026.pdf`) vào vùng upload. Chọn danh mục: *Học bổng*.
  - `00:55`: Bấm **Bắt đầu tải lên & Xử lý OCR**.
  - `01:05`: Màn hình chuyển sang danh sách văn bản. Chỉ con trỏ chuột vào dòng tài liệu vừa upload: **Thanh tiến độ OCR đang nhảy phần trăm theo thời gian thực** (từ `PENDING` $\rightarrow$ `PROCESSING 35%` $\rightarrow$ `75%` $\rightarrow$ `DONE 100%`).
* **Lời thoại thuyết minh (Voice-over)**:
  > *"Tại phân hệ tiếp nhận hồ sơ, cán bộ có thể kéo thả tài liệu dạng PDF hoặc ảnh chụp scan. Hệ thống hỗ trợ xử lý hàng loạt và chụp ảnh trực tiếp qua webcam.*
  >
  > *Ngay khi nạp tài liệu, tiến trình xử lý ngầm Async Worker tự động kích hoạt pipeline xử lý đa tầng: Tự động cân bằng độ tương phản, khử nghiêng trang giấy và đưa qua mô hình nhận dạng VietOCR. Thanh tiến độ hiển thị phần trăm trực quan giúp cán bộ nắm bắt chính xác khối lượng công việc máy đang thực hiện mà không làm gián đoạn các thao tác khác."*

---

### 🔹 PHÂN CẢNH 3: MÀN HÌNH ĐỐI SOÁT SIDE-BY-SIDE & BÓC TÁCH THỰC THỂ (01:30 – 02:45)

* **Thao tác màn hình**:
  - `01:30`: Bấm nút **Chi tiết** trên dòng tài liệu vừa xử lý xong để mở trang `/documents/:id`.
  - `01:40`: Giới thiệu bố cục **2 cửa sổ Side-by-Side**:
    - Bên trái: Bản scan tài liệu gốc phóng to / thu nhỏ linh hoạt.
    - Bên phải: Văn bản trích xuất đã chuẩn hóa.
  - `01:55`: Rê chuột làm nổi bật:
    - **Header 2 cột chuẩn Nghị định 30/2020**: Quốc hiệu - Tiêu ngữ, Tên trường, Số hiệu được khôi phục chuẩn (`Số: 1848/TB-ĐHĐL`).
    - **Trích yếu văn bản**: Dòng `V/v xét cấp học bổng của Công ty TNHH T.A Development...` được bảo toàn nguyên vẹn.
    - **Bảng biểu**: Dữ liệu trong bảng được bóc tách thẳng hàng chuẩn cú pháp Markdown.
  - `02:20`: Chuyển nhanh qua tab **Bóc tách Thông tin AI (Smart Fields)**:
    - Cho thấy các trường được trích xuất tự động: *Số hiệu, Loại văn bản, Ngày ban hành, Đơn vị đề xuất, Tóm tắt AI*.
  - `02:35`: Cán bộ thử gõ chỉnh sửa 1 từ trên Live Editor và bấm **Lưu thay đổi**. Hệ thống thông báo cập nhật thành công.
* **Lời thoại thuyết minh (Voice-over)**:
  > *"Điểm sáng đột phá của DocuCTSV là màn hình đối soát 2 cửa sổ Side-by-Side Live Editor.*
  >
  > *Phía bên trái là bản scan gốc chất lượng cao; phía bên phải là kết quả trích xuất được tự động chuẩn hóa qua 3 lớp: Sửa lỗi chính tả quang học, khôi phục nét chữ số viết tay bị nhận nhầm, và tái cấu trúc Header 2 cột theo đúng Nghị định 30/2020.*
  >
  > *Đặc biệt, hệ thống bảo toàn 100% các từ khóa doanh nghiệp, tiếng Anh và bảng biểu đa cột. Cán bộ chỉ mất vài giây nhìn đối chiếu và chỉnh sửa trực tiếp trên trình soạn thảo trước khi phê duyệt lưu trữ."*

---

### 🔹 PHÂN CẢNH 4: TÌM KIẾM TOÀN VĂN THÔNG MINH ELASTICSEARCH 8 (02:45 – 03:45)

* **Thao tác màn hình**:
  - `02:45`: Bấm vào menu **Tra cứu thông minh** (`/search`).
  - `02:55`: Gõ thử từ khóa có dấu: `"học bổng phát triển"` $\rightarrow$ Kết quả trả về ngay tức thì (< 50ms) với từ khóa được bôi vàng (Highlight).
  - `03:10`: Thử gõ từ khóa **viết sai lỗi chính tả / không dấu**: `"hoc bong devlopment"` (cố tình gõ thiếu chữ 'e') $\rightarrow$ **Elasticsearch Fuzzy Search** vẫn tìm ra chính xác công văn `TB Hoc bong TA. Development`.
  - `03:25`: Thử chọn bộ lọc bên tay trái: Lọc theo Danh mục (*Học bổng*), Trạng thái (*Đã duyệt*), Khoảng ngày tháng $\rightarrow$ Danh sách kết quả phản hồi mượt mà không bị tải lại trang.
* **Lời thoại thuyết minh (Voice-over)**:
  > *"Để giải quyết bài toán tra cứu trong hàng chục ngàn hồ sơ, hệ thống tích hợp máy chủ Elasticsearch 8 chuyên sâu cho tiếng Việt.*
  >
  > *Tốc độ truy vấn đạt mức ấn tượng chỉ 45 mili-giây. Nhờ thuật toán tìm kiếm mờ Fuzzy Search và phân tích hình thái từ, ngay cả khi người dùng gõ không dấu hoặc bản OCR gốc bị mờ sai sót 1 vài ký tự, máy chủ vẫn định vị chính xác tài liệu cần tìm. Các bộ lọc Facets theo phòng ban, thời gian và trạng thái giúp thu hẹp phạm vi tìm kiếm chỉ sau một cú nhấp chuột."*

---

### 🔹 PHÂN CẢNH 5: TRỢ LÝ HỎI ĐÁP QUY CHẾ CTSV BẰNG NGÔN NGỮ TỰ NHIÊN (03:45 – 04:30)

* **Thao tác màn hình**:
  - `03:45`: Tại trang Tìm kiếm, chuyển sang tab **Hỏi đáp Quy chế CTSV (FAQ AI)**.
  - `03:55`: Bấm vào một câu hỏi mẫu hoặc gõ câu hỏi bằng từ viết tắt của sinh viên:  
    `"mghp nd81 can nhung gi"`
  - `04:05`: Bấm **Hỏi đáp Quy chế**. Màn hình hiển thị câu trả lời:
    - Banner tím hiển thị phân giải viết tắt: `mghp nd81` $\rightarrow$ *Miễn giảm học phí Nghị định 81/2021/NĐ-CP*.
    - Trích dẫn Điều/Khoản quy định của ĐH Đà Lạt.
    - Tóm tắt hướng dẫn nộp hồ sơ tại Bộ phận Một cửa Nhà A11.
    - Nút tải trực tiếp **Biểu mẫu BM-02-MGHP (file PDF)**.
  - `04:20`: Thử gõ thêm một câu: `"kkht co duoc diem f khong"` $\rightarrow$ Trả về quy định học bổng khuyến khích học tập.
* **Lời thoại thuyết minh (Voice-over)**:
  > *"DocuCTSV còn đóng vai trò là một Trợ lý thông minh hỗ trợ sinh viên giải đáp quy chế đào tạo và chính sách học vụ.*
  >
  > *Được trang bị bộ từ điển hơn 45 từ viết tắt và tiếng lóng sinh viên như 'mghp', 'kkht', 'hoãn nvqs', hệ thống tự động phân giải ngữ nghĩa câu hỏi, trích dẫn chính xác Điều/Khoản quy định hiện hành và cung cấp trực tiếp đường link tải biểu mẫu hành chính, giúp sinh viên không còn phải mất thời gian đến hỏi trực tiếp tại phòng ban."*

---

### 🔹 PHÂN CẢNH 6: XÁC THỰC MÃ BĂM SHA-256, MÃ QR & KẾT THÚC (04:30 – 05:00)

* **Thao tác màn hình**:
  - `04:30`: Quay lại trang chi tiết văn bản, chuyển sang tab **Con dấu & Mã QR Xác thực**.
  - `04:38`: Rê chuột chỉ vào chuỗi **Mã băm SHA-256** của file gốc và hình ảnh Mã QR chống giả mạo.
  - `04:45`: Mở tab ẩn danh (hoặc dùng điện thoại quét mã QR) truy cập vào link xác thực công khai `/verify/:code`:
    - Trang hiển thị dấu tích xanh: **"Văn bản chính thức được phát hành bởi Trường Đại học Đà Lạt"**.
    - Các thông tin cá nhân của sinh viên được tự động **che mờ PII** theo Nghị định 13 (ví dụ: `Nguyễn V*** A`, MSSV: `221****`).
  - `04:55`: Quay lại trang chính, hiển thị màn hình Dashboard và fade out kết thúc video.
* **Lời thoại thuyết minh (Voice-over)**:
  > *"Về an toàn dữ liệu, mỗi văn bản tải lên được niêm phong bằng mã băm SHA-256, ngăn chặn tuyệt đối hành vi sửa đổi file gốc. Mã QR xác thực công khai tuân thủ nghiêm ngặt Nghị định 13 về bảo vệ dữ liệu cá nhân, tự động ẩn danh thông tin nhạy cảm của người học.*
  >
  > *DocuCTSV là giải pháp toàn diện, kết hợp chặt chẽ giữa Trí tuệ nhân tạo, Xử lý ảnh và Tìm kiếm thông minh, sẵn sàng đưa vào ứng dụng thực tế tại Trường Đại học Đà Lạt. Nhóm chúng em xin trân trọng cảm ơn!"*

---

## 💡 CHECKLIST KỸ THUẬT DÀNH CHO NGƯỜI QUAY VIDEO

1. **Phần mềm quay màn hình khuyến nghị**:
   - **OBS Studio** (Cài đặt: *Output Bitrate 8000 Kbps, 60 FPS, Canvas 1920x1080, thu âm Mic lọc tạp âm Noise Suppression*).
   - Hoặc **CapCut Desktop / Camtasia** nếu muốn chèn hiệu ứng zoom chuột và phụ đề tự động.
2. **Kỹ thuật rê chuột (Mouse Pointer)**:
   - Rê chuột chậm rãi, dứt khoát. Tránh lắc chuột vòng tròn hoặc giật cục.
   - Tại các điểm nhấn (Thanh tiến độ, nút Lưu, Mã QR, Kết quả tìm kiếm), giữ chuột đứng yên 1–2 giây để người xem kịp quan sát.
3. **Âm thanh (Voice-over)**:
   - Đọc với giọng điệu tự tin, nhịp điệu vừa phải (khoảng 130 – 140 từ/phút).
   - Nếu quay màn hình trước rồi lồng tiếng sau (thu âm riêng trên CapCut/Audacity), video sẽ mượt mà và không bị ngắc ngứ.
4. **Nhạc nền (BGM)**:
   - Chọn nhạc nền thể loại *Corporate Tech / Ambient Chill* âm lượng nhỏ (khoảng 10 – 15%), tôn giọng đọc chính lên 100%.
