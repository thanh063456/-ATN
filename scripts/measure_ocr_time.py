import asyncio
import os
import sys
import time
import sqlite3
from app.services.storage_service import storage_service
from app.services.vietocr_service import vietocr_service

sys.stdout.reconfigure(encoding='utf-8')

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "data.db")

async def measure():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # We want PDFs
    cursor.execute("SELECT id, minio_object_key, file_type FROM documents WHERE file_type LIKE '%pdf%' LIMIT 20")
    docs = cursor.fetchall()
    
    print(f"Found {len(docs)} PDF documents for testing.")
    if not docs:
        return
        
    results = []
    
    for doc in docs:
        doc_id = doc['id']
        key = doc['minio_object_key']
        
        print(f"Downloading {key}...")
        try:
            file_bytes = await asyncio.to_thread(storage_service.get_file, key)
        except Exception as e:
            print(f"Failed to download: {e}")
            continue
            
        print(f"Processing doc {doc_id}...")
        
        # Measure first page
        t0 = time.perf_counter()
        raw1, proc1, conf1, pc1 = await asyncio.to_thread(
            vietocr_service.extract_text_from_file, file_bytes, "pdf", "vietocr", [0]
        )
        t_first = time.perf_counter() - t0
        
        # Measure full pages
        t0 = time.perf_counter()
        raw2, proc2, conf2, pc2 = await asyncio.to_thread(
            vietocr_service.extract_text_from_file, file_bytes, "pdf", "vietocr", None
        )
        t_full = time.perf_counter() - t0
        
        results.append({
            'id': doc_id,
            'pages': pc2,
            'first_page_s': t_first,
            'full_s': t_full
        })
        print(f"  Pages: {pc2} | First Page: {t_first:.2f}s | Full: {t_full:.2f}s")
        
    if results:
        avg_first = sum(r['first_page_s'] for r in results) / len(results)
        avg_full = sum(r['full_s'] for r in results) / len(results)
        print("\n--- Summary ---")
        print(f"Average First Page OCR Time: {avg_first:.2f}s")
        print(f"Average Full OCR Time: {avg_full:.2f}s")

if __name__ == "__main__":
    asyncio.run(measure())
