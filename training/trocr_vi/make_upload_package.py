import os
import re
import zipfile
import pandas as pd
from pathlib import Path
import shutil

def is_personal_data(text: str) -> bool:
    # 8-10 digit numbers (phone, MSSV)
    if re.search(r'\b\d{8,10}\b', text): return True
    # Names / Signatures indications
    text_lower = text.lower()
    if "mssv" in text_lower or "họ và tên" in text_lower or "ký tên" in text_lower or "chữ ký" in text_lower:
        return True
    return False

def main():
    base_dir = Path(__file__).resolve().parent.parent.parent
    dataset_dir = base_dir / "dataset"
    splits_dir = dataset_dir / "splits"
    out_zip = base_dir / "trocr_vi_training_package.zip"
    
    if not splits_dir.exists():
        print("No splits directory found in dataset/")
        return
        
    manifest_files = [f for f in os.listdir(splits_dir) if f.endswith(".tsv")]
    
    if not manifest_files:
        print("No manifest files found in dataset/splits/")
        return
        
    excluded_records = []
    
    with zipfile.ZipFile(out_zip, 'w', zipfile.ZIP_DEFLATED) as zf:
        for manifest in manifest_files:
            manifest_path = splits_dir / manifest
            df = pd.read_csv(manifest_path, sep="\t")
            
            clean_records = []
            
            for idx, row in df.iterrows():
                text = str(row['label']) if 'label' in row else str(row.get('text', ''))
                img_path_str = str(row['path']) if 'path' in row else str(row.get('image_path', ''))
                
                # Convert the relative path stored in TSV to absolute path for zipping
                img_path = base_dir / img_path_str
                
                if is_personal_data(text):
                    excluded_records.append({
                        "file": str(img_path.name),
                        "reason": "Matched personal data regex"
                    })
                    continue
                    
                clean_records.append(row)
                
                # Copy image to zip
                if img_path.exists():
                    # Preserve relative path inside dataset
                    rel_path = img_path.relative_to(dataset_dir)
                    zf.write(img_path, arcname=f"dataset/{rel_path}")
                else:
                    excluded_records.append({
                        "file": str(img_path.name),
                        "reason": "File not found"
                    })
            
            # Save clean manifest
            clean_df = pd.DataFrame(clean_records)
            temp_manifest = dataset_dir / f"clean_{manifest}"
            clean_df.to_csv(temp_manifest, sep="\t", index=False)
            zf.write(temp_manifest, arcname=f"dataset/{manifest}")
            temp_manifest.unlink()
            
        # Write exclusion report
        exclusion_df = pd.DataFrame(excluded_records)
        temp_exclusion = dataset_dir / "excluded_report.csv"
        exclusion_df.to_csv(temp_exclusion, index=False)
        zf.write(temp_exclusion, arcname="dataset/excluded_report.csv")
        temp_exclusion.unlink()
        
    print(f"Created upload package: {out_zip}")
    print(f"Excluded {len(excluded_records)} records due to privacy or missing files.")

if __name__ == "__main__":
    main()
