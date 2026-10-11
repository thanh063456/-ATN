import os
import sys
import glob
from pathlib import Path
import unicodedata
import argparse

# Add backend to sys.path
backend_path = str(Path(__file__).resolve().parent.parent / "backend")
sys.path.insert(0, backend_path)

from app.services.vietocr_service import vietocr_service
from app.services.tesseract_service import tesseract_service
from PIL import Image

def main():
    parser = argparse.ArgumentParser(description="Process new PDFs into line crops and pseudo-labels for training")
    parser.add_argument("--input", type=str, required=True, help="Path to folder containing PDF files")
    parser.add_argument("--output_dir", type=str, default="dataset", help="Output dataset directory")
    args = parser.parse_args()

    input_path = Path(args.input)
    if not input_path.exists():
        print(f"Error: Folder {input_path} does not exist.")
        return

    base_dir = Path(__file__).resolve().parent.parent
    dataset_dir = base_dir / args.output_dir
    raw_dir = dataset_dir / "raw_new"
    crops_dir = dataset_dir / "crops_new"
    anno_dir = dataset_dir / "annotations"
    
    raw_dir.mkdir(exist_ok=True, parents=True)
    crops_dir.mkdir(exist_ok=True, parents=True)
    anno_dir.mkdir(exist_ok=True, parents=True)

    # Step 1: Extract PDFs to Images using existing script logic
    # To keep it simple without subprocess, we import extract_pdf_pages
    import extract_pdf_pages
    pdf_files = list(input_path.rglob("*.pdf")) + list(input_path.rglob("*.PDF"))
    pdf_files = sorted(pdf_files)
    print(f"Found {len(pdf_files)} PDFs in {input_path}")
    
    out_anno = anno_dir / "annotation_new_pseudo.txt"
    
    # --- RESUME CAPABILITY ---
    processed_pages = set()
    if out_anno.exists():
        with open(out_anno, "r", encoding="utf-8") as f:
            for line in f:
                if "\t" in line:
                    img_path_str = line.split("\t")[0]
                    # dataset/crops_new/NEW_DOC_001_p01_line_000.png -> NEW_DOC_001_p01
                    doc_id = Path(img_path_str).stem.split("_line_")[0]
                    processed_pages.add(doc_id)
    print(f"Resuming... Found {len(processed_pages)} already processed pages in annotation file.")
    
    # Open annotation file in append mode
    with open(out_anno, "a", encoding="utf-8") as f_anno:
        for idx, pdf in enumerate(pdf_files, start=1):
            prefix = f"NEW_DOC_{idx:03d}"
            
            # Check if this PDF is already extracted by looking for the first page
            first_page_expected = raw_dir / f"{prefix}_p01.png"
            if not first_page_expected.exists():
                images = extract_pdf_pages.extract_pages_from_pdf(pdf, raw_dir, prefix=prefix, dpi=200)
            else:
                # Get all existing pages for this PDF
                import glob
                images = [Path(p) for p in sorted(glob.glob(str(raw_dir / f"{prefix}_p*.png")))]
                
            for img_idx, img_path in enumerate(images):
                doc_id = img_path.stem
                
                if doc_id in processed_pages:
                    continue # Skip already fully processed pages
                    
                try:
                    pil_img = Image.open(img_path).convert("RGB")
                    lines_with_boxes, _, _ = vietocr_service.segment_lines_with_boxes(pil_img)
                    
                    print(f"Processing page {img_idx+1}/{len(images)} of PDF {idx}: {doc_id} -> {len(lines_with_boxes)} lines")
                    
                    for line_idx, (crop_img, box) in enumerate(lines_with_boxes):
                        crop_path = crops_dir / f"{doc_id}_line_{line_idx:03d}.png"
                        
                        # Always overwrite crop image
                        crop_img.save(crop_path)
                            
                        # Predict pseudo label using VietOCR directly
                        try:
                            from app.services.vietocr_engine import VietOCREngine
                            # We should reuse the engine if possible, but initializing here is okay for script
                            # Wait, initializing inside the loop is very slow! Let's just use the global vietocr_service.
                            # vietocr_service has _get_predictor() which returns the engine's predictor.
                            predictor = vietocr_service._get_predictor()
                            text = predictor.predict(crop_img)
                            text = text.strip().replace('\n', ' ').replace('\t', ' ')
                        except:
                            text = ""
                            
                        rel_path = crop_path.relative_to(base_dir).as_posix()
                        
                        # Write to file incrementally
                        f_anno.write(f"{rel_path}\t{text}\n")
                        f_anno.flush()
                        
                except Exception as e:
                    print(f"Error processing {img_path}: {e}")
    
    print("=========================================")
    print(f"Finished processing new PDFs.")
    print(f"Crops saved in {crops_dir}")
    print(f"Pseudo-labels saved to {out_anno}")
    print("Please manually review and correct the pseudo-labels in 'annotation_new_pseudo.txt'.")
    print("Once verified, you can append them to 'annotation_train.txt' or re-run the split script.")
    print("=========================================")

if __name__ == "__main__":
    main()
