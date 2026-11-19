import os
import sys
import pandas as pd
from pathlib import Path

# Add backend to sys.path
backend_path = str(Path(__file__).resolve().parent.parent / "backend")
sys.path.insert(0, backend_path)

from app.services.vietocr_service import vietocr_service
from app.services.tesseract_service import tesseract_service
from PIL import Image
try:
    import editdistance
except ImportError:
    import subprocess
    subprocess.run([sys.executable, "-m", "pip", "install", "editdistance"])
    import editdistance

def main():
    base_dir = Path(__file__).resolve().parent.parent
    annotations_dir = base_dir / "dataset" / "annotations"
    
    # Ideally, we should run this over the re-aligned dataset, but we will support both.
    anno_file = annotations_dir / "annotation_v2_aligned.txt"
    if not anno_file.exists():
        anno_file = annotations_dir / "annotation_train.txt"
        
    if not anno_file.exists():
        print("No annotation file found.")
        return
        
    records = []
    
    with open(anno_file, "r", encoding="utf-8") as f:
        lines = f.readlines()
        
    print(f"Auditing {len(lines)} labels...")
    
    for i, line in enumerate(lines[:100]): # Limit for CPU testing/demonstration, real run would do all
        if "\t" not in line: continue
        img_path, label = line.strip().split("\t", 1)
        abs_img_path = base_dir / img_path
        
        if not abs_img_path.exists():
            continue
            
        try:
            pil_img = Image.open(abs_img_path).convert("RGB")
            
            # Predict with VietOCR
            v_text, _, _ = vietocr_service.extract_text_from_file(None, None, pil_image=pil_img)
            # Predict with Tesseract
            t_text, _, _ = tesseract_service.extract_text_from_file(None, None, pil_image=pil_img)
            
            v_text = v_text.strip()
            t_text = t_text.strip()
            
            # CER vs VietOCR prediction
            cer = editdistance.eval(label.lower(), v_text.lower()) / max(len(label), 1)
            
            # Flag if CER > 15% or disagrees heavily with Tesseract
            if cer > 0.15 or (t_text and t_text.lower() != label.lower() and v_text.lower() == t_text.lower()):
                records.append({
                    "image_path": img_path,
                    "current_label": label,
                    "vietocr_pred": v_text,
                    "tesseract_pred": t_text,
                    "cer": round(cer, 3)
                })
        except Exception as e:
            print(f"Error on {img_path}: {e}")
            
        if (i+1) % 10 == 0:
            print(f"Processed {i+1}/{len(lines)}")
            
    df = pd.DataFrame(records)
    csv_path = base_dir / "dataset" / "audit_report.csv"
    df.to_csv(csv_path, index=False, encoding="utf-8-sig")
    
    # Generate HTML report
    html_path = base_dir / "dataset" / "audit_report.html"
    html_content = "<html><head><meta charset='utf-8'><style>table {border-collapse: collapse; width: 100%;} th, td {border: 1px solid #ddd; padding: 8px;} img {max-height: 50px;}</style></head><body>"
    html_content += "<h2>Label Audit Report (CER > 15% or Tesseract consensus)</h2>"
    html_content += "<table><tr><th>Image</th><th>Path</th><th>Current Label</th><th>VietOCR Pred</th><th>Tesseract Pred</th><th>CER</th></tr>"
    
    for r in records:
        html_content += f"<tr>"
        html_content += f"<td><img src='../{r['image_path']}'></td>"
        html_content += f"<td>{r['image_path']}</td>"
        html_content += f"<td>{r['current_label']}</td>"
        html_content += f"<td>{r['vietocr_pred']}</td>"
        html_content += f"<td>{r['tesseract_pred']}</td>"
        html_content += f"<td>{r['cer']}</td>"
        html_content += f"</tr>"
        
    html_content += "</table></body></html>"
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(html_content)
        
    print(f"Audit completed. Found {len(records)} suspicious labels.")
    print(f"Reports saved to {csv_path} and {html_path}")

if __name__ == "__main__":
    main()
