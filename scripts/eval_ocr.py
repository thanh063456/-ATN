#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
scripts/eval_ocr.py — Comprehensive Benchmark & Evaluation Tool for Vietnamese Administrative OCR

Metrics measured:
1. Line CER & WER (Vietnamese, diacritic-sensitive, NFC-normalized).
2. Truncation rate: % lines where len(pred) < len(gt) - 2 and gt.startswith(pred[:-2]).
3. Line recall: % of GT lines detected and matched.
4. Handwriting-field accuracy: exact match on document number (Số: ...) and date (ngày ...).
5. Latency: p50 and p95 per page and per line, throughput (lines/sec).
6. Outputs JSON results and prints/saves Markdown comparison tables.
"""

from __future__ import annotations

import os
import sys
import re
import time
import json
import argparse
import unicodedata
from pathlib import Path
from typing import List, Dict, Any, Tuple

# Reconfigure stdout/stderr for Windows UTF-8
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import numpy as np
from PIL import Image
import editdistance

# Add backend to path
REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "backend"))

from app.core.config import settings

def normalize_text(text: str) -> str:
    """Normalize text into NFC form and strip excess whitespace."""
    if not text:
        return ""
    text = unicodedata.normalize("NFC", text)
    # Remove synthetic hw tags for raw text comparison if needed
    text = re.sub(r'</?hw>', '', text)
    # Collapse multiple whitespaces
    return " ".join(text.strip().split())

def is_truncated_line(gt_line: str, pred_line: str) -> bool:
    """Check if pred_line is truncated relative to gt_line."""
    gt = normalize_text(gt_line)
    pred = normalize_text(pred_line)
    if len(gt) < 15:
        return False
    if len(pred) < len(gt) - 2:
        # Check prefix match
        check_len = max(5, len(pred) - 2)
        if gt.startswith(pred[:check_len]):
            return True
        # Check high overlap ratio on prefix
        ed = editdistance.eval(gt[:len(pred)], pred)
        if ed <= 2 and len(gt) - len(pred) >= 3:
            return True
    return False

def extract_handwriting_fields(text: str) -> Dict[str, str]:
    """Extract document number and date fields from text."""
    fields = {}
    norm = unicodedata.normalize("NFC", text)
    norm = re.sub(r'</?hw>', '', norm)
    # 1. Document number: Số: .../
    m_doc = re.search(r'(?:Số|So|SỐ)\s*:\s*([0-9A-Za-z\u0110\u0111\-_/]+)', norm, re.IGNORECASE)
    if m_doc:
        fields["doc_number"] = m_doc.group(1).strip()
    else:
        # Check for standalone numbers in line 1-6
        m_num = re.search(r'\b(\d{3,5})\s*/[A-ZĐ\-]+', norm)
        if m_num:
            fields["doc_number"] = m_num.group(1).strip()
            
    # 2. Date: ngày ... tháng ... năm ...
    m_date = re.search(r'(?:ngày|ngay)\s*(\d{1,2})\s*(?:tháng|thang)\s*(\d{1,2})\s*(?:năm|nam)\s*(\d{4})', norm, re.IGNORECASE)
    if m_date:
        fields["date"] = f"{int(m_date.group(1)):02d}/{int(m_date.group(2)):02d}/{m_date.group(3)}"
    return fields

def compute_line_alignment(gt_lines: List[str], pred_lines: List[str]) -> Tuple[List[Tuple[str, str]], int, int]:
    """
    Align GT lines with predicted lines using Needleman-Wunsch / LCS alignment.
    Returns: aligned_pairs (gt, pred), n_matched, n_gt
    """
    gt_clean = [normalize_text(l) for l in gt_lines if normalize_text(l)]
    pred_clean = [normalize_text(l) for l in pred_lines if normalize_text(l)]
    
    m, n = len(gt_clean), len(pred_clean)
    if m == 0 or n == 0:
        return [], 0, m

    # Distance matrix based on CER
    dp = np.zeros((m + 1, n + 1), dtype=float)
    for i in range(m + 1):
        dp[i][0] = i * 1.0
    for j in range(n + 1):
        dp[0][j] = j * 1.0

    for i in range(1, m + 1):
        for j in range(1, n + 1):
            cost = editdistance.eval(gt_clean[i-1], pred_clean[j-1]) / max(len(gt_clean[i-1]), len(pred_clean[j-1]), 1)
            dp[i][j] = min(
                dp[i-1][j] + 0.8,       # deletion
                dp[i][j-1] + 0.8,       # insertion
                dp[i-1][j-1] + cost     # match/substitute
            )

    # Backtrack
    aligned = []
    i, j = m, n
    matched_count = 0
    while i > 0 and j > 0:
        cost = editdistance.eval(gt_clean[i-1], pred_clean[j-1]) / max(len(gt_clean[i-1]), len(pred_clean[j-1]), 1)
        if dp[i][j] == dp[i-1][j-1] + cost:
            aligned.append((gt_clean[i-1], pred_clean[j-1]))
            if cost < 0.6:  # Reasonable alignment threshold
                matched_count += 1
            i -= 1
            j -= 1
        elif dp[i][j] == dp[i-1][j] + 0.8:
            aligned.append((gt_clean[i-1], ""))
            i -= 1
        else:
            aligned.append(("", pred_clean[j-1]))
            j -= 1

    while i > 0:
        aligned.append((gt_clean[i-1], ""))
        i -= 1
    while j > 0:
        aligned.append(("", pred_clean[j-1]))
        j -= 1

    aligned.reverse()
    return aligned, matched_count, m

class OCREvaluator:
    def __init__(self, held_out_file: str = "dataset/splits/held_out_32.json"):
        self.held_out_path = REPO_ROOT / held_out_file
        with open(self.held_out_path, "r", encoding="utf-8") as f:
            self.held_out_stems = json.load(f)
            
        self.labels_dir = REPO_ROOT / "dataset/labels"
        self.raw_dir = REPO_ROOT / "dataset/raw"
        self.crops_dir = REPO_ROOT / "dataset/line_crops"
        
    def evaluate_pipeline(
        self,
        engine_type: str = "trocr",
        use_gt_crops: bool = False,
        crop_padding: int = 8,
        mode_desc: str = "Baseline",
        trocr_config: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Run evaluation across all held-out documents.
        Supports both end-to-end PDF evaluation and isolated GT-box line crop evaluation.
        """
        import torch
        from app.services.trocr_service import trocr_service
        from app.services.trocr_engine import trocr_engine

        total_gt_chars = 0
        total_char_errors = 0
        total_gt_words = 0
        total_word_errors = 0
        
        total_lines_gt = 0
        total_lines_matched = 0
        total_truncated_lines = 0
        
        doc_number_total = 0
        doc_number_correct = 0
        date_total = 0
        date_correct = 0
        
        page_latencies = []
        line_latencies = []
        total_predicted_lines = 0
        
        doc_eval_details = []
        
        print(f"\n========================================================")
        print(f"  EVALUATING: {mode_desc} ({engine_type.upper()})")
        print(f"  Held-out Docs: {len(self.held_out_stems)} | GT-crops: {use_gt_crops} | Pad: {crop_padding}px")
        print(f"  Device: {'CUDA' if torch.cuda.is_available() else 'CPU'}")
        print(f"========================================================")

        for s_idx, stem in enumerate(self.held_out_stems, 1):
            label_path = self.labels_dir / f"{stem}.json"
            if not label_path.exists():
                continue
                
            with open(label_path, "r", encoding="utf-8") as jf:
                label_data = json.load(jf)
                
            gt_lines = [l["text"] for l in label_data["lines"]]
            gt_full_text = "\n".join(gt_lines)
            gt_fields = extract_handwriting_fields(gt_full_text)
            
            t0 = time.perf_counter()
            pred_lines = []
            
            if use_gt_crops:
                # Mode A1/A2: Isolated Recognition on GT-box line crops
                crop_folder = self.crops_dir / stem
                line_pils = []
                for l_item in label_data["lines"]:
                    crop_file = crop_folder / l_item.get("crop", f"line_{l_item['idx']:03d}.png")
                    if crop_file.exists():
                        try:
                            im = Image.open(crop_file).convert("RGB")
                            if crop_padding != 8:
                                # Adjust padding if requested
                                w, h = im.size
                                # crop_padding diff
                                pad_diff = crop_padding - 8
                                if pad_diff > 0:
                                    padded = Image.new("RGB", (w + 2 * pad_diff, h), (255, 255, 255))
                                    padded.paste(im, (pad_diff, 0))
                                    im = padded
                            line_pils.append(im)
                        except Exception:
                            line_pils.append(Image.new("RGB", (100, 32), (255, 255, 255)))
                    else:
                        line_pils.append(Image.new("RGB", (100, 32), (255, 255, 255)))
                        
                t_line_start = time.perf_counter()
                preds = trocr_engine.predict_batch(line_pils)
                t_line_end = time.perf_counter()
                pred_lines = [p.strip() for p in preds]
                if line_pils:
                    line_latencies.append((t_line_end - t_line_start) / len(line_pils))
            else:
                # End-to-end PDF evaluation on Page 1
                pdf_path = self.raw_dir / f"{stem}.pdf"
                if not pdf_path.exists():
                    continue
                with open(pdf_path, "rb") as pf:
                    file_bytes = pf.read()
                    
                t_page_start = time.perf_counter()
                raw_txt, proc_txt, conf, _ = trocr_service.extract_text_from_file(
                    file_bytes, "pdf", pages=[0]
                )
                t_page_end = time.perf_counter()
                used_txt = proc_txt if proc_txt else raw_txt
                pred_lines = [l.strip() for l in used_txt.splitlines() if l.strip()]
                if pred_lines:
                    line_latencies.append((t_page_end - t_page_start) / len(pred_lines))
                    
            page_lat = time.perf_counter() - t0
            page_latencies.append(page_lat)
            total_predicted_lines += len(pred_lines)
            
            # Line Alignment & Metrics
            aligned, matched_cnt, n_gt = compute_line_alignment(gt_lines, pred_lines)
            total_lines_gt += n_gt
            total_lines_matched += matched_cnt
            
            for gt_l, pr_l in aligned:
                if gt_l:
                    # CER
                    gt_norm = normalize_text(gt_l)
                    pr_norm = normalize_text(pr_l)
                    ed_c = editdistance.eval(gt_norm, pr_norm)
                    total_char_errors += ed_c
                    total_gt_chars += len(gt_norm)
                    
                    # WER
                    gt_words = gt_norm.split()
                    pr_words = pr_norm.split()
                    ed_w = editdistance.eval(gt_words, pr_words)
                    total_word_errors += ed_w
                    total_gt_words += len(gt_words)
                    
                    # Truncation
                    if pr_l and is_truncated_line(gt_l, pr_l):
                        total_truncated_lines += 1
                        
            # Handwriting evaluation
            pred_full_text = "\n".join(pred_lines)
            pred_fields = extract_handwriting_fields(pred_full_text)
            
            if "doc_number" in gt_fields:
                doc_number_total += 1
                if pred_fields.get("doc_number") == gt_fields["doc_number"]:
                    doc_number_correct += 1
            if "date" in gt_fields:
                date_total += 1
                if pred_fields.get("date") == gt_fields["date"]:
                    date_correct += 1
                    
            print(f"[{s_idx:02d}/{len(self.held_out_stems):02d}] {stem[:45]:<45} | Lines: {len(pred_lines)}/{n_gt} | Latency: {page_lat:.2f}s", flush=True)

        # Aggregate metrics
        cer = (total_char_errors / max(total_gt_chars, 1)) * 100.0
        wer = (total_word_errors / max(total_gt_words, 1)) * 100.0
        trunc_rate = (total_truncated_lines / max(total_lines_gt, 1)) * 100.0
        line_recall = (total_lines_matched / max(total_lines_gt, 1)) * 100.0
        
        hw_total = doc_number_total + date_total
        hw_correct = doc_number_correct + date_correct
        hw_acc = (hw_correct / max(hw_total, 1)) * 100.0
        
        p50_page = float(np.percentile(page_latencies, 50)) if page_latencies else 0.0
        p95_page = float(np.percentile(page_latencies, 95)) if page_latencies else 0.0
        p50_line = float(np.percentile(line_latencies, 50)) * 1000.0 if line_latencies else 0.0
        p95_line = float(np.percentile(line_latencies, 95)) * 1000.0 if line_latencies else 0.0
        throughput = total_predicted_lines / max(sum(page_latencies), 0.001)
        
        results = {
            "mode": mode_desc,
            "engine": engine_type,
            "use_gt_crops": use_gt_crops,
            "padding": crop_padding,
            "cer_percent": round(cer, 2),
            "wer_percent": round(wer, 2),
            "truncation_rate_percent": round(trunc_rate, 2),
            "line_recall_percent": round(line_recall, 2),
            "hw_exact_match_percent": round(hw_acc, 2),
            "hw_doc_number": f"{doc_number_correct}/{doc_number_total}",
            "hw_date": f"{date_correct}/{date_total}",
            "latency_p50_page_sec": round(p50_page, 2),
            "latency_p95_page_sec": round(p95_page, 2),
            "latency_p50_line_ms": round(p50_line, 1),
            "latency_p95_line_ms": round(p95_line, 1),
            "throughput_lines_sec": round(throughput, 1)
        }
        
        return results

