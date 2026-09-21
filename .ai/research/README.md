# .ai/research — Research Index

## Purpose

Thư mục tập trung toàn bộ nghiên cứu kỹ thuật và học thuật phục vụ dự án Student-Document-OCR.
Mỗi file nghiên cứu một chủ đề cụ thể, từ OCR engine đến Elasticsearch và metadata extraction.

## Scope

Bao gồm 12 tài liệu nghiên cứu chia thành 3 nhóm:

| Nhóm | Files |
|------|-------|
| **OCR Engine** | OCR.md, VietOCR.md, PaddleOCR.md |
| **AI / Training** | Dataset.md, TransferLearning.md, Training.md, Evaluation.md, CER.md, WER.md |
| **Search & Extraction** | Elasticsearch.md, VietnameseSearch.md, MetadataExtraction.md |

## TODO

- [ ] Hoàn thiện benchmark so sánh VietOCR vs PaddleOCR (CER/WER/latency)
- [ ] Cập nhật Dataset.md sau khi thu thập dữ liệu CTSV thực tế
- [ ] Cập nhật Evaluation.md với kết quả thực nghiệm từ Phase 2
- [ ] Nghiên cứu thêm về VietnameseSearch — ICU plugin vs custom analyzer
- [ ] Thêm tài liệu research về Layout Analysis (DocLayNet, PaddleLayout)
- [ ] Tổng hợp findings vào báo cáo (docs/Report.md — Chương 2)

## References

- .ai/ROADMAP.md (Phase 1 & 2)
- .ai/TASKS.md
- training/README.md
- docs/Experiment.md
