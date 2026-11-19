#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
scripts/extract_pdf_pages.py — Trích xuất ảnh từng trang từ các tệp PDF trong CTSV_output

Sử dụng PyMuPDF (fitz) để render trang PDF sang ảnh độ phân giải cao (200/300 DPI),
hỗ trợ Unicode đường dẫn trên Windows và lưu trữ tại dataset/images/.

Cách dùng:
  python scripts/extract_pdf_pages.py --input "d:/Đồ án tốt nghiệp/CTSV_output" --output "dataset/images" --dpi 200
"""

import argparse
import sys
import os
import re
import unicodedata
from pathlib import Path
from typing import List, Dict, Any

# Ensure UTF-8 output on Windows
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

import fitz  # PyMuPDF


def sanitize_filename(name: str, max_length: int = 50) -> str:
    """Chuẩn hóa tên file an toàn cho hệ điều hành, bỏ dấu tiếng Việt và ký tự đặc biệt."""
    # Bỏ dấu tiếng Việt
    nfkd = unicodedata.normalize('NFKD', name)
    no_accent = "".join([c for c in nfkd if not unicodedata.combining(c)])
    no_accent = no_accent.replace('đ', 'd').replace('Đ', 'D')
    # Bỏ ký tự đặc biệt
    clean = re.sub(r'[^a-zA-Z0-9_\-]', '_', no_accent)
    clean = re.sub(r'_+', '_', clean).strip('_')
    if len(clean) > max_length:
        clean = clean[:max_length].rstrip('_')
    return clean or "doc"


def extract_pages_from_pdf(
    pdf_path: Path,
    output_dir: Path,
    prefix: str,
    dpi: int = 200,
    max_pages: int = 50
) -> List[Path]:
    """
    Render từng trang của PDF thành ảnh PNG.
    DPI 200: zoom = 200 / 72 ≈ 2.777
    """
    saved_images = []
    zoom = dpi / 72.0
    mat = fitz.Matrix(zoom, zoom)

    try:
        doc = fitz.open(str(pdf_path))
        num_pages = min(len(doc), max_pages)

        for page_idx in range(num_pages):
            page = doc.load_page(page_idx)
            pix = page.get_pixmap(matrix=mat, alpha=False)
            
            img_filename = f"{prefix}_p{page_idx + 1:02d}.png"
            img_path = output_dir / img_filename
            
            # Lưu ảnh
            pix.save(str(img_path))
            saved_images.append(img_path)
            
        doc.close()
    except Exception as e:
        print(f"[WARN] Lỗi khi xử lý {pdf_path.name}: {e}", file=sys.stderr)

    return saved_images


def main():
    parser = argparse.ArgumentParser(description="Trích xuất trang PDF thành ảnh chất lượng cao")
    parser.add_argument(
        "--input", "-i",
        type=str,
        default=r"d:\Đồ án tốt nghiệp\CTSV_output",
        help="Đường dẫn thư mục chứa PDF hoặc file PDF đơn"
    )
    parser.add_argument(
        "--output", "-o",
        type=str,
        default=r"d:\Đồ án tốt nghiệp\ĐATN\dataset\images",
        help="Thư mục lưu ảnh đầu ra"
    )
    parser.add_argument(
        "--dpi",
        type=int,
        default=200,
        help="Độ phân giải DPI (mặc định 200 DPI cho OCR)"
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=0,
        help="Giới hạn số file PDF cần xử lý (0 = tất cả)"
    )

    args = parser.parse_args()
    input_path = Path(args.input)
    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)

    if not input_path.exists():
        print(f"[ERROR] Đường dẫn không tồn tại: {input_path}", file=sys.stderr)
        sys.exit(1)

    pdf_files: List[Path] = []
    if input_path.is_file() and input_path.suffix.lower() == ".pdf":
        pdf_files = [input_path]
    else:
        # Quét đệ quy tất cả PDF
        pdf_files = sorted(list(input_path.rglob("*.pdf")) + list(input_path.rglob("*.PDF")))

    if not pdf_files:
        print(f"[INFO] Không tìm thấy file PDF nào trong {input_path}")
        return

    if args.limit > 0:
        pdf_files = pdf_files[:args.limit]

    print(f"============================================================")
    print(f" BẮT ĐẦU TRÍCH XUẤT ẢNH TRANG TỪ PDF")
    print(f" - Tổng số PDF: {len(pdf_files)}")
    print(f" - Thư mục nguồn: {input_path}")
    print(f" - Thư mục đích:  {output_dir}")
    print(f" - DPI thiết lập: {args.dpi}")
    print(f"============================================================")

    total_pages = 0
    success_docs = 0

    for idx, pdf in enumerate(pdf_files, start=1):
        parent_folder = pdf.parent.name
        folder_clean = sanitize_filename(parent_folder, max_length=30)
        file_clean = sanitize_filename(pdf.stem, max_length=30)
        prefix = f"CTSV_{idx:03d}_{folder_clean}_{file_clean}"

        images = extract_pages_from_pdf(
            pdf_path=pdf,
            output_dir=output_dir,
            prefix=prefix,
            dpi=args.dpi
        )
        if images:
            success_docs += 1
            total_pages += len(images)
            if idx % 10 == 0 or idx == len(pdf_files):
                print(f"[{idx:03d}/{len(pdf_files):03d}] Đã xử lý: {pdf.name} -> {len(images)} trang (Tổng: {total_pages} trang)")

    print(f"============================================================")
    print(f" HOÀN TẤT TRÍCH XUẤT:")
    print(f" - Thành công: {success_docs}/{len(pdf_files)} PDFs")
    print(f" - Tổng số trang ảnh đã lưu: {total_pages} ảnh (.png)")
    print(f" - Thư mục ảnh: {output_dir}")
    print(f"============================================================")


if __name__ == "__main__":
    main()
