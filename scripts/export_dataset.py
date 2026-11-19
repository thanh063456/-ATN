import os
import random
import zipfile
from pathlib import Path

def main():
    base_dir = Path(__file__).resolve().parent.parent
    anno_file = base_dir / "dataset" / "annotations" / "annotation_new_pseudo.txt"
    train_file = base_dir / "dataset" / "annotations" / "train_annotation.txt"
    val_file = base_dir / "dataset" / "annotations" / "val_annotation.txt"
    zip_path = base_dir / "fine_tune_dataset.zip"
    
    if not anno_file.exists():
        print(f"Error: {anno_file} does not exist.")
        return
        
    print("Reading annotations...")
    with open(anno_file, "r", encoding="utf-8") as f:
        lines = f.readlines()
        
    print(f"Total lines: {len(lines)}")
    
    # Remove empty lines
    lines = [line for line in lines if "\t" in line]
    
    # Shuffle and split
    random.seed(42)
    random.shuffle(lines)
    
    split_idx = int(len(lines) * 0.9)
    train_lines = lines[:split_idx]
    val_lines = lines[split_idx:]
    
    print(f"Train samples: {len(train_lines)}")
    print(f"Val samples: {len(val_lines)}")
    
    with open(train_file, "w", encoding="utf-8") as f:
        f.writelines(train_lines)
        
    with open(val_file, "w", encoding="utf-8") as f:
        f.writelines(val_lines)
        
    print("Zipping dataset...")
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        # Add annotations
        zipf.write(train_file, arcname="annotations/train_annotation.txt")
        zipf.write(val_file, arcname="annotations/val_annotation.txt")
        zipf.write(anno_file, arcname="annotations/annotation_new_pseudo.txt")
        
        # Add images
        crops_dir = base_dir / "dataset" / "crops_new"
        count = 0
        total_crops = len(list(crops_dir.glob("*.png")))
        for img_path in crops_dir.glob("*.png"):
            # arcname=dataset/crops_new/... to match the path in annotations
            zipf.write(img_path, arcname=f"dataset/crops_new/{img_path.name}")
            count += 1
            if count % 5000 == 0:
                print(f"Zipped {count}/{total_crops} images...")
                
    print(f"Done! Dataset exported to: {zip_path}")

if __name__ == "__main__":
    main()
