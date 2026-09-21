#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
training/train.py — Fine-tune VietOCR trên dataset CTSV

Phương án: B — Fine-tune model pretrained (KHÔNG train from scratch)
  Ref: .ai/DECISIONS.md ADR-001, .ai/research/VietOCR.md, .ai/research/TransferLearning.md

Chiến lược
----------
  - Load config `vgg_transformer` với pretrained=True (download weights lần đầu)
  - Hoặc load từ checkpoint cục bộ nếu đã có (--base-weights)
  - LR nhỏ (1e-4) — fine-tune, KHÔNG train from scratch
  - Checkpoint tốt nhất (val CER thấp nhất) → models/
  - TensorBoard logging vào runs/

Dataset format (VietOCR chuẩn)
--------------------------------
  Mỗi dòng trong annotation file:
    <đường_dẫn_ảnh><TAB><nhãn văn bản>
  Ví dụ:
    dataset/crops/DOC_DON_20240601_line_000.png    UBND tỉnh Đồng Nai

Cách chạy
---------
  # Cơ bản (dùng pretrained VietOCR download tự động)
  python training/train.py \\
      --train  dataset/annotations/annotation_train.txt \\
      --val    dataset/annotations/annotation_val.txt \\
      --output models/

  # Có sẵn checkpoint pretrained cục bộ
  python training/train.py \\
      --train        dataset/annotations/annotation_train.txt \\
      --val          dataset/annotations/annotation_val.txt \\
      --base-weights models/vgg_transformer_pretrained.pth \\
      --output       models/ \\
      --iters        5000 \\
      --batch-size   8

  # Resume từ checkpoint đã fine-tune
  python training/train.py \\
      --train   dataset/annotations/annotation_train.txt \\
      --val     dataset/annotations/annotation_val.txt \\
      --resume  models/transformerocr_ctsv_v1.pth \\
      --output  models/

Phụ thuộc
----------
  pip install vietocr torch pillow
  (torch, torchvision: xem training/README.md — cần cài đúng version CUDA)

Ghi chú Windows Unicode path
------------------------------
  VietOCR dùng PIL.Image.open() → hỗ trợ Unicode path nếu Pillow >= 9.x.
  Tuy nhiên annotation file phải ghi path với dấu / (không phải \\).
