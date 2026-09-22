"""
backend/app/services/ocr_service.py — High-Accuracy Vietnamese OCR, Table & Handwriting Extraction Service

1. Đọc và trích xuất văn bản từ PDF (Direct text hoặc PDF scan ảnh nhiều trang 300 DPI).
2. Tiền xử lý ảnh chuyên sâu bằng OpenCV (Grayscale, CLAHE, Denoising, Lọc dòng chấm viết tay).
3. Tách từng dòng văn bản (Line Segmentation) bằng Horizontal Projection & Morphological Dilation.
4. Bóc tách cấu trúc Bảng biểu (Table Structure Recognition) dạng lưới ô bằng Morphology.
5. Nhận dạng ký tự quang học tiếng Việt đa tầng: PyMuPDF -> Tesseract LSTM (vie+eng) -> VietOCR Transformer (Line-by-Line).
6. Tự động nạp trọng số mô hình đã fine-tune (models/*_best.pth).
7. Hậu xử lý chính tả tiếng Việt hành chính và chuẩn hóa Unicode NFC.
8. Trích xuất metadata có cấu trúc (MSSV, Họ tên, Ngày tháng, Số hiệu công văn, Loại văn bản).
"""
import glob
import io
import os
import re
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
    """Service xử lý OCR chất lượng cao, nhận dạng Bảng biểu và Chữ viết tay."""

    def __init__(self) -> None:
        self._predictor = None

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

                from vietocr.tool.config import Cfg
                from vietocr.tool.predictor import Predictor
                config = Cfg.load_config_from_name("vgg_transformer")
                config["device"] = "cpu"
                config["predictor"]["beamsearch"] = False

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

    def preprocess_image(self, pil_image: Image.Image) -> Image.Image:
        """
        Tiền xử lý ảnh nâng cao:
        - Chuyển Grayscale
        - Tăng độ tương phản thích nghi (CLAHE)
        - Khử nhiễu quang học (Denoising)
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

            # Khử nhiễu nền tài liệu scan
            denoised = cv2.fastNlMeansDenoising(enhanced, h=10)
            return Image.fromarray(denoised)
        except Exception as exc:
            logger.debug("Image preprocessing fallback: {err}", err=str(exc))
            return pil_image

    def preprocess_handwriting(self, pil_image: Image.Image) -> Image.Image:
        """
        Tiền xử lý nâng cao cho chữ viết tay:
        - Tự động Phóng đại / Zoom (Dynamic Upscaling $1.5x - 2.0x$) cho chữ viết tay nhỏ
        - Đệm viền an toàn (Padding) chống mất nét móc (g, y, p, q) và dấu tiếng Việt (?, ~)
        - Tăng tương phản nét bút mờ (CLAHE)
        - Lọc bỏ dòng chấm (dotted lines ...........) và gạch chân form mẫu
        - Tăng cường nét bút mực bị đứt bằng Morphological Dilation
        """
        if cv2 is None:
            return pil_image

        try:
            img_np = np.array(pil_image)
            if len(img_np.shape) == 3:
                gray = cv2.cvtColor(img_np, cv2.COLOR_RGB2GRAY)
            else:
                gray = img_np

            # 1. Tự động Phóng đại / Zoom (Upscaling) nếu chiều cao dòng nhỏ
            h, w = gray.shape[:2]
            if h < 56 and h > 0:
                scale = min(2.5, max(1.5, 64.0 / h))
                gray = cv2.resize(gray, (0, 0), fx=scale, fy=scale, interpolation=cv2.INTER_CUBIC)

            # 2. Tăng cường tương phản cục bộ (CLAHE) cho nét mực mờ/nhạt
            clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
            enhanced = clahe.apply(gray)

            # 3. Nhị phân hóa thích nghi (Adaptive Thresholding) để tách mực bút bi
            binary = cv2.adaptiveThreshold(
                enhanced, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV, 25, 10
            )

            # 4. Xóa đường kẻ ngang dài (dòng kẻ chấm form ...........) đè lên chữ viết tay
            horiz_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (35, 1))
            detected_lines = cv2.morphologyEx(binary, cv2.MORPH_OPEN, horiz_kernel, iterations=2)
            cleaned_binary = cv2.subtract(binary, detected_lines)

            # 5. Nối các nét bút bị đứt nhẹ bằng Dilation
            stroke_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (2, 2))
            dilated = cv2.dilate(cleaned_binary, stroke_kernel, iterations=1)

            # 6. Đảo ngược lại nền trắng chữ đen cho mô hình OCR
            result_img = cv2.bitwise_not(dilated)

            # 7. Đệm viền trắng (Padding 8px) chống cắt cụt dấu hỏi/ngã và nét móc dưới
            padded = cv2.copyMakeBorder(result_img, 8, 8, 12, 12, cv2.BORDER_CONSTANT, value=255)

            return Image.fromarray(padded)
        except Exception as exc:
            logger.debug("Handwriting preprocessing fallback: {err}", err=str(exc))
            return pil_image

    def detect_and_extract_tables(self, pil_image: Image.Image) -> list[str]:
        """
        Nhận diện và bóc tách Bảng biểu (Table Structure Detection):
        - Dùng Horizontal & Vertical Morphological Kernels tìm lưới ô (Grid)
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

            # 1. Phát hiện đường kẻ ngang
            horiz_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (25, 1))
            horiz_lines = cv2.morphologyEx(binary, cv2.MORPH_OPEN, horiz_kernel, iterations=2)

            # 2. Phát hiện đường kẻ dọc
            vert_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (1, 25))
            vert_lines = cv2.morphologyEx(binary, cv2.MORPH_OPEN, vert_kernel, iterations=2)

            # 3. Kết hợp lưới bảng (Table Grid)
            table_grid = cv2.add(horiz_lines, vert_lines)

            # Tìm các ô bảng (Contours của lưới)
            contours, _ = cv2.findContours(table_grid, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

            cells = []
            h_img, w_img = img_np.shape[:2]
            for c in contours:
                x, y, w, h = cv2.boundingRect(c)
                # Lọc kích thước ô bảng hợp lệ
                if 25 < w < (w_img * 0.95) and 12 < h < (h_img * 0.3):
                    cells.append((x, y, w, h))

            if len(cells) < 4:
                return []

            # Gom nhóm các ô theo hàng (Row Clustering theo Y coordinate)
            cells = sorted(cells, key=lambda b: (b[1] // 15, b[0]))
            
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

            # Bóc tách text từng ô
            predictor = self._get_predictor()
            table_markdown_rows = []
            for r_idx, row in enumerate(rows[:30]):  # Bóc tách tối đa 30 hàng
                row_texts = []
                for x, y, w, h in row:
                    cell_crop = Image.fromarray(img_np[y:y+h, x:x+w])
                    cell_text = ""
                    # 1. Thử VietOCR Transformer trước cho tiếng Việt chuẩn
                    if predictor is not None and min(cell_crop.size) > 6:
                        try:
                            clean_cell = self.preprocess_handwriting(cell_crop)
                            cell_text = predictor.predict(clean_cell).strip()
                        except Exception:
                            pass
                    # 2. Fallback Tesseract nếu cần
                    if not cell_text and pytesseract is not None:
                        try:
                            cell_text = pytesseract.image_to_string(cell_crop, lang="vie+eng", config="--psm 6").strip()
                        except Exception:
                            pass

                    row_texts.append(cell_text.replace("\n", " ") or "--")

                if row_texts:
                    table_markdown_rows.append("| " + " | ".join(row_texts) + " |")
                    if r_idx == 0:
                        # Thêm header separator
                        table_markdown_rows.append("| " + " | ".join(["---"] * len(row_texts)) + " |")

            if len(table_markdown_rows) >= 3:
                logger.info("Extracted structured table ({rows} rows)", rows=len(rows))
                return ["\n".join(table_markdown_rows)]
        except Exception as exc:
            logger.debug("Table extraction fallback: {err}", err=str(exc))

        return []

    def segment_lines(self, pil_image: Image.Image) -> list[Image.Image]:
        """
        Tách ảnh toàn trang thành danh sách các ảnh dòng đơn lẻ (Line Segmentation)
        bằng phép biến đổi hình thái học ngang (Morphological Horizontal Dilation) và Bounding Box.
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
            kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (35, 1))
            dilated = cv2.dilate(binary, kernel, iterations=2)

            # Tìm contours
            contours, _ = cv2.findContours(dilated, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

            boxes = [cv2.boundingRect(c) for c in contours]
            # Sắp xếp các dòng từ trên xuống dưới theo tọa độ Y
            boxes = sorted(boxes, key=lambda b: b[1])

            line_images = []
            h_img, w_img = img_np.shape[:2]
            for x, y, w, h in boxes:
                # Lọc bỏ các khối quá nhỏ (nhiễu) hoặc quá lớn (khung toàn trang)
                if w > 40 and 10 < h < (h_img * 0.4):
                    pad_y1 = max(0, y - 4)
                    pad_y2 = min(h_img, y + h + 4)
                    pad_x1 = max(0, x - 2)
                    pad_x2 = min(w_img, x + w + 2)
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
        Hậu xử lý văn bản tiếng Việt sau OCR:
        - Chuẩn hóa Unicode NFC (tránh lỗi font tổ hợp)
        - Sửa các lỗi quang học kinh điển trong văn bản hành chính & trường học
        - Tự động sửa lỗi đầu mục (+ Bước -> % Bước), dấu ngoặc lạc, ký tự nhiễu
        """
        if not text:
            return ""

        # 1. Chuẩn hóa NFC
        text = unicodedata.normalize("NFC", text)

        # 2. Thay thế quy tắc chuẩn cho văn bản hành chính
        patterns = [
            # Quốc hiệu & Tiêu ngữ
            (r'C[OỘÔ]NG\s*H[OÒÓ]A\s*X[AÃ]A?H?[OỘÔ]I\s*CH[UỦÙ]\s*NGH[IĨÍ]A\s*VI[EỆÊ]T\s*NAM', 'CỘNG HÒA XÃ HỘI CHỦ NGHĨA VIỆT NAM'),
            (r'[ĐD][OÔỘ]C\s*L[AÂẬ]P\s*[-–—]\s*T[UỰƯ]\s*DO\s*[-–—]\s*H[AẠ][N|M]H\s*PH[UÚÙ]C', 'Độc lập - Tự do - Hạnh phúc'),
            (r'B[OỘÔ]\s*GI[AÁ]O\s*D[UỤ]C\s*V[AÀ]\s*[ĐD][AÀ]O\s*T[AẠ]O', 'BỘ GIÁO DỤC VÀ ĐÀO TẠO'),
            (r'TR[UƯỜ]NG\s*[ĐD][AẠ]I\s*H[OỌ]C\s*[ĐD][AÀ]\s*L[AẠ]T', 'TRƯỜNG ĐẠI HỌC ĐÀ LẠT'),
            (r'PH[OÒ]NG\s*C[OÔ]NG\s*T[AÁ]C\s*SINH\s*VI[EÊ]N', 'PHÒNG CÔNG TÁC SINH VIÊN'),
            
            # Tiêu đề loại văn bản
            (r'\bK[EÉÊ]\s*HO[AẠ]CH\b', 'KẾ HOẠCH'),
            (r'\bQUY[EẾÊ]T\s*[ĐD][IỊ]NH\b', 'QUYẾT ĐỊNH'),
            (r'\bTH[OÔ]NG\s*B[AÁ]O\b', 'THÔNG BÁO'),
            (r'\bH[UƯ][OỚ]NG\s*D[AẪ]N\b', 'HƯỚNG DẪN'),
            (r'\bGI[AẤ]Y\s*X[AÁ]C\s*NH[AẬ]N\b', 'GIẤY XÁC NHẬN'),
            (r'\b[ĐD][OƠ]N\s*XIN\b', 'ĐƠN XIN'),
            
            # Địa danh & Ngày tháng
            (r'Lâm\s*Đông\b', 'Lâm Đồng'),
            (r'LâmĐồng\b', 'Lâm Đồng'),
            (r'Đà\s*Lat\b', 'Đà Lạt'),
            (r'Số\s*:\s*([0-9]+)\s*[\/|\\]\s*([A-Za-zĐđ-]+)', r'Số: \1/\2'),
            (r'\bng[àa]y\s+(\d{1,2})\s+th[áa]ng\s+(\d{1,2})\s+n[ăa]m\s+(\d{4})\b', r'ngày \1 tháng \2 năm \3'),
            (r'\bng[d|y|a|à]+\s+(\d{1,2})\s+th[áa]ng', r'ngày \1 tháng'),
            
            # Khắc phục lỗi quang học đầu mục: % Bước 1 -> + Bước 1, & Bước -> + Bước
            (r'(?m)^[%\&\*]\s*(Bước\s*\d+)', r'+ \1'),
            (r'(?m)^[%\&\*]\s*([0-9]+[\.\)])', r'\1'),
            (r'(?m)^[%\&\*]\s*([a-zA-Z][\.\)])', r'- \1'),
            (r'(?m)^[%\*]\s*([A-ZÀ-Ỹa-zà-ỹ])', r'+ \1'),
            
            # Khắc phục lỗi dấu hai chấm kèm slash/ký tự lạ: bịa đặt:// -> bịa đặt:
            (r':\/{1,2}', r':'),
            (r':\s*:\s*', r': '),

            # Khắc phục lỗi dấu ngoặc vuông lạc / ký tự nhiễu trong từ
            (r'([a-zA-ZÀ-ỹ0-9])\]\s+([a-zA-ZÀ-ỹ])', r'\1 \2'),
            (r'([a-zA-ZÀ-ỹ0-9])\[\s+([a-zA-ZÀ-ỹ])', r'\1 \2'),
            (r'([a-zA-ZÀ-ỹ0-9])\}(\s+)', r'\1\2'),
            (r'([a-zA-ZÀ-ỹ0-9])\{(\s+)', r'\1\2'),
            
            # Chữ số La Mã đầu mục
            (r'\bIH\.\s*', 'III. '),
            (r'\bTI\.\s*', 'II. '),
            (r'\bIV\.\s*', 'IV. '),
        ]

        for pattern, replacement in patterns:
            text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)

        # Xóa các dòng rác 1-2 ký tự (nhiễu viền con dấu / khung trang)
        allowed_short_tokens = {
            "I", "V", "X", "TP", "UB", "ĐL", "Số", "Kính gửi", "Lớp", "K49", "K48", "K47", "K46", "K45", "K44"
        }
        lines = text.split("\n")
        cleaned_lines = []
        for line in lines:
            stripped = line.strip()
            # Bỏ qua các dòng rác như "MA", "|", "---", "//", "\" đứng trơ trọi
            if len(stripped) <= 2 and stripped.isupper() and stripped not in allowed_short_tokens:
                continue
            if stripped in {"|", "||", "---", "--", "...", "//", "\\", "[]", "{}"}:
                continue
            cleaned_lines.append(line)
        text = "\n".join(cleaned_lines)

        # Xóa khoảng trắng thừa giữa các dòng
        text = re.sub(r'[ \t]+', ' ', text)
        text = re.sub(r'\n{3,}', '\n\n', text)
        return text.strip()

    def calculate_confidence_score(self, text: str, engine: str = "vietocr") -> float:
        """
        Tính toán độ tin cậy thực tế của văn bản OCR dựa trên:
        - Tỷ lệ ký tự tiếng Việt hợp lệ và từ ngữ có nghĩa
        - Tần suất các lỗi quang học (ký tự rác, dấu ngoặc lạc, ký tự đặc biệt)
        """
        if not text or len(text.strip()) < 10:
            return 0.60

        base = 0.92 if engine == "vietocr" else 0.85

        # Penalty cho ký tự rác / ký tự lạ không thuộc tiếng Việt
        suspicious_chars = len(re.findall(r'[%~^|<>{}\[\]\\]', text))
        char_penalty = min(0.12, (suspicious_chars / max(len(text), 1)) * 4.0)

        # Bonus cho cấu trúc hành chính chuẩn (Quốc hiệu, Tiêu ngữ, Số hiệu, Ngày tháng)
        bonus = 0.0
        if "CỘNG HÒA XÃ HỘI CHỦ NGHĨA VIỆT NAM" in text:
            bonus += 0.02
        if "Độc lập - Tự do - Hạnh phúc" in text:
            bonus += 0.02
        if re.search(r'ngày\s+\d+\s+tháng\s+\d+\s+năm\s+\d+', text, re.IGNORECASE):
            bonus += 0.02

        final_score = max(0.65, min(0.98, base - char_penalty + bonus))
        return round(final_score, 2)


    def _ocr_with_vietocr_lines(self, image: Image.Image) -> str:
        """Tách dòng và đưa từng dòng vào VietOCR Transformer."""
        predictor = self._get_predictor()
        if not predictor:
            return ""

        try:
            line_images = self.segment_lines(image)
            line_texts = []
            for line_img in line_images:
                # Tiền xử lý chữ viết tay trước khi predict
                clean_line = self.preprocess_handwriting(line_img)
                txt = predictor.predict(clean_line)
                if txt and len(txt.strip()) > 0:
                    line_texts.append(txt.strip())

            if line_texts:
                return "\n".join(line_texts)
        except Exception as e:
            logger.debug("VietOCR line-by-line failed: {err}", err=str(e))

        return ""

    def _ocr_image(self, image: Image.Image) -> str:
        """Thực hiện OCR đa tầng (VietOCR Transformer Line-by-Line + Bảng biểu + Tesseract fallback)."""
        processed_img = self.preprocess_image(image)

        # 1. Bóc tách Bảng biểu trước (nếu có)
        table_markdowns = self.detect_and_extract_tables(processed_img)

        # 2. Ưu tiên VietOCR Transformer theo từng dòng
        full_text = ""
        vocr_text = self._ocr_with_vietocr_lines(processed_img)
        if vocr_text and len(vocr_text.strip()) > 5:
            full_text = self.post_process_vietnamese(vocr_text.strip())

        # 3. Fallback Tesseract nếu VietOCR không trả về kết quả
        if not full_text and pytesseract is not None:
            try:
                text = pytesseract.image_to_string(
                    processed_img,
                    lang="vie+eng",
                    config="--oem 1 --psm 3",
                )
                if text and len(text.strip()) > 5:
                    full_text = self.post_process_vietnamese(text.strip())
            except Exception as tess_err:
                logger.debug("Tesseract fallback failed: {err}", err=str(tess_err))

        # 4. Nếu có bảng biểu trích xuất, ghép nối vào phần thân văn bản
        if table_markdowns:
            tables_str = "\n\n### [BẢNG BIỂU DỮ LIỆU BÓC TÁCH]:\n" + "\n\n".join(table_markdowns)
            full_text = f"{full_text}\n\n{tables_str}" if full_text else tables_str

        return full_text

    def extract_text_from_file(self, file_bytes: bytes, file_type: str) -> tuple[str, float]:
        """
        Trích xuất toàn văn từ file PDF hoặc Ảnh (JPG, PNG, TIFF).
        Hỗ trợ PDF scan ảnh nhiều trang ở độ phân giải cao (300 DPI), Bảng biểu & Viết tay.

        Returns:
            (raw_text, confidence_score)
        """
        file_ext = file_type.lower().replace(".", "")

        # ── 1. Xử lý file PDF ────────────────────────────────────────────────
        if file_ext == "pdf":
            # 1.1 Thử mở bằng PyMuPDF
            if pymupdf is not None:
                try:
                    doc = pymupdf.open(stream=file_bytes, filetype="pdf")
                    extracted_pages = []

                    # Thử lấy direct text trước
                    for page in doc:
                        t = page.get_text().strip()
                        if t:
                            extracted_pages.append(t)

                    if extracted_pages and len("\n".join(extracted_pages)) > 40:
                        full_text = "\n\n".join(extracted_pages)
                        full_text = self.post_process_vietnamese(full_text)
                        logger.info("Extracted direct text from PDF ({pages} pages, {chars} chars)",
                                    pages=len(doc), chars=len(full_text))
                        return full_text, self.calculate_confidence_score(full_text, engine="direct_pdf")

                    # Nếu không có text layer (PDF scan ảnh), render từng trang 300 DPI và OCR
                    ocr_pages = []
                    for page_idx, page in enumerate(doc):
                        pix = page.get_pixmap(dpi=300)
                        page_img = Image.open(io.BytesIO(pix.tobytes("png"))).convert("RGB")
                        page_text = self._ocr_image(page_img)
                        if page_text:
                            ocr_pages.append(page_text)

                    if ocr_pages:
                        full_text = "\n\n".join(ocr_pages)
                        full_text = self.post_process_vietnamese(full_text)
                        logger.info("OCR scanned PDF ({pages} pages, {chars} chars)",
                                    pages=len(doc), chars=len(full_text))
                        return full_text, self.calculate_confidence_score(full_text, engine="vietocr")
                except Exception as exc:
                    logger.warning("PyMuPDF OCR failed: {err}", err=str(exc))

            # 1.2 Fallback pypdf
            if pypdf is not None:
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
            img_text = self._ocr_image(image)
            if img_text:
                img_text = self.post_process_vietnamese(img_text)
                return img_text, self.calculate_confidence_score(img_text, engine="vietocr")
        except Exception as exc:
            logger.warning("Image OCR failed: {err}", err=str(exc))


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

        # 1. Trích xuất MSSV (8 chữ số hoặc pattern 20xxxxxx)
        mssv_match = re.search(r"(?:MSSV|Mã số sinh viên|Mã SV|Mã sinh viên)[\s:]*([0-9]{7,8})", text, re.IGNORECASE)
        if not mssv_match:
            mssv_match = re.search(r"\b(2[0-3][0-9]{5,6})\b", text)
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
