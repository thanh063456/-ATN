"""
scripts/seed_realistic_search_docs.py
Tạo các văn bản và hồ sơ CTSV mẫu chuẩn nghiệp vụ vào CSDL (data.db),
đồng bộ với các từ khóa gợi ý nhanh trên giao diện tìm kiếm:
- 'miễn giảm học phí'
- 'bảo lưu kết quả học tập'
- 'xét học bổng kỳ 1'
- '20210678'
- 'don xin nghi hoc'
- 'Nguyễn Hoàng Nam'
"""
import sqlite3
import uuid
from datetime import datetime, date
import json

def seed():
    conn = sqlite3.connect("data.db")
    c = conn.cursor()

    # Lấy admin user id
    c.execute("SELECT id FROM users LIMIT 1")
    row = c.fetchone()
    user_id = str(row[0]) if row else uuid.uuid4().hex

    # Lấy category ids
    c.execute("SELECT id, code FROM document_categories")
    cat_map = {row[1]: row[0] for row in c.fetchall()}

    docs = [
        {
            "id": "e8a12dc7-1cfb-4ceb-bdfb-9bbcc6d1e829",
            "title": "Đơn xin miễn giảm học phí đối tượng chính sách - Nguyễn Hoàng Nam (20210678)",
            "cat_code": "DON_TU",
            "student_id": "20210678",
            "student_name": "Nguyễn Hoàng Nam",
            "doc_num": "12/ĐN-MGHP",
            "doc_date": "2025-09-15",
            "tags": ["#DonTu", "#MienGiamHocPhi", "#HocPhi", "#NganhCNTT", "#K46"],
            "ocr_text": "CỘNG HÒA XÃ HỘI CHỦ NGHĨA VIỆT NAM\nĐộc lập - Tự do - Hạnh phúc\n\nĐƠN XIN MIỄN GIẢM HỌC PHÍ\nKính gửi: Ban Giám hiệu Trường Đại học Đà Lạt; Phòng Công tác Sinh viên.\nTôi tên là: Nguyễn Hoàng Nam. Sinh ngày: 15/04/2003. Nơi sinh: Lâm Đồng.\nMã số sinh viên: 20210678. Lớp: CTK46, Khoa Công nghệ Thông tin.\nThuộc đối tượng chính sách: Con hộ nghèo theo Nghị định số 81/2021/NĐ-CP của Chính phủ.\nEm làm đơn này kính đề nghị Nhà trường xem xét miễn giảm học phí học kỳ 1 năm học 2025-2026.\nEm xin cam đoan các thông tin kê khai trên là hoàn toàn đúng sự thật.",
            "confidence": 0.985,
        },
        {
            "id": "97992de1-edee-4f9c-a78c-134dbb6b92e6",
            "title": "Đơn xin tạm hoãn và bảo lưu kết quả học tập kỳ 1 - Trần Thị Mai (20210892)",
            "cat_code": "DON_TU",
            "student_id": "20210892",
            "student_name": "Trần Thị Mai",
            "doc_num": "45/ĐN-BL",
            "doc_date": "2025-10-02",
            "tags": ["#DonTu", "#XuLyHocVu", "#XinThoiHoc", "#K46"],
            "ocr_text": "CỘNG HÒA XÃ HỘI CHỦ NGHĨA VIỆT NAM\nĐộc lập - Tự do - Hạnh phúc\n\nĐƠN XIN TẠM HOÃN VÀ BẢO LƯU KẾT QUẢ HỌC TẬP\nKính gửi: Phòng Đào tạo; Phòng Công tác Sinh viên Trường Đại học Đà Lạt.\nHọ và tên sinh viên: Trần Thị Mai. MSSV: 20210892. Lớp: QTK46.\nNay tôi làm đơn này kính xin được tạm hoãn tiến độ học tập và bảo lưu kết quả học tập học kỳ 1 năm học 2025-2026 trong thời hạn 01 học kỳ vì lý do điều trị sức khỏe tại Bệnh viện Đa khoa Lâm Đồng.\nKính mong Quý Phòng xem xét và tạo điều kiện giúp đỡ.",
            "confidence": 0.978,
        },
        {
            "id": "cadc3753-1408-4553-a306-441954750dc2",
            "title": "Thông báo số 1413/TB-ĐHĐL về việc xét duyệt học bổng khuyến khích học tập học kỳ 1",
            "cat_code": "THONG_BAO",
            "student_id": None,
            "student_name": None,
            "doc_num": "1413/TB-ĐHĐL",
            "doc_date": "2025-09-20",
            "tags": ["#HocBong", "#KhenThuong", "#K46", "#K47", "#K48"],
            "ocr_text": "TRƯỜNG ĐẠI HỌC ĐÀ LẠT - PHÒNG CÔNG TÁC SINH VIÊN\nSố: 1413/TB-ĐHĐL. Đà Lạt, ngày 20 tháng 09 năm 2025.\nTHÔNG BÁO VỀ VIỆC XÉT HỌC BỔNG KỲ 1\nHọc bổng khuyến khích học tập học kỳ 1 năm học 2025-2026.\nPhòng Công tác Sinh viên thông báo kế hoạch xét học bổng kỳ 1 cho sinh viên hệ chính quy các khóa K46, K47, K48.\n1. Tiêu chuẩn xét học bổng kỳ 1: Điểm trung bình tích lũy học tập từ 3.2 trở lên, điểm rèn luyện đạt loại Tốt trở lên.\n2. Mức học bổng: Loại Xuất sắc, loại Giỏi và loại Khá tương ứng theo quy chế chi tiêu nội bộ của Nhà trường.\nTrưởng phòng CTSV ký duyệt.",
            "confidence": 0.992,
        },
        {
            "id": "62bf49cb-a11d-4112-af36-a83d63c8be6a",
            "title": "Đơn xin nghỉ học có thời hạn vì lý do cá nhân - Lê Văn Bình (20210543)",
            "cat_code": "DON_TU",
            "student_id": "20210543",
            "student_name": "Lê Văn Bình",
            "doc_num": "08/ĐN-NH",
            "doc_date": "2025-09-30",
            "tags": ["#DonTu", "#XinThoiHoc", "#XuLyHocVu"],
            "ocr_text": "don xin nghi hoc co thoi han.\nKinh gui: Ban Giam hieu, Phong Cong tac Sinh vien Truong Dai hoc Da Lat.\nEm ten la Le Van Binh, MSSV 20210543, lop LKK46.\nEm lam don nay kinh xin nghi hoc hoc ky 1 de tham gia nghia vu quan su tai dia phuong.\nSau khi hoan thanh nghia vu, em xin phep quay tro lai truong tiep tuc hoc tap.",
            "confidence": 0.945,
        },
        {
            "id": "47da571d-db05-4bd4-9a29-607da3ac31c7",
            "title": "Quyết định số 890/QĐ-ĐHĐL Về việc cấp học bổng tài trợ sinh viên NCKH & Khởi nghiệp",
            "cat_code": "QUYET_DINH",
            "student_id": "20210678",
            "student_name": "Nguyễn Hoàng Nam",
            "doc_num": "890/QĐ-ĐHĐL",
            "doc_date": "2025-10-10",
            "tags": ["#HocBong", "#KhoiNghiep", "#CuocThi", "#NganhCNTT", "#K46"],
            "ocr_text": "HIỆU TRƯỞNG TRƯỜNG ĐẠI HỌC ĐÀ LẠT\nQUYẾT ĐỊNH\nVề việc trao học bổng doanh nghiệp tài trợ phát triển tài năng trẻ CNTT và phong trào Khởi nghiệp đổi mới sáng tạo năm 2025.\nĐiều 1. Trao tặng suất học bổng toàn phần trị giá 15.000.000 đồng cho sinh viên Nguyễn Hoàng Nam, MSSV: 20210678, Lớp CTK46, Khoa Công nghệ Thông tin vì thành tích đạt giải Nhất cuộc thi Sáng tạo số sinh viên.\nĐiều 2. Phòng Công tác Sinh viên, Phòng Tài chính Kế toán chịu trách nhiệm thi hành quyết định này.",
            "confidence": 0.990,
        },
        {
            "id": "db4b81d2-638d-4ed7-b39f-48f70d19c60c",
            "title": "Kế hoạch số 1353/KH-ĐHĐL Tổ chức tuần sinh hoạt công dân đầu khóa sinh viên K48",
            "cat_code": "KE_HOACH",
            "student_id": None,
            "student_name": None,
            "doc_num": "1353/KH-ĐHĐL",
            "doc_date": "2025-08-25",
            "tags": ["#SinhHoatCongDan", "#K48"],
            "ocr_text": "TRƯỜNG ĐẠI HỌC ĐÀ LẠT\nSố: 1353/KH-ĐHĐL. KẾ HOẠCH\nTổ chức Tuần sinh hoạt công dân - sinh viên đầu khóa cho tân sinh viên Khóa 48 (K48) năm học 2025-2026.\nMục đích: Nâng cao nhận thức chính trị tư tưởng, phổ biến quy chế học vụ, chế độ chính sách miễn giảm học phí, trợ cấp xã hội và văn hóa học đường Đại học Đà Lạt.",
            "confidence": 0.988,
        },
        {
            "id": "27d43dde-f754-4baa-90f9-553d4c52a740",
            "title": "Hướng dẫn số 205/HD-CTSV Quy trình cấp giấy xác nhận sinh viên và vay vốn Ngân hàng Chính sách",
            "cat_code": "HUONG_DAN",
            "student_id": None,
            "student_name": None,
            "doc_num": "205/HD-CTSV",
            "doc_date": "2025-08-10",
            "tags": ["#HocPhi", "#DonTu"],
            "ocr_text": "HƯỚNG DẪN QUY TRÌNH THỦ TỤC CẤP GIẤY XÁC NHẬN SINH VIÊN VÀ VAY VỐN TÍN DỤNG.\nPhòng Công tác Sinh viên hướng dẫn sinh viên có nhu cầu vay vốn ưu đãi tại Ngân hàng Chính sách Xã hội:\nBước 1: Nộp đơn xin cấp giấy xác nhận sinh viên trực tuyến tại cổng thông tin DocuCTSV.\nBước 2: Hệ thống tự động kiểm tra trạng thái học vụ, đối chiếu xác thực QR và cấp giấy điện tử trong vòng 24 giờ.",
            "confidence": 0.982,
        },
        {
            "id": "b084a041-efe6-4524-9096-9d1a19d565f3",
            "title": "Báo cáo số 77/BC-CTSV Tổng hợp rà soát hồ sơ chính sách miễn giảm học phí học kỳ 1",
            "cat_code": "BAO_CAO",
            "student_id": None,
            "student_name": None,
            "doc_num": "77/BC-CTSV",
            "doc_date": "2025-10-15",
            "tags": ["#MienGiamHocPhi", "#HocPhi"],
            "ocr_text": "BÁO CÁO CÔNG TÁC THỰC HIỆN CHÍNH SÁCH MIỄN GIẢM HỌC PHÍ VÀ TRỢ CẤP XÃ HỘI KỲ 1 NĂM HỌC 2025-2026.\nPhòng Công tác Sinh viên đã tiếp nhận và giải quyết 1.250 hồ sơ xin miễn giảm học phí cho sinh viên diện hộ nghèo, cận nghèo, mồ côi và dân tộc thiểu số vùng đặc biệt khó khăn.",
            "confidence": 0.986,
        },
        {
            "id": "832a3d84-447c-41ed-8dc4-4d6c944f8b07",
            "title": "Biên bản số 12/BB-CTSV Họp hội đồng xét cấp học bổng doanh nghiệp kỳ 1",
            "cat_code": "BIEN_BAN",
            "student_id": None,
            "student_name": None,
            "doc_num": "12/BB-CTSV",
            "doc_date": "2025-10-05",
            "tags": ["#HocBong", "#KhenThuong", "#K46"],
            "ocr_text": "BIÊN BẢN HỌP HỘI ĐỒNG XÉT HỌC BỔNG DOANH NGHIỆP TÀI TRỢ KỲ 1.\nThời gian: 08 giờ 30 ngày 05/10/2025 tại Phòng họp A1.\nThành phần: Trưởng phòng CTSV, đại diện các Khoa CNTT, QTKD và đại diện doanh nghiệp đồng hành.\nKết luận: Nhất trí thông qua danh sách 30 sinh viên tiêu biểu nhận học bổng bao gồm Nguyễn Hoàng Nam (20210678).",
            "confidence": 0.975,
        },
        {
            "id": "af5b5a80-e4d1-4613-bc75-3fcfc5bea23f",
            "title": "Danh sách sinh viên đạt chuẩn nhận hỗ trợ chi phí học tập đợt 1 năm 2025",
            "cat_code": "DANH_SACH",
            "student_id": "20210678",
            "student_name": "Nguyễn Hoàng Nam",
            "doc_num": "05/DS-CTSV",
            "doc_date": "2025-09-28",
            "tags": ["#HocPhi", "#MienGiamHocPhi", "#NganhCNTT"],
            "ocr_text": "DANH SÁCH SINH VIÊN NHẬN HỖ TRỢ CHI PHÍ HỌC TẬP VÀ MIỄN GIẢM HỌC PHÍ ĐỢT 1.\nSTT: 01. Họ và tên: Nguyễn Hoàng Nam. MSSV: 20210678. Lớp: CTK46. Mức hỗ trợ: 100% học phí học kỳ 1 theo quy định tại Nghị định 81.",
            "confidence": 0.991,
        },
        {
            "id": "a8215c6d-f053-48b3-a096-7f19a0f58fb3",
            "title": "Quy chế Công tác Sinh viên trường Đại học Đà Lạt ban hành kèm Quyết định 450/QĐ-ĐHĐL",
            "cat_code": "DIEU_LE_QUY_CHE",
            "student_id": None,
            "student_name": None,
            "doc_num": "450/QĐ-ĐHĐL",
            "doc_date": "2024-09-01",
            "tags": ["#XuLyHocVu", "#SinhHoatCongDan"],
            "ocr_text": "QUY CHẾ CÔNG TÁC SINH VIÊN TRƯỜNG ĐẠI HỌC ĐÀ LẠT.\nChương I: Quy định chung về quyền lợi và nghĩa vụ của sinh viên.\nChương II: Đánh giá kết quả rèn luyện, khen thưởng, kỷ luật, xét học bổng và thủ tục miễn giảm học phí, bảo lưu kết quả học tập.",
            "confidence": 0.995,
        },
        {
            "id": "41fd8ae6-1c59-4624-b4da-0ee3d024e904",
            "title": "Đơn xin xét học bổng khuyến khích học tập - Trần Văn An (20210123)",
            "cat_code": "DON_TU",
            "student_id": "20210123",
            "student_name": "Trần Văn An",
            "doc_num": "19/ĐN-HB",
            "doc_date": "2025-09-22",
            "tags": ["#HocBong", "#DonTu", "#K46"],
            "ocr_text": "CỘNG HÒA XÃ HỘI CHỦ NGHĨA VIỆT NAM\nĐộc lập - Tự do - Hạnh phúc\n\nĐƠN XIN XÉT HỌC BỔNG KHUYẾN KHÍCH HỌC TẬP\nKính gửi: Hội đồng xét học bổng Trường Đại học Đà Lạt; Phòng Công tác Sinh viên.\nEm tên là: Trần Văn An. MSSV: 20210123. Sinh viên lớp CTK46.\nĐiểm trung bình học tập học kỳ vừa qua: 3.65 (loại Giỏi). Điểm rèn luyện: 92 (loại Xuất sắc).\nEm kính xin Hội đồng xem xét cấp học bổng khuyến khích học tập kỳ 1 cho em.",
            "confidence": 0.987,
        }
    ]

    now_iso = datetime.now().isoformat()

    for d in docs:
        raw_id = str(d["id"])
        clean_id = raw_id.replace("-", "")
        cat_code = str(d.get("cat_code", "KHAC"))
        cat_id = cat_map.get(cat_code)
        doc_num = d.get("doc_num")
        has_mghp = isinstance(doc_num, str) and "MGHP" in doc_num

        # Xóa bản ghi cũ nếu có
        c.execute("DELETE FROM documents WHERE id = ? OR id = ?", (clean_id, raw_id))
        c.execute("DELETE FROM document_metadata WHERE document_id = ? OR document_id = ?", (clean_id, raw_id))
        c.execute("DELETE FROM ocr_results WHERE document_id = ? OR document_id = ?", (clean_id, raw_id))

        # Insert document
        c.execute("""
            INSERT INTO documents (
                id, title, original_filename, file_type, file_size_bytes,
                minio_object_key, page_count, category_id, uploaded_by,
                ocr_status, is_public, is_deleted, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            clean_id,
            d["title"],
            f"{clean_id[:8]}_{cat_code.lower()}.pdf",
            "PDF",
            102400,
            f"documents/sample_{clean_id[:8]}.pdf",
            1,
            cat_id,
            user_id,
            "APPROVED",
            1, # is_public = True
            0, # is_deleted = False
            f"{d['doc_date']} 08:30:00",
            f"{d['doc_date']} 08:30:00",
        ))

        # Insert metadata
        extra_payload = {
            "tags": d["tags"],
            "priority_score": 10 if has_mghp else 5,
            "document_type": cat_code,
            "trich_yeu": d["title"],
        }
        meta_id = uuid.uuid4().hex
        c.execute("""
            INSERT INTO document_metadata (
                id, document_id, student_id, student_name, document_date,
                document_number, extra, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            meta_id,
            clean_id,
            d["student_id"],
            d["student_name"],
            d["doc_date"],
            d["doc_num"],
            json.dumps(extra_payload, ensure_ascii=False),
            now_iso,
            now_iso,
        ))

        # Insert OCR Result
        ocr_id = uuid.uuid4().hex
        c.execute("""
            INSERT INTO ocr_results (
                id, document_id, is_latest, raw_text, corrected_text,
                confidence_score, ocr_engine, ocr_engine_version,
                processing_time_ms, status, is_corrected, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            ocr_id,
            clean_id,
            1,
            d["ocr_text"],
            d["ocr_text"],
            d["confidence"],
            "vietocr",
            "vgg_transformer",
            450,
            "DONE",
            0,
            now_iso,
            now_iso,
        ))

    conn.commit()
    conn.close()
    print(f"Successfully seeded {len(docs)} rich CTSV documents into data.db!")

if __name__ == "__main__":
    seed()