def format_markdown_table(results_list: List[Dict[str, Any]]) -> str:
    """Format evaluation benchmark results as a clean Markdown table."""
    headers = [
        "Experiment / Mode", "CER (%)", "WER (%)", "Trunc. Rate (%)",
        "Line Recall (%)", "HW Match (%)", "p50 Page (s)", "Throughput (l/s)"
    ]
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join(["---"] * len(headers)) + " |"
    ]
    for r in results_list:
        row = [
            r["mode"],
            f"{r['cer_percent']:.2f}%",
            f"{r['wer_percent']:.2f}%",
            f"{r['truncation_rate_percent']:.2f}%",
            f"{r['line_recall_percent']:.2f}%",
            f"{r['hw_exact_match_percent']:.2f}%",
            f"{r['latency_p50_page_sec']:.2f}s",
            f"{r['throughput_lines_sec']:.1f}"
        ]
        lines.append("| " + " | ".join(row) + " |")
    return "\n".join(lines)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Vietnamese OCR Evaluation Suite")
    parser.add_argument("--gt-crops", action="store_true", help="Evaluate isolated on GT line crops")
    parser.add_argument("--pad", type=int, default=8, help="Horizontal padding in pixels (0, 8, 16, 24)")
    parser.add_argument("--mode", type=str, default="Baseline E2E", help="Experiment name")
    parser.add_argument("--samples", type=int, default=0, help="Number of held-out samples to evaluate (0 for all 32)")
    parser.add_argument("--out-json", type=str, default="dataset/splits/eval_results.json", help="Output JSON path")
    args = parser.parse_args()
    
    evaluator = OCREvaluator()
    if args.samples > 0:
        gold = "0_1395-KH-ĐHĐL_KE_HOACH_KHAI_GIANG_NH_2025-2026"
        sub = [gold] + [s for s in evaluator.held_out_stems if s != gold][:args.samples - 1]
        evaluator.held_out_stems = sub

    res = evaluator.evaluate_pipeline(
        engine_type="trocr",
        use_gt_crops=args.gt_crops,
        crop_padding=args.pad,
        mode_desc=args.mode
    )
    
    print("\n" + format_markdown_table([res]))
    
    out_p = REPO_ROOT / args.out_json
    existing = []
    if out_p.exists():
        try:
            with open(out_p, "r", encoding="utf-8") as f:
                existing = json.load(f)
        except Exception:
            existing = []
    existing.append(res)
    with open(out_p, "w", encoding="utf-8") as f:
        json.dump(existing, f, ensure_ascii=False, indent=2)
    print(f"\n[Saved result to {out_p}]")
