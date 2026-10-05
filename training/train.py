#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import argparse
import sys
import os
import json
import hashlib
from datetime import datetime
from pathlib import Path
import random
import numpy as np

# Ensure UTF-8 output on Windows
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

def seed_everything(seed=42):
    random.seed(seed)
    os.environ['PYTHONHASHSEED'] = str(seed)
    np.random.seed(seed)
    try:
        import torch
        torch.manual_seed(seed)
        torch.cuda.manual_seed(seed)
        torch.backends.cudnn.deterministic = True
    except ImportError:
        pass

try:
    import torch
    from vietocr.tool.config import Cfg
    from vietocr.model.trainer import Trainer
except ImportError as e:
    print(f"[ERROR] VietOCR or PyTorch not installed: {e}", file=sys.stderr)
    sys.exit(1)

def compute_hash(filepath):
    h = hashlib.sha256()
    with open(filepath, 'rb') as f:
        for chunk in iter(lambda: f.read(8192), b''):
            h.update(chunk)
    return h.hexdigest()

def build_config(args):
    config = Cfg.load_config_from_name(args.model_name)
    config["dataset"]["train_annotation"] = str(args.train.resolve())
    config["dataset"]["valid_annotation"] = str(args.val.resolve())
    config["dataset"]["data_root"] = str(Path.cwd())
    
    if args.resume:
        config["weights"] = str(args.resume.resolve())
    else:
        # Use pretrained weights from env or download
        pretrain = os.environ.get("VIETOCR_PRETRAIN", None)
        if pretrain and os.path.exists(pretrain):
            config["weights"] = pretrain
            config["pretrain"] = pretrain
            
    # Config parameters
    config["trainer"]["iters"] = args.iters
    config["trainer"]["batch_size"] = args.batch_size
    config["trainer"]["print_every"] = args.print_every
    config["trainer"]["valid_every"] = args.valid_every
    config["trainer"]["checkpoint"] = str((args.output / "checkpoints" / f"{args.tag}_checkpoint.pth").resolve())
    config["trainer"]["export"] = str((args.output / f"transformerocr_ctsv_{args.tag}_best.pth").resolve())
    config["trainer"]["log"] = str((args.output / f"{args.tag}.log").resolve())
    
    config["optimizer"] = {"max_lr": args.lr, "pct_start": 0.1}
    config["trainer"]["clip_grad_norm"] = 1.0
    config["device"] = "cuda" if torch.cuda.is_available() else "cpu"
    config.setdefault("dataloader", {})
    config["dataloader"]["num_workers"] = 0
    config["predictor"]["beamsearch"] = False
    
    # Image constraints
    config["dataset"]["image_height"] = 32
    config["dataset"]["image_min_width"] = 32
    config["dataset"]["image_max_width"] = 512
    
    # Vocab expansion
    old_vocab = config['vocab']
    new_chars = 'ùũẩẫằẳẵặẹẻẽỗỡợừỵỷỹ–“…+‘’'
    to_add = [c for c in new_chars if c not in old_vocab]
    if to_add:
        config['vocab'] = old_vocab + ''.join(to_add)
        
    return config

def main():
    parser = argparse.ArgumentParser(description="Fine-tune VietOCR (portable/reproducible)")
    parser.add_argument("--train", type=Path, required=True, help="Train annotation TSV")
    parser.add_argument("--val", type=Path, required=True, help="Val annotation TSV")
    parser.add_argument("--output", type=Path, default=Path("models"), help="Output directory")
    parser.add_argument("--resume", type=Path, help="Resume checkpoint path")
    parser.add_argument("--model_name", type=str, default="vgg_transformer", help="VietOCR base model")
    parser.add_argument("--iters", type=int, default=20000, help="Total iterations")
    parser.add_argument("--batch_size", type=int, default=32, help="Batch size")
    parser.add_argument("--lr", type=float, default=1e-4, help="Learning rate")
    parser.add_argument("--print_every", type=int, default=200, help="Print every N iters")
    parser.add_argument("--valid_every", type=int, default=1000, help="Validate every N iters")
    parser.add_argument("--tag", type=str, default=datetime.now().strftime("%Y%m%d_%H%M"), help="Run tag")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    
    args = parser.parse_args()
    seed_everything(args.seed)
    
    args.output.mkdir(parents=True, exist_ok=True)
    (args.output / "checkpoints").mkdir(exist_ok=True)
    
    config = build_config(args)
    
    trainer = Trainer(config, pretrained=True)
    print("Starting training...")
    trainer.train()
    
    # Generate Sidecar
    export_path = Path(config["trainer"]["export"])
    sidecar_path = export_path.with_suffix(".json")
    
    sidecar_data = {
        "model_name": args.model_name,
        "vocab": config["vocab"],
        "image_height": config["dataset"]["image_height"],
        "image_min_width": config["dataset"]["image_min_width"],
        "image_max_width": config["dataset"]["image_max_width"],
        "train_manifest_hash": compute_hash(args.train),
        "val_manifest_hash": compute_hash(args.val),
        "date": datetime.now().isoformat(),
        "iters": args.iters,
        "lr": args.lr
    }
    
    with open(sidecar_path, "w", encoding="utf-8") as f:
        json.dump(sidecar_data, f, indent=2, ensure_ascii=False)
        
    # Registry
    registry_path = args.output / "registry.json"
    registry = []
    if registry_path.exists():
        with open(registry_path, "r") as f:
            registry = json.load(f)
            
    registry.append({
        "weights": export_path.name,
        "sidecar": sidecar_path.name,
        "sha256": compute_hash(export_path),
        "date": sidecar_data["date"]
    })
    
    with open(registry_path, "w") as f:
        json.dump(registry, f, indent=2)
        
    print(f"Training complete. Best model saved to {export_path}")

if __name__ == "__main__":
    main()
