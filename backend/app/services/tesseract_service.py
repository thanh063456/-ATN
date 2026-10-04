"""
backend/app/services/tesseract_service.py — Tesseract 5 OCR Engine

Wrapper độc lập quanh pytesseract để cung cấp cùng interface với VietOCRService:
  - extract_text_from_file(file_bytes, file_type, engine) → (raw_text, processed_text, confidence)
  - Render PDF bằng PyMuPDF (dpi 200).
  - Chạy pytesseract với lang="vie", oem=1, psm=4.
  - Tự động phát hiện tesseract_cmd và TESSDATA_PREFIX trên Windows / Linux.
  - Nếu thiếu thư viện / binary / vie.traineddata thì raise EngineUnavailableError (KHÔNG fallback sang VietOCR).
"""
from __future__ import annotations

import io
import os
import platform
import time
import unicodedata
from typing import Any

from loguru import logger
from PIL import Image

from app.core.exceptions import EngineUnavailableError

try:
    import pytesseract
    # Cấu hình đường dẫn Tesseract trên Windows nếu chưa có trong PATH
    if platform.system() == "Windows":
        for _candidate in [
            r"C:\Program Files\Tesseract-OCR\tesseract.exe",
            r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
        ]:
            if os.path.exists(_candidate):
                pytesseract.pytesseract.tesseract_cmd = _candidate
                break
    # Trỏ TESSDATA_PREFIX về thư mục chứa model ngôn ngữ cục bộ
    _local_tessdata = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "../../../tessdata")
    )
    if os.path.exists(_local_tessdata):
        os.environ.setdefault("TESSDATA_PREFIX", _local_tessdata)
except ImportError:
    pytesseract = None  # type: ignore[assignment]

try:
    import cv2
    import numpy as np
except ImportError:
    cv2 = None  # type: ignore[assignment]
    np = None   # type: ignore[assignment]

try:
    import pymupdf
except ImportError:
    try:
        import fitz as pymupdf  # type: ignore[no-redef]
    except ImportError:
        pymupdf = None  # type: ignore[assignment]


