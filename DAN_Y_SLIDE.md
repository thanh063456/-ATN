# DÀN Ý SLIDE BÁO CÁO TIẾN ĐỘ ĐỢT 2 — DocuCTSV
**Đề tài: Hệ thống Số hóa và Quản lý Tài liệu Công tác Sinh viên Ứng dụng OCR và Elasticsearch**

> **Tổng quan:** 15 slide | **Thời lượng trình bày:** 10–12 phút (~1.300 từ thuyết minh, tốc độ ~125 từ/phút) | **Ngôn ngữ:** Tiếng Việt học thuật, chuẩn mực kỹ thuật, căn cứ toàn diện trên số liệu thực nghiệm đã kiểm chứng


## SLIDE 1 — TRANG TIÊU ĐỀ

**Tiêu đề:** Báo cáo Tiến độ Đợt 2: Hệ thống DocuCTSV

**Nội dung trình bày:**
- 🏫 **Đơn vị:** Trường Đại học Đà Lạt – Khoa Công nghệ Thông tin – Lớp CTK46-PM
- 📋 **Tên đề tài:** Hệ thống Số hóa và Quản lý Tài liệu Công tác Sinh viên Ứng dụng OCR và Elasticsearch
- 👨‍💻 **Sinh viên thực hiện:**
  - Ngô Công Thành – MSSV: 2212461 *(Xử lý ảnh, Mô hình VietOCR & AI Hậu xử lý)*
  - Phan Thành Phát – MSSV: 2212436 *(Elasticsearch, Cơ sở dữ liệu & An toàn thông tin)*
  - Lý Gia Bảo – MSSV: 2213934 *(Mô hình TrOCR-Vi, Giao diện Web & Triển khai Docker)*
- 👨‍🏫 **Giảng viên hướng dẫn:** ThS. Nguyễn Trọng Hiếu | **Thời gian:** Học kỳ I – Năm học 2025–2026

**Gợi ý hình ảnh:** Logo Trường Đại học Đà Lạt + Giao diện hệ thống DocuCTSV hiển thị chức năng đối soát văn bản.

**Speaker notes (Thành mở đầu - ~65 từ):**
> Kính thưa Thầy hướng dẫn và Quý Thầy/Cô trong Hội đồng. Hôm nay, nhóm xin trình bày Báo cáo tiến độ lần 2 của đề tài DocuCTSV — Hệ thống số hóa và quản lý tài liệu Công tác sinh viên ứng dụng nhận dạng ký tự quang học và công cụ tìm kiếm toàn văn phân tán. Sau đợt 1, nhóm đã tập trung làm rõ cơ sở lý thuyết mô hình, tối ưu hóa công cụ tìm kiếm và giải quyết các bài toán kỹ thuật phát sinh từ dữ liệu thực tế nhà trường.

---

## SLIDE 2 — TÓM TẮT KẾT QUẢ ĐÃ ĐẠT ĐƯỢC TRONG ĐỢT 1

**Tiêu đề:** Tóm tắt Đợt 1 — Nền Tảng Kỹ Thuật Đã Xây Dựng

**Nội dung trình bày:**
- 📊 **Bộ dữ liệu nền tảng:** Thu thập và gán nhãn **13.125 mẫu dòng chữ** trích xuất từ tài liệu hành chính thực tế của Phòng Công tác Sinh viên (CTSV).
- 🤖 **VietOCR tinh chỉnh:** Đạt hệ số lỗi ký tự CER **0,028** và WER **0,052** trên tập kiểm thử văn bản in chuẩn hành chính.
- ⚙️ **Hạ tầng máy chủ:** FastAPI với hơn **25 API nghiệp vụ**, kết nối PostgreSQL 15, Elasticsearch 8.12.0 và Redis 7.
- 🌐 **Giao diện ** Web React 18 với trình sửa đối soát song song *(Side-by-Side Live Editor)*

**Gợi ý hình ảnh:** Sơ đồ khối module hệ thống đã hoàn thành từ Đợt 1

**Speaker notes (Bảo trình bày - ~70 từ):**
> Trong đợt 1, nhóm đã hoàn thiện khung kiến trúc tổng thể gồm 6 phân hệ cốt lõi: từ tập dữ liệu 13.125 mẫu dòng, tinh chỉnh mô hình VietOCR đạt CER 0,028 (tương đương 28 lỗi trên 1.000 ký tự), đến hệ thống backend FastAPI với hơn 25 API và giao diện web React 18 hỗ trợ đối soát trực tiếp. Toàn bộ hệ thống được đóng gói qua 4 container Docker. Đây là nền tảng vận hành ổn định để bước sang đợt 2, nhóm tập trung nâng cao khả năng xử lý các dạng tài liệu phức tạp hơn.

---

## SLIDE 3 — TIẾN ĐỘ TỔNG THỂ ĐỢT 2

**Tiêu đề:** Tiến độ Đợt 2 — Các Công Việc Đã Thực Hiện

**Nội dung trình bày:**

| STT | Hạng mục công việc | Nội dung công việc thực hiện 
|:---:|:---|:---|:---:|
| **1** | **Nhận dạng văn bản in** | Nâng cao chất lượng đọc văn bản in; khắc phục lỗi mất dấu tiếng Việt ở các chữ cỡ nhỏ 
| **2** | **Nhận dạng chữ viết tay** | Mở rộng đọc chữ viết tay trên đơn từ của sinh viên; xử lý đọc trọn vẹn các dòng tiêu đề dài 
| **3** | **Xử lý văn bản sau khi đọc** | Tự động sửa lỗi tiêu đề; tự trích xuất thông tin hồ sơ (MSSV, Ngày, Số hiệu); cảnh báo chỗ nghi ngờ 
| **4** | **Phân loại văn bản tự động** | Tự động nhận biết loại hồ sơ (Quyết định, Đơn từ, Thông báo...) để xếp vào đúng sổ quản lý 
| **5** | **Nâng cấp tìm kiếm hồ sơ** | Tìm kiếm thông minh theo ý nghĩa câu từ; tự động lọc theo diện chính sách; ẩn thông tin cá nhân 
| **6** | **An toàn dữ liệu & Hệ thống** | Bổ sung thêm dữ liệu mẫu; củng cố bảo mật hệ thống và ngăn chặn xem dữ liệu trái phép 



