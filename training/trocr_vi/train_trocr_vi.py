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
import pandas as pd
from PIL import Image
import torch
from torch.utils.data import Dataset
from pathlib import Path
import jiwer
from transformers import (
    TrOCRProcessor,
    VisionEncoderDecoderModel,
    ViTImageProcessor,
    Seq2SeqTrainer,
    Seq2SeqTrainingArguments,
    default_data_collator,
    EarlyStoppingCallback
)

# Thêm backend vào sys.path để import trocr_vi_utils
project_root = Path(__file__).resolve().parent.parent.parent
backend_path = str(project_root / "backend")
if backend_path not in sys.path:
    sys.path.insert(0, backend_path)

from app.services.trocr_vi_utils import create_vi_tokenizer, pad_image_to_square


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
    """PyTorch Dataset thuần cho TrOCR - không phụ thuộc pyarrow hay datasets."""
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
            image = pad_image_to_square(image, target_size=384)
            pixel_values = self.image_processor(images=image, return_tensors="pt").pixel_values.squeeze(0)
        except Exception as exc:
            blank = Image.new("RGB", (384, 384), color=(255, 255, 255))
            pixel_values = self.image_processor(images=blank, return_tensors="pt").pixel_values.squeeze(0)

        encoded = self.tokenizer(
            text,
            padding="max_length",
            max_length=self.max_length,
            truncation=True,
            return_tensors="pt"
        ).input_ids.squeeze(0)

        # Gán token -100 cho pad_token để bỏ qua khi tính cross-entropy loss
        labels = [tok.item() if tok.item() != self.tokenizer.pad_token_id else -100 for tok in encoded]

        return {
            "pixel_values": pixel_values,
            "labels": torch.tensor(labels, dtype=torch.long)
        }


def load_dataset_split(file_path: str, data_dir: str, base_dir: Path) -> pd.DataFrame:
    """Tải và chuẩn hóa DataFrame huấn luyện về 2 cột: image_path và text."""
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Không tìm thấy file: {file_path}")

    # Đọc tsv hoặc txt
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

    # Lọc bỏ giá trị null
    df = df.dropna(subset=["image_path", "text"]).copy()
    df["text"] = df["text"].astype(str).str.strip()
    df = df[df["text"].str.len() > 0]

    # Chuẩn hóa đường dẫn ảnh
    df["image_path"] = df["image_path"].apply(lambda p: resolve_image_path(p, data_dir, base_dir))
    df = df.dropna(subset=["image_path"]).copy()
    
    return df


