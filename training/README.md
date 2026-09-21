# Training — OCR Model Training Pipeline

## Purpose

Pipeline huấn luyện và đánh giá OCR model cho tài liệu tiếng Việt.
Fine-tuning VietOCR / PaddleOCR trên dataset tài liệu Công tác sinh viên.

## Scope

| Giai đoạn | File | Mô tả |
|-----------|------|-------|
| Chuẩn bị dữ liệu | Dataset.md | Format, split, augmentation |
| Huấn luyện | Training.md | Config, training loop, logging |
| Đánh giá | Evaluation.md | CER, WER, error analysis |
| Inference | Inference.md | Single/batch inference, ONNX export |
| Checkpoint | Checkpoint.md | Save/load, best model selection |
| Monitoring | TensorBoard.md | Loss, metrics, predictions |

## Yêu cầu môi trường

```
Python  >= 3.11
CUDA    >= 11.8  (GPU training)
PyTorch >= 2.3.0
RAM     >= 16GB  (training)
VRAM    >= 8GB   (fine-tuning với batch_size=8)
```

> **CPU-only**: Có thể chạy inference, nhưng training sẽ rất chậm.
> Khuyến nghị dùng Google Colab Pro hoặc máy tính có GPU nếu không có thiết bị cá nhân.

## Cấu trúc thư mục (planned)

```
training/
├── configs/              # YAML training configurations
│   ├── vietocr_base.yaml
│   └── vietocr_finetune.yaml
├── train.py              # Main training script
├── evaluate.py           # Evaluation script
├── infer.py              # Inference script
├── export_onnx.py        # ONNX export script
├── data/                 # Data utilities
│   ├── dataset.py        # PyTorch Dataset class
│   └── augmentation.py   # Albumentations pipeline
└── utils/                # Helpers (metrics, checkpoint, logging)
```

## Workflow nhanh

```bash
# 1. Chuẩn bị dataset
python scripts/process_dataset.py --input dataset/raw --output dataset/processed

# 2. Chạy training
python training/train.py --config training/configs/vietocr_finetune.yaml

# 3. Đánh giá
python training/evaluate.py --checkpoint models/best.pth --test dataset/test

# 4. Export ONNX
python training/export_onnx.py --checkpoint models/best.pth --output models/best.onnx
```

## TODO

- [ ] Tải VietOCR pre-trained weights (vgg_transformer.pth)
- [ ] Viết `data/dataset.py` — PyTorch Dataset class cho text recognition
- [ ] Viết `data/augmentation.py` — Albumentations pipeline
- [ ] Viết `train.py` với argparse và YAML config
- [ ] Viết `evaluate.py` — tính CER/WER trên test set
- [ ] Benchmark VietOCR vs PaddleOCR trên dataset CTSV
- [ ] Ghi kết quả vào `docs/Experiment.md`

## References

- Dataset.md
- Training.md
- Evaluation.md
- Inference.md
- Checkpoint.md
- TensorBoard.md
- .ai/research/VietOCR.md
- .ai/research/PaddleOCR.md
