# OCR Engine Benchmark

| Engine | Test Set | CER (%) | WER (%) | Speed (sec/line) | Notes |
|---|---|---|---|---|---|
| **VietOCR (current)** | Printed Real (CTSV) | ~1.5 - 3.0 | ~3.0 - 5.0 | ~0.08 | Very accurate on printed; struggles if skew is severe. |
| **VietOCR (current)** | Handwriting | > 30.0 | > 50.0 | ~0.08 | Hallucinates heavily on digits/dates in handwriting. |
| **Tesseract (v5, vie)** | Printed Real (CTSV) | ~3.0 - 6.0 | ~5.0 - 8.0 | ~0.02 | High accuracy, fast, handles paragraphs well. |
| **Tesseract (v5, vie)** | Handwriting | > 50.0 | > 70.0 | ~0.02 | Emits junk/gibberish (e.g. `Í+42`). Handled via masking. |
| **TrOCR (English Baseline)**| All | > 80.0 | > 90.0 | ~0.15 | Output is English "receipt" text. Loses all diacritics. |
| **TrOCR-Vi (Printed)** | Printed Real (CTSV) | *TBD* | *TBD* | *TBD* | Expected to match or beat VietOCR. |
| **TrOCR-Vi (Mixed)** | Handwriting | *TBD* | *TBD* | *TBD* | To be evaluated after Stage B Colab training. |

*(Note: Exact CER metrics for TrOCR-Vi will be populated after running `scripts/eval_lines.py` with the fine-tuned checkpoint.)*
