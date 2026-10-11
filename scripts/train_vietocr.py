import sys
sys.stdout.reconfigure(encoding='utf-8')

import os
import shutil
import random
from vietocr.tool.config import Cfg
from vietocr.model.trainer import Trainer

# 1. Đường dẫn thư mục
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATASET_DIR = os.path.join(BASE_DIR, 'dataset')
CROPS_DIR = os.path.join(DATASET_DIR, 'crops_new')
ANNOTATION_FILE = os.path.join(DATASET_DIR, 'annotations', 'annotation_new_pseudo.txt')

TRAIN_ANN_FILE = os.path.join(DATASET_DIR, 'annotations', 'train_annotation.txt')
VAL_ANN_FILE = os.path.join(DATASET_DIR, 'annotations', 'val_annotation.txt')

print("--- Step 1: Split Train/Val and Clean special characters ---")

# Đọc toàn bộ nhãn
with open(ANNOTATION_FILE, 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Tải bộ từ vựng chuẩn của VietOCR
config = Cfg.load_config_from_name('vgg_transformer')
vocab_set = set(config['vocab'])

replace_map = {
    '“': '"', '”': '"', '‘': "'", '’': "'",
    '–': '-', '—': '-', '…': '...'
}

clean_lines = []
for line in lines:
    parts = line.strip('\n').split('\t')
    if len(parts) == 2:
        img_path = parts[0]
        label = parts[1]
        
        # Chỉ lấy ảnh có thực trong thư mục crops_new
        full_img_path = os.path.join(BASE_DIR, img_path)
        if not os.path.exists(full_img_path):
            continue
            
        # Chuẩn hóa nhãn
        for k, v in replace_map.items():
            label = label.replace(k, v)
        label = "".join([c for c in label if c in vocab_set])
        
        if label.strip() != "":
            clean_lines.append(f"{img_path}\t{label}\n")

print(f"Total valid images: {len(clean_lines)}")

# Chia tỉ lệ 90% Train, 10% Val
random.seed(42)
random.shuffle(clean_lines)
split_idx = int(len(clean_lines) * 0.9)

with open(TRAIN_ANN_FILE, 'w', encoding='utf-8') as f:
    f.writelines(clean_lines[:split_idx])

with open(VAL_ANN_FILE, 'w', encoding='utf-8') as f:
    f.writelines(clean_lines[split_idx:])
    
print("Dataset splitting successful!")


print("\n--- Step 2: Model Configuration ---")
config['dataset']['name'] = 'custom_data'
config['dataset']['data_root'] = BASE_DIR
config['dataset']['train_annotation'] = TRAIN_ANN_FILE
config['dataset']['valid_annotation'] = VAL_ANN_FILE

config['dataset']['image_height'] = 32
config['dataset']['image_min_width'] = 32
config['dataset']['image_max_width'] = 800

config['dataloader']['num_workers'] = 0 # Trên Windows nên để 0 để tránh lỗi đa luồng
config['trainer']['batch_size'] = 16    # Card RTX 3050 6GB nên để 16

config['trainer']['epochs'] = 15
config['trainer']['log'] = os.path.join(BASE_DIR, 'log')
config['trainer']['checkpoint'] = os.path.join(BASE_DIR, 'checkpoint')
config['trainer']['export'] = os.path.join(BASE_DIR, 'models', 'transformerocr_finetuned.pth')
config['trainer']['metrics'] = 1000

# Tự động Resume nếu đã có file chạy dở
if os.path.exists(config['trainer']['export']):
    print(f"\n[INFO] Found existing model {config['trainer']['export']}. Resuming training...")
    config['weights'] = config['trainer']['export']
    
os.makedirs(config['trainer']['checkpoint'], exist_ok=True)
os.makedirs(os.path.join(BASE_DIR, 'models'), exist_ok=True)

print("\n--- Step 3: Initialize Model and Start Training ---")
# Ensure old LMDB datasets are removed so they are rebuilt with clean annotations
for lmdb_dir in ['train_custom_data', 'valid_custom_data']:
    lmdb_path = os.path.join(BASE_DIR, lmdb_dir)
    if os.path.exists(lmdb_path):
        print(f"Removing old dataset cache: {lmdb_path}")
        shutil.rmtree(lmdb_path)

# Lưu ý: Cần đảm bảo đang cài numpy < 2.0
trainer = Trainer(config, pretrained=True)
trainer.train()

print("\nTraining completed! Model saved at:", config['trainer']['export'])