class TesseractService:
    """
    OCR engine dùng Tesseract (LSTM).

    Interface tương thích:
      extract_text_from_file(file_bytes, file_type, engine=None) → (raw_text, processed_text, confidence)
    """

    LANG    = "vie"
    PSM     = 4   # Assume a single column of text of variable sizes
    OEM     = 1   # Neural nets LSTM only
    CONFIG  = f"--psm {PSM} --oem {OEM}"
    VERSION = "5.3.0"

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

    # ── Kiểm tra khả dụng ─────────────────────────────────────────────────────
    def check_availability(self) -> None:
        """
        Kiểm tra Tesseract binary và traineddata.
        Raise EngineUnavailableError nếu không khả dụng.
        """
        if pytesseract is None:
            raise EngineUnavailableError("tesseract", "Thư viện 'pytesseract' chưa được cài đặt.")
        try:
            ver = pytesseract.get_tesseract_version()
            self.VERSION = str(ver)
        except Exception as exc:
            raise EngineUnavailableError(
                "tesseract",
                f"Không tìm thấy binary Tesseract OCR thực thi được: {exc}. Vui lòng cài đặt Tesseract-OCR."
            ) from exc

        # Kiểm tra ngôn ngữ 'vie'
        try:
            langs = pytesseract.get_languages()
            if "vie" not in langs:
                raise EngineUnavailableError(
                    "tesseract",
                    f"Thiếu file 'vie.traineddata' trong TESSDATA ({os.environ.get('TESSDATA_PREFIX', 'default')})."
                )
        except Exception as exc:
            if isinstance(exc, EngineUnavailableError):
                raise
            logger.warning("Không thể liệt kê danh sách ngôn ngữ Tesseract: {err}", err=str(exc))

    def is_available(self) -> bool:
        """Kiểm tra boolean Tesseract có sẵn sàng không."""
        try:
            self.check_availability()
            return True
        except Exception:
            return False

    # ── Tiền xử lý ảnh ────────────────────────────────────────────────────────
    def preprocess_for_tesseract(self, pil_image: Image.Image) -> Image.Image:
        """
        Tiền xử lý ảnh trước khi đưa vào Tesseract:
        - Grayscale
        - CLAHE (tăng tương phản cục bộ)
        - Otsu threshold
        - Upscale nếu < 300 DPI-equivalent
        """
        if cv2 is None or np is None:
            return pil_image
        try:
            img_np = np.array(pil_image)
            gray = (
                cv2.cvtColor(img_np, cv2.COLOR_RGB2GRAY)
                if len(img_np.shape) == 3
                else img_np.copy()
            )
            h, w = gray.shape[:2]

            # Upscale nếu ảnh quá nhỏ (Tesseract cần ~300 DPI)
            if w < 1200 and w > 0:
                scale = max(1.5, 1800 / float(w))
                gray = cv2.resize(
                    gray, (int(w * scale), int(h * scale)),
                    interpolation=cv2.INTER_LINEAR
                )

            # CLAHE
            clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
            enhanced = clahe.apply(gray)

            # Ngưỡng Otsu (Tesseract thích ảnh đen-trắng rõ ràng)
            _, binary = cv2.threshold(
                enhanced, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU
            )
            return Image.fromarray(binary)
        except Exception as exc:
            logger.debug("preprocess_for_tesseract fallback: {err}", err=str(exc))
            return pil_image

    # ── OCR 1 ảnh (dùng Tesseract) ────────────────────────────────────────────
    def _ocr_image(self, pil_image: Image.Image) -> str:
        """
        OCR toàn bộ một trang ảnh bằng Tesseract PSM 4, OEM 1.
        Trả về văn bản thô (chưa qua post-process).
        """
        self.check_availability()
        processed = self.preprocess_for_tesseract(pil_image)
        raw = pytesseract.image_to_string(
            processed,
            lang=self.LANG,
            config=self.CONFIG,
            output_type=pytesseract.Output.STRING,
        )
        return unicodedata.normalize("NFC", raw).strip()

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
        """Điểm chất lượng heuristic từ tỷ lệ ký tự rác."""
        import re
        if not text or len(text.strip()) < 10:
            return 0.60
        base = 0.82  # Baseline Tesseract
        suspicious  = len(re.findall(r'[%~^|<>{}\\[\\]@#$*]', text))
        char_penalty = min(0.15, (suspicious / max(len(text), 1)) * 5.0)
        return round(max(0.60, min(0.95, base - char_penalty)), 2)

    # ── Extract toàn file ─────────────────────────────────────────────────────
    def extract_text_from_file(
        self,
        file_bytes: bytes,
        file_type: str,
        engine: str | None = None,  # kept for interface compatibility
    ) -> tuple[str, str, float]:
        """
        Trích xuất văn bản từ file PDF hoặc Ảnh bằng Tesseract.

        Returns:
            (raw_text, processed_text, confidence_score)
            raw_text       — văn bản OCR thô trực tiếp từ Tesseract
            processed_text — đã qua hậu xử lý tiếng Việt
            confidence_score — heuristic [0.60, 0.95]
        """
        self.check_availability()

        file_ext = file_type.lower().replace(".", "")
        _s = self._get_settings()
        _dpi = getattr(_s, "ocr_pdf_dpi_default", 200) if _s else 200

        # ── PDF ─────────────────────────────────────────────────────────────
        if file_ext == "pdf":
            if pymupdf is None:
                raise EngineUnavailableError("tesseract", "PyMuPDF chưa được cài đặt để render PDF.")
            try:
                doc = pymupdf.open(stream=file_bytes, filetype="pdf")
                page_raws: list[str] = []
                total = len(doc)
                for idx, page in enumerate(doc):
                    t0 = time.time()
                    pix = page.get_pixmap(dpi=_dpi)
                    page_img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
                    raw = self._ocr_image(page_img)
                    if raw:
                        page_raws.append(raw)
                    logger.info(
                        "Tesseract OCR trang {i}/{t} | {s:.1f}s",
                        i=idx + 1, t=total, s=time.time() - t0,
                    )
                raw_text = "\n\n".join(page_raws)
            except Exception as exc:
                if isinstance(exc, EngineUnavailableError):
                    raise
                logger.warning("Tesseract PDF OCR failed: {err}", err=str(exc))
                raise EngineUnavailableError("tesseract", f"Lỗi render hoặc OCR PDF: {exc}") from exc
        else:
            # ── Ảnh ─────────────────────────────────────────────────────────
            try:
                image = Image.open(io.BytesIO(file_bytes)).convert("RGB")
                raw_text = self._ocr_image(image)
            except Exception as exc:
                if isinstance(exc, EngineUnavailableError):
                    raise
                logger.warning("Tesseract image OCR failed: {err}", err=str(exc))
                raise EngineUnavailableError("tesseract", f"Lỗi OCR ảnh: {exc}") from exc

        if not raw_text:
            return "", "", 0.0

        processed_text = self.post_process_vietnamese(raw_text)
        confidence     = self.heuristic_quality_score(processed_text)
        logger.info(
            "Tesseract hoàn thành: {c} ký tự raw, {cp} ký tự processed, conf={cf}",
            c=len(raw_text), cp=len(processed_text), cf=confidence,
        )
        return raw_text, processed_text, confidence

    # ── Metadata extract ─────────────────────────────────────────────────────
    def extract_metadata(self, text: str) -> dict[str, Any]:
        """Trích xuất metadata có cấu trúc."""
        try:
            from app.services.vietocr_service import vietocr_service
            return vietocr_service.extract_metadata(text)
        except Exception:
            return {}


# Singleton
tesseract_service = TesseractService()
