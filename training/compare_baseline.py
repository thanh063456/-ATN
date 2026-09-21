#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
training/compare_baseline.py — So sánh VietOCR Pretrained vs Fine-tuned

Mục đích
--------
Chạy đánh giá CẢ HAI model trên CÙNG một tập test, xuất:
  1. dataset/statistics/ocr_comparison.csv  — bảng CER/WER từng sample + tổng hợp
  2. dataset/statistics/ocr_comparison_summary.csv — bảng tổng hợp slide-ready
  3. dataset/statistics/improvement_examples/  — ảnh + text của 5-10 dòng cải thiện rõ nhất
  4. dataset/statistics/ocr_comparison_report.md — báo cáo Markdown dán thẳng vào slide

Metrics (theo .ai/research/CER.md, WER.md, Evaluation.md)
-----------------------------------------------------------
  CER = Levenshtein(pred, gt) / len(gt) × 100%   (mục tiêu: < 5%)
  WER = word-level Levenshtein / n_ref_words × 100%  (mục tiêu: < 10%)
  Unicode NFC normalization trước khi so sánh (quan trọng với tiếng Việt)

Ngưỡng đánh giá (CER.md)
  < 2%  : Xuất sắc
  < 5%  : Đạt yêu cầu production
  5-15% : Cần hiệu chỉnh thủ công
  >= 15%: Không đạt

Cách dùng
---------
  python training/compare_baseline.py \\
      --pretrained  models/vgg_transformer_pretrained.pth \\
      --finetuned   models/transformerocr_ctsv_v1_best.pth \\
      --annotation  dataset/annotations/annotation_val.txt \\
      --output-dir  dataset/statistics/

  # Đặt nhãn tùy chỉnh trong bảng
  python training/compare_baseline.py \\
      --pretrained      models/vgg_transformer_pretrained.pth \\
      --finetuned       models/transformerocr_ctsv_v1_best.pth \\
      --annotation      dataset/annotations/annotation_val.txt \\
      --pretrained-label "VietOCR Pretrained (baseline)" \\
      --finetuned-label  "VietOCR Fine-tuned (CTSV v1)" \\
      --top-examples     10

  # Không có GPU
  python training/compare_baseline.py \\
      --pretrained  models/pretrained.pth \\
      --finetuned   models/finetuned.pth \\
      --annotation  dataset/annotations/annotation_val.txt \\
      --cpu

Phụ thuộc
----------
  pip install vietocr torch pillow editdistance

Ghi chú Windows Unicode path
------------------------------
  Dùng np.fromfile + cv2.imdecode để đọc ảnh (không dùng cv2.imread trực tiếp).
  Dùng cv2.imencode + tofile để lưu ảnh minh họa.
