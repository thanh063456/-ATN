#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
scripts/crop_lines.py — Cắt dòng văn bản từ ảnh tài liệu

Ghi chú Windows: cv2.imwrite() không hỗ trợ đường dẫn có ký tự Unicode/tiếng Việt.
Script này dùng cv2.imencode() + numpy.tofile() thay thế để bypass giới hạn đó.

Mô tả
------
Nhận ảnh trang tài liệu (JPG/PNG), dùng OpenCV horizontal projection profile
để phát hiện các dòng văn bản, cắt ra từng dòng riêng lẻ và lưu vào thư mục
output.

Thuật toán (không cần model detection)
----------------------------------------
1. Đọc ảnh → chuyển sang grayscale → nhị phân hoá (Otsu threshold, invert)
2. Tính horizontal projection: đếm số pixel đen trên mỗi hàng ngang
3. Tìm các "vùng có chữ" (connected row ranges với projection > ngưỡng)
4. Thêm padding xung quanh mỗi dòng → crop → lưu file

Đầu vào / Đầu ra
-----------------
  Input:  ảnh .jpg/.png trong --input (ví dụ: dataset/raw/)
  Output: ảnh crop từng dòng trong --output (ví dụ: dataset/crops/)
          Tên file: {stem}_line_{idx:03d}.png

Cách dùng
---------
  python scripts/crop_lines.py --input dataset/raw/ --output dataset/crops/
  python scripts/crop_lines.py --input dataset/raw/scan_001.jpg --output dataset/crops/

Phụ thuộc
----------
  opencv-python-headless, numpy (đã có trong requirements.txt)
"""

import argparse
import sys
import os
from pathlib import Path
from typing import List, Tuple

# Ensure UTF-8 output on Windows
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

# Cố gắng import — báo lỗi rõ ràng nếu thiếu
try:
    import cv2
    import numpy as np
except ImportError as e:
    print(f"[ERROR] Thiếu thư viện: {e}", file=sys.stderr)
    print("       Chạy: pip install opencv-python-headless numpy", file=sys.stderr)
    sys.exit(1)

# ── Tham số mặc định ──────────────────────────────────────────────────────────
DEFAULT_MIN_LINE_HEIGHT   = 8    # px — loại bỏ vùng quá thỏng (nhiễu)
DEFAULT_MAX_LINE_HEIGHT   = 200  # px — loại bỏ vùng quá cao (khả năng không phải dòng chữ)
DEFAULT_ROW_THRESHOLD     = 3    # số pixel đen tối thiểu để coi hàng là "có chữ"
DEFAULT_PADDING           = 4    # px padding thêm trên/dưới mỗi dòng
DEFAULT_MERGE_GAP         = 3    # px — gộp hai vùng cách nhau ≤ gap này thành 1


SUPPORTED_IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".tiff", ".bmp"}


# ── Core functions ─────────────────────────────────────────────────────────────

def load_and_binarize(image_path: Path) -> Tuple[np.ndarray, np.ndarray]:
    """
    Đọc ảnh, chuyển grayscale, nhị phân hoá bằng Otsu.
    Trả về (ảnh gốc BGR, ảnh nhị phân — pixel chữ = 255).

    Ghi chú Windows: cv2.imread() không hỗ trợ path Unicode.
    Dùng numpy.fromfile() + cv2.imdecode() thay thế.
    """
    buf = np.fromfile(str(image_path), dtype=np.uint8)
    img_bgr = cv2.imdecode(buf, cv2.IMREAD_COLOR)
    if img_bgr is None:
        raise ValueError(f"Không đọc được ảnh: {image_path}")

    gray = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY)

    # Tiền xử lý nhẹ: giảm nhiễu trước khi threshold
    denoised = cv2.GaussianBlur(gray, (3, 3), 0)

    # Otsu threshold: tự động tìm ngưỡng tối ưu
    _, binary = cv2.threshold(denoised, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)

    return img_bgr, binary


def compute_horizontal_projection(binary: np.ndarray) -> np.ndarray:
    """
    Tính horizontal projection profile: tổng pixel trắng (= pixel chữ sau invert)
    theo từng hàng ngang.
    Trả về mảng 1D có độ dài = số hàng của ảnh.
    """
    return np.sum(binary > 0, axis=1).astype(np.int32)


def find_line_regions(
    projection: np.ndarray,
    row_threshold: int,
    merge_gap: int,
    min_height: int,
    max_height: int,
) -> List[Tuple[int, int]]:
    """
    Từ projection profile, tìm các vùng hàng liên tiếp có chữ.
    Trả về list (row_start, row_end) — row_end exclusive.
    """
    n_rows = len(projection)
    in_line = False
    start = 0
    regions: List[Tuple[int, int]] = []

    for row in range(n_rows):
        has_ink = projection[row] >= row_threshold
        if has_ink and not in_line:
            in_line = True
            start = row
        elif not has_ink and in_line:
            in_line = False
            regions.append((start, row))

    if in_line:                         # ảnh kết thúc trong vùng có chữ
        regions.append((start, n_rows))

    # ── Bước 2: gộp các vùng cách nhau quá nhỏ (merge_gap) ──────────────────
    if merge_gap > 0 and len(regions) > 1:
        merged: List[Tuple[int, int]] = [regions[0]]
        for r_start, r_end in regions[1:]:
            prev_start, prev_end = merged[-1]
            if r_start - prev_end <= merge_gap:
                merged[-1] = (prev_start, r_end)   # gộp
            else:
                merged.append((r_start, r_end))
        regions = merged

    # ── Bước 3: lọc theo chiều cao ───────────────────────────────────────────
    regions = [
        (s, e) for s, e in regions
        if min_height <= (e - s) <= max_height
    ]

    return regions


def imwrite_unicode(path: Path, img: np.ndarray) -> bool:
    """
    cv2.imwrite() trên Windows không hỗ trợ path có ký tự Unicode/tiếng Việt.
    Dùng cv2.imencode() + numpy.tofile() để bypass.
    """
    ext = path.suffix.lower()   # ".png", ".jpg", ...
    ret, buf = cv2.imencode(ext, img)
    if ret:
        buf.tofile(str(path))
    return ret


def crop_and_save(
    img_bgr: np.ndarray,
    regions: List[Tuple[int, int]],
    output_dir: Path,
    stem: str,
    padding: int,
) -> List[Path]:
    """
    Cắt từng vùng dòng từ ảnh gốc, thêm padding, lưu PNG.
    Trả về list đường dẫn đã lưu.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    h, w = img_bgr.shape[:2]
    saved: List[Path] = []

    for idx, (r_start, r_end) in enumerate(regions):
        top    = max(0, r_start - padding)
        bottom = min(h, r_end   + padding)

        crop = img_bgr[top:bottom, 0:w]
        out_path = output_dir / f"{stem}_line_{idx:03d}.png"
        imwrite_unicode(out_path, crop)
        saved.append(out_path)

    return saved


