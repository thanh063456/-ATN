import os
import sys
import json
import csv
from collections import defaultdict
def format_table(headers, rows):
    col_widths = [len(h) for h in headers]
    for row in rows:
        for i, val in enumerate(row):
            col_widths[i] = max(col_widths[i], len(str(val)))
    
    border = "+" + "+".join(["-" * (w + 2) for w in col_widths]) + "+"
    header_row = "|" + "|".join([f" {headers[i]:<{col_widths[i]}} " for i in range(len(headers))]) + "|"
    
    out = [border, header_row, border]
    for row in rows:
        r_str = "|" + "|".join([f" {str(row[i]):<{col_widths[i]}} " for i in range(len(row))]) + "|"
        out.append(r_str)
    out.append(border)
    return "\n".join(out)

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend")))

from app.services.doctype_service import doctype_service

def old_whole_text_classify(full_text: str) -> str:
    """Mô phỏng bộ phân loại cũ (tìm từ khóa trên toàn bộ văn bản)."""
    t = full_text.lower()
    if "quyết định" in t or "quyet dinh" in t:
        return "QUYET_DINH"
    if "kế hoạch" in t or "ke hoach" in t:
        return "KE_HOACH"
    if "thông báo" in t or "thong bao" in t:
        return "THONG_BAO"
    if "công văn" in t or "kính gửi" in t:
        return "CONG_VAN"
    if "giấy xác nhận" in t or "xác nhận" in t:
        return "GIAY_XAC_NHAN"
    if "đơn xin" in t or "đơn đề nghị" in t:
        return "DON_TU"
    if "danh sách" in t:
        return "DANH_SACH"
    if "điều lệ" in t or "quy chế" in t:
        return "DIEU_LE_QUY_CHE"
    return "KHAC"

def run_trap_tests():
    print("=" * 60)
    print("1. RUNNING TRAP & NOISY OCR TESTS")
    print("=" * 60)
    
    traps = [
        # 1. Quyết định whose body mentions kế hoạch
        ("Quyết định có thân bài nhắc 'kế hoạch'", 
         "TRƯỜNG ĐH BÁCH KHOA\nSố: 123/QĐ-BKHN\nQUYẾT ĐỊNH\nVề việc phê duyệt kế hoạch\nĐiều 1: Phê duyệt kế hoạch học tập năm 2026.", 
         "QUYET_DINH"),
        
        # 2. Thông báo mentioning đơn
        ("Thông báo nhắc tới 'nộp đơn'",
         "TRƯỜNG ĐH BÁCH KHOA\nSố: 456/TB-ĐHBK\nTHÔNG BÁO\nVề việc nộp đơn xin học bổng\nCác sinh viên nộp đơn trước ngày 15.",
         "THONG_BAO"),
         
        # 3. Kế hoạch mentioning học bổng
        ("Kế hoạch nhắc 'học bổng'",
         "TRƯỜNG ĐH BÁCH KHOA\nSố: 789/KH-ĐHBK\nKẾ HOẠCH\nTổ chức xét học bổng học kỳ 1\nMục tiêu: Động viên sinh viên.",
         "KE_HOACH"),
         
        # 4. Công văn with no title (Kính gửi + V/v)
        ("Công văn không có tiêu đề lớn (Kính gửi + V/v)",
         "TRƯỜNG ĐH BÁCH KHOA\nSố: 12/CV-ĐHBK\nKính gửi: Ban giám hiệu\nV/v: Xin tổ chức sự kiện chào tân sinh viên\nCăn cứ nhu cầu sinh viên...",
         "CONG_VAN"),
         
        # 5. Noisy OCR: TRUNG ĐẠI HỌC
        ("Noisy OCR: 'TRUNG ĐẠI HỌC' thay vì TRƯỜNG ĐẠI HỌC",
         "TRUNG ĐẠI HỌC ĐÀ LẠT\nPHÒNG CTSV\nGIẤY XÁC NHẬN\nChứng nhận sinh viên đang theo học tại trường.",
         "GIAY_XAC_NHAN"),
         
        # 6. Noisy OCR: Không dấu (QUYET DINH)
        ("Noisy OCR: Tiêu đề và số hiệu không dấu",
         "BO GIAO DUC VA DAO TAO\nSO: 123/QD-DHDL\nQUYET DINH\nVe viec khen thuong sinh vien xuat sac\nDieu 1: Tang giay khen...",
         "QUYET_DINH"),
         
        # 7. Noisy OCR: Dấu '?' thay cho gạch ngang/gạch chéo
        ("Noisy OCR: Dấu '?' trong số hiệu văn bản",
         "BỘ GIÁO DỤC VÀ ĐÀO TẠO\nSố: 456?TB?ĐHĐL\nTHÔNG BÁO\nVề việc đăng ký môn học học kỳ 2...",
         "THONG_BAO"),
         
        # 8. Noisy OCR: Ký tự số bị nhận diện nhầm (l23/QĐ)
        ("Noisy OCR: Ký tự số nhầm thành 'l' (l23/QĐ)",
         "BỘ GIÁO DỤC VÀ ĐÀO TẠO\nSố: l23/QĐ-ĐHĐL\nQUYẾT ĐỊNH\nVề việc công nhận tốt nghiệp...",
         "QUYET_DINH")
    ]
    
    passed = 0
    for name, text, expected in traps:
        res = doctype_service.classify(text)
        old_pred = old_whole_text_classify(text)
        status = "PASSED" if res.code == expected else "FAILED"
        if status == "PASSED":
            passed += 1
        print(f"[{status}] {name} -> Got: {res.code} (Conf: {res.confidence}) | Expected: {expected} | Old: {old_pred}")
        
    print(f"\nTrap Tests Summary: {passed}/{len(traps)} passed.\n")
    assert passed == len(traps), "Not all trap tests passed!"

