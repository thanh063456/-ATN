import os, json, unicodedata
from collections import Counter
import glob
from pathlib import Path

def main():
    dataset_dir = Path(__file__).resolve().parent.parent / 'dataset'
    # Check if there is an annotations.txt or similar
    annotation_files = glob.glob(str(dataset_dir / '**/*.txt'), recursive=True)
    
    if not annotation_files:
        print("No annotation .txt files found.")
    
    lines_count = 0
    chars = Counter()
    empty_lines = 0
    non_nfc_lines = 0
    odd_chars_lines = 0
    
    expected_chars = set(
        'aàáảãạăằắẳẵặâầấẩẫậbcdeèéẻẽẹêềếểễệfghiìíỉĩịjklmnoòóỏõọôồốổỗộơờớởỡợpqrstuùúủũụưừứửữựvwxyỳýỷỹỵz'
        'AÀÁẢÃẠĂẰẮẲẴẶÂẦẤẨẪẬBCDEÈÉẺẼẸÊỀẾỂỄỆFGHIÌÍỈĨỊJKLMNOÒÓỎÕỌÔỒỐỔỖỘƠỜỚỞỠỢPQRSTUÙÚỦŨỤƯỪỨỬỮỰVWXYỲÝỶỸỴZ'
        '0123456789 .,:;!?\'"()[]{}-–—…+*/\\%=<>@#$&_~^|'
    )
    
    documents = set()
    
    for f in annotation_files:
        with open(f, 'r', encoding='utf-8') as file:
            for line in file:
                line = line.strip()
                if not line:
                    empty_lines += 1
                    continue
                # Assuming format: image_path\ttext or image_path text
                parts = line.split('\t')
                if len(parts) >= 2:
                    text = parts[-1]
                    img_path = parts[0]
                    # Document ID can be parsed from filename e.g. DOC123_crop_4.jpg
                    doc_id = os.path.basename(img_path).split('_')[0]
                    documents.add(doc_id)
                else:
                    text = line
                
                lines_count += 1
                if text != unicodedata.normalize('NFC', text):
                    non_nfc_lines += 1
                for char in text:
                    chars[char] += 1
                    if char not in expected_chars:
                        odd_chars_lines += 1
    
    print(f'Total lines: {lines_count}')
    print(f'Empty lines: {empty_lines}')
    print(f'Non-NFC lines: {non_nfc_lines}')
    print(f'Lines with odd chars: {odd_chars_lines}')
    print(f'Unique characters: {len(chars)}')
    print(f'Total documents: {len(documents)}')
    
    if len(chars) > 0:
        print('Most common characters:', chars.most_common(10))
        
    # Write to docs/trocr_data_inventory.md
    docs_dir = dataset_dir.parent / 'docs'
    docs_dir.mkdir(exist_ok=True)
    with open(docs_dir / 'trocr_data_inventory.md', 'w', encoding='utf-8') as out:
        out.write("# TrOCR Data Inventory\n\n")
        out.write(f"- Total lines: {lines_count}\n")
        out.write(f"- Empty lines: {empty_lines}\n")
        out.write(f"- Non-NFC lines: {non_nfc_lines}\n")
        out.write(f"- Lines with unexpected chars: {odd_chars_lines}\n")
        out.write(f"- Unique characters: {len(chars)}\n")
        out.write(f"- Total documents: {len(documents)}\n")

if __name__ == "__main__":
    main()