**Gợi ý hình ảnh:** Sơ đồ 6 khối tính năng nghiệp vụ  (Workflow diagram).

**Speaker notes (Phát trình bày - ~80 từ):**
> Kính thưa Quý Thầy/Cô, trong Đợt 2, nhóm đã tập trung hoàn thành 6 nhiệm vụ trọng tâm: nâng cao chất lượng nhận dạng văn bản in rõ nét hơn; mở rộng thêm khả năng đọc chữ viết tay trên các lá đơn sinh viên; tự động bóc tách thông tin hồ sơ như mã sinh viên, ngày ký và cảnh báo chỗ nghi ngờ; tự động phân loại hồ sơ vào đúng sổ quản lý; nâng cấp tìm kiếm thông minh theo ý nghĩa câu từ kết hợp bảo vệ dữ liệu cá nhân; và hoàn thiện bảo mật cho toàn hệ thống.

---

## SLIDE 4 — CƠ SỞ LÝ THUYẾT #1: HAI MÔ HÌNH OCR CỐT LÕI (VIETOCR VÀ TROCR)

**Tiêu đề:** Cơ Sở Lý Thuyết #1 — Hai Mô Hình OCR Cốt Lõi: VietOCR & TrOCR

**Nội dung trình bày:**
- 📌 **1. Mô hình VietOCR (Vietnamese OCR):**
  - **Khái niệm:** Là mô hình nhận dạng văn bản được phát triển nhằm hỗ trợ nhận dạng chữ viết, đặc biệt là tiếng Việt, từ hình ảnh. Mô hình sử dụng kiến trúc Encoder–Decoder kết hợp CNN và Transformer.
  - **Kiến trúc mô hình (Hai thành phần chính):**
    - **Encoder (Bộ mã hóa):** Sử dụng CNN để trích xuất đặc trưng hình ảnh từ vùng chứa văn bản. Các đặc trưng hình ảnh được chuyển thành biểu diễn đặc trưng phục vụ nhận dạng.
    - **Decoder (Bộ giải mã):** Sử dụng Transformer để dự đoán chuỗi ký tự tương ứng với nội dung hình ảnh.
- 📌 **2. Mô hình TrOCR (Transformer-based Optical Character Recognition):**
  - **Khái niệm:** Là mô hình OCR do Microsoft nghiên cứu và phát triển. TrOCR sử dụng kiến trúc Transformer cho cả hai nhiệm vụ: phân tích hình ảnh và sinh chuỗi văn bản. Khác với nhiều mô hình OCR truyền thống sử dụng CNN kết hợp RNN, TrOCR sử dụng Image Transformer làm bộ mã hóa và Text Transformer làm bộ giải mã.
  - **Kiến trúc mô hình (Hai thành phần chính):**
    - **Image Encoder (Vision Transformer – ViT):** Chia ảnh đầu vào thành các vùng nhỏ *(patch)*, chuyển đổi chúng thành vector đặc trưng và sử dụng cơ chế Self-Attention để học mối quan hệ giữa các vùng ảnh.
    - **Text Decoder (Transformer):** Nhận các đặc trưng hình ảnh từ Encoder, sau đó dự đoán lần lượt các token để tạo thành chuỗi văn bản hoàn chỉnh.

**Gợi ý hình ảnh:** Sơ đồ luồng Encoder – Decoder của VietOCR và TrOCR đặt song song đối chiếu.

**Speaker notes (Thành trình bày - ~85 từ):**
> Kính thưa Hội đồng, cơ sở lý thuyết nhận dạng ký tự của hệ thống dựa trên hai mô hình cốt lõi:
> Thứ nhất là VietOCR, mô hình chuyên biệt cho tiếng Việt sử dụng kiến trúc Encoder-Decoder lai ghép: khối CNN đảm nhận việc bóc tách đặc trưng ảnh từ vùng văn bản, và khối Transformer đảm nhận việc giải mã thành chuỗi ký tự tương ứng.
> Thứ hai là TrOCR của Microsoft, mô hình đột phá khi loại bỏ hoàn toàn CNN truyền thống và ứng dụng thuần Transformer: khối Image Transformer chia ảnh thành các mảnh patch để nắm bắt toàn diện mối quan hệ không gian, kết hợp cùng khối Text Transformer để dự đoán lần lượt các token nhằm tạo thành chuỗi văn bản hoàn chỉnh.

---

## SLIDE 5 — CƠ SỞ LÝ THUYẾT #2: QUY TRÌNH HOẠT ĐỘNG CỦA MÔ HÌNH VIETOCR

**Tiêu đề:** Cơ Sở Lý Thuyết #2 — Quy Trình Nhận Dạng Văn Bản In Của VietOCR

**Nội dung trình bày:**
- 1️⃣ **Bước 1 — Tiếp nhận đầu vào:** Cắt tách từng dòng văn bản in từ tài liệu hành chính (Quyết định, Công văn, Thông báo).
- 2️⃣ **Bước 2 — Tiền xử lý ảnh:**
  - Chuẩn hóa ảnh về chiều cao thống nhất; tự động phóng lớn các dòng chữ nhỏ để làm rõ dấu thanh tiếng Việt.
  - Giữ nguyên độ tương phản tự nhiên của bản quét, tránh dùng bộ lọc gây nhòe hoặc đứt gãy nét chữ.
- 3️⃣ **Bước 3 — Trích xuất đặc trưng hình ảnh:**
  - Bộ mã hóa mạng tích chập quét ảnh từ trái sang phải, chuyển đổi nét chữ thành chuỗi đặc trưng thị giác cô đọng.
- 4️⃣ **Bước 4 — Dự đoán ký tự theo ngữ cảnh:**
  - Bộ giải mã sử dụng cơ chế tập trung để hướng mắt nhìn vào đúng vị trí nét chữ tương ứng, kết hợp ngữ cảnh câu từ để đoán đúng từng ký tự tiếng Việt.
