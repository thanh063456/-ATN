#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Dataset Report Generator Tool (Step 2.1.5)
Generates dataset/statistics/dataset_report.json and dataset/statistics/dataset_report.md.
If dataset is empty, records DATASET_STATUS = NOT_PROVIDED and "No dataset available."
Does NOT invent fake numbers.
"""

import os
import json
from datetime import datetime, timezone
from typing import Dict, Any

from dataset_statistics import calculate_dataset_statistics


def generate_dataset_report(raw_dir: str, metadata_dir: str, stats_dir: str) -> Dict[str, str]:
    """
    Generate dataset_report.json and dataset_report.md.
    If raw_dir is empty, records "No dataset available." and DATASET_STATUS = NOT_PROVIDED.
    """
    os.makedirs(stats_dir, exist_ok=True)

    stats = calculate_dataset_statistics(raw_dir, metadata_dir)
    status = stats.get("dataset_status", "NOT_PROVIDED")

    report_json_path = os.path.join(stats_dir, "dataset_report.json")
    report_md_path = os.path.join(stats_dir, "dataset_report.md")

    # 1. Build JSON Report
    json_data = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "dataset_status": status,
        "current_version": stats.get("current_version", "v0.1-draft"),
        "message": "No dataset available." if status == "NOT_PROVIDED" else "Dataset files available.",
        "statistics": stats
    }

    with open(report_json_path, "w", encoding="utf-8") as f:
        json.dump(json_data, f, indent=2, ensure_ascii=False)

    # 2. Build Markdown Report
    if status == "NOT_PROVIDED":
        md_content = """# Dataset Summary Report

**DATASET_STATUS**: `NOT_PROVIDED`  
**Current Version**: `v0.1-draft`  
**Generated At**: {timestamp}  

> **Notice**: No dataset available. No raw document files have been uploaded to `dataset/raw/`.

---

## Statistics Summary

- **Total Documents**: 0
- **Total Files**: 0
- **Total Pages**: 0
- **Total Line Crops**: 0
- **Train / Val / Test Split**: 0 / 0 / 0

---
*Generated automatically by `scripts/dataset_report.py`.*
""".format(timestamp=datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC"))
    else:
        md_content = """# Dataset Summary Report

**DATASET_STATUS**: `{status}`  
**Current Version**: `{version}`  
**Generated At**: {timestamp}  

---

## Key Metrics

| Metric | Value |
|--------|-------|
| Total Documents | {num_docs} |
| Total Files | {num_files} |
| Total Storage Size | {total_size_mb:.2f} MB |
| Total Pages | {total_pages} |

---

## File Types Distribution

{file_types_table}

---

## Document Categories Breakdown

{categories_table}

---

## Train / Validation / Test Split

| Split Set | Document Count |
|-----------|----------------|
| Train (80%) | {train_cnt} |
| Validation (10%) | {val_cnt} |
| Test (10%) | {test_cnt} |
| Unassigned | {unassigned_cnt} |

---
*Generated automatically by `scripts/dataset_report.py`.*
""".format(
            status=status,
            version=stats.get("current_version", "v0.1-draft"),
            timestamp=datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC"),
            num_docs=stats["number_of_documents"],
            num_files=stats["number_of_files"],
            total_size_mb=stats["file_sizes"]["total_bytes"] / (1024 * 1024),
            total_pages=stats["pages"]["total_pages"],
            file_types_table="\n".join([f"- **{ext}**: {cnt} files" for ext, cnt in stats["file_types"].items()]) or "No files",
            categories_table="\n".join([f"- **{cat}**: {cnt} docs" for cat, cnt in stats["document_categories"].items()]) or "No categories",
            train_cnt=stats["split_distribution"]["TRAIN"],
            val_cnt=stats["split_distribution"]["VAL"],
            test_cnt=stats["split_distribution"]["TEST"],
            unassigned_cnt=stats["split_distribution"]["UNASSIGNED"],
        )

    with open(report_md_path, "w", encoding="utf-8") as f:
        f.write(md_content)

    return {
        "json_report": report_json_path,
        "md_report": report_md_path
    }


if __name__ == "__main__":
    import sys
    sys.stdout.reconfigure(encoding='utf-8')
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    raw_d = os.path.join(base_dir, "dataset", "raw")
    meta_d = os.path.join(base_dir, "dataset", "metadata")
    stats_d = os.path.join(base_dir, "dataset", "statistics")
    res = generate_dataset_report(raw_d, meta_d, stats_d)
    print(f"Report JSON: {res['json_report']}")
    print(f"Report MD:   {res['md_report']}")
