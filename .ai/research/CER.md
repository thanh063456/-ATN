# CER — Character Error Rate (Tỷ lệ Lỗi Ký tự)

## Purpose

Tài liệu chi tiết về chỉ số CER (Character Error Rate): định nghĩa toán học, thuật toán Levenshtein Distance, cách tính toán trên Python và ngưỡng chấp nhận sản phẩm.

## Scope

Đo lường độ chính xác nhận dạng ký tự của mô hình OCR tiếng Việt.

---

## 1. Định nghĩa Toán học & Công thức

Character Error Rate (CER) được tính dựa trên số lượng phép biến đổi tối thiểu (Khoảng cách Levenshtein) để chuyển chuỗi kết quả OCR dự đoán ($\hat{y}$) thành chuỗi nhãn chuẩn Ground Truth ($y$):

$$\text{CER} = \frac{S + D + I}{N}$$

Trong đó:
- $S$ (Substitutions): Số ký tự bị nhận dạng sai (thay thế).
- $D$ (Deletions): Số ký tự trong nhãn chuẩn bị bỏ sót (xóa).
- $I$ (Insertions): Số ký tự nhận dạng thừa (chèn).
- $N$: Tổng số ký tự trong chuỗi Ground Truth ($y$).

*Lưu ý*: CER có thể vượt quá 100% nếu số ký tự chèn quá nhiều.

---

## 2. Mã nguồn Tự động tính CER với Python

```python
import Levenshtein

def calculate_cer(reference: str, hypothesis: str) -> float:
    """
    Tính Character Error Rate giữa nhãn chuẩn và văn bản dự đoán OCR.
    """
    # Chuẩn hóa Unicode NFC trước khi so sánh
    import unicodedata
    ref = unicodedata.normalize('NFC', reference)
    hyp = unicodedata.normalize('NFC', hypothesis)
    
    if len(ref) == 0:
        return 0.0 if len(hyp) == 0 else 1.0
        
    edit_dist = Levenshtein.distance(ref, hyp)
    return edit_dist / len(ref)
```

---

## 3. Ngưỡng Đạt Mục tiêu (Target Thresholds)

- **Xuất sắc**: CER < 2% (Tài liệu in sắc nét, không nghiêng).
- **Đạt yêu cầu Production**: **CER < 5%**.
- **Cần hiệu chỉnh thủ công**: 5% ≤ CER < 15%.
- **Không đạt / Cần OCR lại**: CER ≥ 15%.

---

## TODO

- [ ] Tích hợp hàm tính CER vào `training/evaluate.py`.

## References

- Evaluation.md
- WER.md
