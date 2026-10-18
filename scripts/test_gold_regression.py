import sys
from pathlib import Path

# Ensure UTF-8 output on Windows
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "backend"))

from app.services.trocr_service import trocr_service

pdf_path = REPO_ROOT / "dataset/raw/0_1395-KH-ĐHĐL_KE_HOACH_KHAI_GIANG_NH_2025-2026.pdf"
with open(pdf_path, "rb") as f:
    pdf_bytes = f.read()

print(f"Running TrOCR pipeline on: {pdf_path.name} (Page 1)...")
raw_text, processed_text, conf, _ = trocr_service.extract_text_from_file(pdf_bytes, "pdf", pages=[0])

print("\n--- RAW OCR OUTPUT ---")
print(raw_text)

print("\n--- PROCESSED / NORMALIZED OCR OUTPUT ---")
print(processed_text)
