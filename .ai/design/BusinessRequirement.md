# Business Requirement — Yêu cầu Nghiệp vụ

## Purpose

Tài liệu xác định các yêu cầu nghiệp vụ (Business Requirements) của Phòng Công tác Sinh viên (CTSV) và bối cảnh áp dụng giải pháp số hóa tài liệu.

## Scope

Quy trình quản lý hồ sơ sinh viên hiện tại, bài toán thực tế, yêu cầu cải tiến và mục tiêu giá trị nghiệp vụ mang lại.

---

## 1. Bối cảnh Nghiệp vụ

Phòng Công tác Sinh viên tại các trường Đại học chịu trách nhiệm tiếp nhận, xử lý và lưu trữ hàng chục ngàn văn bản giấy mỗi năm:
- Đơn xin nghỉ học tạm thời / bảo lưu kết quả học tập.
- Đơn xin miễn giảm học phí / trợ cấp xã hội / học bổng.
- Biên bản xử lý kỷ luật / khen thưởng sinh viên.
- Quyết định công nhận tốt nghiệp / tiếp nhận lại.
- Giấy xác nhận sinh viên / Đơn chuyển ca học.

---

## 2. Vấn đề & Hạn chế của Quy trình Hiện tại

1. **Lưu trữ thủ công tốn diện tích**: Hồ sơ giấy tích tụ qua các khóa gây quá tải kho lưu trữ.
2. **Tra cứu chậm chạp**: Khi cần tìm lại một bản đơn từ 2-3 năm trước của sinh viên, cán bộ phải lật tìm thủ công từng tập hồ sơ (mất từ 30 phút - 2 giờ/lần).
3. **Nguy cơ thất lạc & hư hỏng**: Giấy bị ẩm mốc, mờ mực hoặc thất lạc trong quá trình luân chuyển.
4. **Không có khả năng phân tích / thống kê tổng hợp**: Khó khăn trong việc thống kê xem trong năm có bao nhiêu sinh viên nghỉ học vì lý do sức khỏe, bao nhiêu sinh viên bị kỷ luật,...
5. **Rủi ro rò rỉ thông tin cá nhân**: Hồ sơ giấy không được phân quyền truy cập chặt chẽ.

---

## 3. Mục tiêu Nghiệp vụ (Business Goals)

| ID | Mục tiêu | Chỉ số đo lường (KPI) |
|----|----------|----------------------|
| **BG-01** | Giảm 90% thời gian tra cứu hồ sơ sinh viên | Từ 30-120 phút xuống < 5 giây trên thanh tìm kiếm |
| **BG-02** | Số hóa 100% tài liệu phát sinh mới của Phòng CTSV | 100% đơn từ sau khi tiếp nhận được scan và đưa lên hệ thống |
| **BG-03** | Đảm bảo độ chính xác nhận dạng văn bản tiếng Việt | Tỷ lệ lỗi ký tự (CER) < 5% trên văn bản in chuẩn |
| **BG-04** | Kiểm soát an toàn thông tin & vết thao tác | 100% các hành động xem, tải, sửa, xóa được ghi Audit Log |

---

## 4. Quy trình Nghiệp vụ Mục tiêu (To-Be Workflow)

```
[Tiếp nhận Đơn/Văn bản giấy]
         │
         ▼
[Cán bộ Scan/Chụp ảnh tài liệu]
         │
         ▼
[Upload lên Hệ thống Student-Document-OCR]
         │
         ▼
[Hệ thống tự động OCR & Trích xuất Metadata]
         │
         ▼
[Cán bộ Kiểm tra / Hiệu chỉnh OCR nếu cần]
         │
         ▼
[Hệ thống Index vào Elasticsearch & MinIO]
         │
         ▼
[Tra cứu / Phân tích / Lưu trữ Lâu dài]
```

---

## TODO

- [ ] Phỏng vấn cán bộ phòng CTSV để bổ sung chi tiết quy trình xử lý từng loại đơn.
- [ ] Thống kê khối lượng đơn từ trung bình hàng tháng để tính toán dung lượng storage.

## References

- PROJECT_SPEC.md
- SRS.md
- UseCase.md
