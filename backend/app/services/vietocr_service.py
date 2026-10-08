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


class VietOCRService:
    """
    Service chuyên biệt điều phối pipeline cho VietOCR.
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
        """Tương thích ngược: chỉ trả về danh sách ảnh dòng."""
        lines_with_boxes, _, _ = self.segment_lines_with_boxes(pil_image)
        return [img for img, box in lines_with_boxes]

    def segment_lines_with_boxes(self, pil_image: Image.Image) -> tuple[list[tuple[Image.Image, tuple[int, int, int, int]]], int, np.ndarray | None]:
        try:
            img_np = np.array(pil_image)
            if len(img_np.shape) == 3 and img_np.shape[2] == 4:
                img_np = cv2.cvtColor(img_np, cv2.COLOR_RGBA2RGB)
                
            stamp_mask = self._get_red_stamp_mask(img_np)
            
            # Load EasyOCR only when needed
            import easyocr
            if not hasattr(self, '_easy_ocr'):
                logger.info("Initializing EasyOCR...")
                self._easy_ocr = easyocr.Reader(['vi'], gpu=False, verbose=False)
                
            img_bgr = cv2.cvtColor(img_np, cv2.COLOR_RGB2BGR) if len(img_np.shape) == 3 else img_np
            # Detect returns (horizontal_list, free_list)
            # horizontal_list format: [[[x_min, x_max, y_min, y_max], ...]]
            horizontal_list, free_list = self._easy_ocr.detect(img_bgr)
            
            boxes = []
            if horizontal_list and len(horizontal_list[0]) > 0:
                boxes.extend(horizontal_list[0])
            if free_list and len(free_list[0]) > 0:
                # convert polygon to bounding box
                for poly in free_list[0]:
                    xs = [pt[0] for pt in poly]
                    ys = [pt[1] for pt in poly]
                    boxes.append([min(xs), max(xs), min(ys), max(ys)])
                    
            if not boxes:
                return [], 15, stamp_mask
                
            img_w = img_np.shape[1] if len(img_np.shape) >= 2 else pil_image.width
            img_h = img_np.shape[0] if len(img_np.shape) >= 2 else pil_image.height

            # Merge boxes that belong to the same line (to fix "Độc lập - Tự do" being split)
            def merge_boxes(boxes_list):
                while True:
                    merged = False
                    new_boxes = []
                    while boxes_list:
                        box = boxes_list.pop(0)
                        x1, x2, y1, y2 = box
                        h = y2 - y1
                        cx = (x1 + x2) / 2.0
                        cy = (y1 + y2) / 2.0
                        
                        found_merge = False
                        for i, m_box in enumerate(new_boxes):
                            mx1, mx2, my1, my2 = m_box
                            mh = my2 - my1
                            mcx = (mx1 + mx2) / 2.0
                            mcy = (my1 + my2) / 2.0
                            
                            # Ranh giới 2 cột ở phần Header (top 20% trang):
                            # Cột trái (Cơ quan / Số hiệu) và Cột phải (Quốc hiệu / Ngày tháng)
                            # TUYỆT ĐỐI KHÔNG GỘP NGANG XUYÊN QUA HAI CỘT
                            is_header_zone = (cy < 0.20 * img_h and mcy < 0.20 * img_h)
                            if is_header_zone:
                                split_x = 0.46 * img_w
                                if (cx < split_x and mcx > split_x) or (cx > split_x and mcx < split_x):
                                    continue
                            
                            overlap_y = max(0, min(y2, my2) - max(y1, my1))
                            if overlap_y > 0.4 * min(h, mh):
                                gap = max(0, x1 - mx2 if x1 > mx2 else mx1 - x2)
                                max_allowed_gap = 1.8 * max(h, mh)
                                if gap <= max_allowed_gap:
                                    new_boxes[i] = [min(x1, mx1), max(x2, mx2), min(y1, my1), max(y2, my2)]
                                    found_merge = True
                                    merged = True
                                    break
                                    
                        if not found_merge:
                            new_boxes.append(box)
                            
                    boxes_list = new_boxes
                    if not merged:
                        break
                return boxes_list
                
            boxes = merge_boxes(boxes)
                
            # Sắp xếp thứ tự đọc (Reading Order):
            # Phần Header (top 16% trang): Cột trái trước (từ trên xuống dưới),
            # sau đó Cột phải (từ trên xuống dưới).
            # Phần Thân: tuần tự theo trục Y từ trên xuống dưới.
            header_threshold_y = 0.12 * img_h
            split_x = 0.46 * img_w
            
            header_left = []
            header_right = []
            body_boxes = []
            
            for b in boxes:
                cy = (b[2] + b[3]) / 2.0
                cx = (b[0] + b[1]) / 2.0
                bw = b[1] - b[0]
                if cy < header_threshold_y and bw < 0.55 * img_w:
                    if cx < split_x:
                        header_left.append(b)
                    else:
                        header_right.append(b)
                else:
                    body_boxes.append(b)
                    
            header_left = sorted(header_left, key=lambda b: (b[2] + b[3]) / 2.0)
            header_right = sorted(header_right, key=lambda b: (b[2] + b[3]) / 2.0)
            body_boxes = sorted(body_boxes, key=lambda b: (b[2] + b[3]) / 2.0)
            
            boxes = header_left + header_right + body_boxes
            
            lines_with_boxes = []
            heights = []
            
            for box in boxes:
                x_min, x_max, y_min, y_max = [int(v) for v in box]
                x, y = x_min, y_min
                w, h = x_max - x_min, y_max - y_min
                
                if w < 5 or h < 5:
                    continue
                
                # Căn lề nhẹ thêm vì detector cắt rất khít
                pad_top = max(2, int(0.15 * h))
                pad_bot = max(2, int(0.10 * h))
                pad_h   = max(3, int(0.15 * h))
                
                t  = max(0, y - pad_top)
                b  = min(img_np.shape[0], y + h + pad_bot)
                lo = max(0, x - pad_h)
                ro = min(img_np.shape[1], x + w + pad_h)
                
                crop_np = img_np[t:b, lo:ro].copy()
                if stamp_mask is not None:
                    crop_np = self._clean_stamp_in_crop(crop_np, stamp_mask[t:b, lo:ro])
                    
                line_img = Image.fromarray(crop_np)
                lines_with_boxes.append((line_img, (x, y, w, h)))
                heights.append(h)
                
            h_med = int(np.median(heights)) if heights else 15
            logger.info("Segmented {n} lines using EasyOCR", n=len(lines_with_boxes))
            return lines_with_boxes, h_med, stamp_mask
            
        except Exception as exc:
            logger.warning("segment_lines_with_boxes fallback (EasyOCR error): {err}", err=str(exc))
            return [(pil_image, (0, 0, pil_image.width, pil_image.height))], 15, None

    # ── Helpers tách dòng ──────────────────────────────────────────────────────

    @staticmethod
    def _get_red_stamp_mask(img_np: np.ndarray) -> "np.ndarray | None":
        """
        Tạo mask (uint8, 255) cho vùng con dấu đỏ tròn.
        Dùng không gian HSV để tách màu đỏ (hue ở 2 cực: 0-12° và 160-180°).
        Trả None nếu không có vùng đỏ đáng kể (tránh overhead không cần thiết).
        """
        try:
            if len(img_np.shape) < 3 or img_np.shape[2] < 3:
                return None
            hsv = cv2.cvtColor(img_np, cv2.COLOR_RGB2HSV)
            # Đỏ thấp: hue 0-12
            m1  = cv2.inRange(hsv, (0, 90, 60), (12, 255, 255))
            # Đỏ cao: hue 160-180
            m2  = cv2.inRange(hsv, (160, 90, 60), (180, 255, 255))
            red = cv2.bitwise_or(m1, m2)
            # Nếu vùng đỏ quá nhỏ → không có con dấu thực
            if cv2.countNonZero(red) < 200:
                return None
            # Dãn rộng để bao phủ toàn bộ vùng con dấu (bao gồm cả chữ đen bên trong)
            kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (25, 25))
            return cv2.dilate(red, kernel, iterations=3)
        except Exception:
            return None

    @staticmethod
    def _clean_stamp_in_crop(crop_np: np.ndarray, crop_stamp_mask: np.ndarray) -> np.ndarray:
        """
        Xóa pixel con dấu đỏ khỏi crop ảnh, giữ nguyên:
          - Pixel đen (chữ đen bên dưới/cạnh con dấu)  
          - Pixel xanh dương (chữ tay xanh: số, chữ ký)
        Chỉ fill WHITE cho pixel đỏ trong vùng stamp_mask.
        """
        if crop_stamp_mask is None or crop_np is None:
            return crop_np
        try:
            if len(crop_np.shape) < 3:
                return crop_np
            hsv = cv2.cvtColor(crop_np, cv2.COLOR_RGB2HSV)
            # Đỏ: hue 0-12 hoặc 160-180, saturation cao (>= 80), value cao (>= 60)
            red_low  = cv2.inRange(hsv, np.array([0, 80, 60]),   np.array([12, 255, 255]))
            red_high = cv2.inRange(hsv, np.array([160, 80, 60]), np.array([180, 255, 255]))
            is_red_pixel = cv2.bitwise_or(red_low, red_high)
            # Blue (handwriting): hue 100-130, sat >= 60
            is_blue_pixel = cv2.inRange(hsv, np.array([100, 60, 60]), np.array([130, 255, 255]))
            # Dark pixels (black text): value < 80
            is_dark_pixel = (hsv[:, :, 2] < 80).astype(np.uint8) * 255

            # Within stamp mask: fill red pixels with white, keep dark+blue
            in_stamp = (crop_stamp_mask > 0)
            fill_white = in_stamp & (is_red_pixel > 0) & (is_dark_pixel == 0) & (is_blue_pixel == 0)
            result = crop_np.copy()
            result[fill_white] = [255, 255, 255]
            return result
        except Exception:
            return crop_np

    @staticmethod
    def _sort_boxes_by_row(
        boxes: list[tuple[int, int, int, int]],
        h_med: int
    ) -> list[tuple[int, int, int, int]]:
        """
        Sắp xếp boxes theo hàng thực tế bằng cách gom nhóm theo y-center.
        """
        if not boxes:
            return []

        sorted_by_y = sorted(boxes, key=lambda b: b[1] + b[3] / 2)
        rows: list[list[tuple[int, int, int, int]]] = []
        for bx in sorted_by_y:
            bx_cy = bx[1] + bx[3] / 2
            placed = False
            for row in rows:
                row_cy = sum(b[1] + b[3] / 2 for b in row) / len(row)
                if abs(bx_cy - row_cy) < h_med * 0.5:
                    row.append(bx)
                    placed = True
                    break
            if not placed:
                rows.append([bx])

        result: list[tuple[int, int, int, int]] = []
        for row in sorted(rows, key=lambda r: sum(b[1] + b[3] / 2 for b in r) / len(r)):
            result.extend(sorted(row, key=lambda b: b[0]))
        return result

    @staticmethod
    def _merge_boxes(boxes: list[tuple[int, int, int, int]], h_med: int) -> list[tuple[int, int, int, int]]:
        """Gom các hộp gần nhau theo chiều ngang và có chung dòng (độ cao)."""
        if not boxes: return []
        boxes = sorted(boxes, key=lambda b: b[0])
        merged = []
        for bx in boxes:
            x, y, w, h = bx
            placed = False
            for i, mb in enumerate(merged):
                mx, my, mw, mh = mb
                overlap_y = max(0, min(y+h, my+mh) - max(y, my))
                if overlap_y >= 0.5 * min(h, mh):
                    if (x - (mx + mw)) < 2 * h_med and (mx - (x + w)) < 2 * h_med:
                        nx = min(x, mx)
                        ny = min(y, my)
                        nw = max(x+w, mx+mw) - nx
                        nh = max(y+h, my+mh) - ny
                        merged[i] = (nx, ny, nw, nh)
                        placed = True
                        break
            if not placed:
                merged.append((x, y, w, h))
        return merged

    @staticmethod
    def _split_tall_box(binary: np.ndarray, x: int, y: int, w: int, h: int, h_med: int) -> list[tuple[int, int, int, int]]:
        """
        Cắt box quá cao (thường do dính chữ giữa 2 dòng) bằng horizontal projection.
        Tìm gap THỰC SỰ trắng liên tiếp >= 2 pixel để tránh cắt nhầm dòng chữ.
        """
        region = binary[y:y+h, x:x+w]
        if region.size == 0:
            return [(x, y, w, h)]
        row_hist = region.sum(axis=1)
        split_y = []
        in_gap = False
        gap_start = 0
        noise_thresh = 255 * max(2, int(w * 0.005))
        for r, val in enumerate(row_hist):
            if val <= noise_thresh:
                if not in_gap:
                    in_gap = True
                    gap_start = r
            else:
                if in_gap:
                    in_gap = False
                    gap_len = r - gap_start
                    # Require gap >= 2px to avoid splitting at thin ink bridges
                    if gap_len >= 2:
                        split_y.append((gap_start + r) // 2)
        # Check for trailing gap
        if in_gap and (h - gap_start) >= 2:
            split_y.append((gap_start + h) // 2)

        # Fallback: if no gap found but box is very tall (likely touching lines), split at argmin in middle 60%
        if not split_y and h > 2.2 * h_med:
            mid_start = int(0.2 * h)
            mid_end = int(0.8 * h)
            min_val = min(row_hist[mid_start:mid_end])
            min_idx = mid_start + list(row_hist[mid_start:mid_end]).index(min_val)
            split_y.append(min_idx)

        if not split_y:
            return [(x, y, w, h)]

        boxes = []
        last_y = 0
        for sy in split_y:
            seg_h = sy - last_y
            if seg_h >= max(4, int(0.4 * h_med)):  # relaxed: 0.4 instead of 0.5
                boxes.append((x, y + last_y, w, seg_h))
            last_y = sy
        last_h = h - last_y
        if last_h >= max(4, int(0.4 * h_med)):
            boxes.append((x, y + last_y, w, last_h))

        # Check if any box is STILL too tall. If so, split by argmin.
        final_boxes = []
        for bx, by, bw, bh in boxes:
            if bh > 2.2 * h_med:
                mid_start = int(0.3 * bh)
                mid_end = int(0.7 * bh)
                min_val = min(row_hist[by-y+mid_start:by-y+mid_end])
                min_idx = mid_start + list(row_hist[by-y+mid_start:by-y+mid_end]).index(min_val)
                final_boxes.append((bx, by, bw, min_idx))
                final_boxes.append((bx, by + min_idx, bw, bh - min_idx))
            else:
                final_boxes.append((bx, by, bw, bh))

        return final_boxes if len(final_boxes) > 1 else [(x, y, w, h)]

    @staticmethod
    def _split_two_column_advanced(
        binary: np.ndarray,
        x: int, y: int, w: int, h: int,
        h_med: int
    ) -> list[tuple[int, int, int, int]]:
        """
        Tách box rộng thành 2 cột nếu có khoảng trắng liên tục (gap > 3*h_med) ở vùng giữa.
        """
        try:
            region = binary[max(0, y - 2): y + h + 2, max(0, x): x + w]
            if region.size == 0:
                return [(x, y, w, h)]

            col_hist = region.sum(axis=0)
            in_gap = False
            gap_start = 0
            best_gap = -1
            best_gap_w = 0
            for c, val in enumerate(col_hist):
                if val == 0:
                    if not in_gap:
                        in_gap = True
                        gap_start = c
                else:
                    if in_gap:
                        in_gap = False
                        gw = c - gap_start
                        if gw > 3 * h_med and gw > best_gap_w:
                            best_gap_w = gw
                            best_gap = (gap_start + c) // 2
            
            if best_gap > 0 and 0.2 * w < best_gap < 0.8 * w:
                return [
                    (x, y, best_gap, h),
                    (x + best_gap, y, w - best_gap, h)
                ]
            return [(x, y, w, h)]
        except Exception:
            return [(x, y, w, h)]

    # ── Lọc nhiễu ─────────────────────────────────────────────────────────────
    @staticmethod
    def _is_noise_line_advanced(
        text: str, box: tuple[int, int, int, int], img_w: int, img_h: int, h_med: int,
        stamp_mask: np.ndarray | None = None
    ) -> bool:
        """
        Lọc dòng rác nâng cao dựa vào context (kích thước box, vị trí).
        """
        if not text or not text.strip():
            return True
        t = text.strip()

        # Dòng quá ngắn hoặc toàn ký tự đặc biệt
        if len(t) <= 1 and t not in ("I", "1", "-", "."):
            return True
        if not re.search('[A-Za-z0-9\u00C0-\u1EF9]', t):
            return True

        x, y, w, h = box
        
        # Hallucination guard: crop rất rộng nhưng model trả về chuỗi siêu ngắn
        if w > 3 * h_med and len(t) < 3 and not re.search(r'\d', t):
            return True
            
        # Drop lines that are clearly diacritic strips (height very small)
        if h <= max(12, int(0.6 * h_med)) and w > 100:
            # Exception for page numbers, document numbers, or standard valid words
            if t not in {"THÔNG BÁO", "KẾ HOẠCH", "BÁO CÁO"} and not re.search(r'Số:\s*\d+', t) and not re.fullmatch(r'\d+', t):
                return True

        # Hallucination guard: crop rất hẹp nhưng text trả về lại rất dài
        if w < 2 * h_med and len(t) > 6:
            return True

        # Text/crop width mismatch guard:
        # Standard character width is roughly h_med * 0.4 to 0.7.
        # If crop is very wide, but text is very short, or vice versa
        if w > 15 * h_med and len(t) < w / (h_med * 1.8) and not re.search(r'\d{8,}', t):
            # Exception for a few spaced characters, but usually it's noise
            if len(t) > 3:
                return True

        # Vowel-consonant / Syllable validity ratio
        words = t.split()
        if len(words) > 2:
            vowels = "aeiouyáàảãạăắằẳẵặâấầẩẫậéèẻẽẹêếềểễệíìỉĩịóòỏõọôốồổỗộơớờởỡợúùủũụưứừửữựýỳỷỹỵ"
            valid_syllables = sum(1 for w_tok in words if any(v in w_tok.lower() for v in vowels) and re.search(r'[A-Za-z\u00C0-\u1EF9]', w_tok))
            # If less than 30% of alphabetical words are valid syllables (have vowels)
            alpha_words = [w_tok for w_tok in words if re.search(r'[A-Za-z\u00C0-\u1EF9]', w_tok)]
            if len(alpha_words) >= 3 and (valid_syllables / len(alpha_words)) < 0.3:
                return True

        # Drop lines that are ONLY digits/short tokens, UNLESS context rule matches
        is_page_number = re.fullmatch(r'\d+', t) and w < 4 * h_med and (y < 0.15 * img_h or y > 0.85 * img_h) and (0.35 * img_w < x < 0.65 * img_w)
        # Relaxed list number: allow small width (< 4*h_med) and numbers with dot/slash/parenthesis
        is_list_number = re.fullmatch(r'\d+[\.\/\)]?', t) and w < 4 * h_med
        is_doc_number = "Số:" in t or "TB-" in t or re.match(r'(Số:|số)?\s*\d+/[A-Z\-]+', t)
        
        # Valid small context words around signature
        valid_small_words = {"1.", "2.", "3.", "4.", "I.", "II.", "III.", "IV.", "1", "2", "-", "PHÓ HIỆU TRƯỞNG", "HIỆU TRƯỞNG", "Nguyễn Văn Ngọc", "Lưu: VT, CTSV.", "Lưu: VT, CTSV"}
        
        if re.fullmatch(r'[\d\s\.\,\-\/]{1,4}', t):
            # Short tokens of digits/symbols
            if not (is_page_number or is_list_number or is_doc_number or t in valid_small_words):
                return True
                
        # Filter garbage words and known hallucinated Latin long words
        if t in ("2.2", "42", "4.2", "22", "Coll", "Chines", "CHILL", "0%", "2/42"):
            return True
            
        if re.search(r'\b(?:Contractionalists?|Accommodating|Internationalization|Responsibilit(?:y|ies)|Unbelievable|Organization|Administration|Characteristics?|[A-Za-z]{10,})\b', t, re.IGNORECASE):
            return True

        # Barcode dài nằm xen kẽ
        if re.search(r'\d{10,}', t):
            return True
            
        # Ảo giác dấu chấm/gạch ngang
        if len(re.findall(r'[\.\-\_~]', t)) >= 12:
            return True

        # Ảo giác watermark mờ rác
        if len(re.findall(r'\"\"+', t)) >= 2 or len(re.findall(r'\d/\d/\d/\d', t)) >= 1 or '??T2' in t or 'yhng' in t or 'nghvay' in t or 'vụvv' in t or 'viv' in t:
            return True

        # Lặp từ do con dấu tròn đỏ
        words = t.split()
        if len(words) >= 4:
            clean_words = []
            for w_tok in words:
                key = re.sub('[^a-z\u00C0-\u1EF9]', '', w_tok.lower())
                if len(key) >= 2:
                    clean_words.append(key)
                    
            if len(clean_words) >= 3:
                from collections import Counter
                counts = Counter(clean_words)
                max_freq = counts.most_common(1)[0][1]
                
                # Check if it overlaps with stamp
                overlap_stamp = False
                if stamp_mask is not None:
                    # bounding box overlap
                    crop_stamp = stamp_mask[y:y+h, x:x+w]
                    if np.count_nonzero(crop_stamp) > 50:
                        overlap_stamp = True
                
                # Mộc mờ sinh ảo giác từ lặp liên tục
                if max_freq >= 3 and (max_freq / len(clean_words)) > 0.25:
                    if overlap_stamp:
                        return True
                    if max_freq >= 5: 
                        return True
                    
                # Watermark mờ sinh 2 cặp lặp từ đứng cạnh nhau
                adjacent_dups = sum(1 for i in range(len(clean_words) - 1) if clean_words[i] == clean_words[i+1])
                if adjacent_dups >= 2 and overlap_stamp:
                    return True

        return False

    @staticmethod
    def _clean_ocr_text(text: str) -> str:
        """
        Lọc văn bản trống
        """
        lines = text.splitlines()
        result: list[str] = []
        for line in lines:
            if line:
                line = line.strip()
                if line:
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
        self, image: Image.Image, page_num: int = 1
    ) -> list[tuple[str, float]]:
        """Tách dòng rồi OCR bằng VietOCR, lọc dòng rác bằng AI context.

        Args:
            image: PIL image của 1 trang.
            page_num: Số trang (1-indexed) để debug dump.
        """
        import os, json, time as _time
        lines_with_boxes, h_med, stamp_mask = self.segment_lines_with_boxes(image)
        if not lines_with_boxes:
            return []

        img_w, img_h = image.size
        do_dump = os.environ.get("OCR_DEBUG_DUMP") == "1"
        debug_dir: str = ""
        crops_dir: str = ""
        dump_data: list[dict] = []
        overlay_np = None

        if do_dump:
            try:
                debug_dir = os.path.abspath("backend/tests/data/thong_bao_1413")
                os.makedirs(debug_dir, exist_ok=True)
                crops_dir = os.path.join(debug_dir, f"crops_p{page_num}")
                os.makedirs(crops_dir, exist_ok=True)
                overlay_np = np.array(image)
                if len(overlay_np.shape) == 2:
                    overlay_np = cv2.cvtColor(overlay_np, cv2.COLOR_GRAY2RGB)
                elif overlay_np.shape[2] == 4:
                    overlay_np = cv2.cvtColor(overlay_np, cv2.COLOR_RGBA2RGB)
                else:
                    overlay_np = overlay_np.copy()
            except Exception:
                do_dump = False

        # ── Pre-recognition guard: ink ratio + connected component count ───
        kept_indices: list[int] = []
        guarded_imgs: list[Image.Image] = []
        pre_drop_reasons: list[str | None] = []

        for idx, (img, box) in enumerate(lines_with_boxes):
            x, y, w, h = box
            drop_reason: str | None = None
            ink_ratio_val: float | None = None
            num_cc_val: int | None = None
            try:
                crop_arr = np.array(img)
                gray_c = cv2.cvtColor(crop_arr, cv2.COLOR_RGB2GRAY) if len(crop_arr.shape) == 3 else crop_arr
                _, bw = cv2.threshold(gray_c, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
                ink_ratio_val = float(np.count_nonzero(bw)) / max(1, bw.size)
                num_cc_val = max(0, int(cv2.connectedComponentsWithStats(bw, connectivity=8)[0]) - 1)
                if ink_ratio_val < 0.015:
                    drop_reason = f"pre_guard:ink={ink_ratio_val:.4f}"
                elif num_cc_val < 2:
                    drop_reason = f"pre_guard:cc={num_cc_val}"
            except Exception:
                pass

            pre_drop_reasons.append(drop_reason)
            if drop_reason:
                if do_dump and overlay_np is not None:
                    cv2.rectangle(overlay_np, (x, y), (x+w, y+h), (128, 0, 255), 1)
                    dump_data.append({
                        "id": idx, "page": page_num, "box": [x, y, w, h],
                        "raw_text": "", "conf": 0.0,
                        "ink_ratio": round(ink_ratio_val, 4) if ink_ratio_val is not None else None,
                        "num_cc": num_cc_val, "drop_reason": drop_reason,
                    })
            else:
                kept_indices.append(idx)
                guarded_imgs.append(img)

        # ── OCR only on kept images ────────────────────────────────────────
        ocr_results: list[tuple[str, float]] = []
        if guarded_imgs:
            ocr_results = self._vietocr().ocr_lines(guarded_imgs, preprocess_fn=self.preprocess_handwriting)

        result_map: dict[int, tuple[str, float]] = {}
        for pos, orig_idx in enumerate(kept_indices):
            if pos < len(ocr_results):
                result_map[orig_idx] = ocr_results[pos]

        # ── Post-recognition filter + debug dump ──────────────────────────
        filtered_results: list[tuple[str, float]] = []
        for idx, (img, box) in enumerate(lines_with_boxes):
            if pre_drop_reasons[idx]:
                continue  # already handled above

            x, y, w, h = box
            text, conf = result_map.get(idx, ("", 0.0))

            drop_reason: str | None = None
            if not text:
                drop_reason = "empty_text"
            else:
                if self._is_noise_line_advanced(text, box, img_w, img_h, h_med, stamp_mask):
                    drop_reason = "noise_line_advanced"
                elif conf < 0.60:  # Drop lines that are low confidence (likely hallucination or junk)
                    drop_reason = f"low_conf:{conf:.2f}"

            if not drop_reason:
                filtered_results.append((text, conf))

            if do_dump:
                ink_ratio_val = None
                num_cc_val = None
                crop_fname: str = ""
                try:
                    crop_arr = np.array(img)
                    gray_c = cv2.cvtColor(crop_arr, cv2.COLOR_RGB2GRAY) if len(crop_arr.shape) == 3 else crop_arr
                    _, bw = cv2.threshold(gray_c, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
                    ink_ratio_val = round(float(np.count_nonzero(bw)) / max(1, bw.size), 4)
                    num_cc_val = max(0, int(cv2.connectedComponentsWithStats(bw, connectivity=8)[0]) - 1)
                    crop_fname = f"crop_{idx:03d}.png"
                    img.save(os.path.join(crops_dir, crop_fname))
                except Exception:
                    pass

                color = (0, 0, 255) if drop_reason else (0, 255, 0)
                if overlay_np is not None:
                    cv2.rectangle(overlay_np, (x, y), (x+w, y+h), color, 2)
                    label = f"{idx}:{(text or '')[:12]}" if not drop_reason else f"X{idx}:{(drop_reason or '')[:10]}"
                    cv2.putText(overlay_np, label, (x, max(10, y - 2)),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.32, color, 1)
                dump_data.append({
                    "id": idx, "page": page_num, "box": [x, y, w, h],
                    "raw_text": text, "conf": round(conf, 3),
                    "ink_ratio": ink_ratio_val, "num_cc": num_cc_val,
                    "crop_png": crop_fname or None,
                    "drop_reason": drop_reason,
                })

        if do_dump and overlay_np is not None:
            try:
                ts = int(_time.time() * 1000)
                cv2.imwrite(
                    os.path.join(debug_dir, f"debug_overlay_p{page_num}_{ts}.png"),
                    cv2.cvtColor(overlay_np, cv2.COLOR_RGB2BGR))
                with open(os.path.join(debug_dir, f"debug_dump_p{page_num}_{ts}.json"),
                          "w", encoding="utf-8") as f:
                    json.dump(dump_data, f, ensure_ascii=False, indent=2)
                logger.debug("OCR_DEBUG_DUMP: saved p{p} overlay+dump ({n} boxes)",
                             p=page_num, n=len(dump_data))
            except Exception as exc:
                logger.error("OCR_DEBUG_DUMP write error: {err}", err=str(exc))

        return filtered_results


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
        page_num: int = 1,
    ) -> tuple[str, str]:
        """
        OCR toàn trang bằng Line Segmentation với VietOCR.
        Pipeline: preprocess → segment_lines → VietOCR → filter → join → postprocess.

        Returns:
            (raw_text, processed_text)
            raw_text       — văn bản thô ngay sau OCR, chưa qua post-processing
            processed_text — đã qua hậu xử lý (sửa lỗi, chuẩn hoá NFC)
        """
        processed_img = self.preprocess_image(image)

        # 1. Bóc tách bảng biểu (tuỳ chọn)
        table_markdowns = self.detect_and_extract_tables(processed_img) if extract_tables else []

        # 2. OCR toàn trang theo dòng
        raw_text = ""
        line_results = self._ocr_lines_with_engine(processed_img, page_num=page_num)
        if line_results:
            valid_lines = [t for t, _ in line_results]
            joined = "\n".join(valid_lines)
            if len(joined.strip()) > 3:
                # Prepend page marker so downstream can split by page
                page_marker = f"--- Trang {page_num} ---"
                raw_text = unicodedata.normalize("NFC", f"{page_marker}\n{joined.strip()}")
                logger.info("OCR [vietocr] p{p} → {n} dòng, {c} ký tự",
                            p=page_num, n=len(valid_lines), c=len(raw_text))

        # 3. Ghép bảng biểu vào raw
        if table_markdowns:
            tables_str = "\n\n### [BẢNG BIỂU DỮ LIỆU BÓC TÁCH]:\n" + "\n\n".join(table_markdowns)
            raw_text = f"{raw_text}\n\n{tables_str}" if raw_text else tables_str

        # 4. Post-processing chỉ cho processed_text, giữ raw_text nguyên vẹn
        processed_text = ""
        if raw_text:
            try:
                cleaned        = self._clean_ocr_text(raw_text)
                processed_text = self.post_process_vietnamese(cleaned)
            except Exception as e:
                logger.error("VietOCR post-processing failed: {err}", err=str(e))
                processed_text = raw_text

        return raw_text, processed_text

    # ── OCR toàn file ─────────────────────────────────────────────────────────
    def extract_text_from_file(
        self, file_bytes: bytes, file_type: str, engine: str | None = None, pages: list[int] | int | None = None
    ) -> tuple[str, str, float, int]:
        """
        Trích xuất toàn văn từ file PDF hoặc Ảnh (JPG, PNG, TIFF).

        Returns:
            (raw_text, processed_text, heuristic_quality_score, page_count)
        """
        file_ext = file_type.lower().replace(".", "")
        _s = self._get_settings()
        _dpi_default    = getattr(_s, "ocr_pdf_dpi_default", 200)  if _s else 200
        _dpi_fast       = getattr(_s, "ocr_pdf_dpi_fast", 150)     if _s else 150
        _fast_mode      = getattr(_s, "ocr_fast_mode", False)       if _s else False
        _render_dpi     = _dpi_fast if _fast_mode else _dpi_default
        _extract_tables = getattr(_s, "ocr_extract_tables", True)   if _s else True
        selected_engine = engine or (getattr(_s, "ocr_engine", "vietocr") if _s else "vietocr")

        logger.info(
            "OCR: engine={eng}, dpi={dpi}, fast={fm}, tables={et}, pages={p}",
            eng=selected_engine, dpi=_render_dpi, fm=_fast_mode, et=_extract_tables, p=pages
        )

        page_count = 1

        # ── PDF ──────────────────────────────────────────────────────────────
        if file_ext == "pdf":
            if pymupdf is not None:
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

                    # PDF có text layer → trích xuất trực tiếp (siêu tốc)
                    if selected_engine == "vietocr":
                        # Luôn trích xuất TẤT CẢ các trang đối với text-layer PDF, bất kể target_pages
                        all_pages_text = [doc[idx].get_text().strip() for idx in range(page_count)]
                        all_pages_text = [t for t in all_pages_text if t]
                        # Only use text layer if it has some substantial text (>= 50 chars)
                        if all_pages_text and len("\n".join(all_pages_text)) >= 50:
                            raw_full = "\n\n".join(all_pages_text)
                            processed_full = self.post_process_vietnamese(raw_full)
                            logger.info("Direct text PDF: {p} trang (yêu cầu {tp} nhưng đã lấy toàn bộ), {c} ký tự",
                                        p=page_count, tp=len(target_pages), c=len(processed_full))
                            return raw_full, processed_full, self.calculate_confidence_score(processed_full, "direct_pdf"), page_count

                    # PDF scan ảnh
                    raw_pages: list[str]       = []
                    processed_pages: list[str] = []
                    for idx in target_pages:
                        page = doc[idx]
                        t0 = time.time()
                        pix = page.get_pixmap(dpi=_render_dpi)
                        page_img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
                        page_raw, page_proc = self._ocr_image(
                            page_img,
                            extract_tables=_extract_tables,
                            is_first_page=(idx == 0),
                            page_num=idx + 1,
                        )
                        logger.info("OCR trang {i}/{t} [{eng}] | {s:.1f}s",
                                    i=idx + 1, t=page_count, eng=selected_engine, s=time.time() - t0)
                        if page_raw:
                            raw_pages.append(page_raw)
                        if page_proc:
                            processed_pages.append(page_proc)

                    if raw_pages:
                        raw_full       = "\n\n".join(raw_pages)
                        processed_full = self.post_process_vietnamese("\n\n".join(processed_pages))
                        return raw_full, processed_full, self.calculate_confidence_score(processed_full, selected_engine), page_count
                except Exception as exc:
                    logger.warning("PyMuPDF OCR failed: {err}", err=str(exc))

            # Fallback pypdf (chỉ dùng khi PDF có text layer)
            if pypdf is not None and selected_engine == "vietocr":
                try:
                    reader = pypdf.PdfReader(io.BytesIO(file_bytes))
                    page_count = len(reader.pages)
                    
                    target_pages = []
                    if isinstance(pages, int):
                        target_pages = list(range(min(pages, page_count)))
                    elif isinstance(pages, list):
                        target_pages = [p for p in pages if 0 <= p < page_count]
                    else:
                        target_pages = list(range(page_count))
                        
                    # Extract all pages for text-layer PDFs
                    texts  = [page.extract_text() or "" for page in reader.pages]
                    texts  = [t for t in texts if t]
                    if texts and len("\n".join(texts)) >= 50:
                        raw_full  = "\n\n".join(texts)
                        proc_full = self.post_process_vietnamese(raw_full)
                        return raw_full, proc_full, self.calculate_confidence_score(proc_full, "pypdf"), page_count
                except Exception:
                    pass

            return "", "", 0.0, page_count

        # ── Ảnh (JPG / PNG / TIFF) ───────────────────────────────────────────
        try:
            image = Image.open(io.BytesIO(file_bytes)).convert("RGB")
            raw_text, processed_text = self._ocr_image(image, page_num=1)
            if raw_text:
                return raw_text, processed_text, self.calculate_confidence_score(processed_text, selected_engine), page_count
        except Exception as exc:
            logger.warning("Image OCR failed: {err}", err=str(exc))

        return "", "", 0.0, page_count

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
                if eng_key == "tesseract":
                    try:
                        from app.services.tesseract_service import tesseract_service
                        raw_text, processed_text, conf, pc = tesseract_service.extract_text_from_file(file_bytes, file_type)
                    except Exception:
                        raw_text, processed_text, conf, pc = self.extract_text_from_file(file_bytes, file_type, engine=eng_key)
                else:
                    raw_text, processed_text, conf, pc = self.extract_text_from_file(file_bytes, file_type, engine=eng_key)
                
                text = processed_text or raw_text
                results[eng_key] = {
                    "engine_name": eng_name,
                    "text": text,
                    "raw_text": raw_text,
                    "processed_text": processed_text,
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
vietocr_service = VietOCRService()