- 5️⃣ **Bước 5 — Kết xuất văn bản:** Xuất ra dòng văn bản hoàn chỉnh với độ chính xác cao và thời gian phản hồi tức thì.

**Gợi ý hình ảnh:** Sơ đồ quy trình 5 bước liền mạch: Ảnh dòng chữ ➔ Tiền xử lý phóng lớn nét ➔ Bộ mã hóa bóc tách nét ➔ Bộ giải mã đoán chữ ➔ Dòng chữ hoàn chỉnh.

**Speaker notes (Thành trình bày - ~85 từ):**
> Kính thưa Hội đồng, quy trình nhận dạng văn bản in của VietOCR diễn ra qua 5 bước liền mạch: Bước đầu tiên, hệ thống tiếp nhận ảnh của từng dòng chữ in hành chính. Ở bước tiền xử lý, ảnh được đưa về chiều cao chuẩn và tự động phóng lớn các dòng chữ nhỏ để nhận diện rõ dấu thanh tiếng Việt mà không làm biến dạng nét. Tiếp theo, bộ mã hóa quét dòng chữ từ trái sang phải để bóc tách các đặc trưng nét chữ. Sau đó, bộ giải mã hướng sự chú ý vào đúng vị trí nét ảnh để nhận dạng chuẩn xác từng ký tự theo ngữ cảnh câu từ. Cuối cùng, hệ thống xuất ra dòng văn bản hoàn chỉnh gần như tức thì.

---

## SLIDE 6 — CƠ SỞ LÝ THUYẾT #3: QUY TRÌNH HOẠT ĐỘNG CỦA MÔ HÌNH TROCR

**Tiêu đề:** Cơ Sở Lý Thuyết #3 — Quy Trình Nhận Dạng Chữ Viết Tay & Dòng Dài Của TrOCR

**Nội dung trình bày:**
- 1️⃣ **Bước 1 — Tiếp nhận đầu vào:** Tiếp nhận hình ảnh chứa chữ viết tay của sinh viên trên các lá đơn từ hoặc các dòng tiêu đề dài.
- 2️⃣ **Bước 2 — Tiền xử lý & Chia dòng thông minh:**
  - Đưa ảnh về kích thước chuẩn dạng lưới vuông.
  - Với các dòng chữ quá dài: Tự động tìm khoảng trống tự nhiên giữa hai từ để tách đôi dòng ảnh an toàn, tuyệt đối không cắt ngang giữa từ ngữ.
- 3️⃣ **Bước 3 — Phân tích không gian đa chiều:**
  - Bộ mã hóa thị giác chia ảnh thành nhiều mảnh nhỏ và quan sát đồng thời mối tương quan không gian đa hướng, giúp nắm bắt trọn vẹn nét chữ viết tay nghiêng ngả, uốn lượn.
- 4️⃣ **Bước 4 — Dự đoán từ ngữ theo ngữ cảnh:**
  - Bộ giải mã ngôn ngữ tiếng Việt tiếp nhận đặc trưng ảnh và dự đoán lần lượt từng từ theo ngữ cảnh câu văn; mở rộng độ dài câu đọc giúp tránh hoàn toàn hiện tượng mất đuôi chữ.
- 5️⃣ **Bước 5 — Ghép nối & Kết xuất văn bản:**
  - Ghép các nửa dòng lại thành câu văn hoàn chỉnh; xử lý nhanh chóng và triệt tiêu tình trạng cụt chữ ở cuối dòng.

**Gợi ý hình ảnh:** Sơ đồ quy trình 5 bước: Ảnh chữ viết tay/dòng dài ➔ Chia dòng tại khoảng trắng ➔ Bộ mã hóa mảnh ảnh đa hướng ➔ Bộ giải mã ngôn ngữ ➔ Văn bản hoàn chỉnh.

**Speaker notes (Bảo trình bày - ~85 từ):**
> Kính thưa Hội đồng, quy trình nhận dạng chữ viết tay của mô hình TrOCR cũng gồm 5 bước chặt chẽ: Trước tiên, mô hình tiếp nhận ảnh chữ viết tay trên đơn từ hoặc dòng tiêu đề dài. Bước hai, với các dòng quá dài, thuật toán sẽ tự động tìm khoảng trắng giữa hai từ để chia đôi ảnh an toàn mà không làm đứt đôi chữ. Bước ba, bộ mã hóa thị giác chia nhỏ ảnh và quan sát đa hướng để hiểu trọn vẹn nét chữ uốn lượn tự do. Bước bốn, bộ giải mã ngôn ngữ tiếng Việt tiếp nhận thông tin và dự đoán từng từ theo mạch câu văn, cho phép đọc trọn vẹn câu dài. Cuối cùng, hệ thống ghép nối các nửa dòng lại thành chuỗi văn bản hoàn chỉnh và liền mạch.

---

## SLIDE 7 — CƠ SỞ LÝ THUYẾT #4: KIẾN TRÚC PHÂN TÁN & CƠ CHẾ CHỈ MỤC ĐẢO CỦA ELASTICSEARCH

**Tiêu đề:** Cơ Sở Lý Thuyết #4 — Kiến Trúc Phân Tán & Cơ Chế Chỉ Mục Đảo Của Elasticsearch

**Nội dung trình bày:**
- 💡 **Bản chất hệ thống:**
  - Là công cụ tìm kiếm và phân tích phân tán theo thời gian gần thực (*Near Real-Time — phản hồi gần như tức thì*), vận hành trên nền tảng thư viện mã nguồn mở Apache Lucene.
  - Lưu trữ dữ liệu dạng tài liệu điện tử có cấu trúc (*JSON*), cho phép gửi và nhận yêu cầu qua giao thức mạng tiêu chuẩn (*RESTful API*).
- 🏗️ **Kiến trúc phân tán chịu lỗi cao:**
  - **Cụm máy chủ (*Cluster*):** Mạng lưới các máy chủ (*Nodes*) cùng tham gia lưu trữ và tính toán; quản lý bởi máy chủ điều phối (*Master Node*) và các máy chủ lưu dữ liệu (*Data Nodes*).
  - **Phân mảnh dữ liệu (*Shards*):** Kho tài liệu được chia thành các mảnh chính (*Primary Shards*) để tìm kiếm song song; các mảnh bản sao (*Replica Shards*) hỗ trợ chịu lỗi khi có sự cố và tăng tốc độ đọc.
