"""
backend/app/services/trocr_service.py — TrOCR Service

Điều phối quy trình OCR chuyên biệt cho Microsoft TrOCR:
  - Tách dòng ảnh bằng morphological line segmentation
  - Gửi các dòng qua TrOCREngine (Vision Transformer)
  - Trả về 3-tuple: (raw_text, processed_text, confidence_score)
  - Báo lỗi EngineUnavailableError khi TrOCR không chạy được (KHÔNG fallback sang VietOCR).
"""
from __future__ import annotations

import io
import re
import time
import unicodedata
from typing import Any

import numpy as np
from loguru import logger
from PIL import Image

from app.core.exceptions import EngineUnavailableError

try:
    import cv2
except ImportError:
    cv2 = None

try:
    import pymupdf
except ImportError:
    try:
        import fitz as pymupdf
    except ImportError:
        pymupdf = None


class TrOCRService:
    """Service chuyên biệt điều phối pipeline cho Microsoft TrOCR."""

    VERSION = "trocr-base-printed"

    def __init__(self) -> None:
        self._settings = None

    def _get_settings(self):
        if self._settings is None:
            try:
                from app.core.config import settings
                self._settings = settings
            except Exception:
                pass
        return self._settings

    @staticmethod
    def _trocr():
        from app.services.trocr_engine import trocr_engine
        return trocr_engine

    # ── Tiền xử lý ảnh ────────────────────────────────────────────────────────
    def preprocess_image(self, pil_image: Image.Image) -> Image.Image:
        """
        Tiền xử lý ảnh toàn trang:
        Grayscale → CLAHE (tăng tương phản) → GaussianBlur (khử nhiễu nhẹ).
        """
        if cv2 is None:
            return pil_image
        try:
            img_np = np.array(pil_image)
            gray = cv2.cvtColor(img_np, cv2.COLOR_RGB2GRAY) if len(img_np.shape) == 3 else img_np
            clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
            enhanced = clahe.apply(gray)
            blurred = cv2.GaussianBlur(enhanced, (3, 3), 0)
            return Image.fromarray(blurred)
        except Exception as exc:
            logger.debug("preprocess_image fallback: {err}", err=str(exc))
            return pil_image

    def preprocess_handwriting(self, pil_image: Image.Image) -> Image.Image:
        """
        Tiền xử lý từng dòng ảnh:
        Upscale nếu < 48px cao → CLAHE → Padding chống cắt dấu tiếng Việt.
        """
        if cv2 is None:
            return pil_image
        try:
            img_np = np.array(pil_image)
            gray = cv2.cvtColor(img_np, cv2.COLOR_RGB2GRAY) if len(img_np.shape) == 3 else img_np

            h, w = gray.shape[:2]
            if h < 48 and h > 0:
                scale = min(2.0, max(1.5, 56.0 / float(h)))
                gray = cv2.resize(gray, (0, 0), fx=scale, fy=scale, interpolation=cv2.INTER_LINEAR)

            clahe = cv2.createCLAHE(clipLimit=1.5, tileGridSize=(4, 4))
            enhanced = clahe.apply(gray)
            padded = cv2.copyMakeBorder(enhanced, 4, 4, 6, 6, cv2.BORDER_CONSTANT, value=255)
            return Image.fromarray(padded)
        except Exception as exc:
            logger.debug("preprocess_handwriting fallback: {err}", err=str(exc))
            return pil_image

    # ── Tách dòng ─────────────────────────────────────────────────────────────
    def segment_lines(self, pil_image: Image.Image) -> list[Image.Image]:
        """Tách ảnh thành danh sách ảnh dòng đơn lẻ."""
        if cv2 is None:
            return [pil_image]

        try:
            img_np = np.array(pil_image)
            gray = cv2.cvtColor(img_np, cv2.COLOR_RGB2GRAY) if len(img_np.shape) == 3 else img_np.copy()
            h_img, w_img = gray.shape[:2]

            _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)

            kw = max(40, w_img // 20)
            kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (kw, 1))
            dilated = cv2.dilate(binary, kernel, iterations=1)

            contours, _ = cv2.findContours(dilated, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            raw_boxes = [cv2.boundingRect(c) for c in contours]

            valid_boxes = [
                (x, y, w, h) for x, y, w, h in raw_boxes
                if w >= 15 and 6 <= h <= h_img * 0.6
            ]

            valid_boxes.sort(key=lambda b: (b[1] // 20, b[0]))

            line_images: list[Image.Image] = []
            for x, y, w, h in valid_boxes:
                t = max(0, y - 4)
                b = min(h_img, y + h + 4)
                lo = max(0, x - 3)
                ro = min(w_img, x + w + 3)
                line_images.append(Image.fromarray(img_np[t:b, lo:ro]))

            return line_images if line_images else [pil_image]
        except Exception as exc:
            logger.warning("TrOCR segment_lines error: {err}", err=str(exc))
            return [pil_image]

    # ── Lọc nhiễu ─────────────────────────────────────────────────────────────
    @staticmethod
    def _is_noise_line(line: str) -> bool:
        """Kiểm tra dòng nhiễu."""
        s = line.strip()
        if not s:
            return True
        if len(s) <= 2 and not s.isalnum():
            return True
        return False

    # ── Hậu xử lý ─────────────────────────────────────────────────────────────
    def post_process_vietnamese(self, text: str) -> str:
        """Gọi pipeline hậu xử lý tiếng Việt dùng chung."""
        try:
            from app.services.text_postprocessing import post_process_vietnamese as _pp
            return _pp(text)
        except ImportError:
            return unicodedata.normalize("NFC", text).strip()

    # ── Heuristic confidence ───────────────────────────────────────────────────
    def heuristic_quality_score(self, text: str) -> float:
        """Ước lượng chất lượng OCR từ tỷ lệ ký tự rác."""
        if not text or len(text.strip()) < 10:
            return 0.60
        base = 0.90
        suspicious = len(re.findall(r'[%~^|<>{}\\[\\]@#$*]', text))
        char_penalty = min(0.15, (suspicious / max(len(text), 1)) * 5.0)
        return round(max(0.60, min(0.98, base - char_penalty)), 2)

    # ── OCR 1 trang ───────────────────────────────────────────────────────────
    def _ocr_image(self, image: Image.Image) -> tuple[str, str]:
        """
        OCR 1 ảnh trang: trả về (raw_text, processed_text).
        """
        processed_img = self.preprocess_image(image)
        line_images = self.segment_lines(processed_img)

        # Giới hạn dòng để TrOCR CPU không bị nghẽn quá lâu
        MAX_LINES_TROCR = 60
        if len(line_images) > MAX_LINES_TROCR:
            line_images = line_images[:MAX_LINES_TROCR]

        line_results = self._trocr().ocr_lines(line_images, preprocess_fn=self.preprocess_handwriting)
        valid_lines = [t for t, _ in line_results if not self._is_noise_line(t)]
        raw_text = "\n".join(valid_lines).strip()
        processed_text = self.post_process_vietnamese(raw_text) if raw_text else ""
        return raw_text, processed_text

    # ── OCR toàn file ─────────────────────────────────────────────────────────
    def extract_text_from_file(
        self, file_bytes: bytes, file_type: str, engine: str | None = None
    ) -> tuple[str, str, float]:
        """
        Trích xuất toàn văn từ file PDF hoặc Ảnh bằng Microsoft TrOCR.

        Returns:
            (raw_text, processed_text, confidence_score)
        """
        file_ext = file_type.lower().replace(".", "")
        _render_dpi = 150

        raw_pages: list[str] = []
        proc_pages: list[str] = []

        if file_ext == "pdf":
            if pymupdf is None:
                raise EngineUnavailableError("trocr", "PyMuPDF chưa được cài đặt để render PDF.")
            try:
                doc = pymupdf.open(stream=file_bytes, filetype="pdf")
                total = len(doc)
                for idx, page in enumerate(doc):
                    t0 = time.time()
                    pix = page.get_pixmap(dpi=_render_dpi)
                    page_img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
                    p_raw, p_proc = self._ocr_image(page_img)
                    logger.info("TrOCR trang {i}/{t} | {s:.1f}s", i=idx + 1, t=total, s=time.time() - t0)
                    if p_raw:
                        raw_pages.append(p_raw)
                    if p_proc:
                        proc_pages.append(p_proc)
            except Exception as exc:
                if isinstance(exc, EngineUnavailableError):
                    raise
                logger.error("TrOCR PDF extraction error: {err}", err=str(exc))
                raise EngineUnavailableError("trocr", f"Lỗi OCR PDF bằng TrOCR: {exc}") from exc
        else:
            try:
                image = Image.open(io.BytesIO(file_bytes)).convert("RGB")
                p_raw, p_proc = self._ocr_image(image)
                if p_raw:
                    raw_pages.append(p_raw)
                if p_proc:
                    proc_pages.append(p_proc)
            except Exception as exc:
                if isinstance(exc, EngineUnavailableError):
                    raise
                logger.error("TrOCR image extraction error: {err}", err=str(exc))
                raise EngineUnavailableError("trocr", f"Lỗi OCR ảnh bằng TrOCR: {exc}") from exc

        raw_text = "\n\n".join(raw_pages)
        processed_text = "\n\n".join(proc_pages)
        confidence = self.heuristic_quality_score(processed_text) if processed_text else 0.0

        return raw_text, processed_text, confidence

    # ── So sánh engine ────────────────────────────────────────────────────────
    def compare_ocr_engines(self, file_bytes: bytes, file_type: str) -> dict[str, Any]:
        """So sánh hiệu năng VietOCR / TrOCR / Tesseract độc lập."""
        from app.services.vietocr_service import vietocr_service
        from app.services.tesseract_service import tesseract_service

        results: dict[str, Any] = {}
        for eng_key, eng_name in [
            ("vietocr", "VietOCR (vgg_transformer)"),
            ("trocr", "Microsoft TrOCR (Vision Transformer)"),
            ("tesseract", "Tesseract 5 (LSTM Baseline)"),
        ]:
            t0 = time.time()
            try:
                if eng_key == "tesseract":
                    raw, proc, conf = tesseract_service.extract_text_from_file(file_bytes, file_type)
                elif eng_key == "trocr":
                    raw, proc, conf = self.extract_text_from_file(file_bytes, file_type)
                else:
                    raw, proc, conf = vietocr_service.extract_text_from_file(file_bytes, file_type, "vietocr")

                text = proc or raw
                results[eng_key] = {
                    "engine_name": eng_name,
                    "text": text,
                    "raw_text": raw,
                    "processed_text": proc,
                    "confidence": conf,
                    "inference_time_seconds": round(time.time() - t0, 3),
                    "char_count": len(text),
                    "word_count": len(text.split()),
                    "status": "SUCCESS" if text else "EMPTY",
                }
            except Exception as exc:
                results[eng_key] = {
                    "engine_name": eng_name,
                    "text": "",
                    "raw_text": "",
                    "processed_text": "",
                    "confidence": 0.0,
                    "inference_time_seconds": round(time.time() - t0, 3),
                    "status": f"FAILED: {exc}",
                }
        return results

    def extract_metadata(self, text: str) -> dict[str, Any]:
        try:
            from app.services.vietocr_service import vietocr_service
            return vietocr_service.extract_metadata(text)
        except Exception:
            return {}


# Singleton
trocr_service = TrOCRService()
