import os
import sys
from pathlib import Path
import glob

# Add backend to sys.path
backend_path = str(Path(__file__).resolve().parent.parent / "backend")
sys.path.insert(0, backend_path)

from PIL import Image

def main():
    base_dir = Path(__file__).resolve().parent.parent
    crops_dir = base_dir / "dataset" / "crops_new"
    anno_dir = base_dir / "dataset" / "annotations"
    out_anno = anno_dir / "annotation_new_pseudo.txt"
    
    if not crops_dir.exists():
        print(f"Error: {crops_dir} not found.")
        return
        
    crop_files = sorted(glob.glob(str(crops_dir / "*.png")))
    print(f"Found {len(crop_files)} crops. Starting pseudo-labeling with VietOCR...")
    
    # Initialize VietOCR Engine
    try:
        from app.services.vietocr_engine import VietOCREngine
        engine = VietOCREngine()
        predictor = engine.get_predictor()
    except Exception as e:
        print(f"Failed to load VietOCR: {e}")
        return
        
    existing_files = set()
    if out_anno.exists():
        with open(out_anno, "r", encoding="utf-8") as f:
            for line in f:
                if "\t" in line:
                    existing_files.add(line.split("\t")[0])
                else:
                    existing_files.add(line.strip())
                    
    print(f"Found {len(existing_files)} already labeled crops. Resuming from where we left off...")

    # Write annotations
    with open(out_anno, "a", encoding="utf-8") as f:
        for idx, crop_path in enumerate(crop_files):
            rel_path = Path(crop_path).relative_to(base_dir).as_posix()
            if rel_path in existing_files:
                continue
                
            try:
                pil_img = Image.open(crop_path).convert("RGB")
                text = predictor.predict(pil_img)
                text = text.strip().replace('\n', ' ').replace('\t', ' ')
                
                f.write(f"{rel_path}\t{text}\n")
                
                if (idx + 1) % 100 == 0:
                    print(f"Processed {idx + 1}/{len(crop_files)} crops...")
                    f.flush()
            except Exception as e:
                print(f"Error on {crop_path}: {e}")
                
    print(f"Done. Saved labels to {out_anno}")

if __name__ == "__main__":
    main()
