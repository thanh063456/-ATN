# VietOCR — Nghiên cứu & Tích hợp Engine Nhận dạng Chi tiết

## Purpose

Nghiên cứu sâu về kiến trúc, cơ chế hoạt động, tùy chỉnh cấu hình và tích hợp thư viện VietOCR làm Text Recognition Engine chính cho hệ thống Student-Document-OCR.

## Scope

Kiến trúc VGG-Transformer / ResNet-Transformer, Dataset format, Inference pipeline, Benchmark hiệu năng và giải pháp Fine-tuning.

---

## 1. Kiến trúc Mô hình VietOCR

VietOCR là thư viện OCR chuyên biệt cho tiếng Việt phát triển bởi tác giả Nguyễn Thịnh Quốcs. Mô hình thuộc lớp **Seq2Seq Architecture** bao gồm 2 phần chính:

```
Input Line Crop Image (Preserve original aspect ratio)
            │
            ▼
┌────────────────────────┐
│ VietOCR Preprocessing  │ (Dynamic Resize & Padding to H=32px in DataLoader)
└───────────┬────────────┘
            │ Tensor (3x32xW)
            ▼
┌────────────────────────┐
│  CNN Feature Extractor │ (VGG16 / ResNet50 backbone)
└───────────┬────────────┘
            │ Spatial Feature Maps
            ▼
┌────────────────────────┐
│ Sequence Encoder       │ (Transformer Encoder)
└───────────┬────────────┘
            │ Context Vectors
            ▼
┌────────────────────────┐
│ Sequence Decoder       │ (Transformer Decoder with Attention & Beam Search)
└───────────┬────────────┘
            │ Probabilities over Vocabulary
            ▼
Output Text String ("Đơn xin bảo lưu kết quả học tập")
```

### 1.1 CNN Feature Extractor (Backbone)
- **VGG Backbone (`vgg_transformer`)**: Nhẹ hơn, nén đặc trưng không gian tốt, phù hợp cho tài liệu in ấn chuẩn. Khuyến nghị dùng cho sản phẩm chính.
- **ResNet Backbone (`resnet_transformer`)**: Phù hợp hơn với các font chữ phức tạp hoặc nhiễu cao nhưng dung lượng model lớn hơn.

### 1.2 Transformer Sequence Encoder & Decoder
- **Encoder**: Chuyển đổi feature map từ CNN thành chuỗi các vector ngữ cảnh.
- **Decoder**: Tự động sinh từng ký tự UTF-8 dựa trên Attention Mechanism và Beam Search (mặc định `beam_width = 5`).

---

## 2. Quy trình Tích hợp Inference trong Python

```python
from PIL import Image
from vietocr.tool.config import Cfg
from vietocr.tool.predictor import Predictor

class VietOCREngine:
    def __init__(self, weight_path: str = None, device: str = 'cpu'):
        # Load cấu hình chuẩn vgg_transformer
        self.config = Cfg.load_config_from_name('vgg_transformer')
        
        if weight_path:
            self.config['weights'] = weight_path
        
        self.config['device'] = device
        self.config['predictor']['beamsearch'] = True
        
        # Khởi tạo Predictor
        self.detector = Predictor(self.config)

    def predict_line(self, line_img: Image.Image) -> tuple[str, float]:
        """
        Nhận dạng 1 dòng chữ ảnh crop.
        Returns: (text_string, confidence_probability)
        """
        text, prob = self.detector.predict(line_img, return_prob=True)
        return text.strip(), float(prob)
```

---

## 3. Quy trình Fine-tuning VietOCR với Custom Dataset

1. **Chuẩn bị Dữ liệu**:
   - Ảnh crop từng dòng chữ có chiều cao chuẩn 32px.
   - File `labels.txt` dạng Tab-separated: `path/to/img.jpg\tNội dung dòng chữ`.
2. **Cấu hình Training**:
   - Base weights: `vgg_transformer.pth` (Pre-trained trên dataset tiếng Việt rộng lớn).
   - Learning rate: `1e-4` với Cosine Annealing Scheduler.
   - Optimizer: `Adam` (weight_decay=`1e-5`).
   - Monitor Metric: Character Error Rate (CER) trên tập Validation.

---

## TODO

- [ ] Chạy benchmark tốc độ inference của VietOCR vgg_transformer trên CPU (mục tiêu < 50ms/line).
- [ ] Xây dựng mô-đun Custom Vocabulary nếu cần bổ sung các ký tự đặc biệt trong đơn từ CTSV.

## References

- https://github.com/pbcquoc/vietocr
- OCR.md
- Training.md
- CER.md
