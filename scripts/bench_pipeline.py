import os
import sys
import time
import json
import argparse
from pathlib import Path

# Thêm đường dẫn tới backend vào sys.path để import
backend_dir = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_dir))

from app.services.vietocr_service import vietocr_service
from app.services.trocr_service import trocr_service
from PIL import Image

def get_files_to_test(data_dir: Path):
    pdf_files = list(data_dir.rglob("*.pdf"))
    if pdf_files:
        return pdf_files
    # Fallback to PNGs
    return list(data_dir.rglob("*.png"))

def compute_cer(hyp: str, ref: str) -> float:
    import Levenshtein
    if not ref:
        return 1.0 if hyp else 0.0
    return Levenshtein.distance(hyp, ref) / len(ref)

def compute_wer(hyp: str, ref: str) -> float:
    import Levenshtein
    hyp_words = hyp.split()
    ref_words = ref.split()
    if not ref_words:
        return 1.0 if hyp_words else 0.0
    return Levenshtein.distance(hyp_words, ref_words) / len(ref_words)

def run_benchmark(data_dir: Path):
    print(f"Running benchmark on {data_dir}...")
    gold_path = data_dir / "gold.txt"
    if not gold_path.exists():
        print(f"Warning: {gold_path} not found.")
        gold_text = ""
        gold_lines = []
    else:
        with open(gold_path, "r", encoding="utf-8") as f:
            gold_text = f.read().strip()
        gold_lines = [line.strip() for line in gold_text.split("\n") if line.strip()]

    files = get_files_to_test(data_dir)
    if not files:
        print(f"No PDF or PNG files found in {data_dir}.")
        return

    # Sort files
    files.sort()
    
    t0 = time.time()
    extracted_texts = []
    total_crops = 0
    total_junk = 0
    
    # Process files
    for f in files:
        if f.suffix.lower() == ".pdf":
            raw, proc, conf = vietocr_service.extract_text_from_file(f.read_bytes(), "pdf", "vietocr")
            extracted_texts.append(proc)
        else:
            img = Image.open(f).convert("RGB")
            raw, proc = vietocr_service._ocr_image(img, is_first_page=True)
            extracted_texts.append(proc)
            
        # Parse debug dump if available
        dump_path = data_dir / f"{f.stem}_dump.json"
        if dump_path.exists():
            with open(dump_path, "r", encoding="utf-8") as dump_f:
                dump_data = json.load(dump_f)
                total_crops += len(dump_data)
                total_junk += sum(1 for d in dump_data if d.get("drop_reason"))

    total_time = time.time() - t0
    final_text = "\n\n".join(extracted_texts).strip()
    
    cer = compute_cer(final_text, gold_text)
    wer = compute_wer(final_text, gold_text)
    
    # Check missing lines
    missing_lines = []
    import Levenshtein
    hyp_lines = [line.strip() for line in final_text.split("\n") if line.strip()]
    for g_line in gold_lines:
        best_match = 0
        for h_line in hyp_lines:
            dist = Levenshtein.distance(g_line, h_line)
            sim = 1.0 - (dist / max(len(g_line), len(h_line), 1))
            if sim > best_match:
                best_match = sim
        if best_match < 0.6:
            missing_lines.append(g_line)

    print("-" * 50)
    print(f"Total time: {total_time:.2f}s")
    print(f"Total crops: {total_crops}")
    print(f"Junk lines: {total_junk}")
    print(f"CER: {cer:.4f}")
    print(f"WER: {wer:.4f}")
    print(f"Missing lines ({len(missing_lines)}):")
    for ml in missing_lines:
        print(f"  - {ml}")
    print("-" * 50)
    
    return {
        "time": total_time,
        "crops": total_crops,
        "junk": total_junk,
        "cer": cer,
        "wer": wer,
        "missing": len(missing_lines)
    }

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-dir", type=str, default="backend/tests/data/thong_bao_1413")
    args = parser.parse_args()
    
    try:
        import Levenshtein
    except ImportError:
        import subprocess
        subprocess.check_call([sys.executable, "-m", "pip", "install", "Levenshtein"])
        
    os.environ["OCR_DEBUG_DUMP"] = "1"
    run_benchmark(Path(args.data_dir))
