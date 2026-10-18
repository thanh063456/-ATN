#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
scripts/test_pipeline_improvements.py

Unit test and verification for pipeline enhancements:
1. Color-channel red stamp suppression while preserving blue/black ink.
2. Long-line horizontal overlap chunking & stitching.
3. Handwriting field validation and <hw> tagging.
4. Line-preserving post-processing.
"""

import sys
import re
import unicodedata
from pathlib import Path
import numpy as np
from PIL import Image

def suppress_red_stamp(img_np: np.ndarray) -> np.ndarray:
    """
    Suppress red seal ink by color-channel filtering:
    Replaces high-R, low-G/B pixels with background luminance while strictly
    preserving black text (low R,G,B) and blue handwriting (B > R + 15).
    """
    if len(img_np.shape) < 3 or img_np.shape[2] < 3:
        return img_np
        
    out = img_np.copy()
    r = out[:, :, 0].astype(int)
    g = out[:, :, 1].astype(int)
    b = out[:, :, 2].astype(int)
    
    # Red stamp criteria: prominent red, noticeably higher than green and blue
    is_red = (r > 120) & ((r - g) > 30) & ((r - b) > 30)
    
    # Blue ink protection: Blue channel clearly higher than red
    is_blue = (b > r + 15) & (b > 60)
    
    # Dark black text protection: all channels low
    is_black = (r < 80) & (g < 80) & (b < 80)
    
    # Red mask to remove
    to_remove = is_red & (~is_blue) & (~is_black)
    
    # Replace with white background
    out[to_remove] = [255, 255, 255]
    return out

def merge_overlapping_texts(text1: str, text2: str, min_overlap_words: int = 2) -> str:
    """
    Merge two overlapping text segments decoded from horizontal line chunks.
    Aligns by matching word n-grams at the junction.
    """
    t1 = text1.strip()
    t2 = text2.strip()
    if not t1:
        return t2
    if not t2:
        return t1
    if t1 == t2:
        return t1
        
    w1 = t1.split()
    w2 = t2.split()
    
    # Search for maximum word overlap from end of w1 matching start of w2
    max_k = min(len(w1), len(w2))
    best_overlap = 0
    
    for k in range(max_k, min_overlap_words - 1, -1):
        suffix = " ".join(w1[-k:]).lower()
        prefix = " ".join(w2[:k]).lower()
        if suffix == prefix:
            best_overlap = k
            break
            
    if best_overlap >= min_overlap_words:
        # Merge: take w1, plus remainder of w2
        merged = " ".join(w1 + w2[best_overlap:])
        return merged
        
    # Fallback: check character-level overlap
    max_char_k = min(len(t1), len(t2), 40)
    for k in range(max_char_k, 6, -1):
        if t1[-k:].lower() == t2[:k].lower():
            return t1 + t2[k:]
            
    # If no clean overlap found, concatenate with space
    return t1 + " " + t2

def tag_handwriting_in_line(line: str) -> str:
    """
    Tag handwritten document number digits and dates with <hw>...</hw>.
    Example:
      'Số: 1395/KH-ĐHĐL' -> 'Số: <hw>1395</hw>/KH-ĐHĐL'
      'Lâm Đồng, ngày 22 tháng 8 năm 2025' -> 'Lâm Đồng, ngày <hw>22</hw> tháng 8 năm 2025'
    """
    line_norm = unicodedata.normalize("NFC", line)
    
    # Tag document number
    def repl_doc(m):
        prefix = m.group(1)
        num = m.group(2)
        suffix = m.group(3)
        return f"{prefix}<hw>{num}</hw>{suffix}"
        
    line_norm = re.sub(
        r'((?:Số|So|SỐ)\s*:\s*)(\d{1,5})([/\\][A-Za-zĐđ0-9\-_]+)',
        repl_doc,
        line_norm
    )
    
    # Tag date day if handwritten
    def repl_date(m):
        prefix = m.group(1)
        day = m.group(2)
        suffix = m.group(3)
        return f"{prefix}<hw>{day}</hw>{suffix}"
        
    line_norm = re.sub(
        r'(ng[àaá]y\s+)(\d{1,2})(\s+th[áa]ng)',
        repl_date,
        line_norm,
        flags=re.IGNORECASE
    )
    
    return line_norm

def test_all():
    print("[1] Testing red stamp suppression...")
    test_img = np.zeros((100, 100, 3), dtype=np.uint8)
    test_img[:, :] = [255, 255, 255] # White bg
    test_img[10:30, 10:30] = [220, 20, 20] # Red stamp
    test_img[15:25, 15:25] = [20, 20, 20]  # Black text inside stamp
    test_img[40:60, 40:60] = [30, 40, 210] # Blue ink
    
    cleaned = suppress_red_stamp(test_img)
    assert np.all(cleaned[12, 12] == [255, 255, 255]), "Red pixel was not suppressed!"
    assert np.all(cleaned[20, 20] == [20, 20, 20]), "Black text inside stamp was altered!"
    assert np.all(cleaned[50, 50] == [30, 40, 210]), "Blue ink was altered!"
    print("  -> Red stamp suppression PASSED!")

    print("[2] Testing overlap merging...")
    c1 = "Căn cứ kế hoạch số 1153/KH-BGDĐT ngày 08/8/2025 của Bộ Giáo dục và Đào tạo về việc tổ chức"
    c2 = "Bộ Giáo dục và Đào tạo về việc tổ chức với những nội dung cụ thể như sau:"
    merged = merge_overlapping_texts(c1, c2)
    expected = "Căn cứ kế hoạch số 1153/KH-BGDĐT ngày 08/8/2025 của Bộ Giáo dục và Đào tạo về việc tổ chức với những nội dung cụ thể như sau:"
    assert merged == expected, f"Merged mismatch:\nGot:      {merged}\nExpected: {expected}"
    print("  -> Overlap merging PASSED!")

    print("[3] Testing handwriting tagging...")
    s1 = "Số: 1395/KH-ĐHĐL"
    t1 = tag_handwriting_in_line(s1)
    assert t1 == "Số: <hw>1395</hw>/KH-ĐHĐL", f"Mismatch: {t1}"
    
    s2 = "Lâm Đồng, ngày 22 tháng 8 năm 2025"
    t2 = tag_handwriting_in_line(s2)
    assert t2 == "Lâm Đồng, ngày <hw>22</hw> tháng 8 năm 2025", f"Mismatch: {t2}"
    print("  -> Handwriting tagging PASSED!")

if __name__ == "__main__":
    test_all()
    print("\nALL PRELIMINARY TESTS PASSED!")
