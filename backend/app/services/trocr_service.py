"""
backend/app/services/ocr_service.py — OCR Orchestrator

Điều phối toàn bộ pipeline OCR:
  ┌─────────────────────────────────────────────────────┐
  │  vietocr_engine.py  ←──── engine chính (VietOCR)   │
  │  trocr_engine.py    ←──── engine phụ  (TrOCR)      │
  │  ocr_service.py     ←──── orchestrator (file này)  │
  └─────────────────────────────────────────────────────┘

Chịu trách nhiệm:
  - Tiền xử lý ảnh (preprocess_image, preprocess_handwriting)
  - Tách dòng (segment_lines)
  - Điều hướng engine theo config
  - OCR file PDF / Ảnh đầy đủ
  - Hậu xử lý văn bản tiếng Việt
  - Tính điểm chất lượng (heuristic)
  - Trích xuất metadata (MSSV, tên, ngày, số hiệu)

Mọi ngưỡng số đọc từ backend/app/core/config.py.
"""
import io
import re
import time
import unicodedata
from datetime import date
from typing import Any

import numpy as np
from loguru import logger
from PIL import Image

try:
    import cv2
except ImportError:
    cv2 = None

try:
    import pymupdf  # PyMuPDF
except ImportError:
    try:
        import fitz as pymupdf
    except ImportError:
        pymupdf = None

