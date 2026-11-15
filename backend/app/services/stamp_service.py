"""
backend/app/services/stamp_service.py — Red Seal / Stamp Detection & Color Separation

Áp dụng giải pháp không gian màu HSV & Phép toán hình thái học (Morphology) để:
1. Phát hiện và trích xuất con dấu đỏ (Red Stamp Detection & Cropping).
2. Tách lớp mực đỏ (Red Ink Removal / Inpainting) nhằm khôi phục nét chữ đen
   bị con dấu đè lên, giúp hạ thấp đáng kể tỷ lệ lỗi CER cho VietOCR và TrOCR.
"""

from __future__ import annotations

import base64
import io
from dataclasses import dataclass, field
from typing import Any, List, Optional, Tuple

import cv2
import numpy as np
from PIL import Image
from loguru import logger


@dataclass
class DetectedStamp:
    bbox: Tuple[int, int, int, int]  # (x, y, w, h)
    confidence: float
    area: float
    aspect_ratio: float
    image_base64: str = ""
    is_circular: bool = False


@dataclass
class StampExtractionResult:
    has_stamp: bool
    stamps: List[DetectedStamp] = field(default_factory=list)
    cleaned_image: Optional[Image.Image] = None
    cleaned_image_base64: str = ""
    red_pixel_ratio: float = 0.0


