import os
import sys

# Ensure UTF-8 output on Windows
try:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8")
except Exception:
    pass

import argparse
from pathlib import Path
from PIL import Image
import pandas as pd
import torch
from torch.utils.data import Dataset
import jiwer
from transformers import (
    RobertaTokenizer,
    ViTImageProcessor,
    TrOCRProcessor,
    VisionEncoderDecoderModel,
    Seq2SeqTrainer,
    Seq2SeqTrainingArguments,
    default_data_collator,
    EarlyStoppingCallback,
)

project_root = Path(__file__).resolve().parent.parent.parent


_path_cache = {}

def resolve_image_path(path_str: str, data_dir: str, base_dir: Path) -> str | None:
    """Kiểm tra và trả về đường dẫn ảnh tuyệt đối hợp lệ."""
    if not path_str or pd.isna(path_str):
        return None
    p = str(path_str).strip()
    if p in _path_cache:
        return _path_cache[p]

    cand = base_dir / p
    if cand.exists():
        res = str(cand.resolve())
        _path_cache[p] = res
        return res

    if os.path.isabs(p) and os.path.exists(p):
        _path_cache[p] = p
        return p

    candidates = [
        Path(data_dir) / p,
        base_dir / "dataset" / "crops_new" / os.path.basename(p),
        Path(data_dir) / "crops_new" / os.path.basename(p),
        base_dir / "dataset" / p,
    ]
    for cand in candidates:
        if cand.exists():
            res = str(cand.resolve())
            _path_cache[p] = res
            return res
    _path_cache[p] = None
    return None


class TrOCRDataset(Dataset):
    """PyTorch Dataset cho TrOCR - chuẩn Byte-Level BPE tiếng Việt."""
    def __init__(self, df: pd.DataFrame, image_processor, tokenizer, max_length: int = 64):
        self.df = df.reset_index(drop=True)
        self.image_processor = image_processor
        self.tokenizer = tokenizer
        self.max_length = max_length

    def __len__(self):
        return len(self.df)

    def __getitem__(self, idx: int):
        row = self.df.iloc[idx]
        img_path = row["image_path"]
        text = str(row["text"]) if row["text"] is not None else ""

        try:
            image = Image.open(img_path).convert("RGB")
            pixel_values = self.image_processor(images=image, return_tensors="pt").pixel_values.squeeze(0)
        except Exception:
            blank = Image.new("RGB", (384, 384), color=(255, 255, 255))
            pixel_values = self.image_processor(images=blank, return_tensors="pt").pixel_values.squeeze(0)

        encoded = self.tokenizer(
            text,
            padding="max_length",
            max_length=self.max_length,
            truncation=True,
            return_tensors="pt",
        ).input_ids.squeeze(0)

        # Gán token -100 cho pad_token để bỏ qua khi tính cross-entropy loss
        labels = [tok.item() if tok.item() != self.tokenizer.pad_token_id else -100 for tok in encoded]

        return {
            "pixel_values": pixel_values,
            "labels": torch.tensor(labels, dtype=torch.long),
        }


def load_dataset_split(file_path: str, data_dir: str, base_dir: Path) -> pd.DataFrame:
    """Tải và chuẩn hóa DataFrame huấn luyện về 2 cột: image_path và text."""
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Không tìm thấy file: {file_path}")

    try:
        df = pd.read_csv(file_path, sep="\t", encoding="utf-8")
    except Exception:
        df = pd.read_csv(file_path, sep="\t", encoding="utf-8", header=None, names=["path", "label"])

    if len(df.columns) == 2 and "image_path" not in df.columns:
        df.columns = ["image_path", "text"]
    else:
        if "path" in df.columns:
            df = df.rename(columns={"path": "image_path"})
        if "label" in df.columns:
            df = df.rename(columns={"label": "text"})

    df = df.dropna(subset=["image_path", "text"]).copy()
    df["text"] = df["text"].astype(str).str.strip()
    df = df[df["text"].str.len() > 0]

    df["image_path"] = df["image_path"].apply(lambda p: resolve_image_path(p, data_dir, base_dir))
    df = df.dropna(subset=["image_path"]).copy()

    return df


