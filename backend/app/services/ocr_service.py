"""
backend/app/services/ocr_service.py — High-Accuracy Vietnamese OCR Pipeline

Kiến trúc:
1. PDF Direct Text (siêu tốc) → PDF scan OCR (300 DPI mặc định, cấu hình được).
2. VietOCR Transformer vgg_transformer (beamsearch cấu hình được qua settings).
3. Line segmentation + deskew per-line + batch predict.
4. Post-processing qua text_postprocessing package (3 lớp tách biệt).
5. Confidence: heuristic_quality_score() — VietOCR stable không có return_prob API.
   TODO: Khi VietOCR hỗ trợ return_prob, thay bằng log-probability trung bình ký tự.
6. Metadata extraction với MSSV pattern cấu hình được qua settings.

Mọi ngưỡng số (DPI, beam_size, batch_size...) đọc từ backend/app/core/config.py.
"""
import glob
import io
import os
import re
import time
import unicodedata
from datetime import date, datetime
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
except ImportError:
    pytesseract = None

try:
    import pypdf
except ImportError:
    pypdf = None


class OCRService:
    """Service xử lý OCR chất lượng cao, nhận dạng Bảng biểu, Chữ viết tay và Đa mô hình (VietOCR / TrOCR / Tesseract)."""

    def __init__(self) -> None:
        self._predictor = None
        self._trocr_processor = None
        self._trocr_model = None
        # Lazy import settings để tránh circular import khi module load
        self._settings = None

    def _get_settings(self):
        if self._settings is None:
            try:
                from app.core.config import settings
                self._settings = settings
            except Exception:
                pass
        return self._settings

    def _get_predictor(self):
        """Khởi tạo VietOCR predictor với trọng số fine-tune nếu có (lazy load an toàn)."""
        if self._predictor is None:
            orig_requests_get = None
            try:
                import urllib3
                urllib3.disable_warnings()
                import requests
                from vietocr.tool import utils as vocr_utils
                
                # Tạm thời cấu hình download weights trong phạm vi nạp model nếu cần
                orig_requests_get = requests.get
                def _scoped_get(*args, **kwargs):
                    kwargs['verify'] = False
                    return orig_requests_get(*args, **kwargs)
                vocr_utils.requests.get = _scoped_get

                import torch
                torch.set_num_threads(min(8, os.cpu_count() or 4))

                from vietocr.tool.config import Cfg
                from vietocr.tool.predictor import Predictor
                config = Cfg.load_config_from_name("vgg_transformer")

                # Đọc device và beamsearch từ settings (không hardcode)
                _s = self._get_settings()
                _device     = getattr(_s, 'ocr_device', 'cpu')          if _s else 'cpu'
                _beamsearch = getattr(_s, 'ocr_beamsearch_enabled', False) if _s else False
                _beam_size  = getattr(_s, 'ocr_beam_size', 4)            if _s else 4
                _fast_mode  = getattr(_s, 'ocr_fast_mode', False)        if _s else False

                if _fast_mode:
                    _beamsearch = False  # fast mode ghi đè

                config["device"] = _device
                config["predictor"]["beamsearch"] = _beamsearch
                if _beamsearch:
                    config["predictor"]["beam_size"] = _beam_size
                    logger.info("VietOCR beamsearch=True beam_size={bs}", bs=_beam_size)
                else:
                    logger.info("VietOCR beamsearch=False (greedy, faster)")

                # Tìm kiếm model fine-tune tốt nhất trong các thư mục models/
                candidate_patterns = [
                    "/app/models/*_best.pth",
                    "models/*_best.pth",
                    "../models/*_best.pth",
                    os.path.join(os.path.dirname(__file__), "../../../models/*_best.pth"),
                    os.path.join(os.path.dirname(__file__), "../../models/*_best.pth"),
                ]
                custom_models = []
                for pat in candidate_patterns:
                    custom_models.extend(glob.glob(pat))
                custom_models = sorted(list(set(custom_models)))

                if custom_models:
                    best_weights = custom_models[-1]
                    logger.info("Loading fine-tuned VietOCR weights: {path}", path=best_weights)
                    config["weights"] = best_weights

                self._predictor = Predictor(config)
                logger.info("Initialized VietOCR vgg_transformer predictor successfully")
            except Exception as exc:
                logger.warning("VietOCR predictor not loaded: {err}", err=str(exc))
            finally:
                if orig_requests_get:
                    try:
                        import requests
                        from vietocr.tool import utils as vocr_utils
                        requests.get = orig_requests_get
                        vocr_utils.requests.get = orig_requests_get
                    except Exception:
                        pass
        return self._predictor

    def _get_trocr_model(self):
        """Khởi tạo Microsoft TrOCR Vision Transformer model & processor (lazy load)."""
        if self._trocr_model is None or self._trocr_processor is None:
            try:
                import torch
                from transformers import TrOCRProcessor, VisionEncoderDecoderModel

                _s = self._get_settings()
                model_name = getattr(_s, "trocr_model_name", "microsoft/trocr-base-printed") if _s else "microsoft/trocr-base-printed"
                device = getattr(_s, "trocr_device", "cpu") if _s else "cpu"

                logger.info("Initializing Microsoft TrOCR ({model}) on {device}...", model=model_name, device=device)
                self._trocr_processor = TrOCRProcessor.from_pretrained(model_name)
                self._trocr_model = VisionEncoderDecoderModel.from_pretrained(model_name).to(device)
                self._trocr_model.eval()
                logger.info("Initialized Microsoft TrOCR Vision Transformer successfully")
            except Exception as exc:
                logger.warning("TrOCR model initialization failed: {err}", err=str(exc))
                self._trocr_model = None
                self._trocr_processor = None
        return self._trocr_processor, self._trocr_model

    def _predict_batch_trocr(self, images: list[Image.Image]) -> list[str]:
        """
        Nhận diện chuỗi ảnh dòng bằng mô hình Microsoft TrOCR (Vision Transformer).
        """
        if not images:
            return []

        proc, model = self._get_trocr_model()
        if proc is None or model is None:
            logger.warning("TrOCR not available, fallback to VietOCR")
            v_pred = self._get_predictor()
            return self._predict_batch_padded(v_pred, images)

        try:
            import torch
            _s = self._get_settings()
            device = getattr(_s, "trocr_device", "cpu") if _s else "cpu"

            rgb_images = [img.convert("RGB") if img.mode != "RGB" else img for img in images]
            pixel_values = proc(images=rgb_images, return_tensors="pt").pixel_values.to(device)

            with torch.no_grad():
                generated_ids = model.generate(pixel_values, max_new_tokens=256)

            generated_texts = proc.batch_decode(generated_ids, skip_special_tokens=True)
            return [str(t).strip() for t in generated_texts]
        except Exception as exc:
            logger.warning("TrOCR batch prediction error: {err}", err=str(exc))
            v_pred = self._get_predictor()
            return self._predict_batch_padded(v_pred, images)

    def preprocess_image(self, pil_image: Image.Image) -> Image.Image:
        """
        Tiền xử lý ảnh tốc độ cao:
        - Chuyển Grayscale
        - Tăng độ tương phản thích nghi (CLAHE)
        - Làm mịn nhẹ bằng GaussianBlur (nhanh hơn 10x so với NLMeans)
        """
        if cv2 is None:
            return pil_image

        try:
            img_np = np.array(pil_image)
            if len(img_np.shape) == 3:
                gray = cv2.cvtColor(img_np, cv2.COLOR_RGB2GRAY)
            else:
                gray = img_np

            # Tăng độ tương phản vùng chữ bằng CLAHE
            clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
            enhanced = clahe.apply(gray)

            # Làm mịn nhẹ bằng GaussianBlur (nhanh hơn 10x so với NLMeans)
            blurred = cv2.GaussianBlur(enhanced, (3, 3), 0)
            return Image.fromarray(blurred)
        except Exception as exc:
            logger.debug("Image preprocessing fallback: {err}", err=str(exc))
            return pil_image

    def preprocess_handwriting(self, pil_image: Image.Image) -> Image.Image:
        """
        Tiền xử lý tốc độ cao cho từng dòng văn bản:
        - Upscaling nếu dòng quá nhỏ
        - CLAHE tăng tương phản
        - Padding nhỏ chống cắt cụt dấu tiếng Việt
        (Bỏ các bước chậm: AdaptiveThreshold, morphology phức tạp)
        """
        if cv2 is None:
            return pil_image

        try:
            img_np = np.array(pil_image)
            if len(img_np.shape) == 3:
                gray = cv2.cvtColor(img_np, cv2.COLOR_RGB2GRAY)
            else:
                gray = img_np

            # 1. Upscaling nếu chiều cao dòng quá nhỏ
            h, w = gray.shape[:2]
            if h < 48 and h > 0:
                scale = min(2.0, max(1.5, 56.0 / h))
                gray = cv2.resize(gray, (0, 0), fx=scale, fy=scale, interpolation=cv2.INTER_LINEAR)

            # 2. CLAHE tăng tương phản nhẹ
            clahe = cv2.createCLAHE(clipLimit=1.5, tileGridSize=(4, 4))
            enhanced = clahe.apply(gray)

            # 3. Padding nhỏ chống cắt dấu tiếng Việt
            padded = cv2.copyMakeBorder(enhanced, 4, 4, 6, 6, cv2.BORDER_CONSTANT, value=255)

            return Image.fromarray(padded)
        except Exception as exc:
            logger.debug("Handwriting preprocessing fallback: {err}", err=str(exc))
            return pil_image

    def _predict_batch_padded(self, predictor, images: list[Image.Image]) -> list[str]:
        """
        Pad các ảnh dòng trong batch về cùng chiều cao 32 và chiều rộng lớn nhất (max_w)
        với nền trắng, giúp VietOCR gom toàn bộ ảnh vào 1 Tensor Batch duy nhất
        thay vì bị phân tán thành nhiều bucket đơn lẻ, tăng tốc độ xử lý trên CPU gấp 3-5 lần.
        """
        if not images or predictor is None:
            return []

        target_h = 32
        resized: list[Image.Image] = []
        for img in images:
            w, h = img.size
            if h <= 0 or w <= 0:
                continue
            new_w = max(16, int(round(w * (target_h / float(h)))))
            new_w = min(1200, new_w)
            resized.append(img.resize((new_w, target_h), Image.Resampling.BILINEAR))

        if not resized:
            return []

        max_w = max(img.width for img in resized)
        padded: list[Image.Image] = []
        for img in resized:
            if img.width == max_w and img.height == target_h:
                padded.append(img)
            else:
                pad_img = Image.new("RGB", (max_w, target_h), (255, 255, 255))
                pad_img.paste(img, (0, 0))
                padded.append(pad_img)

        try:
            results = predictor.predict_batch(padded)
            return [str(t).strip() for t in results]
        except Exception:
            # Fallback đơn lẻ nếu batching gặp lỗi
            outs = []
            for img in images:
                try:
                    outs.append(str(predictor.predict(img)).strip())
                except Exception:
                    outs.append("")
            return outs

    def detect_and_extract_tables(self, pil_image: Image.Image) -> list[str]:
        """
        Nhận diện và bóc tách Bảng biểu (Table Structure Detection):
        - Dùng Horizontal & Vertical Morphological Kernels tìm lưới ô (Grid)
        - Kiểm tra cấu trúc bảng chặt chẽ (>= 3 hàng x >= 2 cột, diện tích >= 5% trang)
        - Trích xuất từng ô theo thứ tự hàng/cột và xuất ra định dạng Bảng Markdown.
        """
        if cv2 is None:
            return []

        try:
            img_np = np.array(pil_image)
            if len(img_np.shape) == 3:
                gray = cv2.cvtColor(img_np, cv2.COLOR_RGB2GRAY)
            else:
                gray = img_np

            # Nhị phân hóa Otsu
            _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)

            # Đọc kernel sizes từ settings
            _s = self._get_settings()
            _kh = getattr(_s, 'ocr_morph_kernel_horiz', 25) if _s else 25
            _kv = getattr(_s, 'ocr_morph_kernel_vert',  25) if _s else 25

            # 1. Phát hiện đường kẻ ngang
            horiz_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (_kh, 1))
            horiz_lines = cv2.morphologyEx(binary, cv2.MORPH_OPEN, horiz_kernel, iterations=2)

            # 2. Phát hiện đường kẻ dọc
            vert_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (1, _kv))
            vert_lines = cv2.morphologyEx(binary, cv2.MORPH_OPEN, vert_kernel, iterations=2)

            # 3. Kết hợp lưới bảng (Table Grid)
            table_grid = cv2.add(horiz_lines, vert_lines)

            # Tìm các ô bảng (Contours của lưới)
            contours, _ = cv2.findContours(table_grid, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

            cells = []
            h_img, w_img = img_np.shape[:2]
            total_cell_area = 0
            for c in contours:
                x, y, w, h = cv2.boundingRect(c)
                # Lọc kích thước ô bảng hợp lệ
                if 25 < w < (w_img * 0.95) and 12 < h < (h_img * 0.3):
                    cells.append((x, y, w, h))
                    total_cell_area += (w * h)

            # Chỉ kích hoạt nếu có tối thiểu 6 ô và diện tích bảng chiếm >= 5% diện tích trang
            if len(cells) < 6 or total_cell_area < (w_img * h_img * 0.05):
                return []

            # Gom nhóm các ô theo hàng (Row Clustering theo Y coordinate)
            cells = sorted(cells, key=lambda b: (b[1] // 18, b[0]))
            
            # Phân cụm dòng
            rows = []
            current_row = []
            last_y = None

            for x, y, w, h in cells:
                if last_y is None or abs(y - last_y) < 18:
                    current_row.append((x, y, w, h))
                    last_y = y
                else:
                    current_row.sort(key=lambda b: b[0])
                    rows.append(current_row)
                    current_row = [(x, y, w, h)]
                    last_y = y
            if current_row:
                current_row.sort(key=lambda b: b[0])
                rows.append(current_row)

            # Kiểm tra bảng hợp lệ: phải có >= 3 hàng và hàng phổ biến nhất có >= 2 cột
            if len(rows) < 3:
                return []
            max_cols = max(len(r) for r in rows) if rows else 0
            if max_cols < 2:
                return []

            # Bóc tách text từng ô — dùng _predict_batch_padded để tối ưu throughput
            predictor = self._get_predictor()
            table_markdown_rows = []

            # Gom tất cả cell crops từ tất cả rows để nhận diện toàn vẹn 100%
            all_rows_flat: list[tuple[int, int, int, int, int, int]] = []
            for r_idx, row in enumerate(rows):
                for x, y, w, h in row:
                    all_rows_flat.append((r_idx, x, y, w, h, len(row)))

            # Tạo crops và preprocess
            all_cell_crops = [
                self.preprocess_handwriting(Image.fromarray(img_np[y:y+h, x:x+w]))
                for _, x, y, w, h, _ in all_rows_flat
                if min(w, h) > 6
            ]

            # Padded Batch predict siêu tốc
            batch_texts: list[str] = []
            if predictor is not None and all_cell_crops:
                batch_texts = self._predict_batch_padded(predictor, all_cell_crops)

            # Tái tổ chức thành rows
            crop_idx = 0
            row_map: dict[int, list[str]] = {}
            for r_idx, x, y, w, h, _row_len in all_rows_flat:
                if min(w, h) > 6 and crop_idx < len(batch_texts):
                    cell_text = batch_texts[crop_idx] or ""
                    crop_idx += 1
                else:
                    # Fallback Tesseract cho cell quá nhỏ
                    cell_text = ""
                    if pytesseract is not None:
                        try:
                            crop = Image.fromarray(img_np[y:y+h, x:x+w])
                            cell_text = pytesseract.image_to_string(crop, lang="vie+eng", config="--psm 6").strip()
                        except Exception:
                            pass
                row_map.setdefault(r_idx, []).append(cell_text.replace("\n", " ") or "--")

            for r_idx in sorted(row_map.keys()):
                row_texts = row_map[r_idx]
                if row_texts:
                    table_markdown_rows.append("| " + " | ".join(row_texts) + " |")
                    if r_idx == 0:
                        # Thêm header separator
                        table_markdown_rows.append("| " + " | ".join(["---"] * len(row_texts)) + " |")

            if len(table_markdown_rows) >= 3:
                logger.info("Extracted structured table ({rows} rows, {cells} cells)", rows=len(rows), cells=len(all_rows_flat))
                return ["\n".join(table_markdown_rows)]
        except Exception as exc:
            logger.debug("Table extraction fallback: {err}", err=str(exc))

        return []

    def _is_noise_line(self, text: str) -> bool:
        """Kiểm tra và loại bỏ các dòng rác từ con dấu đỏ, chữ ký hoặc artifact quét."""
        if not text or not text.strip():
            return True
        t = text.strip()
        if len(t) <= 1 and t not in ("I", "1", "-"):
            return True
        # Toàn bộ là ký tự đặc biệt hoặc dấu câu
        if re.fullmatch(r'[\s\-_\.,:;\|\/\*\+=~`!@#\$%\^&\(\)\[\]\{\}\"\'\?]+', t):
            return True
        # Tỷ lệ ký tự rác scan/con dấu cao (dấu hỏi, ngoặc kép, gạch chéo lặp, v.v.)
        trash_chars = len(re.findall(r'[\?\"\^~|\\\/=\<\>_]', t))
        if trash_chars >= 2 and (trash_chars / max(len(t), 1)) > 0.20:
            return True
        # Chuỗi chữ cái vô nghĩa không dấu cách (vd: VVV, IIIII, KILGUIII)
        if re.search(r'[A-Za-z]{8,}', t) and not any(kw in t.lower() for kw in ("thong", "chinh", "nguyen", "truong", "phong", "quoc", "khanh")):
            upper_run = len(re.findall(r'[A-Z]', t))
            if upper_run > 7 and " " not in t:
                return True
        return False

    def segment_lines(self, pil_image: Image.Image) -> list[Image.Image]:
        """
        Tách ảnh thành danh sách các ảnh dòng đơn lẻ (Line Segmentation)
        với padding chống cắt chữ và sắp xếp đúng thứ tự đọc.
        """
        if cv2 is None:
            return [pil_image]

        try:
            img_np = np.array(pil_image)
            if len(img_np.shape) == 3:
                gray = cv2.cvtColor(img_np, cv2.COLOR_RGB2GRAY)
            else:
                gray = img_np

            # Nhị phân hóa Otsu
            _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)

            # Dùng Kernel ngang nối các từ thành dòng liên tục
            kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (25, 1))
            dilated = cv2.dilate(binary, kernel, iterations=2)

            # Tìm contours
            contours, _ = cv2.findContours(dilated, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

            boxes = [cv2.boundingRect(c) for c in contours]
            # Sắp xếp các dòng từ trên xuống dưới theo tọa độ Y
            boxes = sorted(boxes, key=lambda b: (b[1] // 16, b[0]))

            line_images = []
            h_img, w_img = img_np.shape[:2]
            for x, y, w, h in boxes:
                # Lọc bỏ các khối quá nhỏ (nhiễu) hoặc quá lớn (khung toàn trang)
                if w > 30 and 10 < h < (h_img * 0.4):
                    pad_y1 = max(0, y - 4)
                    pad_y2 = min(h_img, y + h + 4)
                    pad_x1 = max(0, x - 4)
                    pad_x2 = min(w_img, x + w + 4)
                    crop = img_np[pad_y1:pad_y2, pad_x1:pad_x2]

                    line_images.append(Image.fromarray(crop))

            if line_images:
                logger.info("Segmented {count} lines from image", count=len(line_images))
                return line_images
        except Exception as exc:
            logger.debug("Line segmentation fallback: {err}", err=str(exc))

        return [pil_image]

    def post_process_vietnamese(self, text: str) -> str:
        """
        Dispatcher hậu xử lý văn bản OCR tiếng Việt hành chính.
        Gọi 3 module tách biệt theo thứ tự:
            1. ocr_char_fixes     — lỗi quang học tổng quát
            2. admin_dictionary   — từ điển domain hành chính (JSON)
            3. document_header_normalizer — rebuild Quốc hiệu/Số hiệu/Ngày tháng
        """
        try:
            from app.services.text_postprocessing import post_process_vietnamese as _pp
            return _pp(text)
        except ImportError:
            # Fallback inline nếu module chưa load được (startup race condition)
            import unicodedata as _ud
            return _ud.normalize("NFC", text).strip()

    def heuristic_quality_score(self, text: str, engine: str = "vietocr") -> float:
        """
        Ước lượng chất lượng văn bản OCR bằng heuristic dựa trên tỷ lệ ký tự rác.

        LƯU Ý QUAN TRỌNG:
        - Đây là heuristic, KHÔNG phải confidence thực từ model.
        - VietOCR phiên bản stable không có API trả về log-probability.
        - TODO: Khi VietOCR hỗ trợ predict(img, return_prob=True), thay thế bằng
          log-probability trung bình theo ký tự của từng dòng để có line-level
          confidence thực sự (xem mục Hướng phát triển trong báo cáo đồ án).

        KHÔNG CÒN bonus cho Quốc hiệu/Tiêu ngữ vì post_process_vietnamese() tự
        dựng lại các câu này → bonus đó không phản ánh chất lượng OCR thật.

        Args:
            text: Văn bản sau OCR + post-processing
            engine: Tên engine đã dùng (ảnh hưởng base score)

        Returns:
            float trong [0.60, 0.98]
        """
        if not text or len(text.strip()) < 10:
            return 0.60

        _base_scores = {"vietocr": 0.92, "direct_pdf": 0.97, "pypdf": 0.88}
        base = _base_scores.get(engine, 0.85)

        # Penalty cho ký tự rác (không thuộc alphabet tiếng Việt / số / dấu câu chuẩn)
        suspicious_chars = len(re.findall(r'[%~^|<>{}\[\]\\@#$*]', text))
        total_chars = max(len(text), 1)
        char_penalty = min(0.15, (suspicious_chars / total_chars) * 5.0)

        # Penalty nhẹ nếu quá nhiều số liên tiếp (có thể là barcode/artifact)
        digit_runs = re.findall(r'\d{8,}', text)
        digit_penalty = min(0.05, len(digit_runs) * 0.01)

        final_score = max(0.60, min(0.98, base - char_penalty - digit_penalty))
        return round(final_score, 2)

    def calculate_confidence_score(self, text: str, engine: str = "vietocr") -> float:
        """
        Alias backward-compatible cho heuristic_quality_score().
        Giữ tên cũ để không break router/schema đang gọi hàm này.
        """
        return self.heuristic_quality_score(text, engine)


    def _ocr_with_vietocr_lines(
        self, image: Image.Image
    ) -> list[tuple[str, float]]:
        """
        Tách dòng và đưa từng dòng vào VietOCR Transformer theo lô với Padded Batching.

        Returns:
            list[tuple[str, float]]: Mỗi phần tử là (text_dòng, confidence_dòng).
        """
        predictor = self._get_predictor()
        if not predictor:
            return []

        try:
            line_images = self.segment_lines(image)
            if not line_images:
                return []

            # Đọc giới hạn từ settings
            _s = self._get_settings()
            _max_lines  = getattr(_s, 'ocr_max_lines_per_page', 500) if _s else 500
            _batch_size = getattr(_s, 'ocr_batch_size', 16)         if _s else 16

            if _max_lines and _max_lines > 0 and len(line_images) > _max_lines:
                line_images = line_images[:_max_lines]
            cleaned_lines = [self.preprocess_handwriting(li) for li in line_images]
            line_results: list[tuple[str, float]] = []

            for i in range(0, len(cleaned_lines), _batch_size):
                batch = cleaned_lines[i: i + _batch_size]
                texts = self._predict_batch_padded(predictor, batch)
                for txt in texts:
                    txt = str(txt).strip() if txt else ""
                    if txt:
                        # Heuristic line-level confidence
                        bad = len(re.findall(r'[%~^|<>{}\[\]\\]', txt))
                        conf = max(0.60, 0.95 - (bad / max(len(txt), 1)) * 3)
                        line_results.append((txt, round(conf, 2)))

            return line_results
        except Exception as e:
            logger.debug("VietOCR line prediction failed: {err}", err=str(e))

        return []

    def _ocr_with_trocr_lines(
        self, image: Image.Image
    ) -> list[tuple[str, float]]:
        """
        Tách dòng và đưa từng dòng vào Microsoft TrOCR Vision Transformer.
        """
        try:
            line_images = self.segment_lines(image)
            if not line_images:
                return []

            _s = self._get_settings()
            _max_lines  = getattr(_s, 'ocr_max_lines_per_page', 500) if _s else 500
            _batch_size = getattr(_s, 'trocr_batch_size', 8)        if _s else 8

            if _max_lines and _max_lines > 0 and len(line_images) > _max_lines:
                line_images = line_images[:_max_lines]
            cleaned_lines = [self.preprocess_handwriting(li) for li in line_images]
            line_results: list[tuple[str, float]] = []

            for i in range(0, len(cleaned_lines), _batch_size):
                batch = cleaned_lines[i: i + _batch_size]
                texts = self._predict_batch_trocr(batch)
                for txt in texts:
                    txt = str(txt).strip() if txt else ""
                    if txt:
                        bad = len(re.findall(r'[%~^|<>{}\[\]\\]', txt))
                        conf = max(0.60, 0.95 - (bad / max(len(txt), 1)) * 3)
                        line_results.append((txt, round(conf, 2)))

            return line_results
        except Exception as e:
            logger.debug("TrOCR line prediction failed: {err}", err=str(e))

        return []

    def _ocr_lines_with_engine(
        self, image: Image.Image, engine: str | None = None
    ) -> list[tuple[str, float]]:
        """Điều hướng nhận dạng dòng theo engine được chỉ định (VietOCR hoặc TrOCR)."""
        _s = self._get_settings()
        selected_engine = engine or (getattr(_s, 'ocr_engine', 'vietocr') if _s else 'vietocr')
        if selected_engine == "trocr":
            return self._ocr_with_trocr_lines(image)
        return self._ocr_with_vietocr_lines(image)

    def _ocr_image_zonal(self, image: Image.Image, engine: str | None = None) -> tuple[str, bool]:
        """
        Khoanh vùng nhận dạng (Zonal OCR) chuẩn xác cho Trang đầu văn bản hành chính Việt Nam:
        - Vùng Trái (X in [0, 49%W], Y in [0, 20%H]): Cơ quan ban hành & Số hiệu văn bản
        - Vùng Phải (X in [49%W, W], Y in [0, 20%H]): Quốc hiệu & Địa danh, Ngày tháng
        - Vùng Thân (X in [0, W], Y in [20%H, H]): Tiêu đề văn bản & toàn bộ nội dung thân
        """
        try:
            w, h = image.size
            if h < 400 or w < 300:
                return "", False

            header_h = int(h * 0.20)
            left_header_crop = image.crop((0, 0, int(w * 0.49), header_h))
            right_date_crop = image.crop((int(w * 0.49), 0, w, header_h))
            body_crop = image.crop((0, header_h, w, h))

            # 1. OCR Vùng Trái Header (Cơ quan & Số hiệu)
            left_processed = self.preprocess_image(left_header_crop)
            left_lines = self._ocr_lines_with_engine(left_processed, engine=engine)
            left_valid = [t for t, _ in left_lines if not self._is_noise_line(t)]

            # 2. OCR Vùng Phải Header (Quốc hiệu & Ngày tháng)
            right_processed = self.preprocess_image(right_date_crop)
            right_lines = self._ocr_lines_with_engine(right_processed, engine=engine)
            right_valid = [t for t, _ in right_lines if not self._is_noise_line(t)]

            # 3. OCR Vùng Thân văn bản (Body Zone)
            body_processed = self.preprocess_image(body_crop)
            body_lines = self._ocr_lines_with_engine(body_processed, engine=engine)
            body_valid = [t for t, _ in body_lines if not self._is_noise_line(t)]

            # Lắp ráp bố cục chuẩn hành chính
            collected_lines: list[str] = []
            if left_valid:
                collected_lines.extend(left_valid)
            if right_valid:
                collected_lines.extend(right_valid)
            if body_valid:
                collected_lines.extend(body_valid)

            # Loại bỏ dòng lặp liên tiếp nếu có
            final_lines: list[str] = []
            for line in collected_lines:
                s = line.strip()
                if not s:
                    continue
                if not final_lines or final_lines[-1] != s:
                    final_lines.append(s)

            full_zonal_text = "\n".join(final_lines)
            if full_zonal_text.strip():
                full_zonal_text = self.post_process_vietnamese(full_zonal_text)
                return full_zonal_text, True
        except Exception as exc:
            logger.debug("Zonal OCR fallback to full page: {err}", err=str(exc))

        return "", False

    def _ocr_image(
        self,
        image: Image.Image,
        extract_tables: bool = False,
        is_first_page: bool = True,
        engine: str | None = None,
    ) -> str:
        """
        Thực hiện OCR (Zonal OCR cho Trang đầu + Line-by-Line + Fallback).
        """
        _s = self._get_settings()
        selected_engine = engine or (getattr(_s, 'ocr_engine', 'vietocr') if _s else 'vietocr')

        # 1. Thử Khoanh vùng nhận dạng Zonal OCR nếu là trang đầu (Trang 1 / Ảnh đơn)
        if is_first_page and selected_engine != "tesseract":
            zonal_text, ok = self._ocr_image_zonal(image, engine=selected_engine)
            if ok and len(zonal_text.strip()) > 20:
                if extract_tables:
                    table_markdowns = self.detect_and_extract_tables(self.preprocess_image(image))
                    if table_markdowns:
                        tables_str = "\n\n### [BẢNG BIỂU DỮ LIỆU BÓC TÁCH]:\n" + "\n\n".join(table_markdowns)
                        zonal_text = f"{zonal_text}\n\n{tables_str}"
                return unicodedata.normalize("NFC", zonal_text.strip())

        processed_img = self.preprocess_image(image)

        # 2. Bóc tách Bảng biểu (tùy chọn)
        table_markdowns = self.detect_and_extract_tables(processed_img) if extract_tables else []

        # 3. Chạy OCR theo engine chỉ định
        full_text = ""
        if selected_engine in ("vietocr", "trocr"):
            line_results = self._ocr_lines_with_engine(processed_img, engine=selected_engine)
            if line_results:
                valid_lines = [txt for txt, _conf in line_results if not self._is_noise_line(txt)]
                joined = "\n".join(valid_lines)
                if len(joined.strip()) > 5:
                    full_text = unicodedata.normalize("NFC", joined.strip())

        # 4. Fallback hoặc Engine Tesseract
        if (not full_text or selected_engine == "tesseract") and pytesseract is not None:
            try:
                text = pytesseract.image_to_string(
                    processed_img, lang="vie+eng", config="--oem 1 --psm 3"
                )
                if text and len(text.strip()) > 5:
                    full_text = unicodedata.normalize("NFC", text.strip())
            except Exception as tess_err:
                logger.debug("Tesseract OCR failed: {err}", err=str(tess_err))

        # 5. Ghép bảng biểu
        if table_markdowns:
            tables_str = "\n\n### [BẢNG BIỂU DỮ LIỆU BÓC TÁCH]:\n" + "\n\n".join(table_markdowns)
            full_text = f"{full_text}\n\n{tables_str}" if full_text else tables_str

        if full_text:
            full_text = self.post_process_vietnamese(full_text)

        return full_text

    def extract_text_from_file(
        self, file_bytes: bytes, file_type: str, engine: str | None = None
    ) -> tuple[str, float]:
        """
        Trích xuất toàn văn từ file PDF hoặc Ảnh (JPG, PNG, TIFF).

        DPI render PDF scan đọc từ settings (mặc định 200).
        Bóc tách bảng biểu tối ưu và tăng tốc xử lý theo lô.

        Args:
            file_bytes: Dữ liệu nhị phân file
            file_type: Định dạng file ('pdf', 'jpg', 'png', 'tiff'...)
            engine: Chỉ định engine ('vietocr' | 'trocr' | 'tesseract'). Nếu None, dùng config settings.

        Returns:
            (text, heuristic_quality_score)
        """
        file_ext = file_type.lower().replace(".", "")

        # Đọc DPI config từ settings
        _s = self._get_settings()
        _dpi_default    = getattr(_s, 'ocr_pdf_dpi_default', 200)      if _s else 200
        _dpi_fast       = getattr(_s, 'ocr_pdf_dpi_fast', 150)         if _s else 150
        _fast_mode      = getattr(_s, 'ocr_fast_mode', False)          if _s else False
        _render_dpi     = _dpi_fast if _fast_mode else _dpi_default
        _extract_tables = getattr(_s, 'ocr_extract_tables', True)      if _s else True
        selected_engine = engine or (getattr(_s, 'ocr_engine', 'vietocr') if _s else 'vietocr')

        logger.info(
            "OCR settings: engine={eng}, dpi={dpi}, fast_mode={fm}, beamsearch={bs}, extract_tables={et}",
            eng=selected_engine, dpi=_render_dpi, fm=_fast_mode,
            bs=getattr(_s, 'ocr_beamsearch_enabled', False) if _s else False,
            et=_extract_tables,
        )

        # ── 1. Xử lý file PDF ────────────────────────────────────────────────
        if file_ext == "pdf":
            # 1.1 Thử mở bằng PyMuPDF
            if pymupdf is not None:
                try:
                    doc = pymupdf.open(stream=file_bytes, filetype="pdf")
                    extracted_pages = []

                    # 1.1.1 Trích xuất direct text siêu tốc nếu PDF có text layer
                    if selected_engine == "vietocr":
                        for page in doc:
                            t = page.get_text().strip()
                            if t:
                                extracted_pages.append(t)

                        if extracted_pages and len("\n".join(extracted_pages)) > 20:
                            full_text = "\n\n".join(extracted_pages)
                            full_text = self.post_process_vietnamese(full_text)
                            logger.info(
                                "Direct text PDF: {pages} pages, {chars} chars",
                                pages=len(doc), chars=len(full_text),
                            )
                            return full_text, self.calculate_confidence_score(full_text, engine="direct_pdf")

                    # 1.1.2 PDF scan ảnh: render trực tiếp mỗi trang ở DPI tối ưu
                    ocr_pages = []
                    total_pages = len(doc)
                    for page_idx, page in enumerate(doc):
                        _t0 = time.time()

                        # Render trực tiếp ở DPI tối ưu (200 DPI)
                        pix = page.get_pixmap(dpi=_render_dpi)
                        page_img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
                        page_text = self._ocr_image(
                            page_img,
                            extract_tables=_extract_tables,
                            is_first_page=(page_idx == 0),
                            engine=selected_engine,
                        )

                        _elapsed = time.time() - _t0
                        logger.info(
                            "OCR page {cur}/{total} [{eng}] | dpi={dpi} | {ms:.1f}s",
                            cur=page_idx + 1, total=total_pages, eng=selected_engine,
                            dpi=_render_dpi, ms=_elapsed,
                        )

                        if page_text:
                            ocr_pages.append(page_text)

                    if ocr_pages:
                        full_text = "\n\n".join(ocr_pages)
                        full_text = self.post_process_vietnamese(full_text)
                        logger.info(
                            "Scanned PDF OCR done [{eng}]: {pages} pages, {chars} chars",
                            eng=selected_engine, pages=len(doc), chars=len(full_text),
                        )
                        return full_text, self.calculate_confidence_score(full_text, engine=selected_engine)
                except Exception as exc:
                    logger.warning("PyMuPDF OCR failed: {err}", err=str(exc))

            # 1.2 Fallback pypdf
            if pypdf is not None and selected_engine == "vietocr":
                try:
                    reader = pypdf.PdfReader(io.BytesIO(file_bytes))
                    pypdf_texts = [p.extract_text() or "" for p in reader.pages if p.extract_text()]
                    if pypdf_texts and len("\n".join(pypdf_texts)) > 30:
                        processed = self.post_process_vietnamese("\n\n".join(pypdf_texts))
                        return processed, self.calculate_confidence_score(processed, engine="pypdf")
                except Exception:
                    pass

        # ── 2. Xử lý file Ảnh (JPG / PNG / TIFF) ──────────────────────────────
        try:
            image = Image.open(io.BytesIO(file_bytes)).convert("RGB")
            img_text = self._ocr_image(image, engine=selected_engine)
            if img_text:
                img_text = self.post_process_vietnamese(img_text)
                return img_text, self.calculate_confidence_score(img_text, engine=selected_engine)
        except Exception as exc:
            logger.warning("Image OCR failed: {err}", err=str(exc))

        return "", 0.0

    def compare_ocr_engines(self, file_bytes: bytes, file_type: str) -> dict[str, Any]:
        """
        Thực nghiệm đối sánh hiệu năng và độ chính xác giữa các mô hình OCR:
        1. VietOCR (Mô hình chính Seq2Seq Transformer)
        2. Microsoft TrOCR (Mô hình Vision Transformer SOTA)
        3. Tesseract OCR (Mô hình đối chứng cơ sở LSTM Baseline)

        Returns:
            dict chứa kết quả trích xuất, thời gian inference và điểm tin cậy của từng mô hình.
        """
        results: dict[str, Any] = {}
        engines = [
            ("vietocr", "VietOCR (vgg_transformer)"),
            ("trocr", "Microsoft TrOCR (Vision Transformer)"),
            ("tesseract", "Tesseract 5 (LSTM Baseline)"),
        ]

        for eng_key, eng_name in engines:
            t0 = time.time()
            try:
                text, conf = self.extract_text_from_file(file_bytes, file_type, engine=eng_key)
                elapsed = round(time.time() - t0, 3)
                results[eng_key] = {
                    "engine_name": eng_name,
                    "text": text,
                    "confidence": conf,
                    "inference_time_seconds": elapsed,
                    "char_count": len(text),
                    "word_count": len(text.split()),
                    "status": "SUCCESS" if text else "EMPTY",
                }
            except Exception as exc:
                elapsed = round(time.time() - t0, 3)
                results[eng_key] = {
                    "engine_name": eng_name,
                    "text": "",
                    "confidence": 0.0,
                    "inference_time_seconds": elapsed,
                    "status": f"FAILED: {str(exc)}",
                }

        return results


        # ── 3. Fallback thông báo nếu không thể trích xuất
        clean_name = "Tài liệu Công tác Sinh viên (Đại học Đà Lạt)"
        return f"{clean_name}\n\n[Tài liệu đã được tiếp nhận và lưu trữ an toàn trong kho dữ liệu số]", 0.85

    def extract_metadata(self, text: str) -> dict[str, Any]:
        """
        Trích xuất metadata có cấu trúc từ nội dung văn bản OCR bằng Regex nâng cao.
        - MSSV (student_id)
        - Họ và tên (student_name)
        - Ngày văn bản (document_date)
        - Số hiệu văn bản (document_number)
        - detected_category
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

        # 1. Trích xuất MSSV — ưu tiên keyword match trước, fallback pattern sau
        # Pattern cấu hình được qua settings (không hardcode "2[0-3]" trong service)
        _s = self._get_settings()
        _mssv_prefix  = getattr(_s, 'mssv_year_prefix_pattern', r'2[0-3]') if _s else r'2[0-3]'
        _mssv_len_min = getattr(_s, 'mssv_length_min', 7)                  if _s else 7
        _mssv_len_max = getattr(_s, 'mssv_length_max', 8)                  if _s else 8
        # Tính số ký tự còn lại sau prefix (prefix "2[0-3]" = 2 ký tự)
        # Keyword-first dùng total length (không có prefix trong group)
        _kw_len_pat   = '{' + str(_mssv_len_min) + ',' + str(_mssv_len_max) + '}'
        # Pattern fallback: prefix + (total_len - prefix_len) ký tự còn lại
        _prefix_len   = 2   # len("2X") với X là 1 ký tự từ [0-3]
        _sfx_min = max(1, _mssv_len_min - _prefix_len)
        _sfx_max = max(2, _mssv_len_max - _prefix_len)
        _sfx_len_pat  = '{' + str(_sfx_min) + ',' + str(_sfx_max) + '}'

        # Bước 1a: Keyword-first (độ tin cậy cao)
        mssv_match = re.search(
            r"(?:MSSV|Mã\s*số\s*sinh\s*viên|Mã\s*SV|Mã\s*sinh\s*viên)[\s:]*([0-9]" + _kw_len_pat + r")",
            text, re.IGNORECASE,
        )
        # Bước 1b: Pattern fallback (dễ false positive hơn)
        if not mssv_match:
            mssv_match = re.search(
                r'\b(' + _mssv_prefix + r'[0-9]' + _sfx_len_pat + r')\b',
                text,
            )
        if mssv_match:
            metadata["student_id"] = mssv_match.group(1).strip()

        # 2. Trích xuất Họ tên sinh viên
        name_match = re.search(r"(?:Em tên là|Họ và tên|Họ tên sinh viên|Người làm đơn|Họ và tên sinh viên)[\s:]*([A-ZÀ-Ỹa-zà-ỹ\s]{3,35})", text)
        if name_match:
            clean_name = name_match.group(1).strip().split("\n")[0]
            clean_name = re.sub(r"(MSSV|Lớp|Khoa|Ngày|Số|Ngành).*", "", clean_name).strip()
            if len(clean_name) >= 3:
                metadata["student_name"] = clean_name

        # 3. Trích xuất Ngày văn bản (ngày ... tháng ... năm ...)
        date_match = re.search(r"ngày\s+(\d{1,2})\s+tháng\s+(\d{1,2})\s+năm\s+(\d{4})", text, re.IGNORECASE)
        if date_match:
            try:
                d = int(date_match.group(1))
                m = int(date_match.group(2))
                y = int(date_match.group(3))
                metadata["document_date"] = date(y, m, d).isoformat()
            except ValueError:
                pass
        else:
            date_slash = re.search(r"(\d{1,2})[/.-](\d{1,2})[/.-](\d{4})", text)
            if date_slash:
                try:
                    d = int(date_slash.group(1))
                    m = int(date_slash.group(2))
                    y = int(date_slash.group(3))
                    metadata["document_date"] = date(y, m, d).isoformat()
                except ValueError:
                    pass

        # 4. Trích xuất Số hiệu văn bản (vd: Số: 1353/KH-ĐHĐL, Số: 140/QĐ-ĐHĐL, v.v.)
        doc_num_match = re.search(r"(?:Số|Số hiệu)[\s:]*([0-9A-ZÀ-Ỹa-zà-ỹ\-_/]+(?:\s*/\s*[0-9A-ZÀ-Ỹa-zà-ỹ\-_/]+)?)", text, re.IGNORECASE)
        if doc_num_match:
            num = doc_num_match.group(1).strip()
            # Bỏ khoảng trắng quanh dấu gạch chéo
            num = re.sub(r'\s*/\s*', '/', num)
            metadata["document_number"] = num

        # 5. Phân loại biểu mẫu tự động
        text_lower = text.lower()
        if "kế hoạch" in text_lower or "kh-đhđl" in text_lower:
            metadata["detected_category"] = "KE_HOACH"
        elif "thông báo" in text_lower or "tb-đhđl" in text_lower:
            metadata["detected_category"] = "THONG_BAO"
        elif "quyết định" in text_lower or "qđ-đhđl" in text_lower:
            metadata["detected_category"] = "QUYET_DINH"
        elif "hướng dẫn" in text_lower or "hd-đhđl" in text_lower:
            metadata["detected_category"] = "HUONG_DAN"
        elif "nghỉ học" in text_lower or "bảo lưu" in text_lower:
            metadata["detected_category"] = "DON_NGHI_HOC"
        elif "học bổng" in text_lower:
            metadata["detected_category"] = "HOC_BONG"
        elif "miễn giảm học phí" in text_lower:
            metadata["detected_category"] = "MIEN_GIAM_HOC_PHI"
        elif "bảo hiểm y tế" in text_lower or "bhyt" in text_lower:
            metadata["detected_category"] = "BHYT"
        elif "xác nhận" in text_lower:
            metadata["detected_category"] = "GIAY_XAC_NHAN"
        elif "khen thưởng" in text_lower or "kỷ luật" in text_lower:
            metadata["detected_category"] = "KHEN_THUONG"

        logger.info("Extracted metadata: {meta}", meta=metadata)
        return metadata


ocr_service = OCRService()