# Frozen dataset representing real page 1 document templates
FROZEN_PAGE1_BENCHMARK = [
    # THONG_BAO
    ("THONG_BAO", "BỘ GIÁO DỤC VÀ ĐÀO TẠO\nTRƯỜNG ĐẠI HỌC ĐÀ LẠT\nSố: 1413/TB-ĐHĐL\nTHÔNG BÁO\nVề việc cảnh giác với các thủ đoạn tội phạm lừa đảo\nKính gửi các đơn vị..."),
    ("THONG_BAO", "TRƯỜNG ĐẠI HỌC ĐÀ LẠT\nSố: 209/TB-CTSV\nTHÔNG BÁO\nVề việc gia hạn đóng học phí học kỳ 1 năm học 2026\nNay thông báo đến sinh viên toàn trường..."),
    ("THONG_BAO", "BỘ GIÁO DỤC VÀ ĐÀO TẠO\nSố: 88/TB-BGDĐT\nTHÔNG BÁO\nVề việc tổ chức kỳ thi Olympic Tin học sinh viên 2026..."),
    ("THONG_BAO", "TRƯỜNG ĐH ĐÀ LẠT\nSố: 55/TB\nTHÔNG BÁO\nVề việc nhận bằng tốt nghiệp đợt 2..."),
    
    # KE_HOACH
    ("KE_HOACH", "BỘ GIÁO DỤC VÀ ĐÀO TẠO\nTRƯỜNG ĐẠI HỌC ĐÀ LẠT\nSố: 1353/KH-ĐHĐL\nKẾ HOẠCH\nTổ chức nhập học cho sinh viên khóa 49 trúng tuyển\nI. Mục đích yêu cầu..."),
    ("KE_HOACH", "TRƯỜNG ĐẠI HỌC ĐÀ LẠT\nSố: 45/KH-CTSV\nKẾ HOẠCH\nKiểm tra sức khỏe đầu khóa cho sinh viên K49\n1. Mục tiêu và phạm vi..."),
    ("KE_HOACH", "TRƯỜNG ĐẠI HỌC ĐÀ LẠT\nSố: 78/KH-ĐHĐL\nKẾ HOẠCH\nThực tập tốt nghiệp và làm khóa luận năm 2026..."),
    
    # QUYET_DINH
    ("QUYET_DINH", "BỘ GIÁO DỤC VÀ ĐÀO TẠO\nTRƯỜNG ĐẠI HỌC ĐÀ LẠT\nSố: 588/QĐ-ĐHĐL\nQUYẾT ĐỊNH\nVề việc cấp học bổng khuyến khích học tập kỳ 2\nHIỆU TRƯỞNG TRƯỜNG ĐẠI HỌC ĐÀ LẠT\nCăn cứ quy chế đào tạo..."),
    ("QUYET_DINH", "BỘ GIÁO DỤC VÀ ĐÀO TẠO\nSố: 102/QĐ-ĐHĐL\nQUYẾT ĐỊNH\nVề việc khen thưởng sinh viên có thành tích xuất sắc\nĐiều 1: Tặng giấy khen cho 15 sinh viên..."),
    ("QUYET_DINH", "BỘ GIÁO DỤC\nSố: 99/QĐ-BGDĐT\nQUYẾT ĐỊNH\nBan hành quy định công tác sinh viên đối với cơ sở giáo dục..."),
    
    # CONG_VAN
    ("CONG_VAN", "BỘ GIÁO DỤC VÀ ĐÀO TẠO\nTRƯỜNG ĐẠI HỌC ĐÀ LẠT\nSố: 1290/CV-ĐHĐL\nKính gửi: Các khoa chuyên môn\nV/v: Báo cáo số liệu sinh viên tốt nghiệp năm 2026\nThực hiện chỉ đạo của Ban Giám hiệu..."),
    ("CONG_VAN", "TRƯỜNG ĐH ĐÀ LẠT\nPHÒNG CÔNG TÁC SINH VIÊN\nSố: 14/CV-CTSV\nKính gửi: Ngân hàng Chính sách Xã hội Tỉnh Lâm Đồng\nV/v xác nhận danh sách sinh viên vay vốn tín dụng..."),
    ("CONG_VAN", "UBND TỈNH LÂM ĐỒNG\nSố: 512/UBND-VX\nKính gửi: Trường Đại học Đà Lạt\nV/v phối hợp tổ chức Festival Hoa Đà Lạt 2026..."),
    
    # GIAY_XAC_NHAN
    ("GIAY_XAC_NHAN", "TRƯỜNG ĐẠI HỌC ĐÀ LẠT\nPHÒNG CÔNG TÁC SINH VIÊN\nGIẤY XÁC NHẬN\nPhòng CTSV chứng nhận sinh viên: Nguyễn Văn A\nMSSV: 2210123, sinh ngày 01/01/2004..."),
    ("GIAY_XAC_NHAN", "TRƯỜNG ĐẠI HỌC ĐÀ LẠT\nGIẤY XÁC NHẬN\nChứng nhận sinh viên hiện đang theo học hệ đại học chính quy..."),
    
    # DON_TU
    ("DON_TU", "CỘNG HÒA XÃ HỘI CHỦ NGHĨA VIỆT NAM\nĐộc lập - Tự do - Hạnh phúc\nĐƠN XIN NGHỈ HỌC TẠM THỜI\nKính gửi: Ban Giám hiệu Trường ĐH Đà Lạt\nEm tên là: Lê Thị Mai, MSSV: 2110456..."),
    ("DON_TU", "CỘNG HÒA XÃ HỘI CHỦ NGHĨA VIỆT NAM\nĐƠN XIN CẤP HỌC BỔNG\nKính gửi: Phòng Công tác Sinh viên\nTên em là: Trần Đức Bo, sinh viên lớp CTK45..."),
    ("DON_TU", "CỘNG HÒA XÃ HỘI CHỦ NGHĨA VIỆT NAM\nĐƠN ĐỀ NGHỊ MIỄN GIẢM HỌC PHÍ\nKính gửi: Hội đồng xét miễn giảm học phí\nHọ và tên: Hoàng Văn Thái, MSSV: 2310789..."),
    
    # DANH_SACH
    ("DANH_SACH", "TRƯỜNG ĐẠI HỌC ĐÀ LẠT\nDANH SÁCH\nSinh viên được nhận học bổng tài trợ doanh nghiệp năm học 2025-2026\nSTT | Họ và tên | MSSV | Lớp | Số tiền..."),
    ("DANH_SACH", "DANH SÁCH SINH VIÊN THAM GIA HOẠT ĐỘNG TÌNH NGUYỆN\nSTT | Mã sinh viên | Họ tên | Khoa..."),
    
    # DIEU_LE_QUY_CHE
    ("DIEU_LE_QUY_CHE", "TRƯỜNG ĐẠI HỌC ĐÀ LẠT\nQUY CHẾ\nĐào tạo trình độ đại học theo hệ thống tín chỉ\nChương I: Quy định chung\nĐiều 1. Phạm vi áp dụng..."),
    
    # BIEN_BAN
    ("BIEN_BAN", "CỘNG HÒA XÃ HỘI CHỦ NGHĨA VIỆT NAM\nBIÊN BẢN BÀN GIAO CƠ SỞ VẬT CHẤT\nHôm nay ngày 10 tháng 10 năm 2026, tại phòng Lab 1..."),

    # KHAC
    ("KHAC", "THƯ CẢM ƠN\nKính gửi các nhà hảo tâm đã tài trợ chương trình..."),
    ("KHAC", "Tài liệu lưu trữ nội bộ không có tiêu đề quy chuẩn."),
    ("KHAC", "TÀI LIỆU TUYÊN TRUYỀN\nNội dung giới thiệu tài liệu..."),
]

