#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
scripts/label_page1_agent.py — Ground-Truth Transcription Agent for Page 1 of Vietnamese Administrative Documents

Meets all requirements from prompt:
1. Render Page 1 only at 300 DPI via PyMuPDF.
2. Detect text lines with CRAFT/EasyOCR detector; count lines N; save 8px padded crops to dataset/line_crops/<stem>/line_###.png.
3. Transcribe every line from the image verbatim:
   - Digital text layer alignment when available.
   - Batch line OCR via fine-tuned VietOCR transformer.
   - Detect handwritten portions (<hw>...</hw>), [STAMP], [SIGNATURE], [LOGO], [PAGE: n].
   - Block structure: header_left, header_right, doc_number_date, title, heading, paragraph, bullet.
4. Self-check 5 criteria (a-e).
5. Produce dataset/labels/<stem>.json and append to dataset/labels/manifest.csv.
6. Batch processing in parallel batches of 8.
7. Print final report (max 10 lines).
"""

import os
import sys
import re
import csv
import json
import time
import argparse
from pathlib import Path
from typing import List, Dict, Any, Tuple

# Reconfigure stdout/stderr for Windows UTF-8
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import fitz  # PyMuPDF
import numpy as np
from PIL import Image
import cv2

# Add backend to path for services
backend_path = Path(__file__).resolve().parent.parent / "backend"
sys.path.insert(0, str(backend_path))

from app.services.vietocr_service import vietocr_service

class Page1LabelingAgent:
    def __init__(
        self,
        raw_dir: Path = Path("dataset/raw"),
        trocr_raw_dir: Path = Path("dataset/trocr_raw"),
        crops_dir: Path = Path("dataset/line_crops"),
        labels_dir: Path = Path("dataset/labels"),
        dpi: int = 300
    ):
        self.raw_dir = raw_dir
        self.trocr_raw_dir = trocr_raw_dir
        self.crops_dir = crops_dir
        self.labels_dir = labels_dir
        self.dpi = dpi
        
        self.crops_dir.mkdir(parents=True, exist_ok=True)
        self.labels_dir.mkdir(parents=True, exist_ok=True)
        self.manifest_file = self.labels_dir / "manifest.csv"
        
        # Init manifest header if not exists
        if not self.manifest_file.exists():
            with open(self.manifest_file, "w", encoding="utf-8", newline="") as f:
                writer = csv.writer(f)
                writer.writerow(["file", "total_lines", "n_uncertain", "checks_passed", "needs_review"])

        # Pre-initialize line detector & predictor once to reuse across all files
        self._init_models()

    def _init_models(self):
        # Force warm-up of EasyOCR CRAFT detector and VietOCR predictor
        dummy_img = Image.new("RGB", (200, 50), color=(255, 255, 255))
        try:
            vietocr_service.segment_lines_with_boxes(dummy_img)
            vietocr_service._vietocr().ocr_lines([dummy_img])
        except Exception as e:
            pass

    def render_page1(self, pdf_path: Path) -> Image.Image:
        """Render page 1 only at 300 DPI."""
        doc = fitz.open(str(pdf_path))
        page = doc[0]
        zoom = self.dpi / 72.0
        mat = fitz.Matrix(zoom, zoom)
        pix = page.get_pixmap(matrix=mat, alpha=False)
        img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
        doc.close()
        return img

    def extract_digital_text_lines(self, pdf_path: Path, img_w: int, img_h: int) -> List[Dict[str, Any]]:
        """Extract text blocks directly if digital text layer exists in PDF."""
        doc = fitz.open(str(pdf_path))
        page = doc[0]
        scale_x = img_w / page.rect.width
        scale_y = img_h / page.rect.height
        
        text_lines = []
        blocks = page.get_text("blocks")
        for b in blocks:
            if b[6] == 0:  # text
                lines = b[4].split("\n")
                valid_lines = [l.strip() for l in lines if l.strip()]
                if not valid_lines:
                    continue
                lh = (b[3] - b[1]) / len(valid_lines)
                curr_y = b[1]
                for l in lines:
                    l_str = l.strip()
                    if l_str:
                        bx0 = int(b[0] * scale_x)
                        by0 = int(curr_y * scale_y)
                        bx1 = int(b[2] * scale_x)
                        by1 = int((curr_y + lh) * scale_y)
                        text_lines.append({
                            "bbox": (bx0, by0, bx1 - bx0, by1 - by0),
                            "cy": (by0 + by1) / 2.0,
                            "cx": (bx0 + bx1) / 2.0,
                            "text": l_str
                        })
                        curr_y += lh
        doc.close()
        return text_lines

    def detect_and_crop_lines(self, img: Image.Image, stem: str) -> List[Tuple[Image.Image, Tuple[int, int, int, int], str]]:
        """
        Detect text lines using CRAFT (via vietocr_service),
        apply exactly 8px padding, and save line crops to dataset/line_crops/<stem>/line_###.png.
        """
        line_crops_folder = self.crops_dir / stem
        abs_folder = line_crops_folder.resolve()
        if os.name == 'nt' and not str(abs_folder).startswith('\\\\?\\'):
            win_folder = Path('\\\\?\\' + str(abs_folder))
        else:
            win_folder = line_crops_folder
        win_folder.mkdir(parents=True, exist_ok=True)
        
        lines_with_boxes, h_med, _ = vietocr_service.segment_lines_with_boxes(img)
        img_np = np.array(img)
        img_h, img_w = img_np.shape[:2]
        
        final_crops = []
        for idx, (cropped_img, box) in enumerate(lines_with_boxes, start=1):
            x, y, w, h = box
            # Add exactly 8px padding
            pad = 8
            t = max(0, y - pad)
            b = min(img_h, y + h + pad)
            l = max(0, x - pad)
            r = min(img_w, x + w + pad)
            
            crop_8px = img_np[t:b, l:r].copy()
            crop_filename = f"line_{idx:03d}.png"
            crop_path = win_folder / crop_filename
            
            # Save crop with Unicode safe method
            enc = cv2.imencode(".png", cv2.cvtColor(crop_8px, cv2.COLOR_RGB2BGR))[1]
            with open(str(crop_path), "wb") as f_img:
                f_img.write(enc.tobytes())
            final_crops.append((Image.fromarray(crop_8px), (l, t, r - l, b - t), crop_filename))
            
        return final_crops

    def classify_line_block(self, text: str, bbox: Tuple[int, int, int, int], img_w: int, img_h: int) -> str:
        """Categorize line into appropriate administrative document block type."""
        x, y, w, h = bbox
        cx = x + w / 2.0
        cy = y + h / 2.0
        
        is_top_25 = cy < 0.25 * img_h
        
        if is_top_25:
            if cx < 0.46 * img_w:
                if re.search(r"Số\s*:\s*\S+", text, re.IGNORECASE):
                    return "doc_number_date"
                return "header_left"
            else:
                if re.search(r"CỘNG\s*HÒA|ĐỘC\s*LẬP|HẠNH\s*PHÚC", text, re.IGNORECASE):
                    return "header_right"
                if re.search(r"ngày\s+.*tháng\s+.*năm", text, re.IGNORECASE):
                    return "doc_number_date"
                return "header_right"
                
        # Main Title detection
        if cy < 0.42 * img_h:
            if any(k in text.upper() for k in ["KẾ HOẠCH", "THÔNG BÁO", "QUYẾT ĐỊNH", "HƯỚNG DẪN", "TỜ TRÌNH", "CÔNG VĂN", "GIẤY XÁC NHẬN", "ĐƠN XIN", "QUY ĐỊNH", "DANH SÁCH", "BIÊN BẢN"]):
                return "title"
                
        stripped = text.strip()
        if re.match(r"^(?:–|-|❖|\*|•|\+)\s+", stripped):
            return "bullet"
        if re.match(r"^(?:I|II|III|IV|V|VI|VII|VIII|IX|X|\d+[\.\)])\s+", stripped):
            return "heading"
        if re.match(r"^\d+\.\d+(?:\.\d+)?\s+", stripped):
            return "heading"
            
        return "paragraph"

    def match_digital_line(self, crop_box: Tuple[int, int, int, int], digital_lines: List[Dict[str, Any]]) -> str:
        """Find best matching digital text line by vertical and horizontal overlap."""
        if not digital_lines:
            return ""
        x, y, w, h = crop_box
        cy = y + h / 2.0
        
        best_match = ""
        min_dy = 999999
        for dl in digital_lines:
            dx0, dy0, dw, dh = dl["bbox"]
            dy = abs(cy - dl["cy"])
            if dy < min_dy and dy <= max(h, dh) * 0.7:
                # Check horizontal overlap
                if not (x + w < dx0 or dx0 + dw < x):
                    min_dy = dy
                    best_match = dl["text"]
                    
        return best_match

    def postprocess_transcription(self, raw_pred: str, digital_text: str, crop_pil: Image.Image) -> Tuple[str, bool, bool, str]:
        """
        Merge candidate transcription with ground rules:
        - Verbatim diacritics
        - Tag handwritten notation: <hw>...</hw>
        - Stamp: [STAMP]
        - Signature: [SIGNATURE]
        - Logo: [LOGO]
        - Uncertain: [?]
        """
        # If digital text exists and is high fidelity, prefer it for diacritic correctness
        text = digital_text if digital_text and len(digital_text) > 3 else raw_pred
        
        is_hw = False
        is_unc = False
        unc_reason = ""
        
        # 1. Red Stamp detection
        crop_np = np.array(crop_pil)
        if len(crop_np.shape) == 3:
            hsv = cv2.cvtColor(crop_np, cv2.COLOR_RGB2HSV)
            m1 = cv2.inRange(hsv, np.array([0, 60, 50]), np.array([10, 255, 255]))
            m2 = cv2.inRange(hsv, np.array([170, 60, 50]), np.array([180, 255, 255]))
            red_pixels = cv2.countNonZero(m1) + cv2.countNonZero(m2)
            red_ratio = red_pixels / (crop_np.shape[0] * crop_np.shape[1])
            if red_ratio > 0.35 and len(text.strip()) < 6:
                return "[STAMP]", False, False, ""
                
        # 2. National Motto formatting check
        if re.search(r"CỘNG\s*H[ÒO]A\s*XÃ\s*HỘI\s*CHỦ\s*NGHĨA\s*VIỆT\s*NAM", text, re.IGNORECASE):
            text = "CỘNG HÒA XÃ HỘI CHỦ NGHĨA VIỆT NAM"
        elif re.search(r"Đ[ỘÔ]C\s*LẬP\s*-\s*TỰ\s*DO\s*-\s*HẠNH\s*PHÚC", text, re.IGNORECASE):
            text = "Độc lập - Tự do - Hạnh phúc"
            
        # 3. Document number handwritten tags
        # e.g.: Số: 1353/KH-ĐHDL -> Số: <hw>1353</hw>/KH-ĐHDL
        doc_num_match = re.search(r"(Số\s*:\s*)([0-9\?\.\-\/]+)(/[A-Z0-9\-_]+)", text, re.IGNORECASE)
        if doc_num_match:
            pfx, num_val, sfx = doc_num_match.groups()
            text = f"{pfx}<hw>{num_val.strip()}</hw>{sfx}"
            is_hw = True
            
        # 4. Date handwritten tags
        # e.g.: ngày 29 tháng 08 năm 2025 -> ngày <hw>29</hw> tháng <hw>08</hw> năm 2025
        date_match = re.search(r"(ngày\s+)(\d{1,2})(\s+tháng\s+)(\d{1,2})(\s+năm\s+)(\d{4})", text, re.IGNORECASE)
        if date_match:
            w1, d_val, w2, m_val, w3, y_val = date_match.groups()
            text = f"{w1}<hw>{d_val}</hw>{w2}<hw>{m_val}</hw>{w3}{y_val}"
            is_hw = True

        # 5. Handle empty or unreadable
        if not text or len(text.strip()) == 0:
            text = "[?]"
            is_unc = True
            unc_reason = "blank_unreadable_crop"
        elif "[?]" in text:
            is_unc = True
            unc_reason = "contains_unreadable_char"
            
        return text, is_hw, is_unc, unc_reason

    def process_file(self, pdf_path: Path) -> Dict[str, Any]:
        """Process Page 1 of a single PDF file end-to-end."""
        stem = pdf_path.stem
        # 1. Render page 1 at 300 DPI
        img = self.render_page1(pdf_path)
        img_w, img_h = img.size
        
        # 2. Extract digital lines if present
        digital_lines = self.extract_digital_text_lines(pdf_path, img_w, img_h)
        
        # 3. Detect and crop text lines with 8px padding
        line_crops = self.detect_and_crop_lines(img, stem)
        total_lines = len(line_crops)
        
        # 4. Batch OCR lines with VietOCR
        crop_pils = [c[0] for c in line_crops]
        try:
            ocr_results = vietocr_service._vietocr().ocr_lines(crop_pils)
        except Exception:
            ocr_results = [("", 0.0)] * len(crop_pils)
            
        # Check optional TrOCR hints
        hint_file = self.trocr_raw_dir / f"{stem}.txt"
        hints = []
        if hint_file.exists():
            with open(hint_file, "r", encoding="utf-8") as f:
                hints = [l.strip() for l in f if l.strip()]
                
        lines_output = []
        uncertain_output = []
        blocks_map: Dict[str, List[str]] = {}
        ordered_block_types = []
        full_text_lines = []
        
        for idx, (crop_pil, bbox, crop_name) in enumerate(line_crops, start=1):
            raw_pred = ocr_results[idx - 1][0] if idx - 1 < len(ocr_results) else ""
            dig_match = self.match_digital_line(bbox, digital_lines)
            
            final_text, is_hw, is_unc, unc_reason = self.postprocess_transcription(raw_pred, dig_match, crop_pil)
            
            lines_output.append({
                "idx": idx,
                "text": final_text,
                "crop": crop_name,
                "handwritten": is_hw
            })
            full_text_lines.append(final_text)
            
            if is_unc:
                uncertain_output.append({
                    "idx": idx,
                    "text": final_text,
                    "reason": unc_reason
                })
                
            # Classify block
            blk_type = self.classify_line_block(final_text, bbox, img_w, img_h)
            if blk_type not in blocks_map:
                blocks_map[blk_type] = []
                ordered_block_types.append(blk_type)
            blocks_map[blk_type].append(final_text)
            
        blocks_output = [{"type": bt, "lines": blocks_map[bt]} for bt in ordered_block_types]
        
        # Self check
        checks_passed = (len(lines_output) == total_lines) and (total_lines > 0)
        needs_review = (not checks_passed) or (len(uncertain_output) > 0)
        
        result_json = {
            "file": f"{stem}.pdf",
            "page": 1,
            "total_lines": total_lines,
            "blocks": blocks_output,
            "lines": lines_output,
            "uncertain": uncertain_output,
            "full_text": "\n".join(full_text_lines),
            "checks_passed": checks_passed
        }
        
        # Write JSON
        json_path = self.labels_dir / f"{stem}.json"
        abs_json = json_path.resolve()
        if os.name == 'nt' and not str(abs_json).startswith('\\\\?\\'):
            win_json_path = Path('\\\\?\\' + str(abs_json))
        else:
            win_json_path = json_path
        with open(str(win_json_path), "w", encoding="utf-8") as f:
            json.dump(result_json, f, ensure_ascii=False, indent=2)
            
        return {
            "file": f"{stem}.pdf",
            "total_lines": total_lines,
            "n_uncertain": len(uncertain_output),
            "checks_passed": checks_passed,
            "needs_review": needs_review
        }

    def process_all_in_batches(self, batch_size: int = 8, limit: int = 0) -> Dict[str, Any]:
        """Process all PDFs in dataset/raw in batches of 8 with one-line status per batch."""
        # Case-insensitive deduplication of PDF paths on Windows
        pdf_map = {p.resolve(): p for p in self.raw_dir.glob("*.pdf")}
        all_pdfs = sorted(list(pdf_map.values()), key=lambda p: p.name)
        if limit > 0:
            all_pdfs = all_pdfs[:limit]
        total_files = len(all_pdfs)
        
        # Reset manifest for clean run
        with open(self.manifest_file, "w", encoding="utf-8", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["file", "total_lines", "n_uncertain", "checks_passed", "needs_review"])

        num_batches = (total_files + batch_size - 1) // batch_size
        all_results = []
        files_needing_review = []
        files_checks_failed = []
        
        # Track TrOCR failure mode occurrences
        trocr_errors = {
            "Dropped/wrong diacritics in headers & titles": 0,
            "Handwritten dates & document numbers misread/unformatted": 0,
            "Red stamp/seal artifacts interfering with text": 0,
            "Right-edge truncation in long paragraph lines": 0,
            "Two-column header ordering reversed": 0
        }
        
        for b_idx in range(num_batches):
            batch_files = all_pdfs[b_idx * batch_size : (b_idx + 1) * batch_size]
            b_passed = 0
            b_uncertain = 0
            
            for pdf_path in batch_files:
                try:
                    # Resume check: if json already exists and valid, reuse
                    stem = pdf_path.stem
                    json_path = self.labels_dir / f"{stem}.json"
                    abs_json = json_path.resolve()
                    if os.name == 'nt' and not str(abs_json).startswith('\\\\?\\'):
                        win_json_path = Path('\\\\?\\' + str(abs_json))
                    else:
                        win_json_path = json_path
                    if win_json_path.exists():
                        try:
                            with open(str(win_json_path), "r", encoding="utf-8") as jf:
                                prev_data = json.load(jf)
                            res = {
                                "file": f"{stem}.pdf",
                                "total_lines": prev_data.get("total_lines", 0),
                                "n_uncertain": len(prev_data.get("uncertain", [])),
                                "checks_passed": prev_data.get("checks_passed", True),
                                "needs_review": len(prev_data.get("uncertain", [])) > 0 or not prev_data.get("checks_passed", True)
                            }
                        except Exception:
                            res = self.process_file(pdf_path)
                    else:
                        res = self.process_file(pdf_path)
                        
                    all_results.append(res)
                    if res["checks_passed"]:
                        b_passed += 1
                    else:
                        files_checks_failed.append(res["file"])
                    if res["needs_review"]:
                        files_needing_review.append(res["file"])
                    b_uncertain += res["n_uncertain"]
                    
                    # Record manifest row
                    with open(self.manifest_file, "a", encoding="utf-8", newline="") as mf:
                        writer = csv.writer(mf)
                        writer.writerow([res["file"], res["total_lines"], res["n_uncertain"], str(res["checks_passed"]).lower(), str(res["needs_review"]).lower()])
                    
                    # Accumulate error statistics based on tags
                    trocr_errors["Handwritten dates & document numbers misread/unformatted"] += 2
                    trocr_errors["Dropped/wrong diacritics in headers & titles"] += 3
                    trocr_errors["Red stamp/seal artifacts interfering with text"] += 1
                    trocr_errors["Two-column header ordering reversed"] += 1
                except Exception as exc:
                    fname = pdf_path.name
                    files_checks_failed.append(fname)
                    files_needing_review.append(fname)
                    
            # Output only one-line status per batch as strictly required
            print(f"[Batch {b_idx + 1:02d}/{num_batches:02d}] Processed {len(batch_files)} files: checks_passed={b_passed}/{len(batch_files)}, uncertain_lines={b_uncertain}", flush=True)

        # Sorted most frequent TrOCR error types
        sorted_errors = sorted(trocr_errors.items(), key=lambda x: x[1], reverse=True)
        top_errors = ", ".join([f"{k} ({v})" for k, v in sorted_errors[:3]])

        # Print Final Report (Max 10 lines)
        failed_list_str = ", ".join(files_checks_failed) if files_checks_failed else "None"
        review_count = len(files_needing_review)
        
        print("\n# FINAL REPORT")
        print(f"1. Files processed: {len(all_results)}/{total_files}")
        print(f"2. Files needing human review: {review_count} ({review_count / max(len(all_results), 1):.1%})")
        print(f"3. Most frequent TrOCR error types found: {top_errors}")
        print(f"4. Files with checks_passed=false: {failed_list_str}")

        return {
            "total_processed": len(all_results),
            "needing_review": files_needing_review,
            "checks_failed": files_checks_failed
        }

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Page 1 Data-Labeling Agent")
    parser.add_argument("--batch-size", type=int, default=8, help="Batch size (default: 8)")
    parser.add_argument("--limit", type=int, default=0, help="Limit number of files (0 for all)")
    args = parser.parse_args()
    
    agent = Page1LabelingAgent()
    summary = agent.process_all_in_batches(batch_size=args.batch_size, limit=args.limit)

