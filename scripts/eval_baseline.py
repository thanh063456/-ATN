import csv
import os
import sys
import sqlite3
import json
from collections import defaultdict

sys.stdout.reconfigure(encoding='utf-8')

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "data.db")
CSV_PATH = os.path.join(BASE_DIR, "data_private", "work", "doctype", "gt_verified.csv")

def baseline_classify(text):
    if not text:
        return "UNKNOWN"
    tl = text.lower()
    if "kế hoạch" in tl or "kh-đhđl" in tl:
        return "KE_HOACH"
    elif "thông báo" in tl or "tb-đhđl" in tl:
        return "THONG_BAO"
    elif "quyết định" in tl or "qđ-đhđl" in tl:
        return "QUYET_DINH"
    elif "hướng dẫn" in tl or "hd-đhđl" in tl:
        return "HUONG_DAN"
    elif "nghỉ học" in tl or "bảo lưu" in tl:
        return "DON_NGHI_HOC"
    elif "học bổng" in tl:
        return "HOC_BONG"
    elif "miễn giảm học phí" in tl:
        return "MIEN_GIAM_HOC_PHI"
    elif "bảo hiểm y tế" in tl or "bhyt" in tl:
        return "BHYT"
    elif "xác nhận" in tl:
        return "GIAY_XAC_NHAN"
    elif "khen thưởng" in tl or "kỷ luật" in tl:
        return "KHEN_THUONG"
    return "UNKNOWN"

def print_metrics(y_true, y_pred, title):
    print(f"\n--- {title} ---")
    correct = sum(1 for t, p in zip(y_true, y_pred) if t == p)
    total = len(y_true)
    accuracy = correct / total if total > 0 else 0
    print(f"Overall Accuracy: {accuracy:.2%} ({correct}/{total})")
    
    classes = sorted(list(set(y_true) | set(y_pred)))
    
    # Confusion Matrix
    print("\nConfusion Matrix (True \\ Predicted):")
    print(f"{'True Label':<20} | " + " | ".join(f"{c:<15}" for c in classes))
    print("-" * 120)
    
    matrix = defaultdict(lambda: defaultdict(int))
    for t, p in zip(y_true, y_pred):
        matrix[t][p] += 1
        
    for t in classes:
        row = f"{t:<20} | "
        for p in classes:
            row += f"{matrix[t][p]:<15} | "
        print(row)
        
    # Per-class accuracy
    print("\nPer-class Accuracy:")
    for c in classes:
        true_c = sum(1 for t in y_true if t == c)
        if true_c > 0:
            correct_c = matrix[c][c]
            print(f" - {c}: {correct_c/true_c:.2%} ({correct_c}/{true_c})")

def main():
    if not os.path.exists(CSV_PATH):
        print(f"Error: {CSV_PATH} not found.")
        return
        
    y_true = []
    y_pred_full = []
    y_pred_page1 = []
    
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    with open(CSV_PATH, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            doc_id = row['doc_id']
            # Treat verified_label as ground truth. If it's missing or UNKNOWN, skip?
            label = row.get('verified_label', '').strip()
            if not label or label == "UNKNOWN":
                continue
                
            cursor.execute("SELECT raw_text, page_texts FROM ocr_results WHERE document_id = ? AND is_latest = 1", (doc_id,))
            res = cursor.fetchone()
            if not res:
                continue
                
            full_text = res['raw_text'] or ""
            page1_text = full_text
            
            if res['page_texts']:
                try:
                    pages = json.loads(res['page_texts'])
                    if isinstance(pages, list) and len(pages) > 0:
                        page1_text = pages[0]
                except Exception:
                    pass
                    
            y_true.append(label)
            y_pred_full.append(baseline_classify(full_text))
            y_pred_page1.append(baseline_classify(page1_text))
            
    print_metrics(y_true, y_pred_full, "BASELINE: FULL TEXT")
    print_metrics(y_true, y_pred_page1, "BASELINE: PAGE 1 ONLY")

if __name__ == "__main__":
    main()
