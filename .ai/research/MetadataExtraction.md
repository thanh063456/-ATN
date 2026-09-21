# Metadata Extraction — Trích xuất Dữ liệu Có cấu trúc từ OCR

## Purpose

Nghiên cứu các giải pháp trích xuất tự động thông tin có cấu trúc (MSSV, Họ tên, Ngày tháng, Số công văn) từ văn bản OCR thô.

## Scope

Rule-based Regex Patterns, Heuristic Layout Analysis, và định dạng JSON Output.

---

## 1. Phương pháp Trích xuất Rule-based (Regex Engine)

Do tài liệu Công tác sinh viên có cấu trúc biểu mẫu khá chuẩn, phương pháp **Regular Expressions (Regex)** mang lại độ chính xác cao và tốc độ xử lý tức thì (< 1ms).

### Các Pattern Regex Chính

| Trường Metadata | Biểu thức Regex (Python Pattern) | Ví dụ Khớp |
|-----------------|----------------------------------|------------|
| **Mã số sinh viên (MSSV)** | `r'(?:MSSV\|Mã\s+số\s+sinh\s+viên\|SV):\s*([0-9]{8,10})'` | `MSSV: 20211234` -> `20211234` |
| **Ngày tháng đơn** | `r'ngày\s+([0-3]?[0-9])\s+tháng\s+([0-1]?[0-9])\s+năm\s+([2][0][2-9][0-9])'` | `ngày 15 tháng 08 năm 2025` |
| **Họ và tên** | `r'(?:Họ\s+và\s+tên\|Sinh\s+viên):\s*([A-ZÀÁÂÃÈÉÊÌÍÒÓÔÕÙÚĂĐĨŨƠƯĂẠẢẤẦẨẪẬẮẰẲẴẶẸẺẼỀỀỂỄỆỈỊỌỎỐỒỔỖỘỚỜỞỠỢỤỦỨỪỬỮỰỲỴÝỶỸ\s]{3,40})'` | `Họ và tên: NGUYỄN VĂN A` |
| **Số công văn** | `r'(?:Số\|Số\s+hiệu):\s*([0-9]{1,5}\/[A-Z0-9\-]+)'` | `Số: 123/QĐ-CTSV` |

---

## 2. Quy trình Thực thi Python

```python
import re
from datetime import date

class MetadataExtractor:
    def extract(self, text: str) -> dict:
        metadata = {}
        
        # 1. Trích xuất MSSV
        mssv_match = re.search(r'(?:MSSV|Mã\s+sinh\s+viên|SV):\s*([0-9]{8,10})', text, re.IGNORECASE)
        if mssv_match:
            metadata['student_id'] = mssv_match.group(1)
            
        # 2. Trích xuất Ngày
        date_match = re.search(r'ngày\s+([0-3]?[0-9])\s+tháng\s+([0-1]?[0-9])\s+năm\s+(20[2-9][0-9])', text, re.IGNORECASE)
        if date_match:
            d, m, y = date_match.groups()
            metadata['document_date'] = f"{y}-{int(m):02d}-{int(d):02d}"
            
        return metadata
```

---

## TODO

- [ ] Bổ sung các mẫu Regex cho các loại đơn mới phát sinh.
- [ ] Nghiên cứu phương pháp Named Entity Recognition (NER) nhẹ nếu Regex không đủ linh hoạt.

## References

- OCR.md
- .ai/design/ERD.md
