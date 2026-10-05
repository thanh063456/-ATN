"""
backend/tests/test_tesseract_service.py
"""
import pytest
from unittest.mock import patch
from app.services.tesseract_service import tesseract_service
from PIL import Image

def test_tesseract_noise_filtering():
    """T3 strings with low conf or high non-letter ratio must be dropped."""
    # Mock image_to_data to return specific noise lines
    mock_data = {
        'level': [5, 5, 5, 5, 5, 5],
        'page_num': [1, 1, 1, 1, 1, 1],
        'block_num': [1, 1, 2, 2, 3, 3],
        'par_num': [1, 1, 1, 1, 1, 1],
        'line_num': [1, 1, 1, 1, 1, 1],
        'word_num': [1, 2, 1, 2, 1, 2],
        'left': [0, 10, 0, 10, 0, 10],
        'top': [0, 0, 10, 10, 20, 20],
        'width': [10, 10, 10, 10, 10, 10],
        'height': [10, 10, 10, 10, 10, 10],
        'conf': [
            30, 35,  # Low conf < 40 -> dropped
            35, 30,  # Junk strings usually have low conf < 40
            80, 80   # Good conf and good letters
        ],
        'text': [
            "H", "B",         # Low conf
            "M ˆ 4", "Ì Ấ n", # Junk
            "Bước", "1"        # Good line
        ]
    }
    
    with patch("pytesseract.image_to_data", return_value=mock_data):
        # We need to bypass check_availability because it might fail if Tesseract is not installed
        with patch.object(tesseract_service, "check_availability"):
            with patch.object(tesseract_service, "preprocess_for_tesseract", return_value=Image.new("RGB", (10,10))):
                result = tesseract_service._ocr_image(Image.new("RGB", (100, 100)))
                
                assert "H B" not in result
                assert "M ˆ 4 Ì Ấ n" not in result
                assert "Bước 1" in result
