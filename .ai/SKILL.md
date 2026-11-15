---
name: de-ai-web-design
description: Thiết kế giao diện website, landing page, dashboard, app UI sao cho trông như do con người thiết kế có chủ đích, không mang "mùi AI" (template chung chung, gradient tím, card bo tròn giống hệt nhau, copy sáo rỗng). Make sure to use this skill whenever the user asks to build, redesign, or polish any website, landing page, web app, component, or HTML/React UI, or says things like "bớt AI", "trông đỡ AI hơn", "nhìn như template", "thiết kế có cá tính", "make it look less AI-generated", even if they don't mention this skill by name. Dùng kèm với frontend-design skill nếu có.
---

# Thiết kế web bớt "mùi AI"

Mục tiêu: giao diện có quyết định thiết kế riêng cho đúng nội dung này, chứ không phải bản trung bình của mọi trang web mà model từng thấy.

"Mùi AI" không đến từ một lỗi riêng lẻ. Nó đến từ việc **chọn mặc định ở mọi trục cùng lúc**: màu mặc định, font mặc định, bố cục mặc định, câu chữ mặc định. Chỉ cần phá vỡ vài trục một cách có chủ đích là trang đã khác hẳn.

## Quy trình

1. **Hiểu đề bài trước khi vẽ.** Xác định cụ thể: sản phẩm/chủ đề là gì, ai dùng, việc chính của trang là gì. Nếu brief mơ hồ, tự đề xuất một giả định cụ thể và nói rõ trong phản hồi. Chất liệu thiết kế nằm ở chính chủ đề: một quán cà phê rang xay, một phần mềm kế toán, một đội bóng phủi sẽ trông rất khác nhau.
2. **Viết kế hoạch ngắn** (vài dòng, trước khi code):
   - Màu: 4-6 giá trị hex có tên và có vai trò.
   - Chữ: font nào, dùng làm gì, thang cỡ chữ.
   - Bố cục: 1-2 câu mô tả ý tưởng, kèm sơ đồ ASCII nếu cần. Nêu rõ canh trái/giữa.
   - Một thứ duy nhất sẽ là điểm nhớ của trang.
3. **Tự kiểm tra kế hoạch với danh sách "dấu hiệu AI" bên dưới.** Chỗ nào giống mặc định thì đổi, và nói ngắn gọn đã đổi gì, vì sao.
4. **Code**, rồi **soi lại** bằng checklist cuối file. Nếu môi trường cho chụp màn hình thì chụp để xem.

Nếu brief của người dùng chỉ định rõ một phong cách (kể cả phong cách nằm trong danh sách dưới), **làm đúng theo brief**. Danh sách chỉ để tránh dùng chúng như mặc định khi brief chưa nói gì.

## Dấu hiệu AI cần tránh (và thay bằng gì)

### Màu sắc
- **Gradient tím-xanh / xanh-hồng** làm nền hero hoặc chữ. → Chọn màu từ chính chủ đề (vật liệu, ngành, văn hóa), thường là 1 màu nền + 1 màu nhấn.
- **Nền kem ấm + serif + cam đất**, hoặc **nền đen + một màu nhấn neon xanh lá/đỏ cam**. Hai công thức "khác biệt" này giờ cũng là mặc định. → Thử nền sáng lạnh, nền màu đặc, nền trắng thật, hoặc palette tương phản thấp có chủ ý.
- **Đen thuần tinted** kiểu #0B0B0B, #111 cho mọi thứ. → Chọn màu chữ/nền có sắc độ liên quan đến palette.
- **Gradient mờ, blob, glow, glassmorphism** chỉ để "cho đẹp". → Bỏ. Nếu cần chiều sâu, dùng ảnh, texture, hoặc đổ bóng có logic nguồn sáng.
- Màu nhấn rải khắp nơi. → Màu nhấn chỉ dùng cho hành động chính và trạng thái.

