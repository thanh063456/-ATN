#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Dataset Input Validator Tool (Step 2.1.5)
Validates raw document files in dataset/raw/ without modifying or deleting any files.
Handles empty dataset/raw/ gracefully with DATASET_STATUS = NOT_PROVIDED.
"""

import os
import re
import hashlib
import json
from pathlib import Path
from typing import Dict, List, Any, Optional

SUPPORTED_EXTENSIONS = {'.pdf', '.jpg', '.jpeg', '.png', '.tiff'}
MAX_FILE_SIZE_BYTES = 50 * 1024 * 1024  # 50MB

# Pattern: DOC_{TYPE}_{YYYYMMDD}_{UUID8}.{ext}
CONVENTION_PATTERN = re.compile(
    r'^DOC_[A-Z0-9_]+_\d{8}_[a-fA-F0-9]{8}\.(pdf|jpg|jpeg|png|tiff)$',
    re.IGNORECASE
)

# Magic bytes for corruption checks
MAGIC_BYTES = {
    '.pdf': b'%PDF',
    '.png': b'\x89PNG\r\n\x1a\n',
    '.jpg': b'\xff\xd8',
    '.jpeg': b'\xff\xd8',
    '.tiff': (b'II*\x00', b'MM\x00*')
}


def check_file_extension(filename: str) -> bool:
    """Verify if the file extension is supported."""
    ext = Path(filename).suffix.lower()
    return ext in SUPPORTED_EXTENSIONS


def check_file_size(filepath: str, max_bytes: int = MAX_FILE_SIZE_BYTES) -> Dict[str, Any]:
    """Verify file size (must be > 0 and <= max_bytes)."""
    try:
        size = os.path.getsize(filepath)
        if size == 0:
            return {"valid": False, "size_bytes": 0, "error": "FILE_EMPTY"}
        if size > max_bytes:
            return {"valid": False, "size_bytes": size, "error": "FILE_TOO_LARGE"}
        return {"valid": True, "size_bytes": size, "error": None}
    except Exception as e:
        return {"valid": False, "size_bytes": 0, "error": f"CANNOT_READ_SIZE: {str(e)}"}


def check_filename_convention(filename: str) -> bool:
    """Check if the filename follows the project naming convention."""
    return bool(CONVENTION_PATTERN.match(filename))


def check_file_corrupted(filepath: str) -> bool:
    """Basic magic bytes check to detect severely corrupted files."""
    ext = Path(filepath).suffix.lower()
    if ext not in MAGIC_BYTES:
        return False  # Cannot check magic bytes, assume not corrupted
    
    expected = MAGIC_BYTES[ext]
    try:
        with open(filepath, 'rb') as f:
            header = f.read(16)
            if isinstance(expected, tuple):
                return not any(header.startswith(sig) for sig in expected)
            return not header.startswith(expected)
    except Exception:
        return True  # Cannot open file, mark as corrupted


def calculate_file_hash(filepath: str) -> str:
    """Calculate SHA256 hash of a file for duplicate detection."""
    sha256 = hashlib.sha256()
    try:
        with open(filepath, 'rb') as f:
            while chunk := f.read(8192):
                sha256.update(chunk)
        return sha256.hexdigest()
    except Exception:
        return ""


def find_duplicate_files(raw_dir: str) -> Dict[str, List[str]]:
    """Detect duplicate files by SHA256 content hash."""
    hashes: Dict[str, List[str]] = {}
    if not os.path.isdir(raw_dir):
        return {}

    for root, _, files in os.walk(raw_dir):
        for fname in files:
            if fname.startswith('.'):
                continue
            fp = os.path.join(root, fname)
            fhash = calculate_file_hash(fp)
            if fhash:
                hashes.setdefault(fhash, []).append(fp)

    # Return only hashes with > 1 file
    return {h: paths for h, paths in hashes.items() if len(paths) > 1}


def validate_raw_dataset(raw_dir: str) -> Dict[str, Any]:
    """
    Validate all files in dataset/raw/.
    Does NOT modify or delete any files.
    Handles empty raw_dir with DATASET_STATUS = NOT_PROVIDED.
    """
    report = {
        "dataset_status": "NOT_PROVIDED",
        "total_files": 0,
        "valid_files": 0,
        "invalid_files": 0,
        "duplicates_count": 0,
        "errors": [],
        "warnings": [],
        "file_details": []
    }

    if not os.path.isdir(raw_dir):
        report["warnings"].append(f"Directory not found: {raw_dir}")
        return report

    files = [f for f in os.listdir(raw_dir) if not f.startswith('.')]
    if not files:
        report["warnings"].append("dataset/raw/ is empty. DATASET_STATUS = NOT_PROVIDED.")
        return report

    report["dataset_status"] = "PROVIDED"
    report["total_files"] = len(files)

    for fname in sorted(files):
        fp = os.path.join(raw_dir, fname)
        if not os.path.isfile(fp):
            continue

        file_info = {
            "filename": fname,
            "path": fp,
            "extension": Path(fname).suffix.lower(),
            "valid": True,
            "issues": []
        }

        # 1. Extension check
        if not check_file_extension(fname):
            file_info["valid"] = False
            file_info["issues"].append("UNSUPPORTED_EXTENSION")
            report["errors"].append(f"File '{fname}': Unsupported extension '{file_info['extension']}'")

        # 2. Size check
        size_res = check_file_size(fp)
        file_info["size_bytes"] = size_res["size_bytes"]
        if not size_res["valid"]:
            file_info["valid"] = False
            file_info["issues"].append(size_res["error"])
            report["errors"].append(f"File '{fname}': {size_res['error']}")

        # 3. Filename convention check (Warning only)
        if not check_filename_convention(fname):
            file_info["issues"].append("NON_CONVENTION_FILENAME")
            report["warnings"].append(f"File '{fname}': Filename does not match convention DOC_TYPE_YYYYMMDD_UUID8.ext")

        # 4. Corruption check
        if check_file_corrupted(fp):
            file_info["valid"] = False
            file_info["issues"].append("CORRUPTED_HEADER")
            report["errors"].append(f"File '{fname}': Header corrupted or unreadable")

        if file_info["valid"]:
            report["valid_files"] += 1
        else:
            report["invalid_files"] += 1

        report["file_details"].append(file_info)

    # 5. Duplicate check
    duplicates = find_duplicate_files(raw_dir)
    report["duplicates_count"] = len(duplicates)
    for fhash, paths in duplicates.items():
        rel_paths = [os.path.basename(p) for p in paths]
        report["warnings"].append(f"Duplicate content detected across files: {rel_paths} (SHA256: {fhash[:8]}...)")

    return report


if __name__ == "__main__":
    import sys
    sys.stdout.reconfigure(encoding='utf-8')
    raw_directory = os.path.join(os.path.dirname(__file__), "..", "dataset", "raw")
    result = validate_raw_dataset(raw_directory)
    print(json.dumps(result, indent=2, ensure_ascii=False))
