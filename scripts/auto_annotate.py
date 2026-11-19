#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
scripts/auto_annotate.py — Tự động sinh nhãn mẫu cho crops bằng VietOCR
"""
import sys
import os
import urllib3
urllib3.disable_warnings()

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

import requests
from vietocr.tool import utils
orig_get = requests.get
def patched_get(*args, **kwargs):
    kwargs['verify'] = False
    return orig_get(*args, **kwargs)
requests.get = patched_get
utils.requests.get = patched_get

from vietocr.tool.config import Cfg
from vietocr.tool.predictor import Predictor
from PIL import Image
from pathlib import Path

def main():
    print("[1/3] Khoi tao VietOCR vgg_transformer predictor...")
    config = Cfg.load_config_from_name('vgg_transformer')
    config['device'] = 'cpu'
    config['predictor']['beamsearch'] = False
    detector = Predictor(config)

    crops_dir = Path('dataset/crops')
    all_crops = sorted(list(crops_dir.glob('*.png')))
    # Lay 500 mau crop dai dien de tao bo du lieu mau train/val
    sample_crops = all_crops[:500]
    print(f"[2/3] Dang nhan dang va gan nhan cho {len(sample_crops)} anh crop...")

    lines_train = []
    lines_val = []
    split_idx = int(len(sample_crops) * 0.85)

    for idx, crop_path in enumerate(sample_crops):
        try:
            txt = detector.predict(Image.open(crop_path)).strip()
            if not txt:
                txt = "Van ban CTSV"
            rel_path = crop_path.as_posix()
            line = f"{rel_path}\t{txt}\n"
            if idx < split_idx:
                lines_train.append(line)
            else:
                lines_val.append(line)
        except Exception as e:
            pass

        if (idx + 1) % 50 == 0 or (idx + 1) == len(sample_crops):
            print(f"  -> Da xu ly: {idx + 1}/{len(sample_crops)} mau")

    out_train = Path('dataset/annotations/annotation_train.txt')
    out_val = Path('dataset/annotations/annotation_val.txt')
    out_train.parent.mkdir(parents=True, exist_ok=True)

    with open(out_train, 'w', encoding='utf-8') as f:
        f.writelines(lines_train)

    with open(out_val, 'w', encoding='utf-8') as f:
        f.writelines(lines_val)

    print(f"[3/3] Hoan tat: Train {len(lines_train)} mau, Val {len(lines_val)} mau.")

if __name__ == '__main__':
    main()