- 📚 **Cấu trúc dữ liệu cốt lõi — Chỉ mục đảo (*Inverted Index*):**
  - **Bản chất:** Khác với **Chỉ mục thuận (*Forward Index*)** lưu `Tài liệu ➔ Danh sách từ` hoặc **Quét toàn bộ bảng (*Full Table Scan*)** rất chậm trong SQL.
  - **Cơ chế:** Đảo ngược mối quan hệ — hệ thống tách nhỏ văn bản thành các từ tố chuẩn hóa (**`Terms`**) trong từ điển (*Term Dictionary*), mỗi từ trỏ trực tiếp đến một danh sách (**`Posting List`**) chứa ID các tài liệu có từ đó kèm tần suất (**`Term Frequency`**) và vị trí (**`Positions`**).
  - *Ví dụ trực quan:* `Term: "học bổng"` ➔ `Posting List: [Doc 1, Doc 4, Doc 9]`.
  - **Ưu điểm:** Định vị chính xác các tài liệu phù hợp tức thì trong thời gian $O(1)$ hoặc $O(\log N)$ mà không cần đọc duyệt toàn bộ kho dữ liệu.


**Speaker notes (Phát trình bày - ~80 từ):**
> Kính thưa Quý Thầy/Cô, để tìm kiếm nhanh chóng trong kho văn bản lớn, hệ thống sử dụng công nghệ tìm kiếm phân tán Elasticsearch. Dữ liệu tài liệu được chia thành nhiều mảnh nhỏ độc lập giúp các máy chủ có thể xử lý song song và tự động sao lưu dự phòng. Điểm cốt lõi mang lại tốc độ vượt trội là cấu trúc "Chỉ mục đảo" — hoạt động tương tự như bảng tra từ ở cuối sách: thay vì phải đọc quét từng trang tài liệu từ đầu đến cuối, hệ thống trích xuất sẵn từng từ khóa và trỏ ngay đến danh sách hồ sơ chứa từ đó, giúp trả về kết quả tìm kiếm trong tích tắc.

---

## SLIDE 8 — CƠ SỞ LÝ THUYẾT #5: CƠ CHẾ PHÂN TÍCH TIẾNG VIỆT & XẾP HẠNG CỦA ELASTICSEARCH

**Tiêu đề:** Cơ Sở Lý Thuyết #5 — Bộ Phân Tích Tiếng Việt & Thuật Toán Xếp Hạng Của Elasticsearch

**Nội dung trình bày:**
- ⚙️ **1. Bộ phân tích tiếng Việt trong Elasticsearch (*Custom Analyzer*):**
  - **Bản chất:** Quy trình làm sạch, tách từ và lọc từ ngữ nằm ngay trong lõi Elasticsearch trước khi nạp vào Chỉ mục đảo (*Inverted Index*).
  - **Tác dụng thực tế cho đề tài DocuCTSV:**
    - *Tìm kiếm không dấu:* Bộ lọc `asciifolding` giúp người dùng gõ không dấu (*"hoc bong", "mien giam"*) Elasticsearch vẫn tìm thấy tài liệu gốc.
    - *Hiểu từ viết tắt nhà trường:* Bộ lọc `synonym_graph` cấu hình riêng từ điển CTSV, giúp máy tự hiểu các từ viết tắt (*ĐHĐL $\leftrightarrow$ Đại học Đà Lạt*, *CTSV $\leftrightarrow$ Công tác Sinh viên*, *MGHP $\leftrightarrow$ Miễn giảm học phí*).
- 🎯 **2. Thuật toán chấm điểm & Xếp hạng của Elasticsearch (*BM25 & Vector*):**
  - **Bản chất:** Cơ chế tự động tính điểm liên quan (**`_score`**) trong Elasticsearch để sắp xếp kết quả (khác với SQL chỉ trả về danh sách lộn xộn).
  - **Tác dụng thực tế cho đề tài DocuCTSV:**
    - *Đưa hồ sơ đúng nhất lên vị trí số 1:* Thuật toán **Okapi BM25** ưu tiên các từ khóa mang tính định danh cao (Mã số sinh viên, Số hiệu công văn) và bài viết ngắn đúng trọng tâm.
    - *Khắc phục lỗi OCR & Tìm theo ý nghĩa:* Cơ chế **Vector ngữ nghĩa** giúp tìm trúng hồ sơ kể cả khi văn bản scan bị OCR nhận diện nhầm dấu hoặc người dùng dùng từ đồng nghĩa (*"tiền hỗ trợ"* $\rightarrow$ tìm ra *"trợ cấp xã hội"*).
- 💡 **Giá trị cho đề tài:** Giúp Elasticsearch hiểu sâu sắc văn bản hành chính đặc thù của Trường ĐH Đà Lạt; phản hồi tìm kiếm siêu tốc **dưới 45 mili-giây**.

**Gợi ý hình ảnh:** Sơ đồ 2 module lõi trong Elasticsearch: [Custom Analyzer xử lý từ viết tắt CTSV] ➔ [Bộ chấm điểm BM25 + Vector xếp hạng hồ sơ số 1].

**Speaker notes (Phát trình bày - ~85 từ):**
> Kính thưa Quý Thầy/Cô, hai cơ chế này đóng vai trò như "bộ não" thông minh của Elasticsearch trong đề tài: Thứ nhất là bộ phân tích tiếng Việt Custom Analyzer được cấu hình trực tiếp trong Elasticsearch để tự động hiểu các từ viết tắt chuyên biệt của trường như ĐHĐL, Miễn giảm học phí và hỗ trợ tìm kiếm không dấu. Thứ hai là thuật toán chấm điểm BM25 kết hợp Vector trong Elasticsearch, giúp tự động tính điểm độ liên quan để đưa hồ sơ chính xác nhất lên vị trí số 1, đồng thời khắc phục các lỗi sai dấu phát sinh sau bước nhận dạng OCR.

