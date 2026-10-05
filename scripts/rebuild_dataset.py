import os
import sys
import glob
import json
from pathlib import Path
import unicodedata

# Add backend to sys.path
backend_path = str(Path(__file__).resolve().parent.parent / "backend")
sys.path.insert(0, backend_path)

from app.services.vietocr_service import vietocr_service
from app.services.tesseract_service import tesseract_service
from PIL import Image
try:
    from rapidfuzz import fuzz
except ImportError:
    import subprocess
    subprocess.run([sys.executable, "-m", "pip", "install", "rapidfuzz"])
    from rapidfuzz import fuzz

def normalize(text):
    return unicodedata.normalize('NFC', str(text).strip())

def main():
    base_dir = Path(__file__).resolve().parent.parent
    raw_dir = base_dir / "dataset" / "raw"
    old_crops_dir = base_dir / "dataset" / "crops"
    new_crops_dir = base_dir / "dataset" / "crops_v2"
    annotations_dir = base_dir / "dataset" / "annotations"
    
    new_crops_dir.mkdir(exist_ok=True, parents=True)
    
    # 1. Load old annotations
    old_anno_file = annotations_dir / "annotation_full.txt"
    if not old_anno_file.exists():
        # Maybe it's in train?
        old_anno_file = annotations_dir / "annotation_train.txt"
        
    old_labels = {} # dict mapping doc_id -> list of (old_path, label)
    if old_anno_file.exists():
        with open(old_anno_file, "r", encoding="utf-8") as f:
            for line in f:
                if "\t" not in line: continue
                img_path, label = line.strip().split("\t", 1)
                doc_id = os.path.basename(img_path).split('_line_')[0]
                if doc_id not in old_labels:
                    old_labels[doc_id] = []
                old_labels[doc_id].append((img_path, normalize(label)))
                
    raw_images = glob.glob(str(raw_dir / "*.*"))
    print(f"Found {len(raw_images)} raw images and {sum(len(v) for v in old_labels.values())} old labels.")
    
    new_annotations = []
    legacy_annotations = []
    
    for raw_img_path in raw_images:
        doc_id = os.path.basename(raw_img_path).rsplit('.', 1)[0]
        if doc_id not in old_labels:
            print(f"Skipping {doc_id}, no old labels.")
            continue
            
        try:
            pil_img = Image.open(raw_img_path).convert("RGB")
        except Exception as e:
            print(f"Error opening {raw_img_path}: {e}")
            continue
            
        # Segment using current segmenter
        lines_with_boxes, _, _ = vietocr_service.segment_lines_with_boxes(pil_img)
        print(f"Doc {doc_id}: Segmented {len(lines_with_boxes)} new crops. Old crops: {len(old_labels[doc_id])}")
        
        doc_old_labels = old_labels[doc_id].copy()
        used_old_idxs = set()
        
        for idx, (crop_img, box) in enumerate(lines_with_boxes):
            # Run quick OCR using Tesseract for alignment
            try:
                # Tesseract might be faster for this quick alignment
                ocr_text, _, _ = tesseract_service.extract_text_from_file(None, None, pil_image=crop_img)
            except:
                ocr_text = ""
                
            best_score = -1
            best_old_idx = -1
            best_label = ""
            best_old_path = ""
            
            for o_idx, (old_path, old_label) in enumerate(doc_old_labels):
                if o_idx in used_old_idxs: continue
                
                score = fuzz.ratio(ocr_text.lower(), old_label.lower())
                if score > best_score:
                    best_score = score
                    best_old_idx = o_idx
                    best_label = old_label
                    best_old_path = old_path
                    
            if best_score > 60:
                # Matched
                used_old_idxs.add(best_old_idx)
                new_crop_path = f"dataset/crops_v2/{doc_id}_line_{idx:03d}.png"
                abs_new_crop_path = new_crops_dir / f"{doc_id}_line_{idx:03d}.png"
                crop_img.save(abs_new_crop_path)
                new_annotations.append((new_crop_path, best_label))
            else:
                # Unmatched
                pass
                
        # Any unused old labels are flagged as legacy
        for o_idx, (old_path, old_label) in enumerate(doc_old_labels):
            if o_idx not in used_old_idxs:
                legacy_annotations.append((old_path, old_label))
                
    # Save the new annotations
    with open(annotations_dir / "annotation_v2_aligned.txt", "w", encoding="utf-8") as f:
        for path, label in new_annotations:
            f.write(f"{path}\t{label}\n")
            
    with open(annotations_dir / "annotation_v2_legacy.txt", "w", encoding="utf-8") as f:
        for path, label in legacy_annotations:
            f.write(f"{path}\t{label}\n")
            
    print(f"Re-aligned {len(new_annotations)} crops.")
    print(f"Legacy crops (unmatched): {len(legacy_annotations)}")
    
if __name__ == "__main__":
    main()
