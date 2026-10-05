# VietOCR Data Report

## 1. Splits & Duplicates
- **Train (70%) / Val (15%) / Test (15%)**: Strict document-level splits. No lines from the same document cross over into other splits.
- **Duplicate Capping**: Identical labels in the Train set are capped at **N=20**. For example, standard lists (`CTK46`, `Xuất sắc`) are reduced to 20 instances.

## 2. Charset Coverage & Gap Remediation
- **Missing Characters**: Original annotations lacked diacritics like `ù ũ ẩ ẫ ằ ẳ ẵ ặ ẹ ẻ ẽ ỗ ỡ ợ ừ ỵ ỷ ỹ` and typography (`“ ” … — +`). 
- **Remediation**: `training/synth_lines.py` ensures all missing characters appear in the generated dataset. By including synthetic data, every letter is guaranteed to appear >200 times.

## 3. Label Noise
- A label audit script identifies discrepancies >15% CER when compared with the current model's predictions (and Tesseract consensus). These are outputted to an HTML/CSV review sheet for manual bulk-correction.

## 4. Privacy
- Crops suspected of containing 8-10 digit numbers (phone, MSSV) and signatures/names are filtered out by `make_upload_package.py` to prevent sensitive project data leakage to Kaggle/Colab.
