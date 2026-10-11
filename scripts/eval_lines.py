import sys
sys.stdout.reconfigure(encoding='utf-8')
import os


# Ensure backend path is in sys.path
backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../backend"))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from app.services.vietocr_service import vietocr_service

def load_text(path):
    with open(path, "r", encoding="utf-8") as f:
        return f.read().strip()

def main():
    os.environ['OCR_DEBUG_DUMP'] = '1'
    gold_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../tests/data/gold_thong_bao_1413.txt"))
    gold_text = load_text(gold_path)
    
    pdf_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../uploads/documents/508fc54d-e7fc-4b7b-ba93-a123660c387f_0_Canh_giac_thu_doan_toi_pham.pdf"))
    if not os.path.exists(pdf_path):
        # Fallback to image
        pdf_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../dataset/images/CTSV_020_2025-09-04-Thong_bao_Ve_viec_c_0_Canh_giac_thu_doan_toi_pham_p01.png"))
        
    with open(pdf_path, "rb") as f:
        file_bytes = f.read()
    
    file_ext = os.path.splitext(pdf_path)[1].replace(".", "").lower()
    if file_ext == "png":
        file_ext = "image/png"
    elif file_ext == "pdf":
        file_ext = "application/pdf"
        
    raw_text, processed_text, conf = vietocr_service.extract_text_from_file(file_bytes, file_ext)
    
    import re
    import editdistance
    
    # Normalize spaces and newlines
    norm_gold = re.sub(r'\s+', ' ', gold_text).strip().lower()
    norm_pred = re.sub(r'\s+', ' ', processed_text).strip().lower()
    
    cer = editdistance.eval(norm_gold, norm_pred) / max(len(norm_gold), 1)
    
    print("--- OCR Result (Processed) ---")
    print(processed_text)
    print("------------------------------")
    print(f"CER: {cer*100:.2f}%")
    print("Missing Lines: Check manually for now.")
    print("Junk Lines: Check manually for now.")

if __name__ == "__main__":
    main()
