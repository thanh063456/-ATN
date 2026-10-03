"""
backend/app/services/ocr_service.py — Compatibility alias for vietocr_service
"""
from app.services.vietocr_service import VietOCRService, vietocr_service

OCRService = VietOCRService
ocr_service = vietocr_service

__all__ = ["OCRService", "ocr_service"]
