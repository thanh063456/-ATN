#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Dataset Statistics Tool (Step 2.1.5)
Calculates statistics for dataset files and metadata.
Returns DATASET_STATUS = NOT_PROVIDED if dataset is empty.
Does NOT generate fake data or fake numbers.
"""

import os
import json
from pathlib import Path
from typing import Dict, List, Any


def calculate_dataset_statistics(raw_dir: str, metadata_dir: str) -> Dict[str, Any]:
    """
    Calculate statistics over dataset/raw/ and dataset/metadata/inventory.json.
    Returns DATASET_STATUS = NOT_PROVIDED with zero counts if empty.
    """
    stats = {
        "dataset_status": "NOT_PROVIDED",
        "current_version": "v0.1-draft",
        "number_of_documents": 0,
        "number_of_files": 0,
        "file_types": {},
        "file_sizes": {
            "total_bytes": 0,
            "min_bytes": 0,
            "max_bytes": 0,
            "mean_bytes": 0
        },
        "pages": {
            "total_pages": 0,
            "pages_per_doc_mean": 0
        },
        "document_categories": {},
        "resolution": {
            "min_dpi": None,
            "max_dpi": None,
            "distribution": {}
        },
        "quality": {
            "GOOD": 0,
            "ACCEPTABLE": 0,
            "REJECT": 0,
            "UNAUDITED": 0
        },
        "annotation_status": {
            "UNANNOTATED": 0,
            "IN_PROGRESS": 0,
            "ANNOTATED": 0,
            "VERIFIED": 0
        },
        "split_distribution": {
            "TRAIN": 0,
            "VAL": 0,
            "TEST": 0,
            "UNASSIGNED": 0
        }
    }

    if not os.path.isdir(raw_dir):
        return stats

    raw_files = [f for f in os.listdir(raw_dir) if not f.startswith('.')]
    if not raw_files:
        return stats

    # Data is present
    stats["dataset_status"] = "PROVIDED"
    stats["number_of_documents"] = len(raw_files)
    stats["number_of_files"] = len(raw_files)

    # Read inventory.json if present
    inv_path = os.path.join(metadata_dir, "inventory.json")
    records = []
    if os.path.isfile(inv_path):
        try:
            with open(inv_path, "r", encoding="utf-8") as f:
                records = json.load(f)
        except Exception:
            records = []

    total_bytes = 0
    sizes = []

    for fname in raw_files:
        fp = os.path.join(raw_dir, fname)
        ext = Path(fname).suffix.lower()
        stats["file_types"][ext] = stats["file_types"].get(ext, 0) + 1

        if os.path.isfile(fp):
            sz = os.path.getsize(fp)
            sizes.append(sz)
            total_bytes += sz

    if sizes:
        stats["file_sizes"]["total_bytes"] = total_bytes
        stats["file_sizes"]["min_bytes"] = min(sizes)
        stats["file_sizes"]["max_bytes"] = max(sizes)
        stats["file_sizes"]["mean_bytes"] = round(total_bytes / len(sizes), 2)

    # Aggregate inventory records if available
    for r in records:
        doc_type = r.get("document_type") or "UNKNOWN"
        stats["document_categories"][doc_type] = stats["document_categories"].get(doc_type, 0) + 1

        q = r.get("quality") or "UNAUDITED"
        stats["quality"][q] = stats["quality"].get(q, 0) + 1

        ann_s = r.get("annotation_status") or "UNANNOTATED"
        stats["annotation_status"][ann_s] = stats["annotation_status"].get(ann_s, 0) + 1

        sp = r.get("split") or "UNASSIGNED"
        stats["split_distribution"][sp] = stats["split_distribution"].get(sp, 0) + 1

    return stats


if __name__ == "__main__":
    import sys
    sys.stdout.reconfigure(encoding='utf-8')
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    raw_d = os.path.join(base_dir, "dataset", "raw")
    meta_d = os.path.join(base_dir, "dataset", "metadata")
    res = calculate_dataset_statistics(raw_d, meta_d)
    print(json.dumps(res, indent=2, ensure_ascii=False))
