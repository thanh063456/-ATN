#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
training/evaluate.py — Đánh giá checkpoint VietOCR trên tập val/test

Metrics
-------
  CER (Character Error Rate) = Levenshtein(pred, gt) / len(gt)   × 100%
  WER (Word Error Rate)      = Levenshtein(pred_words, gt_words) / len(gt_words) × 100%

  Cả hai metric: càng nhỏ càng tốt. Mục tiêu CTSV: CER < 5%, WER < 10%.
  Ref: .ai/research/VietOCR.md, training/Evaluation.md

Cách dùng
---------
  python training/evaluate.py \\
      --checkpoint models/transformerocr_ctsv_v1_best.pth \\
      --annotation dataset/annotations/annotation_val.txt

  # Với beamsearch (chính xác hơn, chậm hơn)
  python training/evaluate.py \\
      --checkpoint models/transformerocr_ctsv_v1_best.pth \\
      --annotation dataset/annotations/annotation_val.txt \\
      --beamsearch

  # Lưu kết quả chi tiết ra JSON
  python training/evaluate.py \\
      --checkpoint models/transformerocr_ctsv_v1_best.pth \\
      --annotation dataset/annotations/annotation_val.txt \\
      --output     models/eval_results.json

  # So sánh nhiều checkpoint
  python training/evaluate.py \\
      --checkpoint models/v1_best.pth models/v2_best.pth \\
      --annotation dataset/annotations/annotation_val.txt

Phụ thuộc
----------
  pip install vietocr torch pillow editdistance
  editdistance: tính Levenshtein distance nhanh hơn python-Levenshtein