class StampService:
    """Service xử lý con dấu đỏ bằng kỹ thuật phân tích dải màu HSV và OpenCV Morphology."""

    # Dải màu đỏ trong không gian HSV (OpenCV H: 0-180, S: 0-255, V: 0-255)
    # Màu đỏ nằm ở 2 dải cận biên của kênh Hue
    LOWER_RED_1 = np.array([0, 50, 50], dtype=np.uint8)
    UPPER_RED_1 = np.array([12, 255, 255], dtype=np.uint8)

    LOWER_RED_2 = np.array([165, 50, 50], dtype=np.uint8)
    UPPER_RED_2 = np.array([180, 255, 255], dtype=np.uint8)

    @classmethod
    def get_red_mask(cls, img_bgr: np.ndarray) -> np.ndarray:
        """Tạo mặt nạ nhị phân cho các điểm ảnh có màu đỏ trong không gian HSV."""
        hsv = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2HSV)
        mask1 = cv2.inRange(hsv, cls.LOWER_RED_1, cls.UPPER_RED_1)
        mask2 = cv2.inRange(hsv, cls.LOWER_RED_2, cls.UPPER_RED_2)
        red_mask = cv2.bitwise_or(mask1, mask2)
        return red_mask

    @classmethod
    def detect_and_extract_stamps(
        cls,
        image: Image.Image,
        min_area: int = 1200,
        padding: int = 8,
        inpaint_text: bool = True,
    ) -> StampExtractionResult:
        """
        Phát hiện toàn bộ con dấu đỏ trên trang tài liệu:
        - Trích xuất bounding box và cắt ảnh con dấu dưới dạng Base64 PNG.
        - Khôi phục nét chữ đen bị con dấu đè lên bằng inpainting.
        """
        if image is None:
            return StampExtractionResult(has_stamp=False)

        # Chuyển đổi PIL Image sang numpy array BGR
        img_rgb = np.array(image.convert("RGB"))
        img_bgr = cv2.cvtColor(img_rgb, cv2.COLOR_RGB2BGR)
        h, w = img_bgr.shape[:2]

        red_mask = cls.get_red_mask(img_bgr)
        total_pixels = h * w
        red_pixels = int(cv2.countNonZero(red_mask))
        red_ratio = float(red_pixels / max(total_pixels, 1))

        # Nếu lượng pixel đỏ quá ít (< 0.05% trang), không có con dấu đáng kể
        if red_pixels < 200:
            return StampExtractionResult(
                has_stamp=False,
                stamps=[],
                cleaned_image=image,
                red_pixel_ratio=red_ratio,
            )

        # Kết nối các nét mực đỏ rời rạc của con dấu thành khối hình thái học
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (9, 9))
        closed_mask = cv2.morphologyEx(red_mask, cv2.MORPH_CLOSE, kernel, iterations=2)
        dilated_mask = cv2.dilate(closed_mask, kernel, iterations=2)

        contours, _ = cv2.findContours(dilated_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        detected_stamps: List[DetectedStamp] = []
        stamp_combined_mask = np.zeros((h, w), dtype=np.uint8)

        for cnt in contours:
            area = float(cv2.contourArea(cnt))
            if area < min_area:
                continue

            bx, by, bw, bh = cv2.boundingRect(cnt)
            aspect_ratio = float(bw) / max(bh, 1)

            # Con dấu cơ quan hành chính Việt Nam hình tròn hoặc oval elip: 0.6 <= aspect_ratio <= 1.6
            if not (0.55 <= aspect_ratio <= 1.75):
                continue

            # Giới hạn kích thước tối thiểu và tối đa hợp lý trên trang A4
            if bw < 35 or bh < 35 or bw > w * 0.7 or bh > h * 0.7:
                continue

            # Tính độ tròn (circularity)
            perimeter = cv2.arcLength(cnt, True)
            circularity = (4 * np.pi * area) / max((perimeter * perimeter), 0.001)
            is_circular = circularity > 0.45

            # Tọa độ cắt có padding
            x1 = max(0, bx - padding)
            y1 = max(0, by - padding)
            x2 = min(w, bx + bw + padding)
            y2 = min(h, by + bh + padding)

            crop_bgr = img_bgr[y1:y2, x1:x2]
            crop_rgb = cv2.cvtColor(crop_bgr, cv2.COLOR_BGR2RGB)
            crop_pil = Image.fromarray(crop_rgb)

            # Chuyển ảnh crop sang base64 PNG
            buf = io.BytesIO()
            crop_pil.save(buf, format="PNG")
            b64_str = f"data:image/png;base64,{base64.b64encode(buf.getvalue()).decode('utf-8')}"

            confidence = min(0.99, max(0.50, float(0.60 + 0.30 * min(circularity, 1.0) + 0.10 * min(area / 10000.0, 1.0))))

            detected_stamps.append(
                DetectedStamp(
                    bbox=(int(x1), int(y1), int(x2 - x1), int(y2 - y1)),
                    confidence=round(confidence, 3),
                    area=round(area, 1),
                    aspect_ratio=round(aspect_ratio, 2),
                    image_base64=b64_str,
                    is_circular=is_circular,
                )
            )

            # Gom vùng con dấu vào mặt nạ tổng thể
            cv2.drawContours(stamp_combined_mask, [cnt], -1, 255, -1)

        # ── Tách lớp mực đỏ & Khôi phục nét chữ đen (Inpainting / Filtering) ───
        cleaned_pil = image
        cleaned_b64 = ""

        if inpaint_text and red_pixels > 0:
            try:
                # Phân biệt mực đỏ thuần túy với nét chữ đen bị mực đỏ đè lên:
                # Nét chữ đen có cường độ sáng thấp (Grayscale <= 95)
                gray = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY)
                dark_text_mask = gray < 95

                # Mặt nạ mực đỏ cần tẩy: là pixel đỏ nhưng KHÔNG PHẢI nét chữ đen
                pure_red_ink = cv2.bitwise_and(red_mask, red_mask, mask=cv2.bitwise_not(dark_text_mask.astype(np.uint8) * 255))

                # Làm dày nhẹ mặt nạ mực đỏ để inpaint mượt
                pure_red_dilated = cv2.dilate(pure_red_ink, np.ones((3, 3), np.uint8), iterations=1)

                # Inpaint bằng thuật toán Telea
                inpainted_bgr = cv2.inpaint(img_bgr, pure_red_dilated, inpaintRadius=3, flags=cv2.INPAINT_TELEA)
                inpainted_rgb = cv2.cvtColor(inpainted_bgr, cv2.COLOR_BGR2RGB)
                cleaned_pil = Image.fromarray(inpainted_rgb)

                buf_clean = io.BytesIO()
                cleaned_pil.save(buf_clean, format="JPEG", quality=90)
                cleaned_b64 = f"data:image/jpeg;base64,{base64.b64encode(buf_clean.getvalue()).decode('utf-8')}"
            except Exception as inpaint_exc:
                logger.warning(f"Lỗi khi inpaint bóc tách con dấu: {inpaint_exc}")

        return StampExtractionResult(
            has_stamp=len(detected_stamps) > 0,
            stamps=detected_stamps,
            cleaned_image=cleaned_pil,
            cleaned_image_base64=cleaned_b64,
            red_pixel_ratio=round(red_ratio, 4),
        )

    @classmethod
    def remove_red_stamp_for_ocr(cls, pil_image: Image.Image) -> Image.Image:
        """
        Hàm tiện ích nhanh dùng trong tiền xử lý OCR:
        Loại bỏ lớp mực đỏ con dấu, chỉ giữ lại nét chữ đen nguyên bản.
        """
        if pil_image is None or cv2 is None:
            return pil_image
        try:
            img_rgb = np.array(pil_image.convert("RGB"))
            img_bgr = cv2.cvtColor(img_rgb, cv2.COLOR_RGB2BGR)

            red_mask = cls.get_red_mask(img_bgr)
            if cv2.countNonZero(red_mask) < 50:
                return pil_image

            gray = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY)
            dark_text_mask = (gray < 95).astype(np.uint8) * 255
            pure_red_ink = cv2.bitwise_and(red_mask, red_mask, mask=cv2.bitwise_not(dark_text_mask))
            pure_red_dilated = cv2.dilate(pure_red_ink, np.ones((3, 3), np.uint8), iterations=1)

            inpainted_bgr = cv2.inpaint(img_bgr, pure_red_dilated, inpaintRadius=2, flags=cv2.INPAINT_TELEA)
            return Image.fromarray(cv2.cvtColor(inpainted_bgr, cv2.COLOR_BGR2RGB))
        except Exception as exc:
            logger.debug(f"remove_red_stamp_for_ocr fallback: {exc}")
            return pil_image


stamp_service = StampService()

