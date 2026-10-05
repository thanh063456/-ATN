# TrOCR-Vi Training Runbook (Kaggle & Colab)

Since local GPU compute is not available, training must be executed remotely on Kaggle or Google Colab (T4, P100, or A100).

## 1. Prepare Upload Package
Before moving to the cloud, run the privacy upload packaging script locally:
```bash
python training/trocr_vi/make_upload_package.py
```
This will:
- Read `dataset/train.tsv`, `dataset/val.tsv`, etc.
- Scan text for personal data (MSSV, "Họ và tên", signatures).
- Exclude affected records and dump the safe images + manifests into `trocr_vi_training_package.zip`.
- Do NOT commit this zip file. Upload it manually to your private Google Drive or as a Kaggle Private Dataset.

## 2. Google Colab Setup
1. Open `training/trocr_vi/Train_TrOCR_VI.ipynb` in Colab.
2. Go to **Runtime -> Change runtime type** and select **T4 GPU**.
3. Upload `trocr_vi_training_package.zip` to your Google Drive under `/MyDrive/trocr_dataset/` and extract it, or upload it directly to Colab and extract.
4. Update the path in the Notebook cells to point to your extracted `dataset/` directory.
5. Run all cells.

## 3. Training Stages

### Stage A: Printed Baseline (Base/Small Model)
First, verify convergence with printed real & synthetic data.
**Command**:
```bash
python training/trocr_vi/train_trocr_vi.py \
    --data_dir /content/dataset \
    --output_dir /content/drive/MyDrive/trocr-vi-checkpoints \
    --model small \
    --stage printed \
    --epochs 10 \
    --fp16
```
*(Estimates from CPU smoke test: A small model processes 50 samples in ~5 seconds on CPU. On T4 GPU, an epoch of 10,000 samples should take under 10 minutes.)*

### Stage B: Handwriting & Mixed 
Once Stage A yields a validation CER < 5%, unfreeze the encoder (if frozen) and add handwriting.
**Command**:
```bash
python training/trocr_vi/train_trocr_vi.py \
    --data_dir /content/dataset \
    --output_dir /content/drive/MyDrive/trocr-vi-checkpoints \
    --model base \
    --stage mixed \
    --epochs 15 \
    --fp16 \
    --resume /content/drive/MyDrive/trocr-vi-checkpoints/checkpoint-XXXX
```

## 4. Checkpoints & Resuming
- Checkpoints are saved every 200 steps to `--output_dir`.
- If Colab disconnects, pass the `--resume /path/to/last/checkpoint` flag to the script to pick up where it left off.
- The final model weights and tokenizer config will be in `/content/drive/MyDrive/trocr-vi-checkpoints/final_model/`.

## 5. Integrating with the App
After downloading `final_model` locally to `models/trocr-vi/`:
1. In your `.env` or settings, configure:
   `TROCR_MODEL_NAME=./models/trocr-vi`
2. The `TrOCREngine` will now automatically load the custom tokenizer and resize embeddings, dropping the English-only baseline warning in the UI.
