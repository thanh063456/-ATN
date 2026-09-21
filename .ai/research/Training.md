# Training — Pipeline huấn luyện OCR Model

## Purpose

Mô tả đầy đủ pipeline huấn luyện (fine-tuning) VietOCR model trên dataset tài liệu CTSV.
Từ raw data đến trained model sẵn sàng deploy.

## Scope

Pipeline training: Dataset → Annotation → Split → Preprocessing → Augmentation →
Fine-tuning VietOCR → Validation → Checkpoint → Test Evaluation.

---

## 1. Training Pipeline Overview

```
Dataset (tài liệu CTSV)
        │
        ▼
[Step 1] Thu thập và chuẩn bị dữ liệu
        │
        ▼
[Step 2] Annotation (text line + ground truth)
        │
        ▼
[Step 3] Train / Validation / Test Split (80/10/10)
        │
        ▼
[Step 4] Preprocessing (denoise, deskew, normalize)
        │
        ▼
[Step 5] Augmentation (chỉ train set)
        │
        ▼
[Step 6] Load Pre-trained VietOCR (vgg_transformer.pth)
        │
        ▼
[Step 7] Fine-tuning
        │  ├── Monitor: train_loss, val_CER
        │  ├── Early stopping (patience=5 epochs)
        │  └── Save checkpoint khi val_CER tốt nhất
        │
        ▼
[Step 8] Test Set Evaluation
        │
        ▼
[Step 9] Model Selection & Export
```

---

## 2. Dataset Requirements

### Format (VietOCR training format)

VietOCR sử dụng format text line recognition:
- Input: ảnh của một dòng chữ (line image)
- Label: chuỗi ký tự tương ứng (UTF-8)

**File structure:**
```
dataset/
├── train/
│   ├── images/        # line crop images (preserve original aspect ratio)
│   └── labels.txt     # tab-separated: image_path\ttext
├── val/
│   ├── images/
│   └── labels.txt
└── test/
    ├── images/
    └── labels.txt
```

**labels.txt format (NFC Normalized):**
```tsv
train/images/0001.jpg   CỘNG HÒA XÃ HỘI CHỦ NGHĨA VIỆT NAM
train/images/0002.jpg   Họ và tên: Nguyễn Văn A
```

### Lượng dữ liệu (mục tiêu)

| Set | Số text lines | Ghi chú |
|-----|-------------|---------|
| Train | ≥ 3.000 | Tối thiểu để fine-tuning hiệu quả |
| Validation | ≥ 500 | Để monitor overfitting |
| Test | ≥ 500 | Ground truth chất lượng cao (100% verified) |

> **Fallback**: Nếu không thu thập đủ tài liệu CTSV thực tế, bổ sung bằng public Vietnamese OCR datasets.

---

## 3. Annotation Process

**Tool:** LabelMe (dạng polygon/bounding box) hoặc manual text extraction

**Annotation steps:**
1. Phát hiện text lines (bằng text detector hoặc manual)
2. Crop từng line image
3. Ghi ground truth text (phải chính xác 100%)
4. Review lần 2 để đảm bảo quality
5. Xuất labels.txt

**Quality requirements:**
- Không typo trong ground truth
- Unicode chuẩn NFC
- Không include noise text (header, footer trang)

---

## 4. Data Augmentation (Train set only)

**Mục đích:** Tăng diversity, giảm overfitting

| Augmentation | Tham số | Lý do |
|-------------|---------|-------|
| Gaussian noise | σ ∈ [0, 0.05] | Mô phỏng scan quality thấp |
| Brightness/Contrast | ±20% | Mô phỏng độ sáng khác nhau |
| Slight rotation | ±3° | Mô phỏng trang hơi nghiêng |
| JPEG compression | quality ∈ [70, 95] | Mô phỏng ảnh đã nén |
| Blur | σ ∈ [0, 1] | Mô phỏng out-of-focus |

**Không sử dụng:**
- Flip ngang/dọc (phá cấu trúc chữ)
- Mạnh rotation (>5°) — đã handle ở preprocessing
- Cutout/GridDistortion (quá aggressive cho text)

**Tool:** `albumentations`

---

## 5. Model Configuration (VietOCR Fine-tuning)

```yaml
# training/configs/finetune.yaml
model: vgg_transformer
pretrained: true
pretrained_path: models/vgg_transformer.pth

training:
  batch_size: 32          # CPU: giảm xuống 8
  epochs: 50
  learning_rate: 0.0001   # Nhỏ hơn pre-training (fine-tune)
  scheduler: cosine
  warmup_epochs: 2
  optimizer: Adam
  weight_decay: 0.00001
  early_stopping:
    monitor: val_cer
    patience: 5
    mode: min

data:
  train: dataset/train/labels.txt
  val: dataset/val/labels.txt
  image_height: 32        # VietOCR standard
  max_image_width: 1024

checkpoint:
  save_dir: models/checkpoints/
  save_top_k: 3
  monitor: val_cer

logging:
  tensorboard_dir: runs/finetune/
  log_interval: 100       # steps
```

---

## 6. Training Metrics

| Metric | Ý nghĩa | Target |
|--------|---------|--------|
| `train_loss` | Cross-entropy loss (teacher forcing) | Giảm dần |
| `val_CER` | Character Error Rate trên val set | < 5% |
| `val_WER` | Word Error Rate trên val set | < 10% |
| `val_loss` | Loss trên val set (tránh overfitting) | Không tăng |

**Checkpoint strategy:**
- Save model tốt nhất theo `val_CER`
- Lưu top-3 checkpoints
- Xóa checkpoint cũ khi có checkpoint tốt hơn

---

## 7. Baseline Comparison

| Model | CER (pre-test) | WER | Latency (CPU) |
|-------|---------------|-----|---------------|
| Tesseract 5.x | — | — | — |
| VietOCR pre-trained (no fine-tune) | — | — | — |
| VietOCR fine-tuned (Phase 3) | — | — | — |

> Sẽ điền sau khi chạy experiments (xem docs/Experiment.md).

---

## 8. Không làm ở Phase 1

- Không viết code training script
- Không implement Dataset class
- Không chạy training
- Không download pre-trained weights

Những việc này thuộc **Phase 3 (VietOCR Fine-tuning)**.

---

## TODO

- [ ] Xác nhận dataset volume có thể thu thập
- [ ] Chọn annotation tool (LabelMe hoặc CVAT)
- [ ] Xác nhận augmentation parameters sau khi có data
- [ ] Lên kế hoạch GPU access cho training (nếu cần)
- [ ] Nghiên cứu thêm về curriculum learning cho fine-tuning

## References

- .ai/research/VietOCR.md
- .ai/research/Dataset.md
- .ai/research/Evaluation.md
- training/README.md
- training/Training.md
- .ai/DECISIONS.md (ADR-001)
