#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Tạo ảnh PNG giả lập tài liệu CTSV để test pipeline crop_lines → annotation_template → dataset_report.
Ảnh gồm nhiều dòng chữ tiếng Việt in trên nền trắng.
"""
import sys
import os
from pathlib import Path

try:
    from PIL import Image, ImageDraw, ImageFont
    import numpy as np
except ImportError:
    print("Thiếu Pillow. Dùng OpenCV thuần để vẽ.")
    from PIL import Image, ImageDraw  # sẽ fail nếu thiếu, dùng fallback cv2

def make_test_image_cv2(output_path: Path, lines: list) -> None:
    """Tạo ảnh bằng OpenCV. Dùng imencode+tofile để hỗ trợ path Unicode trên Windows."""
    import cv2, numpy as np

    H, W = 60 + len(lines) * 40, 900
    img = np.ones((H, W, 3), dtype=np.uint8) * 255  # nền trắng

    y = 40
    for line in lines:
        cv2.putText(img, line, (20, y), cv2.FONT_HERSHEY_SIMPLEX,
                    0.7, (30, 30, 30), 2, cv2.LINE_AA)
        y += 40

    output_path.parent.mkdir(parents=True, exist_ok=True)
    # cv2.imwrite không hỗ trợ path Unicode trên Windows → dùng imencode+tofile
    ret, buf = cv2.imencode(".png", img)
    if ret:
        buf.tofile(str(output_path))
        print(f"  Created: {output_path.name}  ({len(lines)} lines)")
    else:
        print(f"  [ERROR] imencode thất bại: {output_path.name}")



SAMPLE_DOCUMENTS = [
    {
        "name": "DOC_DON_NGHI_HOC_20240601_abc12345.png",
        "lines": [
            "CONG HOA XA HOI CHU NGHIA VIET NAM",
            "Doc lap - Tu do - Hanh phuc",
            "------------------------------",
            "DON XIN NGHI HOC TAM THOI",
            "Kinh gui: Truong Dai hoc ...",
            "Ten toi la: Nguyen Van A",
            "Ma so sinh vien: 21001234",
            "Ly do nghi hoc: Li do suc khoe",
            "Thoi gian nghi: Tu 01/06/2024",
            "Kinh mong Nha truong chap thuan.",
            "Nguyen Van A",
        ],
    },
    {
        "name": "DOC_HOC_BONG_20240615_def67890.png",
        "lines": [
            "HO SO HOC BONG HOC KY 2 NAM 2024",
            "Ho va ten: Tran Thi B",
            "MSSV: 21005678",
            "Lop: CNTT2021A",
            "Diem trung binh: 3.85 / 4.0",
            "Loai: Xuat sac",
            "Muc hoc bong: 3,000,000 VND",
            "Nguoi xac nhan: Truong Phong CTSV",
        ],
    },
    {
        "name": "DOC_GIAY_XAC_NHAN_20240620_ghi11223.png",
        "lines": [
            "GIAY XAC NHAN SINH VIEN",
            "Truong xac nhan sinh vien:",
            "Ho ten: Le Van C",
            "Ngay sinh: 01/01/2003",
            "MSSV: 20009876",
            "Hien dang theo hoc tai truong.",
            "Xac nhan de lam thu tuc ngan hang.",
            "Dong Nai, ngay 20 thang 06 nam 2024",
            "TRUONG PHONG CTSV",
        ],
    },
]


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    # Dùng cwd() thay vì __file__ — __file__ có thể resolve sai với path Unicode trên Windows
    project_root = Path.cwd()
    raw_dir      = project_root / "dataset" / "raw"

    print(f"[make_test_images] Tạo ảnh test trong: {raw_dir}")
    print()

    for doc in SAMPLE_DOCUMENTS:
        out_path = raw_dir / doc["name"]
        if out_path.exists():
            print(f"  Skip (đã tồn tại): {out_path.name}")
            continue
        make_test_image_cv2(out_path, doc["lines"])

    print()
    print(f"[make_test_images] Hoàn thành — {len(SAMPLE_DOCUMENTS)} ảnh test trong {raw_dir}")