"""

import argparse
import json
import sys
import time
from pathlib import Path
from typing import List, Dict, Optional, Tuple

# ── Guards ────────────────────────────────────────────────────────────────────
try:
    import torch
except ImportError:
    print("[ERROR] PyTorch chưa cài.", file=sys.stderr)
    sys.exit(1)

try:
    from vietocr.tool.config import Cfg
    from vietocr.tool.predictor import Predictor
except ImportError:
    print("[ERROR] VietOCR chưa cài. Chạy: pip install vietocr", file=sys.stderr)
    sys.exit(1)

try:
    from PIL import Image
except ImportError:
    print("[ERROR] Pillow chưa cài. Chạy: pip install pillow", file=sys.stderr)
    sys.exit(1)

try:
    import editdistance
    _EDIT_BACKEND = "editdistance"
except ImportError:
    # Fallback: tự cài Levenshtein thuần Python (chậm hơn nhưng không cần dependency ngoài)
    _EDIT_BACKEND = "builtin"
    print("[WARN] editdistance chưa cài. Dùng fallback thuần Python (chậm hơn).")
    print("       Khuyến nghị: pip install editdistance")


# ── Metric functions ──────────────────────────────────────────────────────────

def _levenshtein(a: str, b: str) -> int:
    """Levenshtein distance thuần Python — dùng khi editdistance chưa cài."""
    if len(a) < len(b):
        return _levenshtein(b, a)
    if not b:
        return len(a)
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a):
        curr = [i + 1]
        for j, cb in enumerate(b):
            curr.append(min(prev[j + 1] + 1, curr[j] + 1, prev[j] + (ca != cb)))
        prev = curr
    return prev[-1]


def edit_distance(a: str, b: str) -> int:
    """Edit distance giữa hai chuỗi, dùng backend nhanh nhất có sẵn."""
    if _EDIT_BACKEND == "editdistance":
        return editdistance.eval(a, b)
    return _levenshtein(a, b)


def compute_cer(prediction: str, ground_truth: str) -> float:
    """
    Character Error Rate = edit_distance(pred, gt) / max(len(gt), 1) × 100.
    Trả về 0.0 nếu cả hai đều rỗng.
    """
    if not ground_truth and not prediction:
        return 0.0
    if not ground_truth:
        return 100.0   # không có gt nhưng có prediction = 100% sai
    dist = edit_distance(prediction, ground_truth)
    return (dist / len(ground_truth)) * 100.0


def compute_wer(prediction: str, ground_truth: str) -> float:
    """
    Word Error Rate = edit_distance(pred_words, gt_words) / max(len(gt_words), 1) × 100.
    """
    pred_words = prediction.split()
    gt_words   = ground_truth.split()
    if not gt_words and not pred_words:
        return 0.0
    if not gt_words:
        return 100.0
    dist = edit_distance(" ".join(pred_words), " ".join(gt_words))
    # Chuẩn WER: edit distance trên word sequence
    n_ref = len(gt_words)
    # dùng word-level edit distance
    prev = list(range(n_ref + 1))
    for pw in pred_words:
        curr = [prev[0] + 1]
        for j, gw in enumerate(gt_words):
            curr.append(min(prev[j + 1] + 1, curr[j] + 1, prev[j] + (pw != gw)))
        prev = curr
    return (prev[-1] / n_ref) * 100.0


# ── Data loading ──────────────────────────────────────────────────────────────

def load_annotation(ann_path: Path, data_root: Path) -> List[Tuple[Path, str]]:
    """
    Đọc file annotation VietOCR format, trả về list (image_path, ground_truth_text).
    Bỏ qua dòng comment (#), dòng không có TAB, dòng nhãn rỗng.
    """
    samples: List[Tuple[Path, str]] = []
    skipped = 0

    with open(ann_path, encoding="utf-8") as f:
        for raw in f:
            line = raw.strip()
            if not line or line.startswith("#"):
                continue
            if "\t" not in line:
                skipped += 1
                continue
            img_rel, _, label = line.partition("\t")
            img_rel = img_rel.strip()
            label   = label.strip()
            if not label:
                skipped += 1
                continue

            # Resolve path: thử relative to data_root trước, rồi absolute
            img_path = data_root / img_rel
            if not img_path.exists():
                img_path = Path(img_rel)
            if not img_path.exists():
                print(f"  [SKIP] Không tìm thấy ảnh: {img_rel}")
                skipped += 1
                continue

            samples.append((img_path, label))

    if skipped > 0:
        print(f"  [WARN] Bỏ qua {skipped} dòng (nhãn rỗng / file không tồn tại / định dạng sai)")

    return samples


def open_image_unicode(path: Path) -> Image.Image:
    """Mở ảnh hỗ trợ path Unicode (dùng bytes thay vì str trên Windows)."""
    with open(str(path), "rb") as f:
        img = Image.open(f)
        img.load()   # force load trước khi file handle đóng
    return img.convert("RGB")


# ── Predictor factory ─────────────────────────────────────────────────────────

def build_predictor(checkpoint: Path, device: str, beamsearch: bool) -> Predictor:
    """
    Khởi tạo VietOCR Predictor từ checkpoint fine-tuned.
    """
    config = Cfg.load_config_from_name("vgg_transformer")
    config["weights"]                  = str(checkpoint.resolve())
    config["device"]                   = device
    config["predictor"]["beamsearch"]  = beamsearch
    config["pretrain"]                 = False   # KHÔNG download lại pretrained
    return Predictor(config)


# ── Evaluation core ───────────────────────────────────────────────────────────

def evaluate_checkpoint(
    checkpoint: Path,
    samples: List[Tuple[Path, str]],
    device: str,
    beamsearch: bool,
    show_errors: int,
) -> Dict:
    """
    Chạy inference trên toàn bộ samples, tính CER/WER tổng hợp.
    Trả về dict kết quả đầy đủ.
    """
    print(f"\n  Checkpoint : {checkpoint.name}")
    print(f"  Samples    : {len(samples)}")
    print(f"  Device     : {device}")
    print(f"  Beamsearch : {beamsearch}")

    predictor = build_predictor(checkpoint, device, beamsearch)

    results      = []
    total_cer    = 0.0
    total_wer    = 0.0
    exact_matches = 0
    t_start      = time.time()

    for i, (img_path, gt) in enumerate(samples, 1):
        try:
            img  = open_image_unicode(img_path)
            pred, conf = predictor.predict(img, return_prob=True)
            pred = pred.strip()
        except Exception as exc:
            print(f"  [ERROR] {img_path.name}: {exc}")
            pred = ""
            conf = 0.0

        cer = compute_cer(pred, gt)
        wer = compute_wer(pred, gt)
        total_cer += cer
        total_wer += wer
        if pred == gt:
            exact_matches += 1

        results.append({
            "image"     : str(img_path),
            "ground_truth": gt,
            "prediction": pred,
            "confidence": round(float(conf), 4),
            "cer"       : round(cer, 2),
            "wer"       : round(wer, 2),
            "exact"     : pred == gt,
        })

        # Progress every 50 samples
        if i % 50 == 0 or i == len(samples):
            elapsed = time.time() - t_start
            print(f"  [{i:4d}/{len(samples)}]  avg CER={total_cer/i:.2f}%  "
                  f"avg WER={total_wer/i:.2f}%  ({elapsed:.1f}s)")

    n = len(samples)
    elapsed = time.time() - t_start
    avg_cer = total_cer / n if n else 0.0
    avg_wer = total_wer / n if n else 0.0
    acc     = exact_matches / n * 100 if n else 0.0

    # Hiển thị top errors
    if show_errors > 0:
        errors = [r for r in results if not r["exact"]]
        errors.sort(key=lambda r: r["cer"], reverse=True)
        print(f"\n  Top-{min(show_errors, len(errors))} lỗi nặng nhất (CER cao nhất):")
        for r in errors[:show_errors]:
            print(f"    CER={r['cer']:6.1f}%  GT : {r['ground_truth'][:60]}")
            print(f"           Pred: {r['prediction'][:60]}")

    return {
        "checkpoint"       : str(checkpoint),
        "n_samples"        : n,
        "avg_cer_percent"  : round(avg_cer, 3),
        "avg_wer_percent"  : round(avg_wer, 3),
        "exact_match_pct"  : round(acc, 2),
        "elapsed_seconds"  : round(elapsed, 1),
        "ms_per_sample"    : round(elapsed / n * 1000, 1) if n else 0,
        "beamsearch"       : beamsearch,
        "samples"          : results,
    }


# ── CLI ────────────────────────────────────────────────────────────────────────

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Đánh giá VietOCR checkpoint — tính CER và WER.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--checkpoint", "-c",
        type=Path, nargs="+", required=True,
        help="Đường dẫn checkpoint .pth (có thể truyền nhiều để so sánh)",
    )
    parser.add_argument(
        "--annotation", "-a",
        type=Path, required=True,
        help="File annotation có nhãn (path<TAB>label)",
    )
    parser.add_argument(
        "--data-root",
        type=Path, default=None,
        help="Thư mục gốc để resolve relative path trong annotation. Mặc định: cwd",
    )
    parser.add_argument(
        "--output", "-o",
        type=Path, default=None,
        help="Lưu kết quả chi tiết ra file JSON. Bỏ qua nếu không cần.",
    )
    parser.add_argument(
        "--beamsearch",
        action="store_true",
        help="Dùng beam search (chính xác hơn, chậm hơn ~3-5x)",
    )
    parser.add_argument(
        "--cpu",
        action="store_true",
        help="Ép dùng CPU dù có GPU",
    )
    parser.add_argument(
        "--show-errors",
        type=int, default=5,
        help="Hiển thị N mẫu lỗi nặng nhất (0 = tắt)",
    )
    return parser


def print_summary_table(all_results: List[Dict]) -> None:
    """In bảng so sánh tất cả checkpoint."""
    print("\n" + "=" * 72)
    print(f"{'Checkpoint':<40} {'CER%':>7} {'WER%':>7} {'Acc%':>7} {'ms/img':>7}")
    print("-" * 72)
    for r in all_results:
        name = Path(r["checkpoint"]).name[:39]
        print(f"{name:<40} {r['avg_cer_percent']:>7.2f} "
              f"{r['avg_wer_percent']:>7.2f} "
              f"{r['exact_match_pct']:>7.2f} "
              f"{r['ms_per_sample']:>7.1f}")
    print("=" * 72)
    print()
    if len(all_results) > 1:
        best = min(all_results, key=lambda r: r["avg_cer_percent"])
        print(f"  ✅ Best CER: {Path(best['checkpoint']).name}  ({best['avg_cer_percent']:.2f}%)")


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    parser = build_parser()
    args   = parser.parse_args()

    # Device
    if args.cpu or not torch.cuda.is_available():
        device = "cpu"
    else:
        device = "cuda"
        print(f"  GPU: {torch.cuda.get_device_name(0)}")

    # Data root
    data_root = args.data_root.resolve() if args.data_root else Path.cwd()

    # Load annotation
    if not args.annotation.exists():
        print(f"[ERROR] File annotation không tồn tại: {args.annotation}", file=sys.stderr)
        sys.exit(1)

    print(f"[evaluate] Đọc annotation: {args.annotation}")
    samples = load_annotation(args.annotation, data_root)
    if not samples:
        print("[ERROR] Không có sample hợp lệ nào. Kiểm tra file annotation và path ảnh.")
        sys.exit(1)

    print(f"           Tìm thấy {len(samples)} samples hợp lệ.")

    # Validate checkpoints exist
    for ckpt in args.checkpoint:
        if not ckpt.exists():
            print(f"[ERROR] Checkpoint không tồn tại: {ckpt}", file=sys.stderr)
            sys.exit(1)

    # Evaluate each checkpoint
    all_results = []
    for ckpt in args.checkpoint:
        result = evaluate_checkpoint(
            checkpoint  = ckpt,
            samples     = samples,
            device      = device,
            beamsearch  = args.beamsearch,
            show_errors = args.show_errors,
        )
        all_results.append(result)

    # Summary table
    print_summary_table(all_results)

    # Save JSON
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        output_data = {
            "annotation": str(args.annotation),
            "n_samples" : len(samples),
            "beamsearch": args.beamsearch,
            "results"   : all_results,
        }
        with open(args.output, "w", encoding="utf-8") as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False)
        print(f"  Kết quả chi tiết: {args.output}")


if __name__ == "__main__":
    main()
