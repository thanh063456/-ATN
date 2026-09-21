# Models — Model Registry & Checkpoint Convention

## Purpose

Thư mục lưu trữ tất cả model checkpoint (`.pth`), exported model (`.onnx`),
training config snapshot (`.yml`) và metrics kết quả (`metrics.json`).

---

## Quy ước đặt tên Checkpoint

### Format bắt buộc

```
transformerocr_ctsv_{version}_{YYYYMMDD}_{n}lines.pth
```

| Thành phần | Ý nghĩa | Ví dụ |
|------------|---------|-------|
| `transformerocr_ctsv` | Tên cố định — VietOCR transformer fine-tuned cho CTSV | |
| `{version}` | Phiên bản thứ tự fine-tune (`v1`, `v2`, ...) | `v1` |
| `{YYYYMMDD}` | Ngày fine-tune kết thúc | `20241015` |
| `{n}lines` | Số dòng dữ liệu training đã dùng | `450lines` |
| `.pth` | PyTorch state dict | |

### Ví dụ thực tế

```
models/
├── transformerocr_ctsv_v1_20241015_450lines_best.pth   ← Best val CER lần 1
├── transformerocr_ctsv_v1_20241015_450lines_checkpoint.pth  ← Checkpoint cuối lần 1
├── transformerocr_ctsv_v2_20241120_1200lines_best.pth  ← Best val CER lần 2 (thêm data)
├── transformerocr_ctsv_v2_20241120_1200lines_checkpoint.pth
├── metrics/
│   ├── eval_v1_20241015.json   ← CER/WER của v1 trên val set
│   └── eval_v2_20241120.json   ← CER/WER của v2 trên val set
└── configs/
    ├── config_v1_20241015.yml  ← Config snapshot khi train v1
    └── config_v2_20241120.yml
```

---

## Model Card (điền sau mỗi lần fine-tune)

Tạo file `models/metrics/model_card_{version}_{date}.md` với nội dung:

```markdown
## Model Card — transformerocr_ctsv_{version}

| Field               | Value |
|---------------------|-------|
| **Architecture**    | VGG-Transformer (VietOCR vgg_transformer) |
| **Base weights**    | vgg_transformer.pth (VietOCR pretrained) |
| **Fine-tune date**  | YYYY-MM-DD |
| **Training data**   | N lines — dataset/annotations/annotation_train.txt |
| **Val data**        | M lines — dataset/annotations/annotation_val.txt |
| **Iterations**      | N_ITERS |
| **Batch size**      | 8 |
| **Learning rate**   | 1e-4 (fine-tune, Cosine Annealing) |
| **Device**          | CPU / GPU: [tên GPU] |
| **Val CER**         | X.XX% |
| **Val WER**         | X.XX% |
| **Exact match**     | X.XX% |
| **Notes**           | [Ghi chú bất thường, data augmentation, v.v.] |
```

---

## So sánh giữa các phiên bản

| Version | Date | Train lines | Val CER | Val WER | Notes |
|---------|------|-------------|---------|---------|-------|
| v1 | 2024-10-15 | 450 | — | — | Baseline fine-tune |
| v2 | 2024-11-20 | 1,200 | — | — | Thêm data đơn học bổng |

> Điền CER/WER sau khi chạy `training/evaluate.py`

---

## Quy trình cập nhật bảng so sánh

```bash
# 1. Fine-tune xong → evaluate ngay
python training/evaluate.py \
    --checkpoint models/transformerocr_ctsv_v2_20241120_1200lines_best.pth \
    --annotation dataset/annotations/annotation_val.txt \
    --output     models/metrics/eval_v2_20241120.json

# 2. Điền CER/WER vào bảng trên
# 3. Commit cả models/metrics/*.json và models/README.md
```

---

## .gitignore — File KHÔNG commit

File `.pth` và `.onnx` rất lớn (50–200MB), KHÔNG commit thẳng vào Git.
Dùng **Git LFS** hoặc **DVC** để quản lý:

```
# Đã có trong .gitignore:
models/*.pth
models/*.onnx
models/**/*.pth
models/**/*.onnx
```

**Lưu trữ checkpoint:**
- Development: lưu local trong `models/`
- Chia sẻ team: Google Drive / OneDrive với link trong `models/CHECKPOINTS.md`
- Production: DVC + remote storage (S3/MinIO)

---

## Tải VietOCR pretrained weights

```bash
# Tự động download khi chạy train.py lần đầu (pretrained=True)
python training/train.py --train ... --val ... --output models/

# Hoặc download thủ công
from vietocr.tool.config import Cfg
config = Cfg.load_config_from_name('vgg_transformer')
# VietOCR cache tại ~/.cache/vietocr/vgg_transformer.pth
```

---

## References

- `training/train.py` — Fine-tune script
- `training/evaluate.py` — CER/WER evaluation
- `.ai/DECISIONS.md` ADR-001 — Quyết định dùng VietOCR VGG-Transformer
- `.ai/research/VietOCR.md` — Kiến trúc và inference pipeline
- `.ai/research/TransferLearning.md` — Chiến lược fine-tune
