import os
import json
import random
import pandas as pd
from pathlib import Path
from collections import Counter

def get_doc_type(doc_id):
    doc_id_lower = doc_id.lower()
    if 'ke_hoach' in doc_id_lower: return 'ke_hoach'
    if 'thong_bao' in doc_id_lower: return 'thong_bao'
    if 'quyet_dinh' in doc_id_lower: return 'quyet_dinh'
    if 'danh_sach' in doc_id_lower: return 'danh_sach'
    if 'bieu_mau' in doc_id_lower or 'don_' in doc_id_lower: return 'bieu_mau'
    return 'other'

def main():
    base_dir = Path(__file__).resolve().parent.parent
    annotations_dir = base_dir / "dataset" / "annotations"
    splits_dir = base_dir / "dataset" / "splits"
    splits_dir.mkdir(exist_ok=True, parents=True)
    
    anno_file = annotations_dir / "annotation_new_pseudo.txt"
    if not anno_file.exists():
        anno_file = annotations_dir / "annotation_train.txt"
        
    records = []
    with open(anno_file, "r", encoding="utf-8") as f:
        for line in f:
            line = line.rstrip('\n')
            if "\t" not in line: 
                # Handle cases where the crop has no text
                path = line.strip()
                label = ""
            else:
                path, label = line.split("\t", 1)
            doc_id = os.path.basename(path).split('_line_')[0]
            records.append({"path": path, "label": label, "doc_id": doc_id, "type": get_doc_type(doc_id)})
            
    df = pd.DataFrame(records)
    
    # Stratified split by document
    docs = df[['doc_id', 'type']].drop_duplicates()
    
    # Simple stratification logic
    train_docs, val_docs, test_docs = [], [], []
    random.seed(42)
    
    for dtype, group in docs.groupby('type'):
        group_docs = group['doc_id'].tolist()
        random.shuffle(group_docs)
        
        n_test = max(1, int(len(group_docs) * 0.15))
        n_val = max(1, int(len(group_docs) * 0.15))
        
        test_docs.extend(group_docs[:n_test])
        val_docs.extend(group_docs[n_test:n_test+n_val])
        train_docs.extend(group_docs[n_test+n_val:])
        
    # Create datasets
    train_df = df[df['doc_id'].isin(train_docs)].copy()
    val_df = df[df['doc_id'].isin(val_docs)].copy()
    test_df = df[df['doc_id'].isin(test_docs)].copy()
    
    # Cap duplicates in train to N=20
    train_df['label_lower'] = train_df['label'].str.lower()
    train_capped = train_df.groupby('label_lower').head(20).drop(columns=['label_lower'])
    
    print(f"Original Train: {len(train_df)}, Capped Train: {len(train_capped)}")
    
    # Save split JSON
    split_info = {
        "train_docs": train_docs,
        "val_docs": val_docs,
        "test_docs": test_docs
    }
    
    with open(splits_dir / "split_v2.json", "w") as f:
        json.dump(split_info, f, indent=2)
        
    # Save TSV for model
    train_capped.to_csv(splits_dir / "train.tsv", sep="\t", index=False)
    val_df.to_csv(splits_dir / "val.tsv", sep="\t", index=False)
    test_df.to_csv(splits_dir / "test.tsv", sep="\t", index=False)
    
    print(f"Saved splits to {splits_dir}")
    print(f"Train: {len(train_capped)} lines | Val: {len(val_df)} lines | Test: {len(test_df)} lines")

if __name__ == "__main__":
    main()