def process_image(
    image_path: Path,
    output_dir: Path,
    row_threshold: int,
    merge_gap: int,
    min_line_height: int,
    max_line_height: int,
    padding: int,
    verbose: bool = True,
) -> List[Path]:
    """Pipeline đầy đủ cho 1 ảnh: load → binarize → project → detect → crop → save."""
    img_bgr, binary = load_and_binarize(image_path)
    projection      = compute_horizontal_projection(binary)
    regions         = find_line_regions(
        projection,
        row_threshold=row_threshold,
        merge_gap=merge_gap,
        min_height=min_line_height,
        max_height=max_line_height,
    )
    saved = crop_and_save(img_bgr, regions, output_dir, image_path.stem, padding)

    if verbose:
        print(f"  {image_path.name:40s}  →  {len(saved):3d} dòng  →  {output_dir}/")

    return saved


def collect_images(input_path: Path) -> List[Path]:
    """Thu thập tất cả ảnh từ file đơn hoặc thư mục."""
    if input_path.is_file():
        if input_path.suffix.lower() in SUPPORTED_IMAGE_EXTS:
            return [input_path]
        else:
            print(f"[WARN] Bỏ qua: {input_path} (không phải định dạng ảnh hỗ trợ)")
            return []
    elif input_path.is_dir():
        imgs = sorted([
            p for p in input_path.rglob("*")
            if p.is_file() and p.suffix.lower() in SUPPORTED_IMAGE_EXTS
        ])
        return imgs
    else:
        print(f"[ERROR] Không tìm thấy: {input_path}", file=sys.stderr)
        sys.exit(1)


# ── CLI ────────────────────────────────────────────────────────────────────────

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Cắt ảnh tài liệu thành từng dòng văn bản (horizontal projection).",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--input", "-i",
        type=Path,
        required=True,
        help="File ảnh hoặc thư mục chứa ảnh đầu vào (dataset/raw/)",
    )
    parser.add_argument(
        "--output", "-o",
        type=Path,
        default=Path("dataset/crops"),
        help="Thư mục lưu ảnh crop từng dòng (dataset/crops/)",
    )
    parser.add_argument(
        "--row-threshold",
        type=int,
        default=DEFAULT_ROW_THRESHOLD,
        help="Số pixel đen tối thiểu trên một hàng để coi là 'có chữ'",
    )
    parser.add_argument(
        "--merge-gap",
        type=int,
        default=DEFAULT_MERGE_GAP,
        help="Gộp hai vùng cách nhau ≤ N px thành một dòng",
    )
    parser.add_argument(
        "--min-height",
        type=int,
        default=DEFAULT_MIN_LINE_HEIGHT,
        help="Chiều cao tối thiểu (px) để giữ một dòng",
    )
    parser.add_argument(
        "--max-height",
        type=int,
        default=DEFAULT_MAX_LINE_HEIGHT,
        help="Chiều cao tối đa (px) để giữ một dòng",
    )
    parser.add_argument(
        "--padding",
        type=int,
        default=DEFAULT_PADDING,
        help="Padding (px) thêm trên/dưới mỗi dòng khi crop",
    )
    parser.add_argument(
        "--quiet", "-q",
        action="store_true",
        help="Không in log từng ảnh",
    )
    return parser


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    parser = build_parser()
    args   = parser.parse_args()

    images = collect_images(args.input)
    if not images:
        print("[WARN] Không tìm thấy ảnh nào. Kiểm tra lại --input.")
        sys.exit(0)

    print(f"[crop_lines] Tìm thấy {len(images)} ảnh — bắt đầu cắt dòng...")
    print(f"             Output: {args.output.resolve()}")
    print()

    total_crops = 0
    for img_path in images:
        try:
            crops = process_image(
                img_path,
                args.output,
                row_threshold=args.row_threshold,
                merge_gap=args.merge_gap,
                min_line_height=args.min_height,
                max_line_height=args.max_height,
                padding=args.padding,
                verbose=not args.quiet,
            )
            total_crops += len(crops)
        except Exception as exc:
            print(f"  [ERROR] {img_path.name}: {exc}", file=sys.stderr)

    print()
    print(f"[crop_lines] Hoàn thành: {total_crops} dòng từ {len(images)} ảnh.")
    print(f"             Crops lưu tại: {args.output.resolve()}")


if __name__ == "__main__":
    main()