"""

import argparse
import sys
import os
import shutil
from datetime import datetime
from pathlib import Path
import urllib3
urllib3.disable_warnings()
import requests
from typing import Optional

# Ensure UTF-8 output on Windows
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

# Patch requests.get for expired SSL certs on upstream vocr.vn
_orig_get = requests.get
def _patched_get(*args, **kwargs):
    kwargs['verify'] = False
    return _orig_get(*args, **kwargs)
requests.get = _patched_get

# ── Guards: import sớm để báo lỗi rõ ràng trước khi chạy ────────────────────
try:
    import torch
except ImportError:
    print("[ERROR] PyTorch chưa được cài đặt.", file=sys.stderr)
    print("        Xem: https://pytorch.org/get-started/locally/", file=sys.stderr)
    sys.exit(1)

try:
    import numpy as np
    if not hasattr(np, 'sctypes'):
        np.sctypes = {
            'float': [np.float16, np.float32, np.float64],
            'int': [np.int8, np.int16, np.int32, np.int64],
            'uint': [np.uint8, np.uint16, np.uint32, np.uint64],
            'complex': [np.complex64, np.complex128],
            'others': [bool, object, bytes, str, np.void]
        }

    import lmdb
    _orig_lmdb_open = lmdb.open
    def _patched_lmdb_open(*args, **kwargs):
        if kwargs.get('map_size', 0) > 1024 * 1024 * 1024:
            kwargs['map_size'] = 1024 * 1024 * 1024
        return _orig_lmdb_open(*args, **kwargs)
    lmdb.open = _patched_lmdb_open

    import vietocr.loader.dataloader as loader_dl
    loader_dl.lmdb.open = _patched_lmdb_open

    import vietocr.tool.utils as vocr_utils
    vocr_utils.requests.get = _patched_get
    from vietocr.tool.config import Cfg
    from vietocr.model.trainer import Trainer
except ImportError as e:
    print(f"[ERROR] VietOCR chưa được cài đặt hoặc lỗi import: {e}", file=sys.stderr)
    print("        Chạy: pip install vietocr", file=sys.stderr)
    sys.exit(1)


# ── Constants ─────────────────────────────────────────────────────────────────
MODEL_NAME         = "vgg_transformer"   # ADR-001: VietOCR VGG+Transformer
DEFAULT_ITERS      = 5_000               # số iteration fine-tune mặc định
DEFAULT_BATCH_SIZE = 8                   # phù hợp VRAM 8GB; giảm xuống 4 nếu thiếu VRAM
DEFAULT_LR         = 1e-4               # fine-tune LR (nhỏ hơn train-from-scratch 1e-3)
DEFAULT_PRINT_EVERY= 200                 # in loss mỗi N iteration
DEFAULT_VALID_EVERY= 500                 # validate mỗi N iteration
CHECKPOINT_PREFIX  = "transformerocr_ctsv"


# ── Validation helpers ────────────────────────────────────────────────────────

def validate_annotation_file(path: Path, label: str) -> int:
    """
    Kiểm tra file annotation hợp lệ.
    Trả về số entry có nhãn không rỗng.
    Raise SystemExit nếu file không tồn tại hoặc không có entry hợp lệ.
    """
    if not path.exists():
        print(f"[ERROR] File {label} không tồn tại: {path}", file=sys.stderr)
        sys.exit(1)

    valid = 0
    empty_label = 0
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "\t" not in line:
                continue
            _, _, lbl = line.partition("\t")
            if lbl.strip():
                valid += 1
            else:
                empty_label += 1

    if valid == 0:
        print(f"[ERROR] {label} không có entry hợp lệ (nhãn rỗng: {empty_label}).", file=sys.stderr)
        print(f"        Hãy gán nhãn xong trước khi chạy training.", file=sys.stderr)
        sys.exit(1)

    if empty_label > 0:
        print(f"[WARN] {label}: {empty_label} dòng nhãn rỗng sẽ bị bỏ qua.")

    return valid


def detect_device(force_cpu: bool = False) -> str:
    """Tự động chọn device tốt nhất."""
    if force_cpu:
        return "cpu"
    if torch.cuda.is_available():
        name = torch.cuda.get_device_name(0)
        vram = torch.cuda.get_device_properties(0).total_memory / (1024**3)
        print(f"  [device] GPU: {name}  ({vram:.1f} GB VRAM)")
        return "cuda"
    print("  [device] CPU only — training sẽ chậm. Khuyến nghị dùng GPU.")
    return "cpu"


# ── Config builder ────────────────────────────────────────────────────────────

def build_config(
    train_annotation:  Path,
    val_annotation:    Path,
    output_dir:        Path,
    base_weights:      Optional[Path],
    resume:            Optional[Path],
    iters:             int,
    batch_size:        int,
    lr:                float,
    print_every:       int,
    valid_every:       int,
    device:            str,
    run_name:          str,
) -> Cfg:
    """
    Xây dựng Cfg object cho VietOCR Trainer.

    Tham khảo: https://github.com/pbcquoc/vietocr
    Các key config quan trọng nhất được đặt ở đây.
    """
    # Load config cơ sở từ VietOCR (pretrained = True → download vgg_transformer.pth nếu chưa có)
    config = Cfg.load_config_from_name(MODEL_NAME)

    # ── Dataset ──────────────────────────────────────────────────────────────
    # VietOCR Trainer nhận annotation dạng list path -> Trainer đọc trực tiếp
    config["dataset"]["train_annotation"]  = str(train_annotation.resolve())
    config["dataset"]["valid_annotation"]  = str(val_annotation.resolve())

    # Không cần data_root riêng vì path trong annotation đã đủ (relative to project root)
    config["dataset"]["data_root"] = str(Path.cwd())

    # ── Model weights ─────────────────────────────────────────────────────────
    if resume is not None:
        # Resume từ checkpoint đang fine-tune
        config["weights"] = str(resume.resolve())
        print(f"  [weights] Resume từ: {resume}")
    elif base_weights is not None:
        # Dùng pretrained weights cục bộ thay vì download
        config["weights"] = str(base_weights.resolve())
        config["pretrain"] = str(base_weights.resolve())
        print(f"  [weights] Base pretrained: {base_weights}")
    else:
        temp_weight = Path(os.environ.get("TEMP", "C:/Users/ncong/AppData/Local/Temp")) / "vgg_transformer.pth"
        if temp_weight.exists():
            config["weights"] = str(temp_weight.resolve())
            config["pretrain"] = str(temp_weight.resolve())
            print(f"  [weights] Dùng pretrained weights từ cache: {temp_weight}")
        else:
            print("  [weights] Dùng VietOCR default pretrained weights.")

    # ── Trainer hyperparameters ───────────────────────────────────────────────
    config["trainer"]["iters"]        = iters
    config["trainer"]["batch_size"]   = batch_size
    config["trainer"]["print_every"]  = print_every
    config["trainer"]["valid_every"]  = valid_every

    # Checkpoint & export paths
    checkpoint_dir = output_dir / "checkpoints"
    checkpoint_dir.mkdir(parents=True, exist_ok=True)
    logs_dir = output_dir / "logs"
    logs_dir.mkdir(parents=True, exist_ok=True)

    config["trainer"]["checkpoint"]   = str(checkpoint_dir / f"{run_name}_checkpoint.pth")
    config["trainer"]["export"]       = str(output_dir / f"{run_name}_best.pth")
    config["trainer"]["log"]          = str(logs_dir / f"{run_name}.log")

    # ── Optimizer ─────────────────────────────────────────────────────────────
    # Fine-tune: LR nhỏ, KHÔNG phải train from scratch
    config["optimizer"] = {
        "max_lr": lr,
        "pct_start": 0.1
    }

    # ── Device & Dataloader ───────────────────────────────────────────────────
    config["device"]                  = device
    config.setdefault("dataloader", {})
    config["dataloader"]["num_workers"] = 0
    config["dataloader"]["pin_memory"]  = False

    # ── Predictor (inference config) ──────────────────────────────────────────
    config["predictor"]["beamsearch"] = False   # tắt beamsearch khi training (chỉ dùng lúc eval)

    return config


# ── Main ──────────────────────────────────────────────────────────────────────

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Fine-tune VietOCR (vgg_transformer) trên dataset CTSV.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--train", type=Path, required=True,
        help="File annotation train (path<TAB>label)",
    )
    parser.add_argument(
        "--val", type=Path, required=True,
        help="File annotation validation (path<TAB>label)",
    )
    parser.add_argument(
        "--output", type=Path, default=Path("models"),
        help="Thư mục lưu checkpoints và best model",
    )
    parser.add_argument(
        "--base-weights", type=Path, default=None,
        help="Path đến pretrained weights cục bộ (.pth). Bỏ qua nếu muốn auto-download.",
    )
    parser.add_argument(
        "--resume", type=Path, default=None,
        help="Resume training từ checkpoint fine-tune đang có.",
    )
    parser.add_argument(
        "--iters", type=int, default=DEFAULT_ITERS,
        help="Số iteration training",
    )
    parser.add_argument(
        "--batch-size", type=int, default=DEFAULT_BATCH_SIZE,
        help="Batch size (giảm xuống 4 nếu thiếu VRAM)",
    )
    parser.add_argument(
        "--lr", type=float, default=DEFAULT_LR,
        help="Learning rate (giữ nhỏ 1e-4 vì đang fine-tune)",
    )
    parser.add_argument(
        "--print-every", type=int, default=DEFAULT_PRINT_EVERY,
        help="In loss mỗi N iteration",
    )
    parser.add_argument(
        "--valid-every", type=int, default=DEFAULT_VALID_EVERY,
        help="Validate và lưu checkpoint mỗi N iteration",
    )
    parser.add_argument(
        "--cpu", action="store_true",
        help="Ép dùng CPU dù có GPU (debug)",
    )
    parser.add_argument(
        "--run-name", type=str, default=None,
        help="Tên run (dùng cho tên file checkpoint). Mặc định: auto-generate theo ngày.",
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Chỉ validate config và dữ liệu, không thực sự chạy training.",
    )
    return parser


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    parser = build_parser()
    args   = parser.parse_args()

    print("=" * 60)
    print(" VietOCR Fine-tune — Student Document OCR (CTSV)")
    print(" Phương án B: Fine-tune pretrained, KHÔNG train from scratch")
    print("=" * 60)

    # ── Validate inputs ───────────────────────────────────────────────────────
    n_train = validate_annotation_file(args.train, "Train annotation")
    n_val   = validate_annotation_file(args.val,   "Val annotation")
    print(f"\n  Train entries: {n_train}")
    print(f"  Val entries  : {n_val}")

    if n_train < 10:
        print(f"\n[WARN] Chỉ có {n_train} mẫu train — quá ít, model có thể overfit nhanh.")
        print("       Khuyến nghị tối thiểu 200 mẫu cho fine-tune có ý nghĩa.")

    # ── Run name ──────────────────────────────────────────────────────────────
    date_str = datetime.now().strftime("%Y%m%d_%H%M")
    run_name = args.run_name or f"{CHECKPOINT_PREFIX}_{date_str}_n{n_train}"
    print(f"\n  Run name : {run_name}")

    # ── Device ────────────────────────────────────────────────────────────────
    device = detect_device(force_cpu=args.cpu)

    # ── Build config ──────────────────────────────────────────────────────────
    print("\n  Đang build VietOCR config...")
    output_dir = args.output.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    config = build_config(
        train_annotation = args.train.resolve(),
        val_annotation   = args.val.resolve(),
        output_dir       = output_dir,
        base_weights     = args.base_weights,
        resume           = args.resume,
        iters            = args.iters,
        batch_size       = args.batch_size,
        lr               = args.lr,
        print_every      = args.print_every,
        valid_every      = args.valid_every,
        device           = device,
        run_name         = run_name,
    )

    # ── Lưu config snapshot ───────────────────────────────────────────────────
    config_snapshot = output_dir / "logs" / f"{run_name}_config.yml"
    config_snapshot.parent.mkdir(parents=True, exist_ok=True)
    config.save(str(config_snapshot))
    print(f"  Config snapshot: {config_snapshot}")

    # ── Dry-run guard ─────────────────────────────────────────────────────────
    if args.dry_run:
        print("\n[DRY-RUN] Config và dữ liệu hợp lệ. Training không được bắt đầu.")
        print(f"  Checkpoint sẽ lưu tại: {config['trainer']['checkpoint']}")
        print(f"  Best model sẽ lưu tại: {config['trainer']['export']}")
        return

    # ── Training ──────────────────────────────────────────────────────────────
    print(f"\n  Bắt đầu fine-tune: {args.iters} iterations, batch={args.batch_size}, lr={args.lr}")
    print(f"  Checkpoint: {config['trainer']['checkpoint']}")
    print(f"  Best model: {config['trainer']['export']}")
    print("  " + "-" * 56)

    trainer = Trainer(config, pretrained=True)
    trainer.train()

    # ── Post-training summary ─────────────────────────────────────────────────
    best_path = Path(config["trainer"]["export"])
    print("\n" + "=" * 60)
    print(" Fine-tune hoàn thành!")
    if best_path.exists():
        size_mb = best_path.stat().st_size / (1024 * 1024)
        print(f" Best model: {best_path}  ({size_mb:.1f} MB)")
        print(f"\n Bước tiếp theo:")
        print(f"   python training/evaluate.py \\")
        print(f"       --checkpoint {best_path} \\")
        print(f"       --annotation dataset/annotations/annotation_val.txt")
    else:
        print(f" [WARN] Không tìm thấy best model tại {best_path}.")
        print("         Kiểm tra logs để xem lỗi.")
    print("=" * 60)


if __name__ == "__main__":
    main()