def main():
    parser = argparse.ArgumentParser(description="Huấn luyện TrOCR chuẩn cho văn bản tiếng Việt")
    parser.add_argument("--data_dir", type=str, default="dataset", help="Thư mục chứa dataset")
    parser.add_argument("--output_dir", type=str, default="models/trocr-vi", help="Thư mục lưu model")
    parser.add_argument(
        "--model_name",
        type=str,
        default="microsoft/trocr-base-printed",
        help="Model pre-trained từ HuggingFace (mặc định: microsoft/trocr-base-printed)",
    )
    parser.add_argument("--epochs", type=int, default=5, help="Số epochs")
    parser.add_argument("--batch_size", type=int, default=4, help="Batch size (RTX 3050 6GB khuyên dùng 4)")
    parser.add_argument("--grad_accum", type=int, default=4, help="Gradient accumulation steps")
    parser.add_argument("--lr", type=float, default=4e-5, help="Learning rate")
    parser.add_argument("--train_file", type=str, default=None, help="Đường dẫn file train cụ thể (tsv hoặc txt)")
    parser.add_argument("--val_file", type=str, default=None, help="Đường dẫn file val cụ thể (tsv hoặc txt)")
    parser.add_argument("--max_samples", type=int, default=-1, help="Giới hạn số mẫu train (debug/smoke test)")
    parser.add_argument("--max_val_samples", type=int, default=150, help="Số mẫu val đánh giá định kỳ (mặc định: 150 để eval chỉ mất ~30s)")
    parser.add_argument("--save_steps", type=int, default=100, help="Lưu checkpoint mỗi N steps (mặc định: 100)")
    parser.add_argument("--eval_steps", type=int, default=100, help="Đánh giá validation mỗi N steps (mặc định: 100)")
    parser.add_argument("--freeze_encoder", action="store_true", help="Đóng băng ViT encoder, chỉ train decoder")
    parser.add_argument("--resume", type=str, default=None, help="Resume từ checkpoint (hoặc 'auto' để tự tìm checkpoint mới nhất)")
    args = parser.parse_args()

    use_cuda = torch.cuda.is_available()
    device_name = torch.cuda.get_device_name(0) if use_cuda else "CPU"
    print(f"\n=======================================================")
    print(f" Thiết bị huấn luyện: {device_name}")
    print(f" Kiến trúc model: {args.model_name}")
    print(f" Batch size: {args.batch_size} (Grad Accum: {args.grad_accum})")
    print(f" Epochs: {args.epochs} | LR: {args.lr}")
    print(f" Đóng băng Encoder: {args.freeze_encoder}")
    print(f"=======================================================\n")

    # 1. Tìm dataset train và val
    candidate_train_paths = [
        args.train_file,
        os.path.join(args.data_dir, "annotations", "train_annotation.txt"),
        os.path.join(project_root, "dataset", "annotations", "train_annotation.txt"),
        os.path.join(args.data_dir, "train_annotation.txt"),
        os.path.join(args.data_dir, "splits", "train.tsv"),
    ]
    candidate_val_paths = [
        args.val_file,
        os.path.join(args.data_dir, "annotations", "val_annotation.txt"),
        os.path.join(project_root, "dataset", "annotations", "val_annotation.txt"),
        os.path.join(args.data_dir, "val_annotation.txt"),
        os.path.join(args.data_dir, "splits", "val.tsv"),
    ]

    train_path = next((p for p in candidate_train_paths if p and os.path.exists(p)), None)
    val_path = next((p for p in candidate_val_paths if p and os.path.exists(p)), None)

    if not train_path:
        raise FileNotFoundError(f"Không tìm thấy file train trong các đường dẫn: {candidate_train_paths}")

    print(f"-> Đang tải Train data từ: {train_path}")
    train_df = load_dataset_split(train_path, args.data_dir, project_root)
    print(f"   Đã nạp {len(train_df):,} mẫu train hợp lệ.")

    if val_path:
        print(f"-> Đang tải Val data từ: {val_path}")
        val_df = load_dataset_split(val_path, args.data_dir, project_root)
        print(f"   Đã nạp {len(val_df):,} mẫu val hợp lệ.")
    else:
        print("   Không tìm thấy val riêng, tự động tách 10% từ train_df.")
        val_df = train_df.sample(frac=0.1, random_state=42)
        train_df = train_df.drop(val_df.index)

    if args.max_samples > 0:
        train_df = train_df.head(args.max_samples)
        val_df = val_df.head(max(int(args.max_samples * 0.2), 2))
        print(f"   [Debug Limit] Giới hạn train: {len(train_df)}, val: {len(val_df)}")

    # 2. Tokenizer và ImageProcessor chuẩn của TrOCR
    print(f"-> Đang tải ImageProcessor và RobertaTokenizer từ {args.model_name}...")
    image_processor = ViTImageProcessor.from_pretrained(args.model_name)
    tokenizer = RobertaTokenizer.from_pretrained(args.model_name)
    processor = TrOCRProcessor(image_processor=image_processor, tokenizer=tokenizer)
    print(f"   Từ vựng BPE chuẩn: {len(tokenizer):,} tokens (bảo toàn 100% trọng số tiền huấn luyện).")

    eval_val_df = val_df.head(args.max_val_samples) if args.max_val_samples > 0 else val_df
    print(f"   Tập train: {len(train_df):,} mẫu | Tập val đánh giá nhanh: {len(eval_val_df):,} mẫu.")

    train_dataset = TrOCRDataset(train_df, image_processor, tokenizer)
    val_dataset = TrOCRDataset(eval_val_df, image_processor, tokenizer)

    # 3. Model VisionEncoderDecoderModel
    print(f"-> Đang nạp model VisionEncoderDecoderModel...")
    model = VisionEncoderDecoderModel.from_pretrained(args.model_name)

    # Cấu hình Token IDs đồng bộ
    model.config.decoder_start_token_id = tokenizer.bos_token_id
    model.config.pad_token_id = tokenizer.pad_token_id
    model.config.eos_token_id = tokenizer.eos_token_id
    model.config.vocab_size = len(tokenizer)

    model.generation_config.decoder_start_token_id = tokenizer.bos_token_id
    model.generation_config.pad_token_id = tokenizer.pad_token_id
    model.generation_config.eos_token_id = tokenizer.eos_token_id
    model.generation_config.max_length = 64
    model.generation_config.repetition_penalty = 1.2
    model.generation_config.no_repeat_ngram_size = 3

    # Kích hoạt gradient checkpointing để tiết kiệm VRAM trên GPU 6GB
    if use_cuda:
        model.gradient_checkpointing_enable()

    if args.freeze_encoder:
        print("   Đóng băng Encoder ViT để tiết kiệm VRAM và tăng tốc...")
        for param in model.encoder.parameters():
            param.requires_grad = False
    else:
        print("   Huấn luyện toàn diện (End-to-End Fine-tuning cả Encoder & Decoder)...")

    # 4. Metric CER & WER
    def compute_metrics(pred):
        labels_ids = pred.label_ids
        pred_ids = pred.predictions
        pred_str = tokenizer.batch_decode(pred_ids, skip_special_tokens=True)
        labels_ids[labels_ids == -100] = tokenizer.pad_token_id
        label_str = tokenizer.batch_decode(labels_ids, skip_special_tokens=True)

        cer = jiwer.cer(reference=label_str, hypothesis=pred_str)
        wer = jiwer.wer(reference=label_str, hypothesis=pred_str)
        return {"cer": round(cer, 4), "wer": round(wer, 4)}

    # 5. Training Arguments & Checkpoint Strategy
    os.makedirs(args.output_dir, exist_ok=True)

    # Tự động tìm checkpoint mới nhất nếu có yêu cầu resume
    resume_from_ckpt = args.resume
    if resume_from_ckpt in ("auto", "True", "true"):
        resume_from_ckpt = None
        if os.path.isdir(args.output_dir):
            existing_ckpts = [
                d for d in os.listdir(args.output_dir)
                if d.startswith("checkpoint-") and os.path.isdir(os.path.join(args.output_dir, d))
            ]
            if existing_ckpts:
                existing_ckpts.sort(key=lambda x: int(x.split("-")[1]))
                resume_from_ckpt = os.path.join(args.output_dir, existing_ckpts[-1])
                print(f"🔄 Tìm thấy checkpoint: Tự động Resume từ {resume_from_ckpt}")
            else:
                print("ℹ️ Chưa có checkpoint cũ nào trong thư mục, bắt đầu huấn luyện từ đầu.")

    training_args = Seq2SeqTrainingArguments(
        output_dir=args.output_dir,
        predict_with_generate=True,
        eval_strategy="steps",
        eval_steps=args.eval_steps,
        save_strategy="steps",
        save_steps=args.save_steps,
        logging_steps=20 if args.max_samples < 0 else 2,
        save_total_limit=3,
        per_device_train_batch_size=args.batch_size,
        per_device_eval_batch_size=args.batch_size,
        gradient_accumulation_steps=args.grad_accum,
        fp16=use_cuda,
        learning_rate=args.lr,
        num_train_epochs=args.epochs,
        load_best_model_at_end=True,
        metric_for_best_model="cer",
        greater_is_better=False,
        dataloader_num_workers=0,
        report_to="none",
    )

    trainer = Seq2SeqTrainer(
        model=model,
        args=training_args,
        compute_metrics=compute_metrics,
        train_dataset=train_dataset,
        eval_dataset=val_dataset,
        data_collator=default_data_collator,
        callbacks=[EarlyStoppingCallback(early_stopping_patience=3)],
    )

    print("\n🚀 Bắt đầu quá trình huấn luyện TrOCR tiếng Việt chuẩn...")
    trainer.train(resume_from_checkpoint=resume_from_ckpt)

    final_model_dir = os.path.join(args.output_dir, "final_model")
    print(f"\n💾 Đang lưu mô hình hoàn tất vào: {final_model_dir}...")
    os.makedirs(final_model_dir, exist_ok=True)
    trainer.save_model(final_model_dir)
    tokenizer.save_pretrained(final_model_dir)
    image_processor.save_pretrained(final_model_dir)
    processor.save_pretrained(final_model_dir)
    print("✅ Hoàn tất huấn luyện và xuất model thành công!")


if __name__ == "__main__":
    main()