### Chữ
- Font mặc định: Inter, Roboto, Arial, system-ui cho mọi thứ; hoặc cặp "serif hiển thị + sans thân bài" đã quá quen. → Chọn font có chủ ý, dùng 1 họ hoặc 2 họ thật sự khác nhau. Với tiếng Việt, **kiểm tra font có đủ dấu và dấu không bị vỡ/lệch** (ví dụ Be Vietnam Pro, Noto Sans/Serif, Lexend, Source Serif 4, Playfair Display có hỗ trợ tiếng Việt).
- **Nhấn một từ trong tiêu đề** bằng in nghiêng/đổi màu/gạch chân gradient. → Để tiêu đề đồng nhất, hoặc để cả cấu trúc câu làm nhiệm vụ nhấn.
- **Nhãn IN HOA giãn chữ phía trên mỗi tiêu đề** (eyebrow). → Bỏ, trừ khi nhãn mang thông tin thật.
- **Font mono cho nhãn dữ liệu nhỏ** khi nội dung không liên quan đến code.
- Thang chữ lộn xộn. → Đặt thang cỡ chữ rõ ràng (ví dụ tỉ lệ 1.25), độ dày có chủ ý. Thân bài dưới ~75 ký tự mỗi dòng; chữ có chân (serif) cần line-height rộng hơn một chút.

### Bố cục
- **Công thức landing page**: hero giữa trang + 3 card tính năng + dải số liệu + testimonial + CTA cuối. → Bắt đầu từ việc trang này cần nói gì theo thứ tự nào, rồi mới chọn khối. Có thể chỉ cần 3 phần.
- **Mọi thứ là card bo tròn giống hệt nhau** với cùng border-radius, cùng đổ bóng xám nhạt. → Dùng phân cấp: có thứ là card, có thứ chỉ là cột chữ, có thứ là bảng, có thứ tràn mép. Mỗi cấp độ bo góc/đổ bóng khác nhau, hoặc không có.
- **Hero = số lớn + nhãn nhỏ + số liệu phụ + gradient.** → Mở đầu bằng thứ đặc trưng nhất của chủ đề: một câu mạnh, một bức ảnh thật, một demo chạy được, một tương tác.
- **Đánh số 01 / 02 / 03** cho các mục không phải chuỗi bước. → Chỉ đánh số khi nội dung thật sự có thứ tự.
- **Đường kẻ, viền, divider rải khắp** làm đồ trang trí. → Mỗi cấu trúc nhìn thấy được phải mang thông tin (nhóm, thứ bậc, thứ tự). Không mang thông tin thì bỏ.
- **Đối xứng tuyệt đối, mọi thứ canh giữa.** → Canh trái là mặc định tốt cho nội dung đọc. Dùng bất đối xứng và khoảng trắng có chủ đích.
- Khoảng cách đều chằn chặn giữa mọi section. → Nhịp thay đổi: chỗ chặt, chỗ thoáng.

### Hình ảnh và biểu tượng
- **Bộ icon line cùng kích thước trong vòng tròn tô màu nhạt** đặt trên mỗi card. → Bỏ icon nếu không giúp nhận diện; nếu cần, dùng ít và nhất quán, không bọc nền.
- **Emoji làm icon** (🚀 ✨ 🔒). → Không dùng.
- **Ảnh minh họa 3D/isometric/người hoạt hình chung chung.** → Dùng ảnh thật, ảnh chụp sản phẩm, đồ họa vẽ tay hoặc hình học thuần theo chủ đề. Không có ảnh thật thì dùng khối màu, typography, hoặc SVG đơn giản thay cho ảnh giả.

### Chuyển động
- **Mọi section fade-in + trượt lên khi cuộn**, mọi card nhấc lên khi hover. → Giữ **một khoảnh khắc** có dàn dựng (ví dụ lúc tải trang) hoặc không có. Chuyển động đáp lại hành động của người dùng (mở, đóng, xác nhận) thì tốt. Tôn trọng `prefers-reduced-motion`.

