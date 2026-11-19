import sqlite3
import os
import csv
import sys
import json
import random

sys.stdout.reconfigure(encoding='utf-8')

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "data.db")
OUTPUT_DIR = os.path.join(BASE_DIR, "data_private", "work", "doctype")
OUTPUT_FILE = os.path.join(OUTPUT_DIR, "gt_verified.csv")

def get_weak_label(filename):
    if not filename: return "UNKNOWN"
    fn = filename.lower()
    if "thong_bao" in fn or "thong-bao" in fn: return "THONG_BAO"
    if "ke_hoach" in fn or "ke-hoach" in fn: return "KE_HOACH"
    if "quyet_dinh" in fn or "quyet-dinh" in fn: return "QUYET_DINH"
    if "cong_van" in fn or "cong-van" in fn or "kinh_gui" in fn: return "CONG_VAN"
    if "danh_sach" in fn or "danh-sach" in fn: return "DANH_SACH"
    if "dieu_le" in fn or "dieu-le" in fn: return "DIEU_LE_QUY_CHE"
    if "nhac_lich" in fn or "nhac-lich" in fn: return "CONG_VAN"
    return "UNKNOWN"

def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # Query docs and their latest OCR results
    query = """
    SELECT d.id, d.original_filename, o.raw_text, o.page_texts 
    FROM documents d
    LEFT JOIN ocr_results o ON d.id = o.document_id AND o.is_latest = 1
    """
    cursor.execute(query)
    rows = cursor.fetchall()
    
    # Randomly select up to 150
    random.seed(42) # frozen set
    sample = random.sample(rows, min(150, len(rows)))
    
    results = []
    
    for row in sample:
        doc_id = row['id']
        filename = row['original_filename']
        weak_label = get_weak_label(filename)
        
        page1_text = ""
        if row['page_texts']:
            try:
                pages = json.loads(row['page_texts'])
                if isinstance(pages, list) and len(pages) > 0:
                    page1_text = pages[0]
            except Exception:
                pass
                
        if not page1_text and row['raw_text']:
            page1_text = row['raw_text'][:600]
            
        # Clean up text for printing
        header = "\n".join([line for line in page1_text.splitlines() if line.strip()][:20])
        
        print("="*60)
        print(f"Doc ID: {doc_id}")
        print(f"Weak Label: {weak_label}")
        print(f"Header Text:\n{header}\n")
        
        results.append({
            'doc_id': doc_id,
            'weak_label': weak_label,
            'verified_label': weak_label # Placeholder for manual review
        })
        
    # Write to CSV
    # If the file exists, we shouldn't overwrite verified_labels if they already exist,
    # but for this script, we just generate it once.
    if not os.path.exists(OUTPUT_FILE):
        with open(OUTPUT_FILE, 'w', encoding='utf-8', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=['doc_id', 'weak_label', 'verified_label'])
            writer.writeheader()
            writer.writerows(results)
        print(f"\n[INFO] Generated {OUTPUT_FILE}. Please review and update 'verified_label'.")
    else:
        print(f"\n[INFO] {OUTPUT_FILE} already exists. Skipping overwrite to preserve manual edits.")

if __name__ == "__main__":
    main()
