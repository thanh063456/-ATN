import sqlite3

conn = sqlite3.connect("data.db")
c = conn.cursor()

new_text = """CỘNG HÒA XÃ HỘI CHỦ NGHĨA VIỆT NAM
Độc lập - Tự do - Hạnh phúc

ĐƠN XIN MIỄN GIẢM HỌC PHÍ
Kính gửi: Ban Giám hiệu Trường Đại học Đà Lạt; Phòng Công tác Sinh viên.
Tôi tên là: Nguyễn Hoàng Nam. Sinh ngày: 15/04/2003. Nơi sinh: Lâm Đồng.
Mã số sinh viên: 20210678. Lớp: CTK46, Khoa Công nghệ Thông tin.
Số CCCD: 068199001234. Điện thoại: 0987654321. Email: hoangnam.dlu@gmail.com.
Thuộc đối tượng chính sách: Con hộ nghèo theo Nghị định số 81/2021/NĐ-CP của Chính phủ.
Em làm đơn này kính đề nghị Nhà trường xem xét miễn giảm học phí học kỳ 1 năm học 2025-2026.
Em xin cam đoan các thông tin kê khai trên là hoàn toàn đúng sự thật."""

c.execute("UPDATE ocr_results SET raw_text = ?, corrected_text = ? WHERE document_id = 'e8a12dc71cfb4cebbdfb9bbcc6d1e829'", (new_text, new_text))
conn.commit()
print("Successfully updated document with CCCD, Phone, Email for PII test!")
conn.close()

