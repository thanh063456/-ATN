import sqlite3
import os
import csv
import re
import sys

# Ensure stdout uses UTF-8
sys.stdout.reconfigure(encoding='utf-8')

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "data.db")
OUTPUT_DIR = os.path.join(BASE_DIR, "data_private", "work", "doctype")
OUTPUT_FILE = os.path.join(OUTPUT_DIR, "gt_weak.csv")

def extract_type_from_filename(filename: str) -> str:
    if not filename:
        return "UNKNOWN"
        
    fn_lower = filename.lower()
    
    # Keyword mapping
    if "thong_bao" in fn_lower or "thong-bao" in fn_lower:
        return "THONG_BAO"
    if "ke_hoach" in fn_lower or "ke-hoach" in fn_lower:
        return "KE_HOACH"
    if "quyet_dinh" in fn_lower or "quyet-dinh" in fn_lower:
        return "QUYET_DINH"
    if "cong_van" in fn_lower or "cong-van" in fn_lower or "kinh_gui" in fn_lower:
        return "CONG_VAN"
    if "danh_sach" in fn_lower or "danh-sach" in fn_lower:
        return "DANH_SACH"
    if "dieu_le" in fn_lower or "dieu-le" in fn_lower:
        return "DIEU_LE_QUY_CHE"
    if "nhac_lich" in fn_lower or "nhac-lich" in fn_lower:
        return "CONG_VAN" # Hoặc KHAC tuỳ, user bảo "Nhạc lịch/huy động...". Ta quy vào KHAC hoặc CONG_VAN.
        
    return "UNKNOWN"

def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute("SELECT id, original_filename FROM documents")
    rows = cursor.fetchall()
    
    results = []
    for row in rows:
        doc_id = row['id']
        filename = row['original_filename']
        
        weak_label = extract_type_from_filename(filename)
        results.append({
            'doc_id': doc_id,
            'weak_label': weak_label,
            'source': 'filename_heuristic'
        })
        
    with open(OUTPUT_FILE, 'w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['doc_id', 'weak_label', 'source'])
        writer.writeheader()
        writer.writerows(results)
        
    print(f"Total documents processed: {len(results)}")
    
    # Count distribution
    counts = {}
    for r in results:
        counts[r['weak_label']] = counts.get(r['weak_label'], 0) + 1
        
    for k, v in counts.items():
        print(f" - {k}: {v}")

if __name__ == "__main__":
    main()
