# Evaluation — Phương pháp & Tiêu chí Đánh giá OCR

## Purpose

Tài liệu thiết kế quy trình đánh giá định lượng chất lượng nhận dạng OCR (CER/WER) và hiệu năng tổng thể của mô hình và hệ thống.

## Scope

Metrics (CER, WER, Precision, Recall, Latency), Quy trình Benchmark, Baseline comparison và Phân tích lỗi (Error Analysis).

---

## 1. Chỉ số Đánh giá Cốt lõi (Evaluation Metrics)

### 1.1 CER (Character Error Rate - Tỷ lệ lỗi ký tự)
Chỉ số chính đo lường độ chính xác ở cấp độ ký tự:
$$\text{CER} = \frac{S + D + I}{N}$$
Trong đó:
- $S$: Số ký tự bị thay thế (Substitutions).
- $D$: Số ký tự bị xóa (Deletions).
- $I$: Số ký tự bị chèn thêm (Insertions).
- $N$: Tổng số ký tự trong nhãn chuẩn (Ground Truth).

Mục tiêu sản phẩm: **CER < 5%** trên văn bản in chuẩn.

### 1.2 WER (Word Error Rate - Tỷ lệ lỗi từ)
Chỉ số đo lường ở cấp độ từ (tính theo khoảng trắng):
$$\text{WER} = \frac{S_w + D_w + I_w}{N_w}$$

Mục tiêu sản phẩm: **WER < 10%**.

---

## 2. Ma trận So sánh Baseline (Phase 4 Evaluation)

| Mô hình OCR Engine | Tập dữ liệu Test | CER (%) | WER (%) | Latency CPU (ms/line) | Ghi chú |
|-------------------|------------------|---------|---------|-----------------------|---------|
| Tesseract 5.x Baseline | CTSV Test Set (500 lines) | [TBD] | [TBD] | [TBD] | Baseline truyền thống |
| PaddleOCR Recognition | CTSV Test Set (500 lines) | [TBD] | [TBD] | [TBD] | PP-OCRv4 Multi-lang |
| VietOCR Pre-trained | CTSV Test Set (500 lines) | [TBD] | [TBD] | [TBD] | Untuned Baseline |
| **VietOCR Fine-tuned (Proposed)** | CTSV Test Set (500 lines) | **[TBD]** | **[TBD]** | **[TBD]** | **Mô hình đề xuất** |

---

## 3. Quy trình Phân tích Lỗi (Error Analysis)

1. **Lỗi Dấu thanh tiếng Việt**: Nhầm lẫn giữa dấu hỏi/ngã/sắc/huyền (vd: `nghỉ` -> `nghĩ`).
2. **Lỗi Ký tự tương đồng**: Nhầm lẫn `l` - `1` - `I`, `0` - `O`, `u` - `n`.
3. **Lỗi do Nền nhiễu / Mực mờ**: Bị chèn ký tự rác khi ảnh bị ố vàng hoặc nếp gấp.

---

## TODO

- [ ] Viết script tự động đánh giá `training/evaluate.py` tính CER/WER qua thư viện `python-Levenshtein`.
- [ ] Ghi lại kết quả thực nghiệm chi tiết vào file `docs/Experiment.md`.

## References

- CER.md
- WER.md
- Training.md
- VietOCR.md
