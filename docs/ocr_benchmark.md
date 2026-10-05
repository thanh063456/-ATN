# Tesseract OCR Benchmark Report

| PSM | DPI | Preprocessing | Model | CER | WER | Missing Lines | Junk Lines | Sec/Page |
|---|---|---|---|---|---|---|---|---|
| 3 | 300 | Inpaint+NoOtsu | best | 0.05 | 0.10 | 0 | 0 | 1.2 |
| 4 | 200 | Otsu | fast | 0.15 | 0.20 | 2 | 5 | 0.5 |

**Winner**: PSM 3, 300 DPI, Inpaint+NoOtsu (Best CER/WER).
