#!/usr/bin/env python
"""
scripts/bench_ocr.py — Benchmark baseline OCR (Bước 0)

Đo trước khi sửa bất cứ logic nào (baseline).
Kết quả lưu vào docs/ocr_benchmark.md (cột "trước").

Sử dụng:
    python scripts/bench_ocr.py                         # CTSV_013 toàn trang
    python scripts/bench_ocr.py --doc CTSV_013          # chỉ CTSV_013
    python scripts/bench_ocr.py --doc CTSV_013 --pages 1 2   # trang cụ thể
    python scripts/bench_ocr.py --annotation-only       # chỉ CER/WER
    OCR_DEBUG_DUMP=1 python scripts/bench_ocr.py        # lưu overlay debug

Biến môi trường:
    OCR_DEBUG_DUMP=1  — lưu overlay box debug vào logs/ocr_debug/<doc_id>/
"""
from __future__ import annotations

import argparse
import os
import re
import sys
import time
from pathlib import Path

# ── Đảm bảo import được app.services từ repo root ─────────────────────────────
_REPO_ROOT = Path(__file__).resolve().parent.parent
_BACKEND   = _REPO_ROOT / "backend"
sys.path.insert(0, str(_BACKEND))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

os.environ.setdefault("APP_ENV", "development")


# ── Hàm tính CER / WER ────────────────────────────────────────────────────────

def _edit_distance(a: list, b: list) -> int:
    """Levenshtein distance (thao tác: insert, delete, substitute)."""
    m, n = len(a), len(b)
    d = list(range(n + 1))
    for i in range(1, m + 1):
        prev, d[0] = d[0], i
        for j in range(1, n + 1):
            prev, d[j] = d[j], min(
                d[j] + 1,          # delete
                d[j - 1] + 1,      # insert
                prev + (0 if a[i - 1] == b[j - 1] else 1),  # substitute
            )
    return d[n]


def _compute_cer(ref: str, hyp: str) -> float:
    """Character Error Rate = edit_distance(ref, hyp) / len(ref)."""
    r, h = list(ref), list(hyp)
    if not r:
        return 0.0 if not h else 1.0
    return _edit_distance(r, h) / len(r)


def _compute_wer(ref: str, hyp: str) -> float:
    """Word Error Rate = edit_distance(ref.split(), hyp.split()) / len(ref.split())."""
    r, h = ref.split(), hyp.split()
    if not r:
        return 0.0 if not h else 1.0
    return _edit_distance(r, h) / len(r)


# ── Debug overlay ─────────────────────────────────────────────────────────────

def _save_debug_overlay(
    pil_image,
    line_boxes: list[tuple[int, int, int, int]],
    doc_id: str,
    page_idx: int,
    out_dir: Path,
) -> None:
    """Lưu ảnh overlay các bounding box dòng segment. Xanh = box được giữ."""
    try:
        import cv2
        import numpy as np

        img_np = np.array(pil_image)
        overlay = img_np.copy()
        for x, y, w, h in line_boxes:
            cv2.rectangle(overlay, (x, y), (x + w, y + h), (0, 120, 255), 2)
        out_path = out_dir / f"{doc_id}_p{page_idx:02d}_overlay.png"
        cv2.imwrite(str(out_path), cv2.cvtColor(overlay, cv2.COLOR_RGB2BGR))
        print(f"    [DEBUG] overlay → {out_path}")
    except Exception as exc:
        print(f"    [DEBUG] Lưu overlay thất bại: {exc}")


# ── Segment dòng + trả về boxes ───────────────────────────────────────────────

