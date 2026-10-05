import os
import argparse
import pandas as pd
from datasets import Dataset, load_metric
from PIL import Image
import torch
from transformers import (
    TrOCRProcessor,
    VisionEncoderDecoderModel,
    ViTImageProcessor,
    Seq2SeqTrainer,
    Seq2SeqTrainingArguments,
    default_data_collator,
    EarlyStoppingCallback
)
import sys
from pathlib import Path

# Add backend to sys.path to import trocr_vi_utils
backend_path = str(Path(__file__).resolve().parent.parent.parent / "backend")
sys.path.insert(0, backend_path)
from app.services.trocr_vi_utils import create_vi_tokenizer, pad_image_to_square

cer_metric = load_metric("cer", trust_remote_code=True)

def preprocess_fn(examples, image_processor, tokenizer, max_length=64):
    pixel_values = []
    for path in examples['image_path']:
        image = Image.open(path).convert("RGB")
        # 3. Image pipeline: pad with white to a square
        image = pad_image_to_square(image, target_size=384)
        pixel_values.append(image_processor(images=image, return_tensors="pt").pixel_values.squeeze())
        
    labels = tokenizer(
        examples['text'],
        padding="max_length",
        max_length=max_length,
        truncation=True
    ).input_ids
    
    # Ignore padding tokens in loss calculation
    labels = [label if label != tokenizer.pad_token_id else -100 for label in labels]
    
    return {"pixel_values": pixel_values, "labels": labels}

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--data_dir", type=str, default="/content/dataset")
    parser.add_argument("--output_dir", type=str, default="/content/drive/MyDrive/trocr-vi-checkpoints")
    parser.add_argument("--model", type=str, default="base", choices=["base", "small"])
    parser.add_argument("--stage", type=str, default="printed", choices=["printed", "handwriting", "mixed"])
    parser.add_argument("--max_samples", type=int, default=-1)
    parser.add_argument("--epochs", type=int, default=10)
    parser.add_argument("--fp16", action="store_true")
    parser.add_argument("--resume", type=str, default=None)
    args = parser.parse_args()
    
    model_name = f"microsoft/trocr-{args.model}-stage1"
    
    # 1. Load Data
    train_path = os.path.join(args.data_dir, f"train_{args.stage}.tsv")
    val_path = os.path.join(args.data_dir, f"val_{args.stage}.tsv")
    
    # Fallback to general train.tsv if stage specific not found
    if not os.path.exists(train_path): train_path = os.path.join(args.data_dir, "train.tsv")
    if not os.path.exists(val_path): val_path = os.path.join(args.data_dir, "val.tsv")
        
    train_df = pd.read_csv(train_path, sep="\t")
    val_df = pd.read_csv(val_path, sep="\t")
    
    if args.max_samples > 0:
        train_df = train_df.head(args.max_samples)
        val_df = val_df.head(max(int(args.max_samples * 0.2), 2))
        
    train_dataset = Dataset.from_pandas(train_df)
    val_dataset = Dataset.from_pandas(val_df)
    
    # 2. Tokenizer and Processor
    image_processor = ViTImageProcessor.from_pretrained(model_name)
    tokenizer = create_vi_tokenizer()
    processor = TrOCRProcessor(image_processor=image_processor, tokenizer=tokenizer)
    
    def compute_metrics(pred):
        labels_ids = pred.label_ids
        pred_ids = pred.predictions
        pred_str = tokenizer.batch_decode(pred_ids, skip_special_tokens=True)
        labels_ids[labels_ids == -100] = tokenizer.pad_token_id
        label_str = tokenizer.batch_decode(labels_ids, skip_special_tokens=True)
        cer = cer_metric.compute(predictions=pred_str, references=label_str)
        return {"cer": cer}

    # 3. Model
    model = VisionEncoderDecoderModel.from_pretrained(model_name)
    model.decoder.resize_token_embeddings(len(tokenizer))
    
    model.config.decoder_start_token_id = tokenizer.bos_token_id
    model.config.pad_token_id = tokenizer.pad_token_id
    model.config.eos_token_id = tokenizer.eos_token_id
    model.config.vocab_size = len(tokenizer)
    model.config.max_length = 64
    
    model.generation_config.decoder_start_token_id = tokenizer.bos_token_id
    model.generation_config.pad_token_id = tokenizer.pad_token_id
    model.generation_config.eos_token_id = tokenizer.eos_token_id
    model.generation_config.max_length = 64
    
    # Freeze encoder for stage 1 printed
    if args.stage == "printed":
        for param in model.encoder.parameters():
            param.requires_grad = False
            
    # Process datasets
    train_dataset = train_dataset.map(lambda x: preprocess_fn(x, image_processor, tokenizer), batched=True, remove_columns=train_dataset.column_names)
    val_dataset = val_dataset.map(lambda x: preprocess_fn(x, image_processor, tokenizer), batched=True, remove_columns=val_dataset.column_names)
    
    # 4. Training
    training_args = Seq2SeqTrainingArguments(
        output_dir=args.output_dir,
        predict_with_generate=True,
        evaluation_strategy="steps",
        eval_steps=200 if args.max_samples < 0 else 5,
        logging_steps=50 if args.max_samples < 0 else 2,
        save_steps=200 if args.max_samples < 0 else 5,
        save_total_limit=3,
        per_device_train_batch_size=8,
        per_device_eval_batch_size=8,
        fp16=args.fp16,
        learning_rate=5e-5,
        num_train_epochs=args.epochs,
        load_best_model_at_end=True,
        metric_for_best_model="cer",
        greater_is_better=False,
        report_to="none"
    )
    
    trainer = Seq2SeqTrainer(
        model=model,
        tokenizer=tokenizer,
        args=training_args,
        compute_metrics=compute_metrics,
        train_dataset=train_dataset,
        eval_dataset=val_dataset,
        data_collator=default_data_collator,
        callbacks=[EarlyStoppingCallback(early_stopping_patience=3)]
    )
    
    print("Starting training...")
    trainer.train(resume_from_checkpoint=args.resume)
    
    print("Saving final model...")
    trainer.save_model(os.path.join(args.output_dir, "final_model"))
    processor.save_pretrained(os.path.join(args.output_dir, "final_model"))
    print("Done!")

if __name__ == "__main__":
    main()