"""

import argparse
import csv
import json
import sys
import time
import unicodedata
from datetime import datetime
from pathlib import Path
from typing import Dict, List, NamedTuple, Optional, Tuple

# ── Guards ────────────────────────────────────────────────────────────────────
try:
    import torch
except ImportError:
    print("[ERROR] PyTorch chưa cài. Xem: https://pytorch.org", file=sys.stderr)
    sys.exit(1)

try:
    from vietocr.tool.config import Cfg
    from vietocr.tool.predictor import Predictor
except ImportError:
    print("[ERROR] VietOCR chưa cài. Chạy: pip install vietocr", file=sys.stderr)
    sys.exit(1)

try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError:
    print("[ERROR] Pillow chưa cài. Chạy: pip install pillow", file=sys.stderr)
    sys.exit(1)

try:
    import editdistance
    _EDIT_BACKEND = "editdistance"
except ImportError:
    _EDIT_BACKEND = "builtin"
    print("[WARN] editdistance chưa cài — dùng fallback thuần Python.")
    print("       Khuyến nghị: pip install editdistance")

try:
    import cv2
    import numpy as np
    _HAS_CV2 = True
except ImportError:
    _HAS_CV2 = False
    print("[WARN] OpenCV chưa cài — bỏ qua sinh ảnh minh họa.")
    print("       Chạy: pip install opencv-python-headless")


# ── Thresholds (từ CER.md) ────────────────────────────────────────────────────
CER_EXCELLENT  = 2.0    # < 2%  : Xuất sắc
CER_PRODUCTION = 5.0    # < 5%  : Đạt production
CER_MANUAL     = 15.0   # < 15% : Cần hiệu chỉnh
# >= 15% : Không đạt

WER_TARGET     = 10.0   # < 10% : Mục tiêu WER


# ── Data types ────────────────────────────────────────────────────────────────
class SampleResult(NamedTuple):
    image_path: str
    ground_truth: str
    pred_pretrained: str
    conf_pretrained: float
    pred_finetuned: str
    conf_finetuned: float
    cer_pretrained: float   # %
    wer_pretrained: float   # %
    cer_finetuned: float    # %
    wer_finetuned: float    # %
    cer_improvement: float  # pretrained - finetuned (positive = improved)
    wer_improvement: float
    exact_pretrained: bool
    exact_finetuned: bool


# ── Metric functions ──────────────────────────────────────────────────────────

def _levenshtein(a: str, b: str) -> int:
    """Pure-Python Levenshtein distance fallback."""
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


def edit_dist(a, b) -> int:
    """Edit distance — dùng editdistance lib nếu có."""
    if _EDIT_BACKEND == "editdistance":
        return editdistance.eval(a, b)
    if isinstance(a, list):
        # word-level: encode as strings then compute
        return _levenshtein(" ".join(a), " ".join(b))
    return _levenshtein(a, b)


def nfc(s: str) -> str:
    """Unicode NFC normalization — bắt buộc cho tiếng Việt (CER.md)."""
    return unicodedata.normalize("NFC", s)


def compute_cer(pred: str, gt: str) -> float:
    """CER % = edit_distance(pred, gt) / len(gt) × 100. NFC normalized."""
    gt_n, pred_n = nfc(gt), nfc(pred)
    if not gt_n and not pred_n:
        return 0.0
    if not gt_n:
        return 100.0
    return edit_dist(gt_n, pred_n) / len(gt_n) * 100.0


def compute_wer(pred: str, gt: str) -> float:
    """WER % = word-level edit distance / len(gt_words) × 100. NFC normalized."""
    gt_words   = nfc(gt).split()
    pred_words = nfc(pred).split()
    if not gt_words and not pred_words:
        return 0.0
    if not gt_words:
        return 100.0
    # Dynamic programming word-level Levenshtein
    n, m = len(gt_words), len(pred_words)
    dp = list(range(n + 1))
    for pw in pred_words:
        ndp = [dp[0] + 1]
        for j, gw in enumerate(gt_words):
            ndp.append(min(dp[j + 1] + 1, ndp[j] + 1, dp[j] + (pw != gw)))
        dp = ndp
    return dp[n] / n * 100.0


def cer_grade(cer: float) -> str:
    """Phân loại CER theo ngưỡng CER.md."""
    if cer < CER_EXCELLENT:
        return "Xuất sắc"
    if cer < CER_PRODUCTION:
        return "Đạt production"
    if cer < CER_MANUAL:
        return "Cần hiệu chỉnh"
    return "Không đạt"


# ── I/O helpers ───────────────────────────────────────────────────────────────

def open_image_unicode(path: Path) -> Image.Image:
    """Mở ảnh hỗ trợ Unicode path (dùng bytes mode)."""
    with open(str(path), "rb") as f:
        img = Image.open(f)
        img.load()
    return img.convert("RGB")


def imread_unicode(path: Path):
    """cv2.imdecode từ path Unicode (bypass cv2.imread giới hạn Windows)."""
    if not _HAS_CV2:
        return None
    buf = np.fromfile(str(path), dtype=np.uint8)
    return cv2.imdecode(buf, cv2.IMREAD_COLOR)


def imwrite_unicode(path: Path, img) -> bool:
    """cv2.imencode + tofile — hỗ trợ Unicode path trên Windows."""
    if not _HAS_CV2:
        return False
    ext = path.suffix.lower()
    ret, buf = cv2.imencode(ext, img)
    if ret:
        buf.tofile(str(path))
    return ret


def load_annotation(ann_path: Path, data_root: Path) -> List[Tuple[Path, str]]:
    """
    Đọc file annotation VietOCR format (path<TAB>label).
    Bỏ comment (#), dòng không TAB, nhãn rỗng, ảnh không tồn tại.
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
            # Resolve path
            img_path = data_root / img_rel
            if not img_path.exists():
                img_path = Path(img_rel)
            if not img_path.exists():
                skipped += 1
                continue
            samples.append((img_path, label))
    if skipped:
        print(f"  [WARN] Bỏ qua {skipped} dòng (nhãn rỗng / file thiếu / sai định dạng)")
    return samples


# ── Predictor ─────────────────────────────────────────────────────────────────

def build_predictor(checkpoint: Path, device: str, beamsearch: bool) -> Predictor:
    config = Cfg.load_config_from_name("vgg_transformer")
    config["weights"]                 = str(checkpoint.resolve())
    config["device"]                  = device
    config["predictor"]["beamsearch"] = beamsearch
    config["pretrain"]                = False
    return Predictor(config)


def run_inference(
    predictor: Predictor,
    samples: List[Tuple[Path, str]],
    label: str,
) -> List[Tuple[str, float]]:
    """
    Chạy inference trên toàn bộ samples.
    Trả về list (prediction, confidence) theo thứ tự samples.
    """
    results = []
    t0 = time.time()
    print(f"\n  [{label}] Đang inference {len(samples)} samples...")
    for i, (img_path, _) in enumerate(samples, 1):
        try:
            img  = open_image_unicode(img_path)
            pred, conf = predictor.predict(img, return_prob=True)
            results.append((pred.strip(), float(conf)))
        except Exception as exc:
            print(f"    [ERROR] {img_path.name}: {exc}")
            results.append(("", 0.0))
        if i % 50 == 0 or i == len(samples):
            elapsed = time.time() - t0
            print(f"    [{i}/{len(samples)}]  {elapsed:.1f}s  "
                  f"({elapsed/i*1000:.0f}ms/sample)")
    return results


# ── Comparison core ───────────────────────────────────────────────────────────

def compare_models(
    samples: List[Tuple[Path, str]],
    preds_pre: List[Tuple[str, float]],
    preds_fine: List[Tuple[str, float]],
) -> List[SampleResult]:
    """Kết hợp prediction hai model, tính metrics từng sample."""
    results = []
    for (img_path, gt), (pred_pre, conf_pre), (pred_fine, conf_fine) in zip(
        samples, preds_pre, preds_fine
    ):
        cer_pre  = compute_cer(pred_pre,  gt)
        wer_pre  = compute_wer(pred_pre,  gt)
        cer_fine = compute_cer(pred_fine, gt)
        wer_fine = compute_wer(pred_fine, gt)
        results.append(SampleResult(
            image_path       = str(img_path),
            ground_truth     = gt,
            pred_pretrained  = pred_pre,
            conf_pretrained  = round(conf_pre, 4),
            pred_finetuned   = pred_fine,
            conf_finetuned   = round(conf_fine, 4),
            cer_pretrained   = round(cer_pre,  2),
            wer_pretrained   = round(wer_pre,  2),
            cer_finetuned    = round(cer_fine, 2),
            wer_finetuned    = round(wer_fine, 2),
            cer_improvement  = round(cer_pre  - cer_fine, 2),
            wer_improvement  = round(wer_pre  - wer_fine, 2),
            exact_pretrained = nfc(pred_pre)  == nfc(gt),
            exact_finetuned  = nfc(pred_fine) == nfc(gt),
        ))
    return results


# ── Output generators ─────────────────────────────────────────────────────────

def save_detail_csv(
    results: List[SampleResult],
    out_path: Path,
    label_pre: str,
    label_fine: str,
) -> None:
    """CSV từng sample — dùng để debug và phân tích chi tiết."""
    fieldnames = [
        "image", "ground_truth",
        f"pred_{label_pre}", f"conf_{label_pre}",
        f"cer_{label_pre}_%", f"wer_{label_pre}_%",
        f"pred_{label_fine}", f"conf_{label_fine}",
        f"cer_{label_fine}_%", f"wer_{label_fine}_%",
        "cer_improvement_%", "wer_improvement_%",
        f"exact_{label_pre}", f"exact_{label_fine}",
    ]
    with open(out_path, "w", encoding="utf-8-sig", newline="") as f:
        # utf-8-sig = UTF-8 with BOM → Excel mở đúng tiếng Việt
        w = csv.writer(f)
        w.writerow(fieldnames)
        for r in results:
            w.writerow([
                Path(r.image_path).name,
                r.ground_truth,
                r.pred_pretrained, r.conf_pretrained,
                r.cer_pretrained, r.wer_pretrained,
                r.pred_finetuned, r.conf_finetuned,
                r.cer_finetuned, r.wer_finetuned,
                r.cer_improvement, r.wer_improvement,
                "Yes" if r.exact_pretrained else "No",
                "Yes" if r.exact_finetuned  else "No",
            ])


def save_summary_csv(
    results: List[SampleResult],
    out_path: Path,
    label_pre: str,
    label_fine: str,
) -> Dict:
    """
    CSV tổng hợp 2 dòng (1 model mỗi dòng) — slide-ready.
    Trả về dict summary để dùng trong báo cáo Markdown.
    """
    n = len(results)
    if n == 0:
        return {}

    avg_cer_pre  = sum(r.cer_pretrained  for r in results) / n
    avg_cer_fine = sum(r.cer_finetuned   for r in results) / n
    avg_wer_pre  = sum(r.wer_pretrained  for r in results) / n
    avg_wer_fine = sum(r.wer_finetuned   for r in results) / n
    exact_pre    = sum(1 for r in results if r.exact_pretrained) / n * 100
    exact_fine   = sum(1 for r in results if r.exact_finetuned)  / n * 100
    cer_improve  = avg_cer_pre  - avg_cer_fine
    wer_improve  = avg_wer_pre  - avg_wer_fine
    exact_improve= exact_fine   - exact_pre

    # Samples trong vùng "cải thiện" (finetuned CER thấp hơn pretrained)
    improved_samples = sum(1 for r in results if r.cer_improvement > 0)
    regressed_samples= sum(1 for r in results if r.cer_improvement < 0)

    rows = [
        ["Model", "Avg CER (%)", "Avg WER (%)", "Exact Match (%)", "Grade (CER)", "n_samples"],
        [label_pre,  f"{avg_cer_pre:.2f}",  f"{avg_wer_pre:.2f}",
         f"{exact_pre:.1f}",  cer_grade(avg_cer_pre),  n],
        [label_fine, f"{avg_cer_fine:.2f}", f"{avg_wer_fine:.2f}",
         f"{exact_fine:.1f}", cer_grade(avg_cer_fine), n],
        ["Improvement (↓ better)",
         f"{cer_improve:+.2f}", f"{wer_improve:+.2f}", f"{exact_improve:+.1f}", "", ""],
    ]

    with open(out_path, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f)
        for row in rows:
            w.writerow(row)

    return {
        "label_pre": label_pre, "label_fine": label_fine,
        "n": n,
        "avg_cer_pre": round(avg_cer_pre, 2), "avg_cer_fine": round(avg_cer_fine, 2),
        "avg_wer_pre": round(avg_wer_pre, 2), "avg_wer_fine": round(avg_wer_fine, 2),
        "exact_pre":   round(exact_pre, 1),   "exact_fine":   round(exact_fine, 1),
        "cer_improve": round(cer_improve, 2),  "wer_improve":  round(wer_improve, 2),
        "exact_improve": round(exact_improve, 1),
        "improved_samples": improved_samples, "regressed_samples": regressed_samples,
        "grade_pre":   cer_grade(avg_cer_pre), "grade_fine":  cer_grade(avg_cer_fine),
    }


# ── Example images ────────────────────────────────────────────────────────────

def _draw_comparison_image(
    crop_img,           # cv2 BGR image of the text line
    gt: str,
    pred_pre: str,
    pred_fine: str,
    cer_pre: float,
    cer_fine: float,
) -> Optional[object]:  # returns cv2 image or None
    """
    Tạo ảnh minh họa: ảnh gốc + 3 dòng text (GT / Pretrained / Fine-tuned).
    Layout:
      ┌─────────────────────────────────────┐
      │  [Ảnh gốc dòng văn bản]             │
      ├─────────────────────────────────────┤
      │ GT      : ...                       │
      │ Pretrain: ...  CER=XX%              │
      │ Finetune: ...  CER=YY%  ▼ IMPROVED  │
      └─────────────────────────────────────┘
    """
    if not _HAS_CV2 or crop_img is None:
        return None

    W_MIN = 800
    h_img, w_img = crop_img.shape[:2]

    # Scale image to minimum width nếu quá nhỏ
    if w_img < W_MIN:
        scale    = W_MIN / w_img
        new_w    = int(w_img * scale)
        new_h    = int(h_img * scale)
        crop_img = cv2.resize(crop_img, (new_w, new_h), interpolation=cv2.INTER_LINEAR)
        h_img, w_img = crop_img.shape[:2]

    # Phần text bên dưới ảnh
    font       = cv2.FONT_HERSHEY_SIMPLEX
    font_scale = 0.55
    thickness  = 1
    line_h     = 28
    pad        = 10
    text_h     = pad + 4 * line_h + pad

    canvas = np.ones((h_img + text_h, max(w_img, W_MIN), 3), dtype=np.uint8) * 245
    canvas[:h_img, :w_img] = crop_img

    # Border between image and text
    cv2.line(canvas, (0, h_img), (canvas.shape[1], h_img), (180, 180, 180), 1)

    def put(y: int, text: str, color=(40, 40, 40)) -> None:
        # Truncate long text để vừa canvas
        max_chars = (canvas.shape[1] - 20) // 10
        if len(text) > max_chars:
            text = text[:max_chars - 3] + "..."
        cv2.putText(canvas, text, (10, y), font, font_scale, color, thickness, cv2.LINE_AA)

    y0 = h_img + pad + line_h
    improved = cer_fine < cer_pre

    put(y0,           f"GT      : {gt}")
    put(y0 + line_h,  f"Pretrain: {pred_pre}   [CER={cer_pre:.1f}%]", color=(180, 60, 60))
    put(y0 + 2*line_h,
        f"Finetune: {pred_fine}   [CER={cer_fine:.1f}%]"
        + ("  << IMPROVED" if improved else ""),
        color=(40, 140, 40) if improved else (60, 60, 180))

    return canvas


def save_improvement_examples(
    results: List[SampleResult],
    out_dir: Path,
    n_examples: int,
    data_root: Path,
) -> List[Dict]:
    """
    Chọn n_examples dòng cải thiện rõ nhất (cer_improvement lớn nhất),
    lưu ảnh minh họa và trả về list metadata.
    """
    out_dir.mkdir(parents=True, exist_ok=True)

    # Sắp xếp theo cải thiện CER giảm dần
    improved = sorted(
        [r for r in results if r.cer_improvement > 0],
        key=lambda r: r.cer_improvement,
        reverse=True,
    )[:n_examples]

    if not improved:
        print("  [WARN] Không có sample nào mà fine-tuned cải thiện so với pretrained.")
        return []

    metadata = []
    for idx, r in enumerate(improved, 1):
        img_path = Path(r.image_path)
        if not img_path.exists():
            img_path = data_root / r.image_path
        if not img_path.exists():
            continue

        out_img_path = out_dir / f"example_{idx:02d}_{img_path.stem}.png"
        saved_img = False

        if _HAS_CV2:
            crop = imread_unicode(img_path)
            vis  = _draw_comparison_image(
                crop, r.ground_truth,
                r.pred_pretrained, r.pred_finetuned,
                r.cer_pretrained,  r.cer_finetuned,
            )
            if vis is not None:
                imwrite_unicode(out_img_path, vis)
                saved_img = True

        meta = {
            "rank"            : idx,
            "image"           : img_path.name,
            "viz_image"       : str(out_img_path) if saved_img else None,
            "ground_truth"    : r.ground_truth,
            "pred_pretrained" : r.pred_pretrained,
            "pred_finetuned"  : r.pred_finetuned,
            "cer_pretrained"  : r.cer_pretrained,
            "cer_finetuned"   : r.cer_finetuned,
            "cer_improvement" : r.cer_improvement,
            "wer_pretrained"  : r.wer_pretrained,
            "wer_finetuned"   : r.wer_finetuned,
        }
        metadata.append(meta)
        print(f"    Example {idx:02d}: CER {r.cer_pretrained:.1f}% → {r.cer_finetuned:.1f}%  "
              f"(↓{r.cer_improvement:.1f}pp)  '{r.ground_truth[:40]}'")

    # Lưu metadata JSON
    meta_json = out_dir / "examples_metadata.json"
    with open(meta_json, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2, ensure_ascii=False)

    return metadata


def save_markdown_report(
    summary: Dict,
    examples: List[Dict],
    out_path: Path,
    label_pre: str,
    label_fine: str,
    annotation_path: str,
) -> None:
    """
    Sinh file Markdown slide-ready: bảng tổng hợp + bảng ví dụ cải thiện.
    Có thể dán thẳng vào báo cáo hoặc convert sang slide.
    """
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    n   = summary.get("n", 0)

    # Improvement indicator
    def delta(val: float, reverse: bool = False) -> str:
        """reverse=True: âm là tốt (CER/WER giảm = tốt)"""
        if reverse:
            sign = "↓" if val > 0 else ("↑" if val < 0 else "→")
            color_good = val > 0
        else:
            sign = "↑" if val > 0 else ("↓" if val < 0 else "→")
            color_good = val > 0
        return f"{sign} {abs(val):.2f}pp"

    lines = [
        f"# Kết quả Thực nghiệm OCR — So sánh Pretrained vs Fine-tuned",
        f"",
        f"**Ngày tạo**: {now}  ",
        f"**Tập test**: `{annotation_path}`  ",
        f"**Số mẫu**: {n} dòng văn bản  ",
        f"",
        f"---",
        f"",
        f"## 1. Bảng Tổng hợp (Slide-ready)",
        f"",
        f"| Metric | {label_pre} | {label_fine} | Cải thiện |",
        f"|--------|{'—'*len(label_pre)}|{'—'*len(label_fine)}|-----------|",
        f"| **CER (%)** ↓ tốt hơn | **{summary['avg_cer_pre']:.2f}%** | **{summary['avg_cer_fine']:.2f}%** | {delta(summary['cer_improve'], reverse=True)} |",
        f"| **WER (%)** ↓ tốt hơn | {summary['avg_wer_pre']:.2f}% | {summary['avg_wer_fine']:.2f}% | {delta(summary['wer_improve'], reverse=True)} |",
        f"| **Exact Match (%)** ↑ tốt hơn | {summary['exact_pre']:.1f}% | {summary['exact_fine']:.1f}% | {delta(summary['exact_improve'])} |",
        f"| **Đánh giá CER** | {summary['grade_pre']} | {summary['grade_fine']} | |",
        f"",
        f"> **Mục tiêu**: CER < 5% (production), WER < 10%  ",
        f"> Ngưỡng đánh giá: Xuất sắc < 2% / Đạt < 5% / Cần hiệu chỉnh < 15% / Không đạt ≥ 15%",
        f"",
        f"---",
        f"",
        f"## 2. Phân tích Chi tiết",
        f"",
        f"- **Số mẫu fine-tuned cải thiện**: {summary['improved_samples']}/{n} ({summary['improved_samples']/n*100:.0f}%)" if n else "",
        f"- **Số mẫu fine-tuned giảm sút**: {summary['regressed_samples']}/{n} ({summary['regressed_samples']/n*100:.0f}%)" if n else "",
        f"- **Cải thiện CER trung bình**: {summary['cer_improve']:+.2f} percentage points",
        f"- **Cải thiện WER trung bình**: {summary['wer_improve']:+.2f} percentage points",
        f"",
        f"---",
        f"",
        f"## 3. Ví dụ Cải thiện Rõ rệt (top {len(examples)})",
        f"",
        f"*Các dòng văn bản mà fine-tuned model nhận dạng tốt hơn pretrained rõ rệt nhất:*",
        f"",
    ]

    if examples:
        lines += [
            f"| # | Ground Truth | Pretrained (CER%) | Fine-tuned (CER%) | Cải thiện |",
            f"|---|--------------|-------------------|-------------------|-----------|",
        ]
        for ex in examples:
            gt   = ex["ground_truth"][:40].replace("|", "\\|")
            pre  = ex["pred_pretrained"][:35].replace("|", "\\|")
            fine = ex["pred_finetuned"][:35].replace("|", "\\|")
            lines.append(
                f"| {ex['rank']} | {gt} | {pre} ({ex['cer_pretrained']:.1f}%) "
                f"| {fine} ({ex['cer_finetuned']:.1f}%) "
                f"| ↓{ex['cer_improvement']:.1f}pp |"
            )
        lines += [
            f"",
            f"*Ảnh minh họa: `dataset/statistics/improvement_examples/`*",
        ]
    else:
        lines.append("> Không có ví dụ cải thiện (model fine-tuned chưa cải thiện trên tập test này).")

    lines += [
        f"",
        f"---",
        f"",
        f"## 4. File Đầu ra",
        f"",
        f"| File | Nội dung |",
        f"|------|---------|",
        f"| `ocr_comparison.csv` | CER/WER từng sample (chi tiết) |",
        f"| `ocr_comparison_summary.csv` | Bảng tổng hợp 2 dòng (slide) |",
        f"| `improvement_examples/` | Ảnh + text ví dụ cải thiện |",
        f"| `ocr_comparison_report.md` | File này |",
        f"",
        f"---",
        f"*Generated by `training/compare_baseline.py`*",
    ]

    with open(out_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))