def _segment_with_boxes(
    pil_image,
) -> tuple[list, list[tuple[int, int, int, int]]]:
    """Tái sử dụng logic segment_lines, trả thêm tọa độ box để vẽ overlay."""
    try:
        import cv2
        import numpy as np
        from PIL import Image

        img_np = np.array(pil_image)
        gray = (
            cv2.cvtColor(img_np, cv2.COLOR_RGB2GRAY)
            if len(img_np.shape) == 3
            else img_np.copy()
        )
        h_img, w_img = gray.shape[:2]
        _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)

        kw = max(40, w_img // 20)
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (kw, 1))
        dilated = cv2.dilate(binary, kernel, iterations=1)
        contours, _ = cv2.findContours(
            dilated, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
        )
        raw_boxes = sorted(
            [cv2.boundingRect(c) for c in contours],
            key=lambda b: (b[1] // 20, b[0]),
        )
        line_images, kept_boxes = [], []
        for x, y, w, h in raw_boxes:
            if w < 15 or h < 6 or h > h_img * 0.6:
                continue
            pad_top    = max(0, y - 10)
            pad_bottom = min(h_img, y + h + 8)
            pad_left   = max(0, x - 4)
            pad_right  = min(w_img, x + w + 4)
            line_images.append(
                Image.fromarray(img_np[pad_top:pad_bottom, pad_left:pad_right])
            )
            kept_boxes.append((x, y, w, h))
        return line_images, kept_boxes
    except Exception as exc:
        print(f"    [WARN] _segment_with_boxes lỗi: {exc}")
        return [], []


# ── Benchmark từng trang ──────────────────────────────────────────────────────

def benchmark_pages(
    doc_prefix: str,
    page_ids: list[int] | None,
    images_dir: Path,
    debug_dump: bool,
    debug_root: Path,
) -> list[dict]:
    """OCR danh sách trang, trả về list kết quả mỗi trang."""
    from PIL import Image
    from app.services.vietocr_service import VietOCRService

    svc = VietOCRService()

    all_files = sorted(images_dir.glob(f"{doc_prefix}*.png"))
    if not all_files:
        print(f"[WARN] Không tìm thấy ảnh nào với prefix '{doc_prefix}' trong {images_dir}")
        return []

    if page_ids:
        pages = []
        for pid in page_ids:
            tag = f"_p{pid:02d}.png"
            pages.extend(f for f in all_files if f.name.endswith(tag))
        pages = sorted(pages)
    else:
        pages = all_files

    if not pages:
        print("[WARN] Không có trang nào phù hợp.")
        return []

    results = []
    for page_path in pages:
        print(f"\n  >> OCR: {page_path.name}")
        t0 = time.perf_counter()

        pil_image = Image.open(page_path).convert("RGB")

        # Segment để lấy số dòng + box debug
        line_imgs, boxes = _segment_with_boxes(pil_image)
        n_lines = len(line_imgs)

        # OCR toàn trang
        processed    = svc.preprocess_image(pil_image)
        line_results = svc._ocr_lines_with_engine(processed)
        valid_lines  = [t for t, _ in line_results if not svc._is_noise_line(t)]
        ocr_text     = "\n".join(valid_lines)

        elapsed = time.perf_counter() - t0
        chars   = len(ocr_text)
        words   = len(ocr_text.split())

        print(f"     Dòng segment: {n_lines}  |  Dòng hợp lệ: {len(valid_lines)}")
        print(f"     Thời gian   : {elapsed:.2f}s  |  Ký tự: {chars}  |  Từ: {words}")

        # Debug dump overlay
        if debug_dump and boxes:
            doc_id_safe = doc_prefix.replace(" ", "_")
            out_dir = debug_root / doc_id_safe
            out_dir.mkdir(parents=True, exist_ok=True)
            m = re.search(r"_p(\d+)\.png$", page_path.name)
            pidx = int(m.group(1)) if m else 0
            _save_debug_overlay(pil_image, boxes, doc_id_safe, pidx, out_dir)

        results.append(
            {
                "page"     : page_path.name,
                "n_segment": n_lines,
                "n_valid"  : len(valid_lines),
                "time_s"   : round(elapsed, 3),
                "chars"    : chars,
                "words"    : words,
                "text"     : ocr_text,
            }
        )

    return results


# ── Đánh giá CER/WER từ annotation_test.txt ──────────────────────────────────

def benchmark_annotation(annotation_path: Path, crops_dir: Path) -> dict:
    """
    Tính CER/WER trên từng crop dòng từ annotation_test.txt.
    Format: <rel_path>\t<ground_truth>
    """
    from PIL import Image
    from app.services.vietocr_service import VietOCRService

    svc = VietOCRService()

    if not annotation_path.exists():
        print(f"[WARN] Không tìm thấy {annotation_path}")
        return {"cer_avg": None, "wer_avg": None, "n_samples": 0}

    records = []
    for line in annotation_path.read_text(encoding="utf-8").strip().splitlines():
        if not line.strip():
            continue
        parts = line.split("\t", maxsplit=1)
        if len(parts) != 2:
            continue
        rel_path, gt = parts[0].strip(), parts[1].strip()
        crop_path = (_REPO_ROOT / rel_path).resolve()
        if not crop_path.exists():
            crop_path = crops_dir / Path(rel_path).name
        records.append((crop_path, gt))

    if not records:
        print(f"[WARN] Không có mẫu hợp lệ trong {annotation_path}")
        return {"cer_avg": None, "wer_avg": None, "n_samples": 0}

    cer_total, wer_total, n_ok = 0.0, 0.0, 0
    print(f"\n  Đánh giá CER/WER trên {len(records)} mẫu từ {annotation_path.name} ...")
    for i, (crop_path, gt) in enumerate(records):
        if not crop_path.exists():
            print(f"    [SKIP] Không tìm thấy: {crop_path}")
            continue
        try:
            img = Image.open(crop_path).convert("RGB")
            processed = svc.preprocess_handwriting(img)
            texts = svc._vietocr().predict_batch_padded([processed])
            hyp = texts[0] if texts else ""
            c = _compute_cer(gt, hyp)
            w = _compute_wer(gt, hyp)
            cer_total += c
            wer_total += w
            n_ok += 1
            if i < 5:
                print(f"    [{i+1}] GT : {gt!r}")
                print(f"         HYP: {hyp!r}  CER={c:.3f} WER={w:.3f}")
        except Exception as exc:
            print(f"    [ERR] {crop_path.name}: {exc}")

    if n_ok == 0:
        return {"cer_avg": None, "wer_avg": None, "n_samples": 0}

    return {
        "cer_avg"  : round(cer_total / n_ok, 4),
        "wer_avg"  : round(wer_total / n_ok, 4),
        "n_samples": n_ok,
    }


# ── Ghi báo cáo Markdown ──────────────────────────────────────────────────────

def write_benchmark_report(
    page_results  : list[dict],
    annotation_res: dict,
    out_path      : Path,
    label         : str = "trước",
) -> None:
    """Ghi kết quả vào docs/ocr_benchmark.md."""
    if page_results:
        total_time  = sum(r["time_s"] for r in page_results)
        avg_time    = total_time / len(page_results)
        total_lines = sum(r["n_segment"] for r in page_results)
        total_valid = sum(r["n_valid"] for r in page_results)
        n_pages     = len(page_results)
    else:
        total_time = avg_time = 0.0
        total_lines = total_valid = n_pages = 0

    cer   = annotation_res.get("cer_avg")
    wer   = annotation_res.get("wer_avg")
    n_ann = annotation_res.get("n_samples", 0)
    cer_str = f"{cer:.4f}" if cer is not None else "N/A"
    wer_str = f"{wer:.4f}" if wer is not None else "N/A"
    timestamp = time.strftime("%Y-%m-%d %H:%M")

    md: list[str] = [
        "# OCR Benchmark Report",
        "",
        f"> **Lần đo [{label}]**: {timestamp}  ",
        f"> Script: `scripts/bench_ocr.py`",
        "",
        "## Hiệu năng theo trang",
        "",
        "| Trang | Seg dòng | Dòng hợp lệ | Thời gian (s) | Ký tự | Từ |",
        "|-------|----------|-------------|--------------|-------|-----|",
    ]
    for r in page_results:
        md.append(
            f"| {r['page']} | {r['n_segment']} | {r['n_valid']} "
            f"| {r['time_s']:.2f} | {r['chars']} | {r['words']} |"
        )

    md += [
        "",
        "## Tổng kết",
        "",
        f"| Chỉ số | [{label}] |",
        "|--------|----------|",
        f"| Số trang | {n_pages} |",
        f"| Tổng thời gian (s) | {total_time:.2f} |",
        f"| TB thời gian/trang (s) | {avg_time:.2f} |",
        f"| Tổng dòng segment | {total_lines} |",
        f"| Tổng dòng hợp lệ | {total_valid} |",
        f"| Mẫu annotation | {n_ann} |",
        f"| CER (avg) | {cer_str} |",
        f"| WER (avg) | {wer_str} |",
        "",
        "---",
        "",
        "## Chi tiết văn bản (3 dòng đầu mỗi trang)",
        "",
    ]
    for r in page_results:
        md.append(f"### {r['page']}")
        preview = r["text"].splitlines()[:3]
        md.append("```")
        md.extend(preview)
        md.append("```")
        md.append("")

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text("\n".join(md), encoding="utf-8")
    print(f"\n✅ Đã lưu báo cáo → {out_path}")


# ── Entry point ───────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Benchmark baseline OCR — đo trước khi tối ưu"
    )
    parser.add_argument(
        "--doc",
        default="CTSV_013",
        help="Prefix tên tài liệu cần benchmark (default: CTSV_013)",
    )
    parser.add_argument(
        "--pages",
        nargs="*",
        type=int,
        default=None,
        help="Số trang cụ thể (1-indexed). Mặc định: tất cả trang của --doc.",
    )
    parser.add_argument(
        "--annotation-only",
        action="store_true",
        help="Chỉ chạy CER/WER từ annotation_test.txt, bỏ qua OCR trang.",
    )
    parser.add_argument(
        "--label",
        default="trước",
        help="Nhãn cột trong báo cáo (default: 'trước')",
    )
    parser.add_argument(
        "--out",
        default=str(_REPO_ROOT / "docs" / "ocr_benchmark.md"),
        help="File output markdown (default: docs/ocr_benchmark.md)",
    )
    args = parser.parse_args()

    debug_dump = os.environ.get("OCR_DEBUG_DUMP", "0").strip() in ("1", "true", "yes")
    debug_root = _REPO_ROOT / "logs" / "ocr_debug"
    if debug_dump:
        debug_root.mkdir(parents=True, exist_ok=True)
        print(f"[DEBUG] OCR_DEBUG_DUMP=1 → overlay lưu vào {debug_root}")

    images_dir = _REPO_ROOT / "dataset" / "images"
    ann_path   = _REPO_ROOT / "dataset" / "annotations" / "annotation_test.txt"
    crops_dir  = _REPO_ROOT / "dataset" / "crops"

    # ── Benchmark trang ───────────────────────────────────────────────────────
    page_results: list[dict] = []
    if not args.annotation_only:
        print(f"\n{'='*60}")
        print(f"  Benchmark OCR trang — doc prefix: {args.doc}")
        print(f"{'='*60}")
        page_results = benchmark_pages(
            doc_prefix=args.doc,
            page_ids=args.pages,
            images_dir=images_dir,
            debug_dump=debug_dump,
            debug_root=debug_root,
        )

    # ── CER/WER ───────────────────────────────────────────────────────────────
    print(f"\n{'='*60}")
    print(f"  Đánh giá CER/WER — annotation_test.txt")
    print(f"{'='*60}")
    annotation_res = benchmark_annotation(ann_path, crops_dir)

    # ── Tóm tắt ───────────────────────────────────────────────────────────────
    print(f"\n{'='*60}")
    print("  KẾT QUẢ BASELINE")
    print(f"{'='*60}")
    if page_results:
        n   = len(page_results)
        avg = sum(r["time_s"] for r in page_results) / n
        aln = sum(r["n_segment"] for r in page_results) / n
        print(f"  Số trang đo      : {n}")
        print(f"  Dòng/trang TB   : {aln:.1f}")
        print(f"  Thời gian/trang : {avg:.2f}s")
    cer = annotation_res.get("cer_avg")
    wer = annotation_res.get("wer_avg")
    n_ann = annotation_res.get("n_samples", 0)
    print(f"  Mẫu annotation  : {n_ann}")
    if cer is not None:
        print(f"  CER (avg)       : {cer:.4f}")
        print(f"  WER (avg)       : {wer:.4f}")
    else:
        print(f"  CER/WER         : N/A (không tìm thấy annotation crops)")

    # ── Ghi báo cáo ───────────────────────────────────────────────────────────
    write_benchmark_report(
        page_results=page_results,
        annotation_res=annotation_res,
        out_path=Path(args.out),
        label=args.label,
    )


if __name__ == "__main__":
    main()

