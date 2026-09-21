#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
scripts/split_dataset.py — Chia annotation đã gán nhãn thành train/val

Mô tả
------
Đọc một file annotation đã gán nhãn đầy đủ (định dạng VietOCR: path<TAB>label),
lọc bỏ dòng chưa có nhãn (nhãn rỗng), chia ngẫu nhiên với seed cố định thành
train/val theo tỉ lệ --train-ratio (mặc định 85/15), lưu ra hai file riêng.

Định dạng file đầu vào (VietOCR chuẩn)
----------------------------------------
    dataset/crops/scan_001_line_000.png	UBND tỉnh Đồng Nai
    dataset/crops/scan_001_line_001.png	Phòng Công tác sinh viên

Hành vi
-------
  - Dòng comment (bắt đầu bằng #) → bỏ qua.
  - Dòng không có TAB hoặc nhãn rỗng → đưa vào báo cáo skipped, KHÔNG ghi vào output.
  - Seed cố định → cùng input cho cùng kết quả split.
  - Nếu input có ≤ 1 sample → toàn bộ vào train, val rỗng + cảnh báo.

Cách dùng
---------
  # Chia file annotation đã gán nhãn xong
  python scripts/split_dataset.py \\
      --input dataset/annotations/annotation_full.txt \\
      --train-output dataset/annotations/annotation_train.txt \\
      --val-output   dataset/annotations/annotation_val.txt \\
      --train-ratio  0.85 \\
      --seed         42

  # Dùng mặc định (input = annotation_train.txt hiện có)
  python scripts/split_dataset.py --input dataset/annotations/annotation_full.txt
"""

import argparse
import random
import sys
from pathlib import Path
from typing import List, Tuple, NamedTuple


# ── Data types ────────────────────────────────────────────────────────────────

class AnnotationEntry(NamedTuple):
    image_path: str
    label: str

    def to_line(self) -> str:
        return f"{self.image_path}\t{self.label}\n"


class SplitResult(NamedTuple):
    train: List[AnnotationEntry]
    val:   List[AnnotationEntry]
    skipped_count: int
    total_input: int


# ── Core ───────────────────────────────────────────────────────────────────────

def parse_annotation_file(input_path: Path) -> Tuple[List[AnnotationEntry], int]:
    """
    Đọc file annotation, trả về (danh sách entry hợp lệ, số dòng bị bỏ qua).
    Bỏ qua: comment (#), dòng không có TAB, dòng nhãn rỗng.
    """
    entries: List[AnnotationEntry] = []
    skipped = 0

    with open(input_path, "r", encoding="utf-8") as f:
        for raw_line in f:
            line = raw_line.rstrip("\n").rstrip("\r")

            # Bỏ comment
            if line.startswith("#"):
                continue

            # Bỏ dòng trống
            if not line.strip():
                continue

            # Phải có đúng 1 TAB
            if "\t" not in line:
                skipped += 1
                continue

            img_path, _, label = line.partition("\t")
            img_path = img_path.strip()
            label    = label.strip()

            if not img_path:
                skipped += 1
                continue

            # Bỏ dòng chưa có nhãn (nhãn rỗng)
            if not label:
                skipped += 1
                continue

            entries.append(AnnotationEntry(image_path=img_path, label=label))

    return entries, skipped


def split_entries(
    entries: List[AnnotationEntry],
    train_ratio: float,
    seed: int,
) -> Tuple[List[AnnotationEntry], List[AnnotationEntry]]:
    """Xáo trộn có seed, chia train/val."""
    if not entries:
        return [], []

    shuffled = entries.copy()
    random.seed(seed)
    random.shuffle(shuffled)

    if len(shuffled) == 1:
        return shuffled, []

    n_train = max(1, int(len(shuffled) * train_ratio))
    return shuffled[:n_train], shuffled[n_train:]


def write_split(out_path: Path, entries: List[AnnotationEntry]) -> None:
    """Ghi danh sách entry ra file annotation."""
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        for entry in entries:
            f.write(entry.to_line())


def print_summary(
    result: SplitResult,
    train_path: Path,
    val_path: Path,
    train_ratio: float,
    seed: int,
) -> None:
    total_annotated = len(result.train) + len(result.val)
    val_ratio = 1.0 - train_ratio

    print("=" * 60)
    print(" Split Dataset — Kết quả")
    print("=" * 60)
    print(f"  Tổng dòng đọc:          {result.total_input}")
    print(f"  Đã gán nhãn (hợp lệ):   {total_annotated}")
    print(f"  Bỏ qua (nhãn rỗng/lỗi): {result.skipped_count}")
    print()
    print(f"  Seed:                    {seed}")
    print(f"  Train ({train_ratio:.0%}):           {len(result.train)} samples → {train_path.name}")
    print(f"  Val   ({val_ratio:.0%}):           {len(result.val):3d} samples → {val_path.name}")
    print("=" * 60)

    if result.skipped_count > 0:
        print(f"\n  [WARN] {result.skipped_count} dòng bị bỏ qua vì nhãn rỗng hoặc sai định dạng.")
        print("         Kiểm tra file input: mỗi dòng phải có đúng 1 TAB và nhãn không rỗng.")

    if len(result.val) == 0:
        print("\n  [WARN] Val set rỗng — input quá ít sample. Thêm dữ liệu trước khi train.")


# ── CLI ────────────────────────────────────────────────────────────────────────

def build_parser() -> argparse.ArgumentParser:
    script_dir   = Path(__file__).resolve().parent
    project_root = script_dir.parent
    anno_dir     = project_root / "dataset" / "annotations"

    parser = argparse.ArgumentParser(
        description="Chia file annotation VietOCR đã gán nhãn thành train/val.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--input", "-i",
        type=Path,
        required=True,
        help="File annotation nguồn đã gán nhãn đầy đủ (format: path<TAB>label)",
    )
    parser.add_argument(
        "--train-output",
        type=Path,
        default=anno_dir / "annotation_train.txt",
        help="File output cho tập train",
    )
    parser.add_argument(
        "--val-output",
        type=Path,
        default=anno_dir / "annotation_val.txt",
        help="File output cho tập validation",
    )
    parser.add_argument(
        "--train-ratio",
        type=float,
        default=0.85,
        help="Tỉ lệ dữ liệu dành cho train (phần còn lại là val)",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed — cố định để split có thể tái lập (reproducible)",
    )
    return parser


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    parser = build_parser()
    args   = parser.parse_args()

    input_path = args.input.resolve()
    if not input_path.exists():
        print(f"[ERROR] File không tồn tại: {input_path}", file=sys.stderr)
        sys.exit(1)

    print(f"[split_dataset] Đọc: {input_path}")

    entries, skipped = parse_annotation_file(input_path)
    total_input      = len(entries) + skipped

    if not entries:
        print("[ERROR] Không có entry hợp lệ nào. Kiểm tra định dạng file annotation.")
        print("        Mỗi dòng phải có: <đường_dẫn_ảnh><TAB><nhãn không rỗng>")
        sys.exit(1)

    train_entries, val_entries = split_entries(entries, args.train_ratio, args.seed)

    write_split(args.train_output, train_entries)
    write_split(args.val_output,   val_entries)

    result = SplitResult(
        train=train_entries,
        val=val_entries,
        skipped_count=skipped,
        total_input=total_input,
    )
    print_summary(result, args.train_output, args.val_output, args.train_ratio, args.seed)


if __name__ == "__main__":
    main()
