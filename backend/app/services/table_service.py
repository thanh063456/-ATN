"""
backend/app/services/table_service.py — Table Extraction using OpenCV Morphology & VietOCR

Áp dụng phép toán hình thái học (Morphological Operations) để:
1. Phát hiện đường viền ngang và dọc của khung bảng biểu trong văn bản hành chính.
2. Tách cấu trúc hàng, cột và từng ô (Cell Segmentation).
3. Đưa ảnh từng ô qua VietOCR để nhận dạng văn bản (hỗ trợ phân đoạn dòng trong ô đoạn văn).
4. Xuất kết quả dưới dạng Markdown Table, JSON có cấu trúc và HTML.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any, List, Optional, Tuple

import cv2
import numpy as np
from PIL import Image
from loguru import logger


@dataclass
class TableCell:
    row_idx: int
    col_idx: int
    bbox: Tuple[int, int, int, int]  # (x, y, w, h)
    text: str = ""
    confidence: float = 1.0


@dataclass
class ExtractedTable:
    table_idx: int
    bbox: Tuple[int, int, int, int]  # (x, y, w, h)
    page_num: int = 1
    headers: List[str] = field(default_factory=list)
    rows: List[List[str]] = field(default_factory=list)
    cells: List[TableCell] = field(default_factory=list)
    row_count: int = 0
    col_count: int = 0
    markdown: str = ""
    html: str = ""


@dataclass
class TableExtractionResult:
    has_table: bool
    tables: List[ExtractedTable] = field(default_factory=list)
    total_tables: int = 0
    total_cells: int = 0


class TableService:
    """Service trích xuất cấu trúc và dữ liệu bảng biểu từ ảnh tài liệu học vụ."""

    @staticmethod
    def _to_gray_thresh(img_np: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """Chuyển ảnh sang thang xám và nhị phân đảo (nét trắng trên nền đen)."""
        if len(img_np.shape) == 3:
            gray = cv2.cvtColor(img_np, cv2.COLOR_RGB2GRAY)
        else:
            gray = img_np

        # Otsu thresholding đảo: đường kẻ và chữ có giá trị 255 (trắng), nền là 0 (đen)
        _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
        return gray, thresh

    @classmethod
    def detect_table_grid(cls, thresh: np.ndarray) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """
        Dùng OpenCV Morphology với structuring element chữ nhật ngang & dọc
        để trích xuất các đường kẻ lưới của bảng biểu và hàn kín các mối nối.
        """
        h, w = thresh.shape[:2]

        # 1. Trích xuất đường kẻ ngang (Horizontal lines)
        kernel_h_len = max(20, w // 45)
        horiz = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, cv2.getStructuringElement(cv2.MORPH_RECT, (kernel_h_len, 1)))
        horiz = cv2.dilate(horiz, cv2.getStructuringElement(cv2.MORPH_RECT, (25, 1)), iterations=1)

        # 2. Trích xuất đường kẻ dọc (Vertical lines)
        kernel_v_len = max(20, h // 60)
        vert = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, cv2.getStructuringElement(cv2.MORPH_RECT, (1, kernel_v_len)))
        vert = cv2.dilate(vert, cv2.getStructuringElement(cv2.MORPH_RECT, (1, 25)), iterations=1)

        # 3. Ma trận lưới bảng (kết hợp các đường kẻ)
        table_grid = cv2.add(horiz, vert)
        # Giãn nở nhẹ 3x3 để đảm bảo các góc giao cắt nối liền 100%, không bị hở điểm ảnh
        table_grid = cv2.dilate(table_grid, np.ones((3, 3), np.uint8), iterations=1)

        return horiz, vert, table_grid

    @staticmethod
    def _clean_cell_text(text: str) -> str:
        """Lọc bỏ các ảo giác lặp từ (ví dụ: 'Thị Thị Thị Thị' hoặc '- - - -')."""
        if not text:
            return ""
        s = text.strip()
        # Loại bỏ các từ ảo giác tiếng Anh phổ biến của VietOCR khi gặp ô trống/nhiễu viền
        hallucinations = {"contraction", "contractionalists", "contract", "contractionist", "contractional"}
        if s.lower() in hallucinations:
            return ""
        # Loại bỏ chuỗi gạch nối lặp lại
        if re.match(r"^[\s\-—_]{3,}$", s):
            return ""
        # Loại bỏ từ đơn lặp liên tiếp quá 2 lần
        words = s.split()
        if len(words) >= 4:
            cleaned_words = []
            repeat_count = 0
            prev_word = None
            for w in words:
                w_lower = w.lower()
                if w_lower == prev_word:
                    repeat_count += 1
                    if repeat_count < 2:
                        cleaned_words.append(w)
                else:
                    prev_word = w_lower
                    repeat_count = 0
                    cleaned_words.append(w)
            s = " ".join(cleaned_words)
        return s.strip()

    @classmethod
    def _ocr_cell_crop(cls, cell_crop: np.ndarray, vietocr_pred=None) -> str:
        """
        Nhận diện chữ trong một ô bảng biểu.
        - Với ô 1 dòng ngắn: gọi VietOCR trực tiếp.
        - Với ô đoạn văn nhiều dòng: phân đoạn dòng bằng EasyOCR/VietOCR pipeline rồi ghép lại.
        """
        if cell_crop.size == 0 or vietocr_pred is None:
            return ""

        h, w = cell_crop.shape[:2]
        if h < 6 or w < 6:
            return ""

        # Kiểm tra xem ô có chứa điểm ảnh chữ hay không (tránh OCR ô trắng)
        if len(cell_crop.shape) == 3:
            gray = cv2.cvtColor(cell_crop, cv2.COLOR_RGB2GRAY)
        else:
            gray = cell_crop

        _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
        
        # Xóa các đường viền mép còn sót lại
        thresh[0:3, :] = 0
        thresh[-3:, :] = 0
        thresh[:, 0:3] = 0
        thresh[:, -3:] = 0

        nz = cv2.findNonZero(thresh)
        if nz is None or len(nz) < 18:
            return ""

        # Cắt sát vùng có chữ (tight bounding box) để loại bỏ khoảng trắng thừa
        tx, ty, tw, th = cv2.boundingRect(nz)
        if tw < 3 or th < 5:
            return ""

        pad = 4
        y1 = max(0, ty - pad)
        y2 = min(h, ty + th + pad)
        x1 = max(0, tx - pad)
        x2 = min(w, tx + tw + pad)
        tight_crop = cell_crop[y1:y2, x1:x2]
        crop_h, crop_w = tight_crop.shape[:2]

        tight_pil = Image.fromarray(tight_crop)

        # 1. Nếu ô là 1 dòng ngắn (chiều cao <= 40px)
        if crop_h <= 40:
            try:
                if crop_h < 32 and crop_h > 4:
                    scale = 36.0 / crop_h
                    tight_pil = tight_pil.resize((max(10, int(crop_w * scale)), 36), Image.Resampling.BILINEAR)
                raw_txt = vietocr_pred.predict(tight_pil)
                return cls._clean_cell_text(raw_txt)
            except Exception:
                return ""

        # 2. Nếu ô là đoạn văn nhiều dòng (chiều cao > 40px)
        try:
            from app.services.vietocr_service import vietocr_service

            lines = vietocr_service._ocr_lines_with_engine(tight_pil)
            if lines:
                text_lines = [cls._clean_cell_text(l[0]) for l in lines if l[0].strip()]
                text_lines = [l for l in text_lines if l]
                if text_lines:
                    return "\n".join(text_lines)

            # Fallback nếu không tách được dòng
            raw_txt = vietocr_pred.predict(tight_pil)
            return cls._clean_cell_text(raw_txt)
        except Exception as exc:
            logger.debug(f"Lỗi OCR ô nhiều dòng: {exc}")
            try:
                return cls._clean_cell_text(vietocr_pred.predict(tight_pil))
            except Exception:
                return ""

    @classmethod
    def extract_tables(
        cls,
        image: Image.Image,
        ocr_cells: bool = True,
        min_table_width: int = 150,
        min_table_height: int = 60,
    ) -> TableExtractionResult:
        """
        Phát hiện và bóc tách toàn bộ bảng biểu trên trang tài liệu.
        Nếu ocr_cells=True, sẽ gọi VietOCR để đọc nội dung chữ trong từng ô.
        """
        if image is None:
            return TableExtractionResult(has_table=False)

        img_rgb = np.array(image.convert("RGB"))
        gray, thresh = cls._to_gray_thresh(img_rgb)
        h_page, w_page = thresh.shape[:2]

        horiz, vert, table_grid = cls.detect_table_grid(thresh)

        # Tìm các vùng bao quanh bảng biểu (bảng hoàn chỉnh)
        table_contours, _ = cv2.findContours(table_grid, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        extracted_tables: List[ExtractedTable] = []
        total_cells_count = 0

        # Lấy predictor của VietOCR nếu cần OCR từng ô
        vietocr_pred = None
        if ocr_cells:
            try:
                from app.services.vietocr_engine import vietocr_engine

                vietocr_pred = vietocr_engine.get_predictor()
            except Exception as ocr_exc:
                logger.debug(f"Không thể nạp VietOCR cho TableService (dùng fallback): {ocr_exc}")

        # Sắp xếp các bảng từ trên xuống dưới
        candidate_tables = []
        for t_cnt in table_contours:
            tx, ty, tw, th = cv2.boundingRect(t_cnt)
            # Lọc bỏ vùng quá bé không phải bảng
            if tw < min_table_width or th < min_table_height:
                continue
            # Bỏ qua nếu vùng chiếm quá 98% trang (nhiễu viền scan toàn trang)
            if tw > w_page * 0.98 and th > h_page * 0.98:
                continue
            candidate_tables.append((tx, ty, tw, th))

        candidate_tables.sort(key=lambda t: t[1])

        tbl_idx = 0
        for tx, ty, tw, th in candidate_tables:
            tbl_idx += 1
            table_roi = table_grid[ty : ty + th, tx : tx + tw]

            # Đảo nhị phân: các ô bên trong biến thành màu trắng (255), đường kẻ biến thành màu đen (0)
            table_cells_img = cv2.bitwise_not(table_roi)
            # Xóa các cạnh ngoài để khung bao bảng không bị tính là 1 ô
            table_cells_img[0:3, :] = 0
            table_cells_img[-3:, :] = 0
            table_cells_img[:, 0:3] = 0
            table_cells_img[:, -3:] = 0

            # Tìm các ô con (cells) bên trong bảng
            c_contours, _ = cv2.findContours(table_cells_img, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

            raw_boxes = []
            for c_cnt in c_contours:
                cx, cy, cw, ch = cv2.boundingRect(c_cnt)
                # Ô hợp lệ phải có kích thước tối thiểu
                if cw >= 15 and ch >= 12 and cw < tw - 4 and ch < th - 4:
                    raw_boxes.append((cx, cy, cw, ch))

            if not raw_boxes:
                continue

            # Gom nhóm các ô thành Hàng (Rows) dựa trên khoảng giao nhau trục y
            raw_boxes.sort(key=lambda b: (b[1], b[0]))
            grouped_rows: List[List[Tuple[int, int, int, int]]] = []
            for b in raw_boxes:
                bx, by, bw, bh = b
                placed = False
                for r in grouped_rows:
                    rx, ry, rw, rh = r[0]
                    inter_y1 = max(by, ry)
                    inter_y2 = min(by + bh, ry + rh)
                    overlap = max(0, inter_y2 - inter_y1)
                    if overlap >= max(10, 0.35 * min(bh, rh)):
                        r.append(b)
                        placed = True
                        break
                if not placed:
                    grouped_rows.append([b])

            # Sắp xếp các ô trong từng hàng từ trái sang phải
            for r in grouped_rows:
                r.sort(key=lambda b: b[0])
            # Sắp xếp các hàng từ trên xuống dưới
            grouped_rows.sort(key=lambda r: r[0][1])

            # Xác định các mốc tọa độ x chuẩn của các cột
            all_xs = sorted([b[0] for b in raw_boxes])
            col_x_starts = []
            for x in all_xs:
                if not any(abs(x - cx) <= 18 for cx in col_x_starts):
                    col_x_starts.append(x)
            col_x_starts.sort()
            num_cols = max(len(col_x_starts), max((len(r) for r in grouped_rows), default=1))

            table_cells: List[TableCell] = []
            table_row_data: List[List[str]] = []

            for r_idx, row_boxes in enumerate(grouped_rows):
                row_texts = [""] * num_cols
                for cx, cy, cw, ch in row_boxes:
                    # Gán ô vào cột phù hợp nhất theo tọa độ x
                    if col_x_starts:
                        best_c_idx = min(range(len(col_x_starts)), key=lambda i: abs(col_x_starts[i] - cx))
                    else:
                        best_c_idx = 0
                    best_c_idx = min(best_c_idx, num_cols - 1)

                    abs_x = tx + cx
                    abs_y = ty + cy

                    cell_text = ""
                    # Cắt ảnh ô con (lùi vào 3px để loại bỏ viền đen)
                    inset = 3
                    crop_y1 = max(0, abs_y + inset)
                    crop_y2 = min(img_rgb.shape[0], abs_y + ch - inset)
                    crop_x1 = max(0, abs_x + inset)
                    crop_x2 = min(img_rgb.shape[1], abs_x + cw - inset)
                    cell_crop = img_rgb[crop_y1:crop_y2, crop_x1:crop_x2]

                    if cell_crop.size > 0 and ocr_cells:
                        cell_text = cls._ocr_cell_crop(cell_crop, vietocr_pred=vietocr_pred)
                    elif not ocr_cells:
                        cell_text = f"Ô ({r_idx+1},{best_c_idx+1})"

                    row_texts[best_c_idx] = cell_text
                    table_cells.append(
                        TableCell(
                            row_idx=r_idx,
                            col_idx=best_c_idx,
                            bbox=(abs_x, abs_y, cw, ch),
                            text=cell_text,
                        )
                    )

                table_row_data.append(row_texts)

            # Lọc bỏ các dòng hoàn toàn trống (khi chạy OCR)
            if ocr_cells:
                table_row_data = [r for r in table_row_data if any(c.strip() for c in r)]

            if not table_row_data:
                continue

            # Dòng đầu tiên được xem là Header của bảng
            headers = table_row_data[0] if table_row_data else []
            data_rows = table_row_data[1:] if len(table_row_data) > 1 else []

            # Sinh định dạng Markdown Table và HTML
            markdown_str = cls._generate_markdown(headers, data_rows)
            html_str = cls._generate_html(headers, data_rows)

            total_cells_count += len(table_cells)

            extracted_tables.append(
                ExtractedTable(
                    table_idx=tbl_idx,
                    bbox=(tx, ty, tw, th),
                    headers=headers,
                    rows=data_rows,
                    cells=table_cells,
                    row_count=len(table_row_data),
                    col_count=num_cols,
                    markdown=markdown_str,
                    html=html_str,
                )
            )

        return TableExtractionResult(
            has_table=len(extracted_tables) > 0,
            tables=extracted_tables,
            total_tables=len(extracted_tables),
            total_cells=total_cells_count,
        )

    @staticmethod
    def _generate_markdown(headers: List[str], rows: List[List[str]]) -> str:
        """Tạo bảng Markdown chuẩn GitHub Flavored Markdown (hỗ trợ <br> cho ô nhiều dòng)."""
        if not headers and not rows:
            return ""

        max_cols = max([len(headers)] + [len(r) for r in rows]) if (headers or rows) else 0
        if max_cols == 0:
            return ""

        padded_headers = list(headers) + [f"Cột {i+1}" for i in range(len(headers), max_cols)]
        clean_headers = [str(h if h else f"Cột {i+1}").replace("|", "\\|").replace("\n", " ") for i, h in enumerate(padded_headers)]

        md_lines = [
            "| " + " | ".join(clean_headers) + " |",
            "| " + " | ".join([":---"] * max_cols) + " |",
        ]

        for row in rows:
            clean_row = [str(c if c else "").replace("|", "\\|").replace("\n", "<br>") for c in row]
            padded_row = clean_row + [""] * (max_cols - len(clean_row))
            md_lines.append("| " + " | ".join(padded_row) + " |")

        return "\n".join(md_lines)

    @staticmethod
    def _generate_html(headers: List[str], rows: List[List[str]]) -> str:
        """Tạo mã HTML table đẹp mắt cho frontend."""
        if not headers and not rows:
            return ""
        html = ['<table class="table-auto border-collapse border border-slate-300 w-full text-sm">']
        if headers:
            html.append("  <thead>\n    <tr class='bg-slate-100'>")
            for h in headers:
                safe_h = (h or "").replace("\n", "<br/>")
                html.append(f"      <th class='border border-slate-300 px-3 py-2 text-left font-bold'>{safe_h}</th>")
            html.append("    </tr>\n  </thead>")

        if rows:
            html.append("  <tbody>")
            for row in rows:
                html.append("    <tr class='hover:bg-slate-50'>")
                for cell in row:
                    safe_c = (cell or "").replace("\n", "<br/>")
                    html.append(f"      <td class='border border-slate-300 px-3 py-2 align-top'>{safe_c}</td>")
                html.append("    </tr>")
            html.append("  </tbody>")
        html.append("</table>")
        return "\n".join(html)


table_service = TableService()
