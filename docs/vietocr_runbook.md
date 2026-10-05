# VietOCR Training Runbook (Colab/Kaggle)

## 1. Local Preparation
Before transferring to the cloud, prepare the dataset by regenerating crops, aligning labels, splitting into Train/Val/Test, and excluding private data:
```bash
# 1. Regenerate crops and align labels
python scripts/rebuild_dataset.py

# 2. Audit labels (generates audit_report.csv for manual bulk-fixes)
python scripts/audit_labels.py

# 3. Create document-level train/val/test splits (split_v2.json)
python scripts/split_v2.py

# 4. Generate upload package (privacy scrubbed)
# Update make_upload_package.py to include dataset/splits/
python training/make_upload_package.py
```
Upload the resulting ZIP to Google Drive (`/MyDrive/vietocr_dataset/`).

## 2. Google Colab Setup
1. Upload `training/Train_VietOCR_VI.ipynb` to Google Colab.
2. Select **T4 GPU** runtime.
3. The notebook will automatically mount Google Drive, unzip the dataset, and install the required dependencies (pinned version of `vietocr`).

## 3. Training Command
Execute the portable training script on the T4 GPU:
```bash
python training/train.py \
    --train dataset/splits/train.tsv \
    --val dataset/splits/val.tsv \
    --output /content/drive/MyDrive/vietocr_checkpoints \
    --iters 20000 \
    --batch_size 32 \
    --lr 0.0001
```

*Note on Runtimes (ESTIMATES):* A 200-iteration chunk on a T4 GPU typically takes ~1-2 minutes. Thus, 20,000 iterations will take approximately 1.5 to 3.5 hours.

## 4. Resuming after disconnect
If Colab disconnects, simply add `--resume /content/drive/MyDrive/vietocr_checkpoints/checkpoints/20261005_1200_checkpoint.pth` to your command to pick up from the exact iteration.

## 5. Integrating with the App (A/B testing)
The training script exports a `.pth` model and a sidecar `.json` containing the metadata (vocab, image sizes). Download these to `models/vietocr_vi/`.

To switch the application to use your new weights, set the environment variable:
```env
VIETOCR_WEIGHTS=./models/vietocr_vi/transformerocr_ctsv_best.pth
```
The app will automatically check `transformerocr_ctsv_best.json` to ensure the image widths and vocab match. You can easily toggle between the original and fine-tuned weights for A/B testing by changing this flag.
