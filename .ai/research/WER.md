# WER — Word Error Rate (Tỷ lệ Lỗi Từ)

## Purpose

Tài liệu chi tiết về chỉ số WER (Word Error Rate): định nghĩa, thuật toán tách từ tiếng Việt, và vai trò của WER đối với chất lượng tìm kiếm Elasticsearch.

## Scope

Đo lường độ chính xác ở cấp độ từ ngữ của mô hình VietOCR.

---

## 1. Định nghĩa Toán học

$$\text{WER} = \frac{S_w + D_w + I_w}{N_w}$$

Trong đó:
- $S_w$: Số từ bị thay thế sai.
- $D_w$: Số từ bị thiếu.
- $I_w$: Số từ bị nhận dạng thừa.
- $N_w$: Tổng số từ trong câu Ground Truth.

---

## 2. Mã nguồn Python tính WER

```python
import Levenshtein
import unicodedata

def calculate_wer(reference: str, hypothesis: str) -> float:
    ref_norm = unicodedata.normalize('NFC', reference)
    hyp_norm = unicodedata.normalize('NFC', hypothesis)
    
    # Tách từ theo khoảng trắng
    ref_words = ref_norm.split()
    hyp_words = hyp_norm.split()
    
    if len(ref_words) == 0:
        return 0.0 if len(hyp_words) == 0 else 1.0
        
    # Tính khoảng cách Levenshtein trên danh sách từ
    return Levenshtein.distance(ref_words, hyp_words) / len(ref_words)
```

---

## 3. Ảnh hưởng của WER tới Elasticsearch Search

- Khi WER cao (> 15%), các từ khóa tìm kiếm chính bị sai chính tả (vd: `nghỉ` -> `nghỉ`), ảnh hưởng trực tiếp tới kết quả Match Query.
- Tích hợp **Fuzzy Search** (Fuzziness=AUTO) trong Elasticsearch giúp bù đắp lỗi cho các trường hợp WER nằm trong khoảng 5% - 10%.

---

## TODO

- [ ] Tích hợp `calculate_wer` vào mô-đun đánh giá tự động.

## References

- CER.md
- Evaluation.md
- Elasticsearch.md