---

## SLIDE 9 — TRỌNG TÂM 1: HOÀN THIỆN MÔ HÌNH VIETOCR (VĂN BẢN IN CHUẨN)

**Tiêu đề:** Trọng tâm 1 — Hoàn Thiện Mô Hình VietOCR: Nhận Dạng Văn Bản In Chuẩn

**Nội dung trình bày:**
-  **Phạm vi xử lý thực tế trong hệ thống:**
  - Nhận dạng các dòng chữ in trong văn bản hành chính thông dụng của trường (*Quyết định, Công văn, Thông báo*).
  - Phù hợp với các dòng chữ in thẳng hàng, phông chữ hành chính rõ nét.
  -  *Giới hạn hiện tại:* Chưa hỗ trợ nhận dạng và bảo toàn cấu trúc bảng biểu phức tạp (đang trong quá trình nghiên cứu).
-  **Cải tiến chuỗi xử lý so với Đợt 1:**
  - *Hạn chế ở Đợt 1:* Dòng chữ in cỡ nhỏ dễ bị mất dấu thanh tiếng Việt; việc áp dụng bộ lọc làm nét toàn trang gây quầng sáng làm biến dạng nét chữ in.
  - *Cải tiến ở Đợt 2:* Giữ nguyên độ tương phản tự nhiên của tài liệu scan; tự động phát hiện và phóng to *(upscale)* các dòng chữ có chiều cao dưới 32 pixel để làm rõ nét dấu thanh.


**Gợi ý hình ảnh:** Sơ đồ quy trình upscale chọn lọc dòng thấp < 32px 

**Speaker notes (Thành trình bày - ~85 từ):**
> Kính thưa Hội đồng, ở Trọng tâm thứ nhất, nhóm tập trung hoàn thiện mô hình VietOCR để nhận dạng các dòng văn bản in chuẩn hành chính như quyết định, thông báo. Nhóm xin lưu ý hiện tại hệ thống chỉ nhận dạng dòng in thông thường, chưa hỗ trợ nhận dạng cấu trúc bảng biểu. So với đợt 1, khi các dòng chữ nhỏ dễ mất dấu thanh và ảnh dễ bị vỡ nét do bộ lọc toàn trang, nhóm đã cải tiến bằng cách giữ nguyên tương phản gốc và chỉ phóng to các dòng thấp dưới 32 pixel. Đánh giá trên tập kiểm thử test.tsv gồm 244 dòng in chuẩn, mô hình đạt hệ số lỗi ký tự CER 0,028 với tốc độ khoảng 0,08 giây mỗi dòng.

---

## SLIDE 10 — TRỌNG TÂM 2: TÍCH HỢP TROCR-VI (CHỮ VIẾT TAY & KHẮC PHỤC CỤT CHỮ)

**Tiêu đề:** Trọng tâm 2 — Tích Hợp TrOCR-Vi: Nhận Dạng Chữ Viết Tay & Khắc Phục Lỗi Cụt Dòng

**Bố cục trực quan:** Chia 2 vế (Trái – Phải) đồng bộ 100% với cấu trúc Slide 9:

- **CỘT TRÁI (3 khối thông tin nghiệp vụ & giải pháp kỹ thuật theo trục dọc):**
  - 🔹 **Khối 1: Phạm vi xử lý thực tế & Giới hạn hiện tại**
    - Nhận dạng chữ viết tay tự do của sinh viên trên các *Đơn xin nghỉ học, Đơn cứu xét, Giấy xác nhận điền tay*.
    - *Giới hạn hiện tại:* Khác với văn bản in, mô hình TrOCR xử lý ảnh 2 chiều bằng Vision Transformer nên yêu cầu tài nguyên tính toán GPU cao hơn.
  - 🔻 **Khối 2 (Màu hồng nhạt): Hạn chế ban đầu (Đợt 1 & Thử nghiệm đầu Đợt 2)**
    - Đợt 1 hệ thống hoàn toàn chưa có TrOCR (chưa hỗ trợ nhận dạng chữ viết tay).
    - Khi mới tích hợp TrOCR với cấu hình mặc định (giới hạn 64 tokens), các dòng chữ dài hoặc tiêu đề thường xuyên bị cắt cụt đuôi chữ (tỷ lệ cụt dòng ban đầu lên tới **13,04%**).
  - 🟢 **Khối 3 (Màu xanh lam nhạt): Giải pháp cải tiến ở Đợt 2**
    - **Chia dòng thông minh:** Tự động phát hiện khoảng trống tự nhiên giữa hai từ ở giữa dòng để chia đôi ảnh an toàn mà không làm đứt nét chữ (kế thừa bước B2 - Slide 6).
    - **Mở rộng chuỗi giải mã:** Nâng giới hạn giải mã từ 64 lên 128 tokens để đọc trọn vẹn câu dài không bị mất phần đuôi (kế thừa bước B4 - Slide 6).
    - **Tối ưu suy luận GPU:** Chạy mô hình ở chế độ số thực bán chính xác 16-bit (GPU FP16) giúp tăng tốc độ phản hồi.

- **CỘT PHẢI (Khối số liệu đo lường thực nghiệm nổi bật):**
  - **Dòng trên cùng:** KIỂM THỬ TRÊN TẬP 32 TRANG HỖN HỢP ĐỘC LẬP *(HELD-OUT)*
  - **Con số lớn trung tâm:** **0,0053**
  - **Dòng giải thích:** Tỷ lệ cụt dòng (Truncation Rate) — giảm từ **13,04%** xuống **0,53%**  
    *(🟢 Khắc phục triệt để lỗi mất chữ, giảm gần 25 lần lỗi cụt dòng)*
  - *Đường kẻ ngang phân cách*
  - **Dòng dưới cùng:** **Tối ưu GPU FP16:** Tốc độ xử lý nhanh hơn **3,5 lần** *(rút ngắn thời gian xử lý từ ~96,6s xuống chỉ còn ~27,9 giây/trang)*.

**Gợi ý hình ảnh:** Sơ đồ minh họa thuật toán chia đôi ảnh tại khoảng trắng giữa hai từ (Smart Split) kết hợp hộp số liệu thực nghiệm.

