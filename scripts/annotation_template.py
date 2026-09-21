#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
scripts/annotation_template.py — Sinh file annotation rỗng theo định dạng VietOCR

Mô tả
------
Quét thư mục dataset/crops/ (hoặc --crops-dir tuỳ chỉnh), tập hợp đường dẫn
tất cả ảnh crop dòng, rồi sinh ra các file annotation với cột nhãn bỏ trống
để người gán nhãn điền thủ công.

Định dạng VietOCR chuẩn
------------------------
Mỗi dòng trong file annotation:
    <đường_dẫn_ảnh><TAB><nhãn>

Ví dụ (sau khi người dùng điền):
    dataset/crops/scan_001_line_000.png	UBND tỉnh Đồng Nai
    dataset/crops/scan_001_line_001.png	Phòng Công tác sinh viên

File sinh ra (cột nhãn rỗng)
------------------------------
    dataset/crops/scan_001_line_000.png	
    dataset/crops/scan_001_line_001.png	

Đầu ra
------
  dataset/annotations/annotation_train.txt  — placeholder train set
  dataset/annotations/annotation_val.txt    — placeholder val set
  (Chia ngẫu nhiên theo tỉ lệ --train-ratio, mặc định 85/15)

Lưu ý
------
  Script này KHÔNG điền nhãn tự động.
  Người dùng phải mở file annotation và điền nhãn thủ công.
  Sau khi điền xong, dùng split_dataset.py để chia train/val chính thức.

Cách dùng
---------
  python scripts/annotation_template.py
  python scripts/annotation_template.py --crops-dir dataset/crops/ --train-ratio 0.85
"""

import argparse
import random
import sys
from pathlib import Path
from typing import List, Tuple

# Ensure UTF-8 output on Windows
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

SUPPORTED_IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".tiff", ".bmp"}
ANNOTATION_TAB = "\t"


# ── Core ───────────────────────────────────────────────────────────────────────

def collect_crop_paths(crops_dir: Path, relative_to: Path) -> List[str]:
    """
    Thu thập tất cả ảnh crop từ crops_dir, trả về đường dẫn relative
    so với thư mục gốc dự án (để annotation path nhất quán, không phụ thuộc
    vào machine).
    """
    if not crops_dir.exists():
        return []

    paths = sorted([
        p for p in crops_dir.rglob("*")
        if p.is_file() and p.suffix.lower() in SUPPORTED_IMAGE_EXTS
    ])

    relative_paths: List[str] = []
    for p in paths:
        try:
            rel = p.relative_to(relative_to)
            relative_paths.append(str(rel).replace("\\", "/"))   # Unix-style path
        except ValueError:
            relative_paths.append(str(p).replace("\\", "/"))

    return relative_paths


def split_paths(
    paths: List[str],
    train_ratio: float,
    seed: int,
) -> Tuple[List[str], List[str]]:
    """
    Chia ngẫu nhiên có seed list paths thành (train, val).
    """
    shuffled = paths.copy()
    random.seed(seed)
    random.shuffle(shuffled)
    n_train = max(1, int(len(shuffled) * train_ratio)) if shuffled else 0
    return shuffled[:n_train], shuffled[n_train:]


def write_annotation_file(
    out_path: Path,
    image_paths: List[str],
    note_header: bool = True,
) -> int:
    """
    Ghi file annotation với nhãn rỗng (chỉ có đường dẫn + TAB).
    Trả về số dòng đã ghi.
    """
    out_path.parent.mkdir(parents=True, exist_ok=True)

    with open(out_path, "w", encoding="utf-8") as f:
        if note_header:
            f.write(
                "# ============================================================\n"
                f"# VietOCR Annotation File — {out_path.name}\n"
                "# Định dạng: <đường_dẫn_ảnh><TAB><nhãn văn bản>\n"
                "#\n"
                "# HƯỚNG DẪN:\n"
                "#   1. Mở file này bằng text editor (VS Code, Notepad++).\n"
                "#   2. Với mỗi dòng, điền nhãn văn bản SAU dấu TAB.\n"
                "#   3. Lưu file với encoding UTF-8.\n"
                "#   4. Chạy split_dataset.py để chia train/val chính thức.\n"
                "#\n"
                "# VÍ DỤ (sau khi điền):\n"
                "#   dataset/crops/scan_001_line_000.png\tUBND tỉnh Đồng Nai\n"
                "# ============================================================\n"
                "#\n"
            )
        for img_path in image_paths:
            # Dòng = path + TAB + nhãn rỗng (người dùng sẽ điền)
            f.write(f"{img_path}{ANNOTATION_TAB}\n")

    return len(image_paths)


# ── CLI ────────────────────────────────────────────────────────────────────────

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Sinh file annotation rỗng theo định dạng VietOCR để gán nhãn thủ công.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )

    # Xác định project root từ vị trí script
    script_dir  = Path(__file__).resolve().parent
    project_root = script_dir.parent

    parser.add_argument(
        "--crops-dir",
        type=Path,
        default=project_root / "dataset" / "crops",
        help="Thư mục chứa ảnh crop dòng",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=project_root / "dataset" / "annotations",
        help="Thư mục lưu file annotation",
    )
    parser.add_argument(
        "--project-root",
        type=Path,
        default=project_root,
        help="Thư mục gốc dự án (dùng để tính relative path trong annotation)",
    )
    parser.add_argument(
        "--train-ratio",
        type=float,
        default=0.85,
        help="Tỉ lệ chia train (phần còn lại là val)",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed để chia reproducible",
    )
    parser.add_argument(
        "--no-header",
        action="store_true",
        help="Không ghi comment hướng dẫn vào đầu file",
    )
    return parser


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    parser = build_parser()
    args   = parser.parse_args()

    crops_dir    = args.crops_dir.resolve()
    output_dir   = args.output_dir.resolve()
    project_root = args.project_root.resolve()

    print(f"[annotation_template] Quét crops từ: {crops_dir}")

    paths = collect_crop_paths(crops_dir, relative_to=project_root)

    if not paths:
        print(f"[WARN] Không tìm thấy ảnh nào trong {crops_dir}.")
        print("       Hãy chạy crop_lines.py trước để sinh ảnh crop.")
        # Vẫn tạo file annotation rỗng (không có entry) để folder tồn tại
        for fname in ["annotation_train.txt", "annotation_val.txt"]:
            out = output_dir / fname
            write_annotation_file(out, [], note_header=not args.no_header)
            print(f"  Đã tạo (rỗng): {out}")
        return

    train_paths, val_paths = split_paths(paths, args.train_ratio, args.seed)

    train_file = output_dir / "annotation_train.txt"
    val_file   = output_dir / "annotation_val.txt"

    n_train = write_annotation_file(train_file, train_paths, note_header=not args.no_header)
    n_val   = write_annotation_file(val_file,   val_paths,   note_header=not args.no_header)

    print(f"[annotation_template] Tổng {len(paths)} ảnh crop:")
    print(f"  Train ({args.train_ratio:.0%}): {n_train} ảnh → {train_file}")
    print(f"  Val   ({1-args.train_ratio:.0%}): {n_val}   ảnh → {val_file}")
    print()
    print("  BƯỚC TIẾP THEO:")
    print("  1. Mở annotation_train.txt và annotation_val.txt.")
    print("  2. Điền nhãn văn bản vào cột SAU dấu TAB cho từng dòng.")
    print("  3. Sau khi gán nhãn xong, chạy split_dataset.py để xác nhận split.")


if __name__ == "__main__":
    main()
