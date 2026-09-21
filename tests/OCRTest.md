# OCR Tests — Kiem thu chat luong OCR

## Purpose

Test suite danh gia chat luong OCR: accuracy tests, edge case tests, regression tests.

## Scope

Accuracy tests voi ground truth. Edge cases: faded, rotated, low-res, handwriting.

## TODO

- [ ] Tao test dataset voi ground truth labels (100 anh + label)
- [ ] Viet test tinh CER/WER tren test set
- [ ] Test: anh chat luong cao (scan DPI 300+)
- [ ] Test: anh mo/nhieu (thap hon DPI 150)
- [ ] Test: anh xoay nghieng (5-10 do)
- [ ] Test: anh co watermark hoac stamp
- [ ] Regression test: so sanh voi baseline (Tesseract)

## References

- .ai/research/Evaluation.md
- PerformanceTest.md
- training/Evaluation.md
