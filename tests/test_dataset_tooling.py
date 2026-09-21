#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Unit Tests for Dataset Tooling (Step 2.1.5)
Tests validator, inventory generator, statistics calculator, and report generator.
All tests pass cleanly when dataset/raw/ is empty.
"""

import os
import sys
import json
import shutil
import tempfile
import unittest
from pathlib import Path

# Add scripts directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "scripts")))

from dataset_validator import (
    check_file_extension,
    check_file_size,
    check_filename_convention,
    check_file_corrupted,
    find_duplicate_files,
    validate_raw_dataset,
)
from dataset_inventory import (
    generate_inventory_records,
    export_inventory,
    generate_and_save_inventory,
)
from dataset_statistics import calculate_dataset_statistics
from dataset_report import generate_dataset_report


class TestFileValidation(unittest.TestCase):

    def test_extension_validation(self):
        """Test supported vs unsupported file extensions."""
        self.assertTrue(check_file_extension("document.pdf"))
        self.assertTrue(check_file_extension("IMAGE.JPG"))
        self.assertTrue(check_file_extension("photo.jpeg"))
        self.assertTrue(check_file_extension("scan.png"))
        self.assertTrue(check_file_extension("file.tiff"))
        self.assertFalse(check_file_extension("script.py"))
        self.assertFalse(check_file_extension("archive.zip"))
        self.assertFalse(check_file_extension("text.txt"))

    def test_filename_convention(self):
        """Test DOC_TYPE_YYYYMMDD_UUID8.ext naming convention."""
        self.assertTrue(check_filename_convention("DOC_DON_NGHI_HOC_20260808_a1b2c3d4.pdf"))
        self.assertTrue(check_filename_convention("DOC_KY_LUAT_20260101_12345678.png"))
        self.assertFalse(check_filename_convention("random_file.pdf"))
        self.assertFalse(check_filename_convention("DOC_INVALID.pdf"))

    def test_file_size_validation(self):
        """Test size validation for empty and non-empty temp files."""
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp_name = tmp.name
        try:
            # Empty file size test
            res_empty = check_file_size(tmp_name)
            self.assertFalse(res_empty["valid"])
            self.assertEqual(res_empty["error"], "FILE_EMPTY")

            # Write content
            with open(tmp_name, "wb") as f:
                f.write(b"Hello World")
            res_valid = check_file_size(tmp_name)
            self.assertTrue(res_valid["valid"])
            self.assertEqual(res_valid["size_bytes"], 11)
        finally:
            if os.path.exists(tmp_name):
                os.remove(tmp_name)

    def test_duplicate_detection(self):
        """Test content duplicate detection via hash."""
        temp_dir = tempfile.mkdtemp()
        try:
            file1 = os.path.join(temp_dir, "file1.png")
            file2 = os.path.join(temp_dir, "file2.png")
            file3 = os.path.join(temp_dir, "file3.png")

            content = b"Exact Duplicate Content"
            with open(file1, "wb") as f: f.write(content)
            with open(file2, "wb") as f: f.write(content)
            with open(file3, "wb") as f: f.write(b"Different Content")

            dups = find_duplicate_files(temp_dir)
            self.assertEqual(len(dups), 1)
            dup_paths = list(dups.values())[0]
            self.assertEqual(len(dup_paths), 2)
            self.assertIn(file1, dup_paths)
            self.assertIn(file2, dup_paths)
        finally:
            shutil.rmtree(temp_dir)


class TestEmptyDatasetHandling(unittest.TestCase):

    def setUp(self):
        self.temp_raw_dir = tempfile.mkdtemp()
        self.temp_meta_dir = tempfile.mkdtemp()
        self.temp_stats_dir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.temp_raw_dir)
        shutil.rmtree(self.temp_meta_dir)
        shutil.rmtree(self.temp_stats_dir)

    def test_validate_empty_dataset(self):
        """Validator should handle empty dataset/raw/ cleanly."""
        res = validate_raw_dataset(self.temp_raw_dir)
        self.assertEqual(res["dataset_status"], "NOT_PROVIDED")
        self.assertEqual(res["total_files"], 0)
        self.assertIn("empty", res["warnings"][0].lower())

    def test_inventory_empty_dataset(self):
        """Inventory generator should handle empty dataset/raw/."""
        records = generate_inventory_records(self.temp_raw_dir)
        self.assertEqual(records, [])

        res = generate_and_save_inventory(self.temp_raw_dir, self.temp_meta_dir)
        self.assertEqual(res["count"], 0)

        with open(res["json_file"], "r", encoding="utf-8") as f:
            data = json.load(f)
            self.assertEqual(data, [])

        with open(res["csv_file"], "r", encoding="utf-8") as f:
            lines = f.readlines()
            self.assertEqual(len(lines), 1)  # Header only

    def test_statistics_empty_dataset(self):
        """Statistics calculator should return DATASET_STATUS = NOT_PROVIDED for empty dataset."""
        stats = calculate_dataset_statistics(self.temp_raw_dir, self.temp_meta_dir)
        self.assertEqual(stats["dataset_status"], "NOT_PROVIDED")
        self.assertEqual(stats["number_of_documents"], 0)
        self.assertEqual(stats["number_of_files"], 0)

    def test_report_empty_dataset(self):
        """Report generator should output 'No dataset available.' for empty dataset."""
        paths = generate_dataset_report(self.temp_raw_dir, self.temp_meta_dir, self.temp_stats_dir)
        
        with open(paths["json_report"], "r", encoding="utf-8") as f:
            jreport = json.load(f)
            self.assertEqual(jreport["dataset_status"], "NOT_PROVIDED")
            self.assertEqual(jreport["message"], "No dataset available.")

        with open(paths["md_report"], "r", encoding="utf-8") as f:
            md_content = f.read()
            self.assertIn("NOT_PROVIDED", md_content)
            self.assertIn("No dataset available.", md_content)


if __name__ == "__main__":
    unittest.main()
