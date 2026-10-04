import re
import sys
import traceback
import argparse
from pathlib import Path

# Adjust path to import backend
_REPO_ROOT = Path(__file__).resolve().parent.parent
_BACKEND = _REPO_ROOT / "backend"
sys.path.insert(0, str(_BACKEND))

import app.core.config  # ensure env is loaded

_original_compile = re.compile

def patched_compile(pattern, flags=0):
    try:
        return _original_compile(pattern, flags)
    except re.error as e:
        print("==="*10)
        print(f"Regex error caught during compile!")
        print(f"Pattern: {pattern!r}")
        print(f"Error: {e}")
        print("Traceback:")
        traceback.print_stack()
        print("==="*10)
        raise

re.compile = patched_compile

def patch_re_func(func_name):
    orig_func = getattr(re, func_name)
    def wrapper(pattern, *args, **kwargs):
        try:
            return orig_func(pattern, *args, **kwargs)
        except re.error as e:
            print("==="*10)
            print(f"Regex error caught during {func_name}!")
            print(f"Pattern: {pattern!r}")
            print(f"Error: {e}")
            print("Traceback:")
            traceback.print_stack()
            print("==="*10)
            raise
    setattr(re, func_name, wrapper)

for name in ('sub', 'search', 'findall', 'split', 'fullmatch', 'finditer'):
    patch_re_func(name)

def run():
    parser = argparse.ArgumentParser()
    parser.add_argument("--text-file", type=str, help="Path to real TrOCR raw text file")
    args = parser.parse_args()

    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
        
    print("Step 2c: Statically compile EVERY regex built dynamically...")
    from app.core.config import settings
    try:
        re.compile(settings.mssv_year_prefix_pattern)
    except re.error as e:
        print(f"Error compiling mssv_year_prefix_pattern: {e}")

    # Text postprocessing patterns
    from app.services.text_postprocessing.ocr_char_fixes import OCR_CHAR_RULES
    for pat, rep, flags, desc in OCR_CHAR_RULES:
        try:
            re.compile(pat, flags)
        except re.error as e:
            print(f"Error compiling OCR_CHAR_RULES '{desc}': {e} for pat={pat!r}")
            
    from app.services.text_postprocessing.document_header_normalizer import _NATIONAL_HEADER_PATTERNS
    for pat, rep in _NATIONAL_HEADER_PATTERNS:
        try:
            re.compile(pat, re.IGNORECASE)
        except re.error as e:
            print(f"Error compiling _NATIONAL_HEADER_PATTERNS: {e} for pat={pat!r}")

    # Extraction patterns
    from app.services.extraction_service import ExtractionService
    
    # Check Admin dictionary
    from app.services.text_postprocessing.admin_dictionary import _load_dictionary, _build_correction_regex
    data = _load_dictionary("")
    for entry in data.get("char_corrections", []):
        try:
            _build_correction_regex(entry)
        except Exception as e:
            print(f"Error compiling admin dictionary entry {entry}: {e}")

    print("\nStep 2b: Test garbage strings...")
    from app.services.text_postprocessing import post_process_vietnamese
    from app.services.extraction_service import extraction_service
    from app.services.trocr_service import trocr_service
    
    test_cases = [
        "Normal string 123",
        "**??+*{}[][]()\\|",
        "* error case",
        "+ nothing to repeat",
        "nothing to repeat at position 18 *",
        "CTSV_013_2025-09-03-Ke_hoach_Trien_khai_0_1435-KH-DHDL_Ke_hoach_Bao_hi_p01.png",
        "10 4 - - - 1 sơn 1 sơn\n22.9 Thị Thứ Thị Thức\nBỘ GIÁO DỤC VÀ ĐÀO TẠO"
    ]
    if args.text_file:
        try:
            with open(args.text_file, "r", encoding="utf-8") as f:
                test_cases.append(f.read())
        except Exception as e:
            print(f"Failed to read --text-file: {e}")
    
    for case in test_cases:
        try:
            print(f"\n[Case] {case[:50]!r}...")
            trocr_service.heuristic_quality_score(case)
            trocr_service.post_process_vietnamese(case)
            trocr_service._is_noise_line(case)
            post_process_vietnamese(case)
            extraction_service.extract_metadata(case)
        except re.error:
            pass  # Already printed by patches
        except Exception as e:
            print(f"  Caught other error: {e}")

if __name__ == "__main__":
    run()