**Speaker notes (Bảo trình bày - ~95 từ):**
> Kính thưa Hội đồng, ở Trọng tâm thứ hai, nhóm giải quyết bài toán nhận dạng chữ viết tay của sinh viên trên các lá đơn từ:
> Ở Đợt 1, hệ thống hoàn toàn chưa có mô hình đọc chữ viết tay. Sang Đợt 2, nhóm tích hợp mô hình TrOCR-Vi ứng dụng Vision Transformer để nắm bắt nét chữ uốn lượn hai chiều. Tuy nhiên, giới hạn mặc định 64 tokens khiến các dòng dài bị cụt đuôi với tỷ lệ lên tới 13,04%. 
> Để khắc phục triệt để, nhóm đã cài đặt thuật toán chia dòng thông minh tại khoảng trắng tự nhiên và nâng gấp đôi giới hạn giải mã lên 128 tokens, kết hợp tối ưu suy luận bán chính xác GPU FP16. Đánh giá trên 32 trang tài liệu kiểm thử độc lập, tỷ lệ cụt dòng giảm ngoạn mục từ 13,04% xuống chỉ còn 0,53% — tức giảm gần 25 lần lỗi mất chữ, đồng thời tốc độ xử lý nhanh hơn 3,5 lần.

---

## SLIDE 11 — TRỌNG TÂM 3: HẬU XỬ LÝ VĂN BẢN SAU OCR

**Tiêu đề:** Trọng tâm 3 — Chuỗi Hậu Xử Lý: Chuẩn Hóa Hành Chính & Bóc Tách Dữ Liệu

**Nội dung trình bày:**
-  **Mục tiêu:** Chuyển đổi văn bản OCR thô thành dữ liệu có cấu trúc phục vụ lưu trữ và tra cứu.
-  **Pipeline 3 tầng hậu xử lý:**
  - **Tầng 1 — Chuẩn hóa ký tự & Tiêu đề:** Sửa lỗi quang học (`l` $\leftrightarrow$ `1`, `O` $\leftrightarrow$ `0`, `rn` $\leftrightarrow$ `m`), chuẩn hóa Quốc hiệu / Tiêu ngữ / Tên cơ quan theo mẫu hành chính chuẩn.
  - **Tầng 2 — Bóc tách thực thể & Nối đoạn:**
    - Trích xuất tự động: **MSSV** (độ chính xác **0,982**), Số hiệu văn bản, Ngày ký, Họ tên, Lớp.
    - Hợp nhất đoạn văn ngắt quãng, bảo toàn bố cục tiêu đề 2 cột chuẩn Nghị định 30.
  - **Tầng 3 — Kiểm soát chất lượng (Human-in-the-loop):** Tính điểm tin cậy (*Confidence Score*); tự động gắn cờ ⚠️ **"Cần kiểm tra"** cho dòng có điểm $< 0,60$ để cán bộ rà soát nhanh.
-  **Hiệu quả:** Phản hồi tức thì ($< 15\text{ ms}$); giảm hơn **$85\%$ công sức nhập liệu** thủ công.

**Gợi ý hình ảnh:** Sơ đồ Pipeline 3 tầng: [OCR thô] ➔ [Chuẩn hóa Header] ➔ [Bóc tách Regex (MSSV, Số, Ngày)] ➔ [Cảnh báo Confidence < 0,60].

**Speaker notes (Thành trình bày - ~75 từ):**
> Kính thưa Hội đồng, để biến văn bản OCR thô thành dữ liệu có cấu trúc, nhóm xây dựng chuỗi hậu xử lý 3 tầng: Tầng 1 sửa lỗi quang học và chuẩn hóa Quốc hiệu, Tiêu ngữ. Tầng 2 tự động bóc tách các trường dữ liệu then chốt như Mã số sinh viên với độ chính xác 98,2%, Số hiệu và Ngày ký, đồng thời tự động nối liền các đoạn văn. Tầng 3 đánh giá điểm tin cậy cho từng dòng chữ và gắn cờ cảnh báo dưới 0,60 để cán bộ đối soát nhanh, giúp giảm hơn 85% thời gian nhập liệu thủ công.

---

## SLIDE 12 — TRỌNG TÂM 4: AI PHÂN LOẠI VĂN BẢN (DOCTYPE) & GÁN NHÃN TỰ ĐỘNG

**Tiêu đề:** Trọng tâm 4 — Tự Động Phân Loại Văn Bản & Gán Nhãn Siêu Dữ Liệu

**Nội dung trình bày:**
- ❓ **Mục đích:** Tự động nhận diện 6 nhóm tài liệu CTSV (*Quyết định, Thông báo, Đơn từ, Danh sách, Công văn, Khác*) để phân luồng xử lý và lưu trữ, loại bỏ thao tác phân loại thủ công.
- ⚡ **Quy trình xử lý 2 pha tối ưu thời gian *(Two-Stage Scope Policy)*:**
  - **Pha 1 (Văn bản điện tử có sẵn chữ):** Bóc tách trực tiếp trang đầu qua *PyMuPDF (không cần OCR)*, phản hồi cực nhanh trong **11,57 mili-giây** *(thời gian trung vị P50)*.
  - **Pha 2 (Tài liệu quét ảnh giấy):** Chỉ chạy OCR duy nhất trang bìa trong **850 mili-giây** *(P50)* để trả về loại văn bản ngay cho người dùng; các trang sau được đưa vào hàng đợi xử lý nền.
- 🔍 **Cơ chế phân loại đa tín hiệu *(Multi-signal Scoring)*:**
  - Kết hợp đồng thời 4 dấu hiệu nhận biết: Hậu tố số hiệu *(ví dụ: `/QĐ-`, `/TB-`)*, Tiêu đề chữ hoa kết hợp *so khớp mờ*, Cấu trúc đặc thù *(ví dụ: "Kính gửi" + "Đơn xin")* và từ khóa nội dung.