# ── CLI ────────────────────────────────────────────────────────────────────────

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="So sánh VietOCR Pretrained vs Fine-tuned — xuất CSV và ảnh minh họa.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--pretrained", type=Path, required=True,
        help="Checkpoint pretrained gốc (.pth)",
    )
    parser.add_argument(
        "--finetuned", type=Path, required=True,
        help="Checkpoint đã fine-tune (.pth)",
    )
    parser.add_argument(
        "--annotation", type=Path, required=True,
        help="File annotation test set (path<TAB>label)",
    )
    parser.add_argument(
        "--output-dir", type=Path,
        default=Path("dataset/statistics"),
        help="Thư mục lưu tất cả output",
    )
    parser.add_argument(
        "--data-root", type=Path, default=None,
        help="Thư mục gốc để resolve relative path trong annotation. Mặc định: cwd",
    )
    parser.add_argument(
        "--pretrained-label", type=str,
        default="VietOCR Pretrained",
        help="Tên hiển thị cho model pretrained trong bảng",
    )
    parser.add_argument(
        "--finetuned-label", type=str,
        default="VietOCR Fine-tuned (CTSV)",
        help="Tên hiển thị cho model fine-tuned trong bảng",
    )
    parser.add_argument(
        "--top-examples", type=int, default=10,
        help="Số ví dụ cải thiện tốt nhất cần xuất ra (0 = tắt)",
    )
    parser.add_argument(
        "--beamsearch", action="store_true",
        help="Dùng beam search (chính xác hơn, chậm hơn ~3-5x)",
    )
    parser.add_argument(
        "--cpu", action="store_true",
        help="Ép dùng CPU dù có GPU",
    )
    return parser


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    parser = build_parser()
    args   = parser.parse_args()

    print("=" * 65)
    print(" OCR Baseline Comparison — Pretrained vs Fine-tuned (CTSV)")
    print("=" * 65)

    # ── Validate inputs ───────────────────────────────────────────────────────
    for name, p in [("--pretrained", args.pretrained), ("--finetuned", args.finetuned)]:
        if not p.exists():
            print(f"[ERROR] {name}: file không tồn tại: {p}", file=sys.stderr)
            sys.exit(1)
    if not args.annotation.exists():
        print(f"[ERROR] --annotation: file không tồn tại: {args.annotation}", file=sys.stderr)
        sys.exit(1)

    data_root = args.data_root.resolve() if args.data_root else Path.cwd()
    out_dir   = args.output_dir.resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    device = "cpu" if (args.cpu or not torch.cuda.is_available()) else "cuda"
    if device == "cuda":
        print(f"  GPU: {torch.cuda.get_device_name(0)}")
    else:
        print("  Device: CPU")

    # ── Load samples ──────────────────────────────────────────────────────────
    print(f"\n  Đọc annotation: {args.annotation}")
    samples = load_annotation(args.annotation, data_root)
    if not samples:
        print("[ERROR] Không có sample hợp lệ. Kiểm tra file annotation.")
        sys.exit(1)
    print(f"  Tìm thấy {len(samples)} samples hợp lệ.")

    # ── Run inference ─────────────────────────────────────────────────────────
    # Pretrained
    print(f"\n  Tải model pretrained: {args.pretrained.name}")
    predictor_pre = build_predictor(args.pretrained, device, args.beamsearch)
    preds_pre = run_inference(predictor_pre, samples, args.pretrained_label)
    del predictor_pre   # giải phóng VRAM trước khi load model tiếp theo
    if device == "cuda":
        torch.cuda.empty_cache()

    # Fine-tuned
    print(f"\n  Tải model fine-tuned: {args.finetuned.name}")
    predictor_fine = build_predictor(args.finetuned, device, args.beamsearch)
    preds_fine = run_inference(predictor_fine, samples, args.finetuned_label)
    del predictor_fine
    if device == "cuda":
        torch.cuda.empty_cache()

    # ── Compare ───────────────────────────────────────────────────────────────
    print("\n  Tính metrics...")
    results = compare_models(samples, preds_pre, preds_fine)

    # ── Save outputs ──────────────────────────────────────────────────────────
    # 1. Detail CSV
    detail_csv = out_dir / "ocr_comparison.csv"
    save_detail_csv(results, detail_csv, args.pretrained_label, args.finetuned_label)
    print(f"\n  [1/4] Detail CSV  : {detail_csv}")

    # 2. Summary CSV
    summary_csv = out_dir / "ocr_comparison_summary.csv"
    summary = save_summary_csv(results, summary_csv, args.pretrained_label, args.finetuned_label)
    print(f"  [2/4] Summary CSV : {summary_csv}")

    # 3. Improvement examples
    if args.top_examples > 0:
        ex_dir = out_dir / "improvement_examples"
        print(f"\n  [3/4] Sinh ảnh minh họa ({args.top_examples} examples) → {ex_dir}")
        examples = save_improvement_examples(results, ex_dir, args.top_examples, data_root)
    else:
        examples = []
        print("  [3/4] Bỏ qua ảnh minh họa (--top-examples 0)")

    # 4. Markdown report
    report_md = out_dir / "ocr_comparison_report.md"
    save_markdown_report(
        summary, examples, report_md,
        args.pretrained_label, args.finetuned_label,
        str(args.annotation),
    )
    print(f"  [4/4] Report MD   : {report_md}")

    # ── Print summary table ───────────────────────────────────────────────────
    n = summary.get("n", 0)
    print("\n" + "=" * 65)
    print(f" KẾT QUẢ THỰC NGHIỆM ({n} mẫu test)")
    print("=" * 65)
    w1 = max(len(args.pretrained_label), len(args.finetuned_label), 28)
    print(f"  {'Model':<{w1}}  {'CER%':>7}  {'WER%':>7}  {'Exact%':>7}  Grade")
    print("  " + "-" * (w1 + 34))
    print(f"  {args.pretrained_label:<{w1}}  {summary['avg_cer_pre']:>7.2f}  "
          f"{summary['avg_wer_pre']:>7.2f}  {summary['exact_pre']:>7.1f}  {summary['grade_pre']}")
    print(f"  {args.finetuned_label:<{w1}}  {summary['avg_cer_fine']:>7.2f}  "
          f"{summary['avg_wer_fine']:>7.2f}  {summary['exact_fine']:>7.1f}  {summary['grade_fine']}")
    print("  " + "-" * (w1 + 34))
    sign_cer = "↓" if summary["cer_improve"] > 0 else ("↑" if summary["cer_improve"] < 0 else "→")
    sign_wer = "↓" if summary["wer_improve"] > 0 else ("↑" if summary["wer_improve"] < 0 else "→")
    print(f"  {'Cải thiện':<{w1}}  "
          f"{sign_cer}{abs(summary['cer_improve']):>6.2f}pp  "
          f"{sign_wer}{abs(summary['wer_improve']):>6.2f}pp  "
          f"{summary['exact_improve']:>+7.1f}pp")
    print("=" * 65)

    if summary["cer_improve"] > 0:
        print(f"\n  ✅ Fine-tuned model cải thiện CER {summary['cer_improve']:.2f}pp "
              f"({summary['improved_samples']}/{n} mẫu cải thiện)")
    else:
        print(f"\n  ⚠️  Fine-tuned model chưa cải thiện — kiểm tra data và số iterations.")

    print(f"\n  Toàn bộ output: {out_dir}/")


if __name__ == "__main__":
    main()