def main():
    parser = argparse.ArgumentParser(description="Huấn luyện TrOCR cho văn bản tiếng Việt")
    parser.add_argument("--data_dir", type=str, default="dataset", help="Thư mục chứa dataset")
    parser.add_argument("--output_dir", type=str, default="models/trocr-vi", help="Thư mục lưu model")
    parser.add_argument("--model", type=str, default="small", choices=["small", "base"], help="Mô hình base (microsoft/trocr-*-stage1)")
    parser.add_argument("--stage", type=str, default="printed", choices=["printed", "handwriting", "mixed"])
    parser.add_argument("--max_samples", type=int, default=-1, help="Giới hạn số mẫu (debug/smoke test)")
    parser.add_argument("--epochs", type=int, default=5, help="Số epochs")
    parser.add_argument("--batch_size", type=int, default=4, help="Batch size trên mỗi GPU (RTX 3050 6GB khuyên dùng 4)")
    parser.add_argument("--grad_accum", type=int, default=4, help="Gradient accumulation steps (effective batch size = 4*4=16)")
    parser.add_argument("--train_file", type=str, default=None, help="Đường dẫn file train cụ thể (tsv hoặc txt)")
    parser.add_argument("--val_file", type=str, default=None, help="Đường dẫn file val cụ thể (tsv hoặc txt)")
    parser.add_argument("--lr", type=float, default=5e-5, help="Learning rate")
    parser.add_argument("--fp16", action="store_true", default=None, help="Bật fp16 (tự động bật nếu có CUDA)")
    parser.add_argument("--resume", type=str, default=None, help="Resume từ checkpoint")
    args = parser.parse_args()

    use_cuda = torch.cuda.is_available()
    device_name = torch.cuda.get_device_name(0) if use_cuda else "CPU"
    print(f"\n=======================================================")
    print(f" Thiết bị huấn luyện: {device_name}")
    print(f" Kiến trúc model: microsoft/trocr-{args.model}-stage1")
    print(f" Batch size: {args.batch_size} (Grad Accum: {args.grad_accum})")
    print(f" Epochs: {args.epochs}")
    print(f"=======================================================\n")

    if args.fp16 is None:
        args.fp16 = use_cuda

    model_name = f"microsoft/trocr-{args.model}-stage1"
    
    # 1. Tìm file train và val
    candidate_train_paths = [
        args.train_file,
        args.data_dir if os.path.isfile(args.data_dir) else None,
        os.path.join(args.data_dir, "train_annotation.txt"),
        os.path.join(args.data_dir, "annotation_train.txt"),
        os.path.join(args.data_dir, f"train_{args.stage}.tsv"),
        os.path.join(args.data_dir, "splits", "train.tsv"),
        os.path.join(args.data_dir, "train.tsv"),
        os.path.join(args.data_dir, "annotations", "train_annotation.txt"),
        os.path.join(project_root, "dataset", "annotations", "train_annotation.txt"),
        os.path.join(project_root, "dataset", "splits", "train.tsv"),
    ]
    candidate_val_paths = [
        args.val_file,
        os.path.join(args.data_dir, "val_annotation.txt"),
        os.path.join(args.data_dir, "annotation_val.txt"),
        os.path.join(args.data_dir, f"val_{args.stage}.tsv"),
        os.path.join(args.data_dir, "splits", "val.tsv"),
        os.path.join(args.data_dir, "val.tsv"),
        os.path.join(args.data_dir, "annotations", "val_annotation.txt"),
        os.path.join(project_root, "dataset", "annotations", "val_annotation.txt"),
        os.path.join(project_root, "dataset", "splits", "val.tsv"),
    ]

    train_path = next((p for p in candidate_train_paths if p and os.path.exists(p)), None)
    val_path = next((p for p in candidate_val_paths if p and os.path.exists(p)), None)

    if not train_path:
        valid_candidates = [p for p in candidate_train_paths if p]
        raise FileNotFoundError(f"Không tìm thấy file train trong các đường dẫn: {valid_candidates}")
    
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

    # 2. Tokenizer và Processor tiếng Việt
    print("-> Đang khởi tạo Tokenizer tiếng Việt và Image Processor...")
    image_processor = ViTImageProcessor.from_pretrained(model_name)
    tokenizer = create_vi_tokenizer()
    processor = TrOCRProcessor(image_processor=image_processor, tokenizer=tokenizer)
    print(f"   Kích thước từ vựng ký tự tiếng Việt: {len(tokenizer)} tokens")

    train_dataset = TrOCRDataset(train_df, image_processor, tokenizer)
    val_dataset = TrOCRDataset(val_df, image_processor, tokenizer)

    def compute_metrics(pred):
        labels_ids = pred.label_ids
        pred_ids = pred.predictions
        pred_str = tokenizer.batch_decode(pred_ids, skip_special_tokens=True)
        labels_ids[labels_ids == -100] = tokenizer.pad_token_id
        label_str = tokenizer.batch_decode(labels_ids, skip_special_tokens=True)
        cer = jiwer.cer(reference=label_str, hypothesis=pred_str)
        return {"cer": round(cer, 4)}

    # 3. Model VisionEncoderDecoder
    print(f"-> Đang tải model {model_name}...")
    model = VisionEncoderDecoderModel.from_pretrained(model_name)
    model.decoder.resize_token_embeddings(len(tokenizer))

    model.config.decoder_start_token_id = tokenizer.bos_token_id
    model.config.pad_token_id = tokenizer.pad_token_id
    model.config.eos_token_id = tokenizer.eos_token_id
    model.config.vocab_size = len(tokenizer)

    model.generation_config.decoder_start_token_id = tokenizer.bos_token_id
    model.generation_config.pad_token_id = tokenizer.pad_token_id
    model.generation_config.eos_token_id = tokenizer.eos_token_id
    model.generation_config.max_length = 64

    # Đóng băng Encoder nếu ở giai đoạn in ấn (tiết kiệm VRAM & tăng tốc hội tụ)
    if args.stage == "printed":
        print("   Đóng băng encoder để tập trung fine-tune decoder tiếng Việt...")
        for param in model.encoder.parameters():
            param.requires_grad = False

    # 4. Training Arguments
    os.makedirs(args.output_dir, exist_ok=True)
    training_args = Seq2SeqTrainingArguments(
        output_dir=args.output_dir,
        predict_with_generate=True,
        eval_strategy="epoch" if args.max_samples < 0 else "steps",
        eval_steps=100 if args.max_samples < 0 else 5,
        save_strategy="epoch" if args.max_samples < 0 else "steps",
        save_steps=100 if args.max_samples < 0 else 5,
        logging_steps=20 if args.max_samples < 0 else 2,
        save_total_limit=2,
        per_device_train_batch_size=args.batch_size,
        per_device_eval_batch_size=args.batch_size,
        gradient_accumulation_steps=args.grad_accum,
        fp16=args.fp16,
        learning_rate=args.lr,
        num_train_epochs=args.epochs,
        load_best_model_at_end=True,
        metric_for_best_model="cer",
        greater_is_better=False,
        dataloader_num_workers=0,
        report_to="none"
    )

    trainer_kwargs = {
        "model": model,
        "args": training_args,
        "compute_metrics": compute_metrics,
        "train_dataset": train_dataset,
        "eval_dataset": val_dataset,
        "data_collator": default_data_collator,
        "callbacks": [EarlyStoppingCallback(early_stopping_patience=3)],
    }
    try:
        trainer = Seq2SeqTrainer(processing_class=tokenizer, **trainer_kwargs)
    except TypeError:
        trainer = Seq2SeqTrainer(tokenizer=tokenizer, **trainer_kwargs)

    print("\n🚀 Bắt đầu quá trình huấn luyện TrOCR...")
    trainer.train(resume_from_checkpoint=args.resume)

    final_model_dir = os.path.join(args.output_dir, "final_model")
    print(f"\n💾 Đang lưu mô hình hoàn tất vào: {final_model_dir}...")
    os.makedirs(final_model_dir, exist_ok=True)
    trainer.save_model(final_model_dir)
    tokenizer.save_pretrained(final_model_dir)
    processor.save_pretrained(final_model_dir)
    print("✅ Hoàn tất huấn luyện và xuất model thành công!")


if __name__ == "__main__":
    main()
