# PaddleOCR — Nghiên cứu Text Detection Engine

## Purpose

Nghiên cứu kiến trúc PaddleOCR (đặc biệt phân hệ PP-OCRv4 Text Detection - DBNet++) nhằm mục đích làm Text Detection Engine (ADR-002) cho hệ thống Student-Document-OCR.

## Scope

Kiến trúc DBNet / DBNet++, quy trình phát hiện vùng chữ (Text Region Detection), cắt dòng (Line Cropping) và đánh giá khả năng tích hợp với VietOCR.

---

## 1. Vai trò của PaddleOCR trong Dự án

Trong kiến trúc OCR 2 giai đoạn (Two-stage OCR Pipeline):
- **Stage 1 (Text Detection)**: Dùng **PaddleOCR Detection (DBNet++)** để tìm vị trí tất cả các dòng chữ trên trang ảnh và trả về danh sách Bounding Boxes.
- **Stage 2 (Text Recognition)**: Crop các vùng ảnh dòng chữ và đưa vào **VietOCR** để nhận dạng văn bản tiếng Việt.

```
Full Page Document Image
          │
          ▼
┌────────────────────────────────┐
│ PaddleOCR Text Detection       │ (DBNet++)
│ (Find Bounding Boxes)          │
└─────────┬──────────────────────┘
          │ Bounding Boxes [(x1,y1,x2,y2), ...]
          ▼
┌────────────────────────────────┐
│ Line Crop & Sort Module        │ (Top-to-bottom, Left-to-right)
└─────────┬──────────────────────┘
          │ List of Line Images (32xW)
          ▼
┌────────────────────────────────┐
│ VietOCR Text Recognition       │
└────────────────────────────────┘
```

---

## 2. Kiến trúc DBNet++ (Real-time Scene Text Detection)

- **Differentiable Binarization (DB)**: Phương pháp nhị phân hóa có thể tính đạo hàm, giúp mạng học đồng thời cả Probability Map và Threshold Map.
- **Backbone**: MobileNetV3 hoặc ResNet18-vd (nhe, tốc độ cao trên CPU).
- **Output**: Bounding polygon / Rotated Bounding Boxes bao quanh từng câu/dòng chữ.

---

## 3. Tích hợp PaddleOCR Detection với Python SDK

```python
import numpy as np
from paddleocr import PaddleOCR

class PaddleTextDetector:
    def __init__(self, lang: str = 'vi', use_gpu: bool = False):
        # Chỉ dùng phân hệ Text Detection (det=True, rec=False)
        self.ocr = PaddleOCR(
            use_angle_cls=True,
            lang=lang,
            det=True,
            rec=False,
            use_gpu=use_gpu
        )

    def detect_lines(self, img_np: np.ndarray) -> list[list[float]]:
        """
        Phát hiện bounding boxes của dòng chữ.
        Returns: list of polygon coordinates [[x1,y1], [x2,y2], [x3,y3], [x4,y4]]
        """
        result = self.ocr.ocr(img_np, det=True, rec=False)
        boxes = result[0] if result and result[0] is not None else []
        return boxes
```

---

## TODO

- [ ] Thực hiện Benchmark PaddleOCR Detection vs CRAFT trên 50 mẫu trang scan CTSV.
- [ ] Chốt quyết định ADR-002 trong `DECISIONS.md`.

## References

- https://github.com/PaddlePaddle/PaddleOCR
- OCR.md
- VietOCR.md
- DECISIONS.md (ADR-002)