def run_benchmark_evaluation():
    print("=" * 60)
    print("2. RUNNING FROZEN BENCHMARK EVALUATION (FIRST-PAGE ONLY)")
    print("=" * 60)
    
    confusion_matrix = defaultdict(lambda: defaultdict(int))
    
    y_true = []
    y_pred_new = []
    y_pred_old = []
    needs_review_count = 0
    
    for expected, text in FROZEN_PAGE1_BENCHMARK:
        y_true.append(expected)
        res = doctype_service.classify(text)
        pred_code = res.code
        if pred_code == "QUYẾT ĐỊNH": pred_code = "QUYET_DINH"
        y_pred_new.append(pred_code)
        confusion_matrix[expected][pred_code] += 1
        
        if res.confidence < 0.70 or pred_code == "KHAC":
            needs_review_count += 1
            
        old_pred = old_whole_text_classify(text)
        y_pred_old.append(old_pred)

    all_classes = sorted(list(set(y_true + y_pred_new)))

    total_samples = len(y_true)
    correct_new = sum(1 for yt, yp in zip(y_true, y_pred_new) if yt == yp)
    correct_old = sum(1 for yt, yp in zip(y_true, y_pred_old) if yt == yp)
    
    acc_new = correct_new / total_samples
    acc_old = correct_old / total_samples
    pct_needs_review = (needs_review_count / total_samples) * 100
    
    # Calculate Precision, Recall, F1 per class
    metrics_table = []
    for cls in all_classes:
        tp = confusion_matrix[cls][cls]
        fp = sum(confusion_matrix[other][cls] for other in all_classes if other != cls)
        fn = sum(confusion_matrix[cls][other] for other in all_classes if other != cls)
        
        prec = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        rec = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        f1 = (2 * prec * rec) / (prec + rec) if (prec + rec) > 0 else 0.0
        support = sum(confusion_matrix[cls].values())
        
        metrics_table.append([cls, f"{prec:.2f}", f"{rec:.2f}", f"{f1:.2f}", support])
        
    print("\nPER-CLASS ACCURACY & METRICS:")
    print(format_table(["Class", "Precision", "Recall", "F1", "Support"], metrics_table))
    
    print(f"\nOVERALL ACCURACY:")
    print(f" - NEW First-Page Classifier: {acc_new * 100:.2f}% ({correct_new}/{total_samples})")
    print(f" - OLD Whole-Text Classifier: {acc_old * 100:.2f}% ({correct_old}/{total_samples})")
    print(f" - Needs Review Rate:         {pct_needs_review:.2f}% ({needs_review_count}/{total_samples})")
    
    # Print Confusion Matrix
    print("\nCONFUSION MATRIX (Rows: True, Cols: Predicted):")
    header = ["True \\ Pred"] + all_classes
    matrix_rows = []
    for true_cls in all_classes:
        row = [true_cls]
        for pred_cls in all_classes:
            row.append(confusion_matrix[true_cls][pred_cls])
        matrix_rows.append(row)
    print(format_table(header, matrix_rows))
    
    assert acc_new >= 0.95, f"Accuracy {acc_new * 100:.2f}% is lower than required 95%!"
    print("\n[SUCCESS] Frozen benchmark accuracy >= 95% threshold achieved!\n")

def main():
    run_trap_tests()
    run_benchmark_evaluation()

if __name__ == "__main__":
    main()