try:
    import pytesseract
    import platform
    import os
    # Cấu hình tự động đường dẫn cho Windows nếu Tesseract chưa được add vào PATH
    if platform.system() == "Windows":
        if os.path.exists(r"C:\Program Files\Tesseract-OCR\tesseract.exe"):
            pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
        elif os.path.exists(r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe"):
            pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe"
            
    # Trỏ TESSDATA_PREFIX về thư mục chứa model ngôn ngữ cục bộ
    local_tessdata = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../backend/tessdata"))
    if os.path.exists(local_tessdata):
        os.environ["TESSDATA_PREFIX"] = local_tessdata
except ImportError:
    pytesseract = None

try:
    import pypdf
except ImportError:
    pypdf = None


class TrOCRService:
    """
    Service chuyên biệt điều phối pipeline cho TrOCR.
    """

    def __init__(self) -> None:
        self._settings = None

    # ── Settings ──────────────────────────────────────────────────────────────
    def _get_settings(self):
        if self._settings is None:
            try:
                from app.core.config import settings
                self._settings = settings
            except Exception:
                pass
        return self._settings

    # ── Engine access (lazy, qua singleton) ───────────────────────────────────
    @staticmethod
    def _vietocr():
        from app.services.vietocr_engine import vietocr_engine
        return vietocr_engine

    @staticmethod
    def _trocr():
        from app.services.trocr_engine import trocr_engine
        return trocr_engine

    # Backward-compat: một số nơi có thể gọi trực tiếp _get_predictor()
    def _get_predictor(self):
        return self._vietocr().get_predictor()

    def _predict_batch_padded(self, predictor, images: list[Image.Image]) -> list[str]:
        return self._vietocr().predict_batch_padded(images)

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
                scale = min(2.0, max(1.5, 56.0 / h))
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
        """
        Tách ảnh thành danh sách ảnh dòng đơn lẻ.
        Dùng kernel ngang rộng để nối từ → dòng liên tục.
        """
        if cv2 is None:
            return [pil_image]

        try:
            img_np = np.array(pil_image)
            gray = cv2.cvtColor(img_np, cv2.COLOR_RGB2GRAY) if len(img_np.shape) == 3 else img_np.copy()
            h_img, w_img = gray.shape[:2]

            _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)

            # Kernel ngang rộng: nối các từ trên cùng dòng thành 1 blob
            # Chiều cao = 1 để tuyệt đối KHÔNG làm dính 2 dòng trên/dưới lại với nhau.
            # Kernel ngang rộng: nối các từ trên cùng dòng thành 1 blob
            # Chiều cao = 1 để tuyệt đối KHÔNG làm dính 2 dòng trên/dưới lại với nhau.
            kw = max(40, w_img // 20)  # ~5% chiều rộng trang, tối thiểu 40px
            kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (kw, 1))
            dilated = cv2.dilate(binary, kernel, iterations=1)

            contours, _ = cv2.findContours(dilated, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            boxes = sorted(
                [cv2.boundingRect(c) for c in contours],
                key=lambda b: (b[1] // 20, b[0]),
            )

            line_images: list[Image.Image] = []
            for x, y, w, h in boxes:
                if w < 15 or h < 6 or h > h_img * 0.6:
                    continue  # bỏ nhiễu điểm và khung viền toàn trang
                pad_top    = max(0, y - 10)
                pad_bottom = min(h_img, y + h + 8)
                pad_left   = max(0, x - 4)
                pad_right  = min(w_img, x + w + 4)
                line_images.append(Image.fromarray(img_np[pad_top:pad_bottom, pad_left:pad_right]))

            if line_images:
                logger.info("Segmented {n} lines ({h}×{w}px)", n=len(line_images), h=h_img, w=w_img)
                return line_images
        except Exception as exc:
            logger.warning("segment_lines fallback: {err}", err=str(exc))

        return [pil_image]

    # ── Lọc nhiễu ─────────────────────────────────────────────────────────────
    @staticmethod
    def _is_noise_line(text: str) -> bool:
        """
        Lọc dòng rác sau OCR. Loại bỏ:
        - Dòng rỗng, quá ngắn.
        - Toàn ký tự đặc biệt (không có chữ/số)
        - Số barcode/artifact hoặc chuỗi số ảo giác dài.
        - Dòng rác chứa toàn dấu chấm/gạch ngang.
        - Dòng từ lặp: sinh ra từ con dấu tròn đỏ (circular stamp) hoặc watermark mờ.
        """
        if not text or not text.strip():
            return True
        t = text.strip()

        # Dòng quá ngắn
        if len(t) <= 1 and t not in ("I", "1", "-", "."):
            return True

        # Không có ký tự chữ cái / chữ số nào
        if not re.search(r'[A-Za-z0-9\u00C0-\u1EF9]', t):
            return True

        # Artifact barcode / số mã vạch
        if re.fullmatch(r'[\d\s\.\,\-]{4,}', t):
            return True
            
        # Barcode dài nằm xen kẽ (VD: Và 1.0000000000099)
        if re.search(r'\d{10,}', t):
            return True
            
        # Ảo giác dấu chấm/gạch ngang
        if len(re.findall(r'[\.\-\_~]', t)) >= 12:
            return True

        words = t.split()
        if len(words) >= 4:
            clean_words = []
            for w in words:
                key = re.sub(r'[^a-z\u00C0-\u1EF9]', '', w.lower())
                if len(key) >= 2:
                    clean_words.append(key)
                    
            if len(clean_words) >= 3:
                from collections import Counter
                counts = Counter(clean_words)
                max_freq = counts.most_common(1)[0][1]
                
                # Mộc mờ sinh ảo giác từ lặp liên tục
                if max_freq >= 3 and (max_freq / len(clean_words)) > 0.25:
                    return True
                    
                # Watermark mờ sinh 2 cặp lặp từ đứng cạnh nhau (VD: LỤC LỤC LỤ THUẬN THUẬN)
                adjacent_dups = sum(1 for i in range(len(clean_words) - 1) if clean_words[i] == clean_words[i+1])
                if adjacent_dups >= 2:
                    return True

        return False

    @staticmethod
    def _clean_ocr_text(text: str) -> str:
        """
        Lọc toàn bộ văn bản sau khi join dòng:
        - Xóa dòng artifact barcode còn sót (chỉ toàn số + dấu chấm)
        - Xóa dòng con dấu tròn đỏ còn sót (từ lặp liên tục)
        - Giữ nguyên tất cả dòng hợp lệ
        """
        lines = text.splitlines()
        result: list[str] = []
        for line in lines:
            if not TrOCRService._is_noise_line(line):
                # Tự động viết hoa chữ cái đầu tiên của dòng nếu nó là chữ thường
                # Giúp sửa các lỗi như "lễ quốc khánh 2/9" -> "Lễ quốc khánh 2/9"
                if line:
                    line = line.strip()
                    if line and line[0].islower():
                        line = line[0].upper() + line[1:]
                result.append(line)
        return "\n".join(result)

    # ── Hậu xử lý ─────────────────────────────────────────────────────────────
    def post_process_vietnamese(self, text: str) -> str:
        """Gọi pipeline hậu xử lý: ocr_char_fixes → admin_dict → header_normalizer."""
        try:
            from app.services.text_postprocessing import post_process_vietnamese as _pp
            return _pp(text)
        except ImportError:
            import unicodedata as _ud
            return _ud.normalize("NFC", text).strip()

    # ── Chấm điểm tin cậy ────────────────────────────────────────────────────
    def heuristic_quality_score(self, text: str, engine: str = "vietocr") -> float:
        """
        Ước lượng chất lượng OCR bằng heuristic dựa trên tỷ lệ ký tự rác.
        Trả về float trong [0.60, 0.98].

        LƯU Ý: Đây là heuristic, KHÔNG phải confidence thực từ model.
        VietOCR stable không có API return_prob → không thể lấy log-probability.
        """
        if not text or len(text.strip()) < 10:
            return 0.60
        _base = {"vietocr": 0.92, "direct_pdf": 0.97, "pypdf": 0.88}.get(engine, 0.85)
        suspicious  = len(re.findall(r'[%~^|<>{}\[\]\\@#$*]', text))
        char_penalty = min(0.15, (suspicious / max(len(text), 1)) * 5.0)
        digit_runs   = re.findall(r'\d{8,}', text)
        digit_penalty = min(0.05, len(digit_runs) * 0.01)
        return round(max(0.60, min(0.98, _base - char_penalty - digit_penalty)), 2)

    def calculate_confidence_score(self, text: str, engine: str = "vietocr") -> float:
        """Alias backward-compatible cho heuristic_quality_score()."""
        return self.heuristic_quality_score(text, engine)

    # ── Điều hướng engine theo dòng ───────────────────────────────────────────
    def _ocr_lines_with_engine(
        self, image: Image.Image
    ) -> list[tuple[str, float]]:
        """Tách dòng rồi OCR bằng TrOCR — giới hạn 60 dòng/trang để đảm bảo tốc độ."""
        line_images = self.segment_lines(image)
        if not line_images:
            return []
        
        # Giới hạn 40 dòng để TrOCR hoàn thành nhanh (< 1-2 phút trên CPU)
        MAX_LINES_TROCR = 40
        if len(line_images) > MAX_LINES_TROCR:
            logger.debug("TrOCR: giới hạn {max} dòng (có {total} dòng)", 
                         max=MAX_LINES_TROCR, total=len(line_images))
            line_images = line_images[:MAX_LINES_TROCR]
            
        return self._trocr().ocr_lines(line_images, preprocess_fn=self.preprocess_handwriting)


    # ── Bóc tách bảng biểu ────────────────────────────────────────────────────
    def detect_and_extract_tables(self, pil_image: Image.Image) -> list[str]:
        """
        Nhận diện và bóc tách bảng biểu bằng Morphological Kernels.
        Yêu cầu: ≥ 3 hàng × ≥ 2 cột, diện tích ≥ 5% trang.
        Xuất ra định dạng Markdown.
        """
        if cv2 is None:
            return []
        try:
            img_np = np.array(pil_image)
            gray = cv2.cvtColor(img_np, cv2.COLOR_RGB2GRAY) if len(img_np.shape) == 3 else img_np
            _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)

            _s = self._get_settings()
            _kh = getattr(_s, "ocr_morph_kernel_horiz", 25) if _s else 25
            _kv = getattr(_s, "ocr_morph_kernel_vert",  25) if _s else 25

            horiz = cv2.morphologyEx(binary, cv2.MORPH_OPEN,
                                     cv2.getStructuringElement(cv2.MORPH_RECT, (_kh, 1)), iterations=2)
            vert  = cv2.morphologyEx(binary, cv2.MORPH_OPEN,
                                     cv2.getStructuringElement(cv2.MORPH_RECT, (1, _kv)), iterations=2)
            grid  = cv2.add(horiz, vert)

            contours, _ = cv2.findContours(grid, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
            h_img, w_img = img_np.shape[:2]

            cells, total_area = [], 0
            for c in contours:
                x, y, w, h = cv2.boundingRect(c)
                if 25 < w < (w_img * 0.95) and 12 < h < (h_img * 0.3):
                    cells.append((x, y, w, h))
                    total_area += w * h

            if len(cells) < 6 or total_area < (w_img * h_img * 0.05):
                return []

            cells = sorted(cells, key=lambda b: (b[1] // 18, b[0]))
            rows: list[list] = []
            cur_row: list = []
            last_y = None
            for x, y, w, h in cells:
                if last_y is None or abs(y - last_y) < 18:
                    cur_row.append((x, y, w, h))
                    last_y = y
                else:
                    rows.append(sorted(cur_row, key=lambda b: b[0]))
                    cur_row = [(x, y, w, h)]
                    last_y = y
            if cur_row:
                rows.append(sorted(cur_row, key=lambda b: b[0]))

            if len(rows) < 3 or (max(len(r) for r in rows) if rows else 0) < 2:
                return []

            all_flat = [(ri, x, y, w, h) for ri, row in enumerate(rows) for x, y, w, h in row]
            crops = [
                self.preprocess_handwriting(Image.fromarray(img_np[y:y+h, x:x+w]))
                for _, x, y, w, h in all_flat
                if min(w, h) > 6
            ]
            batch_texts = self._vietocr().predict_batch_padded(crops) if crops else []

            crop_idx = 0
            row_map: dict[int, list[str]] = {}
            for ri, x, y, w, h in all_flat:
                if min(w, h) > 6 and crop_idx < len(batch_texts):
                    cell_text = batch_texts[crop_idx] or ""
                    crop_idx += 1
                else:
                    cell_text = ""
                    if pytesseract is not None:
                        try:
                            cell_bytes = pytesseract.image_to_string(
                                Image.fromarray(img_np[y:y+h, x:x+w]),
                                lang="vie+eng", config="--psm 6",
                                output_type=pytesseract.Output.BYTES
                            )
                            cell_text = cell_bytes.decode("utf-8", errors="replace").strip()
                        except Exception:
                            pass
                row_map.setdefault(ri, []).append(cell_text.replace("\n", " ") or "--")

            md_rows: list[str] = []
            for ri in sorted(row_map):
                row_texts = row_map[ri]
                md_rows.append("| " + " | ".join(row_texts) + " |")
                if ri == 0:
                    md_rows.append("| " + " | ".join(["---"] * len(row_texts)) + " |")

            if len(md_rows) >= 3:
                logger.info("Extracted table: {r} rows, {c} cells", r=len(rows), c=len(all_flat))
                return ["\n".join(md_rows)]
        except Exception as exc:
            logger.debug("Table extraction failed: {err}", err=str(exc))
        return []

    # ── OCR 1 trang ───────────────────────────────────────────────────────────
    def _ocr_image(
        self,
        image: Image.Image,
        extract_tables: bool = False,
        is_first_page: bool = True,
        engine: str | None = None,
    ) -> str:
        """
        OCR toàn trang bằng Line Segmentation — không chia vùng để tránh mất chữ.
        Pipeline: preprocess → segment_lines → engine OCR → filter → join → postprocess.
        Fallback Tesseract nếu engine chính trả về rỗng.
        """
        _s = self._get_settings()
        selected_engine = engine or (getattr(_s, "ocr_engine", "vietocr") if _s else "vietocr")

        processed_img = self.preprocess_image(image)

        # 1. Bóc tách bảng biểu (tuỳ chọn)
        table_markdowns = self.detect_and_extract_tables(processed_img) if extract_tables else []

        # 2. OCR toàn trang theo dòng
        full_text = ""
        line_results = self._ocr_lines_with_engine(processed_img)
        if line_results:
            valid_lines = [t for t, _ in line_results if not self._is_noise_line(t)]
            joined = "\n".join(valid_lines)
            if len(joined.strip()) > 3:
                full_text = unicodedata.normalize("NFC", joined.strip())
                logger.info("OCR [trocr] → {n} dòng, {c} ký tự",
                            n=len(valid_lines), c=len(full_text))

        # 5. Ghép bảng biểu
        if table_markdowns:
            tables_str = "\n\n### [BẢNG BIỂU DỮ LIỆU BÓC TÁCH]:\n" + "\n\n".join(table_markdowns)
            full_text = f"{full_text}\n\n{tables_str}" if full_text else tables_str

        if full_text:
            full_text = self._clean_ocr_text(full_text)   # lọc artifact + con dấu
            full_text = self.post_process_vietnamese(full_text)

        return full_text

    # ── OCR toàn file ─────────────────────────────────────────────────────────
    def extract_text_from_file(
        self, file_bytes: bytes, file_type: str, engine: str | None = None
    ) -> tuple[str, float]:
        """
        Trích xuất toàn văn từ file PDF hoặc Ảnh (JPG, PNG, TIFF).

        Returns:
            (text, heuristic_quality_score)
        """
        file_ext = file_type.lower().replace(".", "")
        _s = self._get_settings()
        # TrOCR dùng DPI 150 cố định — đủ cho so sánh, nhanh hơn 30% so với 200 DPI
        _render_dpi     = 150
        _extract_tables = False   # Tắt bảng biểu cho TrOCR — chỉ so sánh văn bản chính
        selected_engine = engine or "trocr"

        logger.info(
            "OCR: engine={eng}, dpi={dpi}, fast=False, tables={et}",
            eng=selected_engine, dpi=_render_dpi, et=_extract_tables,
        )

        # ── PDF ──────────────────────────────────────────────────────────────
        if file_ext == "pdf":
            if pymupdf is not None:
                try:
                    doc = pymupdf.open(stream=file_bytes, filetype="pdf")

                    # PDF có text layer → trích xuất trực tiếp (siêu tốc)
                    if selected_engine == "vietocr":
                        pages_text = [page.get_text().strip() for page in doc]
                        pages_text = [t for t in pages_text if t]
                        if pages_text and len("\n".join(pages_text)) > 20:
                            full = self.post_process_vietnamese("\n\n".join(pages_text))
                            logger.info("Direct text PDF: {p} trang, {c} ký tự",
                                        p=len(doc), c=len(full))
                            return full, self.calculate_confidence_score(full, "direct_pdf")

                    # PDF scan ảnh
                    ocr_pages: list[str] = []
                    total = len(doc)
                    for idx, page in enumerate(doc):
                        t0 = time.time()
                        pix = page.get_pixmap(dpi=_render_dpi)
                        page_img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
                        page_text = self._ocr_image(
                            page_img,
                            extract_tables=_extract_tables,
                            is_first_page=(idx == 0),
                        )
                        logger.info("OCR trang {i}/{t} [{eng}] | {s:.1f}s",
                                    i=idx + 1, t=total, eng=selected_engine, s=time.time() - t0)
                        if page_text:
                            ocr_pages.append(page_text)

                    if ocr_pages:
                        full = self.post_process_vietnamese("\n\n".join(ocr_pages))
                        return full, self.calculate_confidence_score(full, selected_engine)
                    return "", 0.0
                except Exception as exc:
                    logger.warning("PyMuPDF OCR failed: {err}", err=str(exc))
                    return "", 0.0

            # Fallback pypdf (chỉ dùng khi PDF có text layer)
            if pypdf is not None and selected_engine == "vietocr":
                try:
                    reader = pypdf.PdfReader(io.BytesIO(file_bytes))
                    texts  = [p.extract_text() or "" for p in reader.pages if p.extract_text()]
                    if texts and len("\n".join(texts)) > 30:
                        full = self.post_process_vietnamese("\n\n".join(texts))
                        return full, self.calculate_confidence_score(full, "pypdf")
                except Exception:
                    pass

        # ── Ảnh (JPG / PNG / TIFF) ───────────────────────────────────────────
        try:
            image = Image.open(io.BytesIO(file_bytes)).convert("RGB")
            text = self._ocr_image(image, engine=selected_engine)
            if text:
                text = self.post_process_vietnamese(text)
                return text, self.calculate_confidence_score(text, selected_engine)
        except Exception as exc:
            logger.warning("Image OCR failed: {err}", err=str(exc))

        return "", 0.0

    # ── So sánh engine ────────────────────────────────────────────────────────
    def compare_ocr_engines(self, file_bytes: bytes, file_type: str) -> dict[str, Any]:
        """So sánh hiệu năng VietOCR / TrOCR / Tesseract trên cùng một tài liệu."""
        results: dict[str, Any] = {}
        for eng_key, eng_name in [
            ("vietocr",  "VietOCR (vgg_transformer)"),
            ("trocr",    "Microsoft TrOCR (Vision Transformer)"),
            ("tesseract","Tesseract 5 (LSTM Baseline)"),
        ]:
            t0 = time.time()
            try:
                text, conf = self.extract_text_from_file(file_bytes, file_type, engine=eng_key)
                results[eng_key] = {
                    "engine_name": eng_name,
                    "text": text,
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
                    "confidence": 0.0,
                    "inference_time_seconds": round(time.time() - t0, 3),
                    "status": f"FAILED: {exc}",
                }
        return results

    # ── Trích xuất metadata ───────────────────────────────────────────────────
    def extract_metadata(self, text: str) -> dict[str, Any]:
        """
        Trích xuất metadata có cấu trúc từ văn bản OCR:
        MSSV, Họ tên, Ngày văn bản, Số hiệu, Loại văn bản.
        """
        metadata: dict[str, Any] = {
            "student_id": None,
            "student_name": None,
            "document_date": None,
            "document_number": None,
            "detected_category": None,
        }
        if not text:
            return metadata

        _s = self._get_settings()
        _mssv_prefix  = getattr(_s, "mssv_year_prefix_pattern", r"2[0-3]") if _s else r"2[0-3]"
        _mssv_len_min = getattr(_s, "mssv_length_min", 7)                   if _s else 7
        _mssv_len_max = getattr(_s, "mssv_length_max", 8)                   if _s else 8
        _kw_len = "{" + str(_mssv_len_min) + "," + str(_mssv_len_max) + "}"
        _sfx_min, _sfx_max = max(1, _mssv_len_min - 2), max(2, _mssv_len_max - 2)
        _sfx_len = "{" + str(_sfx_min) + "," + str(_sfx_max) + "}"

        # 1. MSSV
        m = re.search(
            r"(?:MSSV|Mã\s*số\s*sinh\s*viên|Mã\s*SV|Mã\s*sinh\s*viên)[\s:]*([0-9]" + _kw_len + r")",
            text, re.IGNORECASE,
        ) or re.search(r"\b(" + _mssv_prefix + r"[0-9]" + _sfx_len + r")\b", text)
        if m:
            metadata["student_id"] = m.group(1).strip()

        # 2. Họ tên
        nm = re.search(
            r"(?:Em tên là|Họ và tên|Họ tên sinh viên|Người làm đơn|Họ và tên sinh viên)[\s:]*([A-ZÀ-Ỹa-zà-ỹ\s]{3,35})",
            text,
        )
        if nm:
            name = nm.group(1).strip().split("\n")[0]
            name = re.sub(r"(MSSV|Lớp|Khoa|Ngày|Số|Ngành).*", "", name).strip()
            if len(name) >= 3:
                metadata["student_name"] = name

        # 3. Ngày văn bản
        dm = re.search(r"ngày\s+(\d{1,2})\s+tháng\s+(\d{1,2})\s+năm\s+(\d{4})", text, re.IGNORECASE)
        if dm:
            try:
                metadata["document_date"] = date(int(dm.group(3)), int(dm.group(2)), int(dm.group(1))).isoformat()
            except ValueError:
                pass
        else:
            ds = re.search(r"(\d{1,2})[/.-](\d{1,2})[/.-](\d{4})", text)
            if ds:
                try:
                    metadata["document_date"] = date(int(ds.group(3)), int(ds.group(2)), int(ds.group(1))).isoformat()
                except ValueError:
                    pass

        # 4. Số hiệu văn bản
        sn = re.search(
            r"(?:Số|Số hiệu)[\s:]*([0-9A-ZÀ-Ỹa-zà-ỹ\-_/]+(?:\s*/\s*[0-9A-ZÀ-Ỹa-zà-ỹ\-_/]+)?)",
            text, re.IGNORECASE,
        )
        if sn:
            num = re.sub(r"\s*/\s*", "/", sn.group(1).strip())
            metadata["document_number"] = num

        # 5. Phân loại tự động
        tl = text.lower()
        if "kế hoạch" in tl or "kh-đhđl" in tl:
            metadata["detected_category"] = "KE_HOACH"
        elif "thông báo" in tl or "tb-đhđl" in tl:
            metadata["detected_category"] = "THONG_BAO"
        elif "quyết định" in tl or "qđ-đhđl" in tl:
            metadata["detected_category"] = "QUYET_DINH"
        elif "hướng dẫn" in tl or "hd-đhđl" in tl:
            metadata["detected_category"] = "HUONG_DAN"
        elif "nghỉ học" in tl or "bảo lưu" in tl:
            metadata["detected_category"] = "DON_NGHI_HOC"
        elif "học bổng" in tl:
            metadata["detected_category"] = "HOC_BONG"
        elif "miễn giảm học phí" in tl:
            metadata["detected_category"] = "MIEN_GIAM_HOC_PHI"
        elif "bảo hiểm y tế" in tl or "bhyt" in tl:
            metadata["detected_category"] = "BHYT"
        elif "xác nhận" in tl:
            metadata["detected_category"] = "GIAY_XAC_NHAN"
        elif "khen thưởng" in tl or "kỷ luật" in tl:
            metadata["detected_category"] = "KHEN_THUONG"

        logger.info("Extracted metadata: {meta}", meta=metadata)
        return metadata


# Singleton — giữ tên để không break toàn bộ import hiện tại
trocr_service = TrOCRService()
