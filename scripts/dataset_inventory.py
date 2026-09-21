#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Dataset Inventory Generator Tool (Step 2.1.5)
Generates dataset/metadata/inventory.json and dataset/metadata/inventory.csv.
If fields cannot be determined or dataset is empty, values remain None/null.
Does NOT invent or guess values.
"""

import os
import csv
import json
import uuid
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional

FIELDNAMES = [
    "document_id",
    "source_file",
    "file_type",
    "file_size",
    "document_type",
    "page_count",
    "resolution",
    "language",
    "quality",
    "source",
    "annotation_status",
    "split",
    "created_at"
]


def extract_doc_type_from_filename(filename: str) -> Optional[str]:
    """Attempt to extract document_type if filename follows convention DOC_{TYPE}_..."""
    parts = filename.split("_")
    if len(parts) >= 2 and parts[0].upper() == "DOC":
        return parts[1].upper()
    return None


def generate_inventory_records(raw_dir: str) -> List[Dict[str, Any]]:
    """
    Generate inventory records for files in dataset/raw/.
    If raw_dir is empty or does not exist, returns empty list [].
    Fields that cannot be determined remain None.
    """
    records: List[Dict[str, Any]] = []

    if not os.path.isdir(raw_dir):
        return records

    files = [f for f in os.listdir(raw_dir) if not f.startswith('.')]
    if not files:
        return records

    for fname in sorted(files):
        fp = os.path.join(raw_dir, fname)
        if not os.path.isfile(fp):
            continue

        ext = Path(fname).suffix.lower().replace(".", "").upper()
        try:
            fsize = os.path.getsize(fp)
            ctime = os.path.getctime(fp)
            created_iso = datetime.fromtimestamp(ctime, tz=timezone.utc).isoformat()
        except Exception:
            fsize = None
            created_iso = None

        doc_type = extract_doc_type_from_filename(fname)

        record = {
            "document_id": str(uuid.uuid4()),
            "source_file": fname,
            "file_type": ext,
            "file_size": fsize,
            "document_type": doc_type,  # None if not adhering to convention
            "page_count": None,        # Determined during Step 2.2 processing
            "resolution": None,        # Determined during Step 2.2 processing
            "language": "vi",          # Vietnamese
            "quality": None,           # Determined during Step 2.2 quality audit
            "source": "PHONG_CTSV_SCAN",
            "annotation_status": "UNANNOTATED",
            "split": "UNASSIGNED",
            "created_at": created_iso
        }
        records.append(record)

    return records


def export_inventory(records: List[Dict[str, Any]], metadata_dir: str) -> Dict[str, str]:
    """Export inventory records to JSON and CSV files."""
    os.makedirs(metadata_dir, exist_ok=True)
    json_path = os.path.join(metadata_dir, "inventory.json")
    csv_path = os.path.join(metadata_dir, "inventory.csv")

    # Write JSON
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(records, f, indent=2, ensure_ascii=False)

    # Write CSV
    with open(csv_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        writer.writeheader()
        for r in records:
            # Convert None to empty string for CSV output
            csv_row = {k: ("" if v is None else v) for k, v in r.items()}
            writer.writerow(csv_row)

    return {"json_path": json_path, "csv_path": csv_path}


def generate_and_save_inventory(raw_dir: str, metadata_dir: str) -> Dict[str, Any]:
    """Orchestrate inventory generation and export."""
    records = generate_inventory_records(raw_dir)
    paths = export_inventory(records, metadata_dir)
    return {
        "count": len(records),
        "json_file": paths["json_path"],
        "csv_file": paths["csv_path"]
    }


if __name__ == "__main__":
    import sys
    sys.stdout.reconfigure(encoding='utf-8')
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    raw_d = os.path.join(base_dir, "dataset", "raw")
    meta_d = os.path.join(base_dir, "dataset", "metadata")
    res = generate_and_save_inventory(raw_d, meta_d)
    print(f"Generated inventory for {res['count']} records.")
    print(f"JSON: {res['json_file']}")
    print(f"CSV:  {res['csv_file']}")
