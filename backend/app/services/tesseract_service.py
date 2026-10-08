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
    os.path.join(os.path.dirname(__file__), "../../tessdata")
)
if os.path.exists(_local_tessdata):
    if platform.system() == "Windows" and any(ord(c) > 127 for c in _local_tessdata):
        import subprocess
        import tempfile
        _temp_tessdata = os.path.join(tempfile.gettempdir(), "DocuCTSV_tessdata_link")
        if not os.path.exists(_temp_tessdata):
            try:
                subprocess.run(f'cmd /c mklink /J "{_temp_tessdata}" "{_local_tessdata}"', shell=True, check=True)
            except Exception:
                pass
        os.environ["TESSDATA_PREFIX"] = _temp_tessdata
    else:
        os.environ.setdefault("TESSDATA_PREFIX", _local_tessdata)

import cv2
import numpy as np

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
    PSM     = 3   # Fully automatic page segmentation (handles multiple columns like headers better)
    OEM     = 1   # Neural nets LSTM only
    CONFIG  = f"--psm {PSM} --oem {OEM}"
    VERSION = "5.3.0"

    def __init__(self) -> None:
        self._settings = None

    def _get_settings(self) -> Any:
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
        - Inpaint red stamps
        - Mask out blue handwriting (prevent guessing digits)
        - Grayscale
        - CLAHE (tăng tương phản cục bộ)
        """
        if cv2 is None or np is None:
            return pil_image
        try:
            img_np = np.array(pil_image)
            if len(img_np.shape) == 3:
                hsv = cv2.cvtColor(img_np, cv2.COLOR_RGB2HSV)
                
                # Red mask (stamps)
                lower_red1 = np.array([0, 50, 50])
                upper_red1 = np.array([10, 255, 255])
                mask_red1 = cv2.inRange(hsv, lower_red1, upper_red1)
                
                lower_red2 = np.array([170, 50, 50])
                upper_red2 = np.array([180, 255, 255])
                mask_red2 = cv2.inRange(hsv, lower_red2, upper_red2)
                
                mask_red = cv2.bitwise_or(mask_red1, mask_red2)
                kernel = np.ones((3,3), np.uint8)
                mask_red = cv2.dilate(mask_red, kernel, iterations=1)
                
                if cv2.countNonZero(mask_red) > 0:
                    img_np = cv2.inpaint(img_np, mask_red, 3, cv2.INPAINT_TELEA)
                
                # Blue mask (handwriting)
                lower_blue = np.array([90, 50, 50])
                upper_blue = np.array([140, 255, 255])
                mask_blue = cv2.inRange(hsv, lower_blue, upper_blue)
                mask_blue = cv2.dilate(mask_blue, kernel, iterations=2)
                
                # Erase blue ink to prevent Tesseract from hallucinating digits
                img_np[mask_blue > 0] = [255, 255, 255]
                
                gray = cv2.cvtColor(img_np, cv2.COLOR_RGB2GRAY)
            else:
                gray = img_np.copy()
                
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

            # Do not pre-binarise with global Otsu, use Tesseract's own binarisation
            return Image.fromarray(enhanced)
        except Exception as exc:
            logger.debug("preprocess_for_tesseract fallback: {err}", err=str(exc))
            return pil_image

    # ── OCR 1 ảnh (dùng Tesseract) ────────────────────────────────────────────
    def _ocr_image(self, pil_image: Image.Image) -> str:
        """
        OCR toàn bộ một trang ảnh bằng Tesseract PSM 3, OEM 1.
        Sử dụng image_to_data để lấy thông tin block/par/line/word và confidence.
        Lọc nhiễu và giữ nguyên cấu trúc đoạn văn.
        """
        self.check_availability()
        processed = self.preprocess_for_tesseract(pil_image)
        
        # Step 3: TSV data
        data = pytesseract.image_to_data(
            processed,
            lang=self.LANG,
            config=self.CONFIG,
            output_type=pytesseract.Output.DICT,
        )
        
        lines = []
        current_block = -1
        current_par = -1
        current_line = -1
        
        current_line_words = []
        current_line_confs = []
        
        import re
        
        def flush_line():
            if not current_line_words:
                return
            
            line_text = " ".join(current_line_words)
            mean_conf = sum(current_line_confs) / len(current_line_confs)
            
            # Step 4: Noise filtering on line level
            letters = sum(1 for c in line_text if c.isalpha())
            non_letters = sum(1 for c in line_text if not c.isalpha() and not c.isspace())
            ratio = non_letters / max(len(line_text), 1)
            
            # Drop lines with low mean conf (< 40) or high non-letter ratio (> 0.5) if not a very short bullet
            if len(line_text) >= 5 and ratio > 0.5:
                return
            if mean_conf < 40:
                return
                
            # Step 5: normalize bullet points: "—" to "–"
            line_text = line_text.replace("—", "–")
            
            # Ensure paragraph breaks before "+", "–", "-", "1."
            if re.match(r'^(\+|–|-|\d+\.)\s', line_text):
                if lines and lines[-1] != "":
                    lines.append("")
                    
            lines.append(line_text)

        for i in range(len(data['level'])):
            level = data['level'][i]
            if level == 5: # Word level
                text = data['text'][i].strip()
                try:
                    conf = float(data['conf'][i])
                except:
                    conf = 0.0
                    
                block_num = data['block_num'][i]
                par_num = data['par_num'][i]
                line_num = data['line_num'][i]
                
                if (block_num != current_block or par_num != current_par or line_num != current_line):
                    flush_line()
                    
                    if (block_num != current_block or par_num != current_par) and current_line != -1:
                        if lines and lines[-1] != "":
                            lines.append("") # paragraph break
                            
                    current_block = block_num
                    current_par = par_num
                    current_line = line_num
                    current_line_words = []
                    current_line_confs = []
                
                # Step 4: Drop words with conf < 40
                if text and conf >= 40:
                    current_line_words.append(text)
                    current_line_confs.append(conf)
                    
        flush_line()
        
        raw_text = "\n".join(lines)
        return unicodedata.normalize("NFC", raw_text).strip()

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
        suspicious  = len(re.findall(r'[%~^|<>{}\\\[\]@#$*]', text))
        char_penalty = min(0.15, (suspicious / max(len(text), 1)) * 5.0)
        return round(max(0.60, min(0.95, base - char_penalty)), 2)

    # ── Extract toàn file ─────────────────────────────────────────────────────
    def extract_text_from_file(
        self,
        file_bytes: bytes,
        file_type: str,
        engine: str | None = None,  # kept for interface compatibility
        pages: list[int] | int | None = None,
    ) -> tuple[str, str, float, int]:
        """
        Trích xuất văn bản từ file PDF hoặc Ảnh bằng Tesseract.

        Returns:
            (raw_text, processed_text, confidence_score, page_count)
        """
        self.check_availability()

        file_ext = file_type.lower().replace(".", "")
        _s = self._get_settings()
        _dpi = getattr(_s, "ocr_pdf_dpi_default", 300) if _s else 300

        page_count = 1

        # ── PDF ─────────────────────────────────────────────────────────────
        if file_ext == "pdf":
            if pymupdf is None:
                raise EngineUnavailableError("tesseract", "PyMuPDF chưa được cài đặt để render PDF.")
            try:
                doc = pymupdf.open(stream=file_bytes, filetype="pdf")
                page_count = len(doc)
                
                target_pages = []
                if isinstance(pages, int):
                    target_pages = list(range(min(pages, page_count)))
                elif isinstance(pages, list):
                    target_pages = [p for p in pages if 0 <= p < page_count]
                else:
                    target_pages = list(range(page_count))

                page_raws: list[str] = []
                for idx in target_pages:
                    page = doc[idx]
                    t0 = time.time()
                    pix = page.get_pixmap(dpi=_dpi)
                    page_img = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)
                    raw = self._ocr_image(page_img)
                    if raw:
                        page_raws.append(raw)
                    logger.info(
                        "Tesseract OCR trang {i}/{t} | {s:.1f}s",
                        i=idx + 1, t=page_count, s=time.time() - t0,
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
            return "", "", 0.0, page_count

        processed_text = self.post_process_vietnamese(raw_text)
        confidence     = self.heuristic_quality_score(processed_text)
        logger.info(
            "Tesseract hoàn thành: {c} ký tự raw, {cp} ký tự processed, conf={cf}, pages={p}",
            c=len(raw_text), cp=len(processed_text), cf=confidence, p=page_count
        )
        return raw_text, processed_text, confidence, page_count

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