### Câu chữ (copy)
Copy sáo rỗng làm lộ "mùi AI" nhanh hơn cả layout.
- Tránh: "Nâng tầm trải nghiệm", "Giải pháp toàn diện", "Mở khóa tiềm năng", "Cách mạng hóa", "Hành trình của bạn", "Không chỉ là X, mà còn là Y", "Seamless", "Powerful", "Unlock".
- Tránh ba ý song song cho đủ nhịp ("Nhanh. Đẹp. Dễ dùng.") lặp ở khắp nơi.
- Tránh dấu gạch ngang dài `—` chèn khắp và chuỗi meta nối bằng dấu chấm giữa `A · B · C`.
- Tránh mũi tên `→` gắn sau mọi nút và link.
- **Viết cụ thể.** Tên thật, con số thật, chi tiết thật của sản phẩm. "Rang tại Đà Lạt, giao trong 48 giờ" hơn hẳn "Chất lượng vượt trội".
- Nút nói rõ chuyện gì xảy ra khi bấm: "Lưu thay đổi" thay vì "Gửi". Một hành động giữ một tên xuyên suốt (nút "Đăng bài" thì thông báo là "Đã đăng bài").
- Lỗi và trạng thái trống: nói chuyện gì đã xảy ra và làm gì tiếp, không xin lỗi vòng vo.
- Số liệu, đánh giá, tên khách hàng **không bịa trông như thật**. Nếu là placeholder, đánh dấu rõ hoặc dùng nội dung trung thực.
- Giọng điệu tiếng Việt tự nhiên: câu ngắn, động từ rõ, chữ thường theo câu, tránh văn dịch từ tiếng Anh.

## Nguyên tắc nền

- **Tiêu một lần cho sự táo bạo.** Một thành phần là thứ người ta nhớ. Mọi thứ xung quanh giữ yên tĩnh và kỷ luật.
- **Cấu trúc là thông tin.** Viền, nhãn, số, divider chỉ xuất hiện khi chúng nói điều gì đó về nội dung.
- **Chủ đề quyết định hình thức.** Nếu thay chủ đề bằng một ngành khác mà trang vẫn y nguyên, đó là template.
- **Bớt đi.** Như lời khuyên của Chanel: trước khi ra khỏi nhà, soi gương và bỏ đi một món phụ kiện.

## Mức chất lượng tối thiểu (làm mà không cần khoe)

- Responsive xuống màn hình điện thoại, không cuộn ngang.
- Focus bằng bàn phím nhìn thấy rõ; tương phản màu đạt chuẩn đọc được.
- `prefers-reduced-motion` được tôn trọng.
- Tiếng Việt hiển thị đúng dấu, line-height không cắt dấu.
- CSS không tự triệt tiêu nhau: cẩn thận độ ưu tiên selector, nhất là padding/margin giữa các section.

## Checklist soi lại trước khi giao

Trả lời thẳng từng câu; nếu "có" ở mục nào thì sửa:

1. Có gradient trang trí, blob, glow nào không phục vụ nội dung không?
2. Bỏ logo đi, trang này có thể là của bất kỳ công ty nào không?
3. Có từ 3 card giống hệt nhau trở lên không, và chúng có thật sự cùng hạng không?
4. Có eyebrow in hoa, đánh số 01/02/03, `→`, `·`, `—` rải khắp không?
5. Có từ khóa sáo rỗng nào trong copy không?
6. Có icon/emoji chỉ để lấp chỗ trống không?
7. Có hiệu ứng cuộn/hover áp lên mọi thứ không?
8. Font và màu có phải lựa chọn cho đề bài này, hay là thứ mình chọn cho mọi đề bài?
9. Điểm nhớ duy nhất của trang là gì? Nếu không trả lời được, trang chưa có cá tính.

Khi báo lại cho người dùng, nêu ngắn gọn: các quyết định thiết kế chính (màu, chữ, bố cục, điểm nhớ) và những giả định đã đặt ra. Không giải thích dài dòng về chính skill này.