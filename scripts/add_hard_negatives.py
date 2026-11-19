#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
scripts/add_hard_negatives.py — Inject hard negative samples into the training set.
"""
import os
import random
from pathlib import Path

def main():
    train_file = Path("dataset/annotations/annotation_train.txt")
    if not train_file.exists():
        print("No annotation_train.txt found.")
        return

    lines = train_file.read_text(encoding="utf-8").splitlines()
    
    # Identify hard negative paths or simulate them
    hard_negatives = []
    for line in lines:
        if "\t" not in line:
            continue
        path, label = line.split("\t", 1)
        # Select 5% of data to act as hard negatives (e.g. noise lines)
        if random.random() < 0.05:
            hard_negatives.append(f"{path}\t---")
            
    if hard_negatives:
        with open(train_file, "a", encoding="utf-8") as f:
            for hn in hard_negatives:
                f.write(f"{hn}\n")
        print(f"Added {len(hard_negatives)} hard negative samples to {train_file}.")

if __name__ == "__main__":
    main()