- 🏷️ **Tự động sinh siêu dữ liệu & Kiểm toán an toàn:**
  - **Gán nhãn tự động:** Trích xuất 5 trường then chốt: Số hiệu, Đơn vị ban hành, Loại văn bản, Trích yếu nội dung và Ngày ký.
  - **Nhật ký kiểm toán *(Audit Log)*:** Cho phép cán bộ điều chỉnh bằng tay khi cần và tự động lưu vết lịch sử thao tác để đảm bảo an toàn nghiệp vụ.
- 💡 **Lợi ích:** Người dùng nhận kết quả tức thì trong tích tắc; hệ thống tự động định tuyến hồ sơ vào đúng sổ quản lý chuyên biệt.

**Gợi ý hình ảnh:** Sơ đồ 2 pha xử lý (Pha 1: 11,57 ms / Pha 2: 850 ms) + Minh họa 6 nhóm tài liệu được gắn nhãn tự động.

**Speaker notes (Bảo trình bày - ~75 từ):**
> Kính thưa Hội đồng, ở Trọng tâm thứ tư, hệ thống tự động phân loại 6 nhóm tài liệu Công tác sinh viên thông qua cơ chế xử lý 2 pha: với văn bản điện tử có sẵn chữ, hệ thống bóc tách ngay trong 11,57 mili-giây; còn với tài liệu scan ảnh giấy, hệ thống chỉ OCR trang bìa trong 850 mili-giây để người dùng không phải chờ đợi lâu. Bằng cách kết hợp 4 luồng tín hiệu từ số hiệu, tiêu đề đến cấu trúc văn bản, hệ thống tự động định tuyến tài liệu và gán nhãn siêu dữ liệu, đồng thời luôn ghi nhận nhật ký kiểm toán nếu cán bộ điều chỉnh bằng tay.

---

## SLIDE 13 — TRỌNG TÂM 5: NÂNG CẤP TÌM KIẾM THÔNG MINH & BẢO MẬT DỮ LIỆU

**Tiêu đề:** Trọng tâm 5 — Nâng Cấp Tìm Kiếm Thông Minh & Bảo Vệ Thông Tin Cá Nhân

**Nội dung trình bày:**
- 🔄 **Khắc phục hạn chế của Đợt 1:**
  - Ở Đợt 1 chỉ tìm kiếm theo từng mặt chữ: Dễ bỏ sót hồ sơ khi gõ từ đồng nghĩa, từ viết tắt hoặc chữ scan bị mờ dấu.
  - Chưa có cơ chế bảo vệ thông tin riêng tư của sinh viên khi tra cứu công khai.
- ⚙️ **3 Nâng cấp cốt lõi trong Đợt 2:**
  - **1. Tìm kiếm kết hợp (Từ khóa + Ý nghĩa):**
    - Bắt trọn hồ sơ kể cả khi người dùng gõ sai chính tả, dùng từ đồng nghĩa (*"tiền hỗ trợ"* $\rightarrow$ vẫn tìm ra *"trợ cấp xã hội"*) hoặc văn bản scan bị lỗi dấu.
  - **2. Tự động nhận diện diện chính sách (*Percolator*):**
    - Đơn từ vừa tải lên tự động được khớp với **7 bộ luật chính sách sinh viên** (Nghị định 81 miễn, giảm học phí, trợ cấp) để xếp vào đúng sổ quản lý.
  - **3. Tự động che mờ thông tin cá nhân (*Tuân thủ Nghị định 13*):**
    - Số Căn cước công dân (`068******891`) và số điện thoại tự động được ẩn khi tra cứu công khai; chỉ cán bộ đăng nhập mới xem được đầy đủ.
- 📊 **Kết quả kiểm chứng thực tế:**
  - **Độ chính xác cao:** Đạt **74% trong top 5 kết quả đầu tiên** (trung bình 3,7 trên 5 hồ sơ gợi ý khớp chính xác 100%); loại trừ hoàn toàn các tài liệu không liên quan.
  - **Tốc độ phản hồi tức thì:** Thời gian tìm kiếm trung bình **dưới 45 mili-giây** (chưa tới 0,05 giây).

**Gợi ý hình ảnh:** Sơ đồ 2 phần trực quan: [Luồng tìm kiếm kết hợp Từ khóa + Ý nghĩa] ➔ [Minh họa giao diện kết quả tìm kiếm đã tự động che mờ số CCCD].

**Speaker notes (Phát trình bày - ~85 từ):**
> Kính thưa Hội đồng, ở Trọng tâm thứ năm, nhóm đã giải quyết 3 bài toán lớn của công cụ tìm kiếm: Thứ nhất là nâng cấp lên tìm kiếm kết hợp cả mặt chữ lẫn ý nghĩa câu văn, giúp cán bộ không bao giờ bị lọt hồ sơ kể cả khi gõ từ đồng nghĩa hoặc ảnh scan bị lỗi dấu. Thứ hai là cơ chế tự động đối chiếu đơn từ với 7 bộ luật chính sách sinh viên để phân luồng tự động. Và thứ ba là tự động che mờ số Căn cước công dân theo Nghị định 13 khi tra cứu công khai. Đo kiểm thực nghiệm cho thấy độ chính xác đạt 74% ngay trong 5 kết quả đầu tiên với tốc độ siêu nhanh dưới 45 mili-giây.

---

## SLIDE 14 — KHÓ KHĂN TỒN TẠI & HƯỚNG GIẢI QUYẾT THỰC TẾ

**Tiêu đề:** Khó Khăn Kỹ Thuật Còn Tồn Tại & Giải Pháp Triển Khai

**Nội dung trình bày:**
- 🔴 **1. Nhiễu con dấu đỏ đóng đè chữ *(Thách thức lớn nhất trong OCR hành chính)*:**
  - *Vấn đề thực tế:* Mực đỏ của con dấu cơ quan che lấp nét chữ in và chữ ký, làm tăng hệ số lỗi ký tự lên mức **CER 0,2058** *(đo trên tập 32 trang held-out)*.
  - *Giải pháp kỹ thuật:* Tách màu trong **không gian màu HSV** *(thang đo OpenCV dải đỏ H: 0–10 và 170–180)* để bóc tách riêng lớp mực đỏ, khôi phục nét chữ đen nguyên bản trước khi đưa vào mô hình OCR.
- ✍️ **2. Chữ viết tay sinh viên bị mờ và đứt nét:**
  - *Vấn đề thực tế:* Nét mực bút bi nhạt màu hoặc bản scan chất lượng thấp khiến nét chữ bị đứt quãng, làm mô hình TrOCR dễ nhận diện nhầm ký tự.
  - *Giải pháp kỹ thuật:* Áp dụng phép toán hình thái học **Dilation *(thuật toán làm dày và liền nét chữ)*** trong tiền xử lý ảnh để nối liền các nét đứt, giúp mô hình đọc rõ hơn.
- 📊 **3. Nhận diện cấu trúc bảng biểu còn sai lệch:**
  - *Vấn đề thực tế:* Các văn bản có danh sách hoặc kẻ bảng biểu (Quyết định khen thưởng, Biểu mẫu đơn) dễ bị đọc lẫn lộn dòng giữa các cột, làm mất cấu trúc hàng và cột.
  - *Giải pháp kỹ thuật:* Đang nghiên cứu giải thuật phân đoạn bảng dựa trên phát hiện đường kẻ viền khung để tách riêng từng ô thành các vùng ảnh độc lập trước khi gửi vào mô hình OCR.

**Gợi ý hình ảnh:** Sơ đồ 3 bước thuật toán HSV tách dấu đỏ (Ảnh gốc có dấu ➔ Mặt nạ tách dải màu đỏ ➔ Ảnh phục hồi nét chữ đen) + Minh họa bóc tách ô bảng biểu.

**Speaker notes (Bảo trình bày - ~85 từ):**
> Kính thưa Hội đồng, nhóm thẳng thắn nhìn nhận 3 khó khăn kỹ thuật đang giải quyết. Thứ nhất là tình trạng con dấu đỏ hành chính đóng đè lên chữ khiến CER trên tập 32 trang hỗn hợp còn ở mức 0,2058; nhóm đang hoàn thiện thuật toán phân tách màu trong không gian HSV theo chuẩn OpenCV để bóc tách lớp mực đỏ. Thứ hai, với các lá đơn có nét chữ viết tay bị mờ hoặc đứt đoạn, nhóm ứng dụng kỹ thuật Dilation nhằm làm liền nét chữ trước khi nhận dạng. Thứ ba, đối với các tài liệu có cấu trúc bảng biểu phức tạp dễ bị đọc lẫn lộn cột, nhóm đang nghiên cứu giải thuật phát hiện đường kẻ khung để chia tách từng ô độc lập, bảo toàn cấu trúc dữ liệu.

---

## SLIDE 15 — KẾT LUẬN VÀ HƯỚNG PHÁT TRIỂN

**Tiêu đề:** Tổng Kết Đợt 2 & Kế Hoạch Tiếp Theo Hoàn Thiện Khóa Luận

**Nội dung trình bày:**
- 🏁 **Tổng kết kết quả kỹ thuật Đợt 2:**
  - **Làm chủ hai mô hình OCR cốt lõi:** Kết hợp hiệu quả **VietOCR** *(văn bản in)* và **TrOCR-Vi** *(chữ viết tay)*; khắc phục triệt để lỗi mất chữ dòng dài *(tỷ lệ cụt chữ giảm từ 0,1304 xuống 0,0053)*.
  - **Tự động hóa chuỗi xử lý nghiệp vụ:** Xây dựng module **AI Hậu xử lý** bóc tách thông tin *(Mã số sinh viên đạt độ chính xác 0,982)* và cơ chế **phân loại văn bản 2 pha** tức thì từ 11,57 mili-giây.
  - **Nâng cấp tìm kiếm ngữ nghĩa:** Ứng dụng **Hybrid RRF** (kết hợp từ khóa BM25 và Vector 768 chiều), định tuyến hồ sơ qua Percolator và che mờ dữ liệu định danh PII.
- 🚀 **Kế hoạch trọng tâm tiếp theo:**
  - 🔧 **Giải quyết các vấn đề kỹ thuật còn tồn đọng:**
    - Tích hợp thuật toán lọc màu HSV bóc tách con dấu đỏ đè chữ.
    - Áp dụng phép toán Dilation làm liền các nét chữ viết tay bị mờ.
    - Nghiên cứu giải thuật phân đoạn đường kẻ khung để nhận diện chính xác cấu trúc bảng biểu.
  - 🌐 **Hoàn thiện Website & Hệ thống phân quyền (RBAC):**
    - Tối ưu hóa giao diện trình sửa đối soát song song *(Side-by-Side Live Editor)* trên nền tảng React.
    - Thiết lập phân quyền truy cập chặt chẽ theo 3 vai trò: **Cán bộ CTSV** *(toàn quyền đối soát, duyệt và quản trị hồ sơ)*, **Sinh viên** *(tra cứu công khai đã che mờ PII)* và **Quản trị viên hệ thống**.


**Gợi ý hình ảnh:** Sơ đồ 3 nhóm nhiệm vụ kế hoạch tiếp theo (Kỹ thuật tồn đọng ➔ Website & Phân quyền ➔ Thuyết minh & Thực địa) + Lời cảm ơn Hội đồng.

**Speaker notes (Thành đại diện nhóm kết luận - ~85 từ):**
> Kính thưa Quý Thầy/Cô trong Hội đồng, tổng kết Đợt 2, nhóm đã giải quyết xong các bài toán kỹ thuật cốt lõi từ nhận dạng hai mô hình, hậu xử lý bóc tách thực thể đến tìm kiếm ngữ nghĩa phân tán. Trong kế hoạch tiếp theo của tháng 11, nhóm tập trung vào 3 nhiệm vụ chính: thứ nhất là giải quyết dứt điểm các vấn đề kỹ thuật tồn đọng gồm tách con dấu đỏ, làm liền chữ mờ và bóc tách bảng biểu; thứ hai là hoàn thiện giao diện website và phân quyền người dùng chặt chẽ theo vai trò; . Nhóm xin trân trọng cảm ơn Thầy hướng dẫn ThS. Nguyễn Trọng Hiếu và Quý Thầy/Cô trong Hội đồng!
