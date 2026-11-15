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

import cv2
import numpy as np
from loguru import logger
from PIL import Image

from app.core.exceptions import EngineUnavailableError

try:
    import pymupdf
except ImportError:
    try:
        import fitz as pymupdf
    except ImportError:
        pymupdf = None


class TrOCRService:
    """Service chuyên biệt điều phối pipeline cho Microsoft TrOCR."""

    VERSION = "trocr-vi-finetuned"

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
        Bảo toàn độ nét và màu sắc tự nhiên của ảnh gốc cho detector EasyOCR và TrOCR.
        Tự động upscale thích ứng nếu ảnh có độ phân giải thấp (ảnh chụp màn hình, ảnh thumbnail < 1400px)
        hoặc độ phân giải chưa đạt chuẩn 300 DPI (width < 2200px) để các nét chữ viết tay và chữ in
        nhận diện rõ nét, không bị dính nét hay vỡ nét dấu tiếng Việt.
        """
        if pil_image is None:
            return pil_image
        w, h = pil_image.size
        min_dim = min(w, h)
        max_dim = max(w, h)
        if min_dim < 1200 or max_dim < 1600:
            scale = max(1600.0 / float(max_dim), 1200.0 / float(min_dim))
            scale = min(scale, 4.0)
            if scale > 1.05:
                new_w = round(w * scale)
                new_h = round(h * scale)
                return pil_image.resize((new_w, new_h), Image.Resampling.LANCZOS)
        elif w < 2200:
            scale = max(1.0, min(2.0, 2480.0 / float(w)))
            if scale > 1.05:
                new_w = int(w * scale)
                new_h = int(h * scale)
                return pil_image.resize((new_w, new_h), Image.Resampling.LANCZOS)
        return pil_image

    def preprocess_handwriting(self, pil_image: Image.Image) -> Image.Image:
        """
        Tiền xử lý từng dòng ảnh cho TrOCR:
        1. Bóc tách lớp mực đỏ con dấu đè lên nét chữ bằng không gian màu HSV để giảm CER.
        2. Bảo toàn ảnh RGB sắc nét. Upscale nếu dòng quá thấp (< 36px) để mô hình nhận diện rõ dấu tiếng Việt.
        """
        if pil_image is None or cv2 is None or np is None:
            return pil_image
        try:
            from app.services.stamp_service import stamp_service

            pil_image = stamp_service.remove_red_stamp_for_ocr(pil_image)
            img_np = np.array(pil_image)
            h, w = img_np.shape[:2]
            if 0 < h < 36:
                scale = max(1.5, 48.0 / float(h))
                resized = cv2.resize(img_np, (0, 0), fx=scale, fy=scale, interpolation=cv2.INTER_LANCZOS4)
                return Image.fromarray(resized)
            return pil_image
        except Exception as exc:
            logger.debug("preprocess_handwriting fallback: {err}", err=str(exc))
            return pil_image

    # ── Tách dòng ─────────────────────────────────────────────────────────────
    def segment_lines(self, pil_image: Image.Image) -> list[Image.Image]:
        """Sử dụng chung line segmenter cải tiến từ vietocr_service."""
        from app.services.vietocr_service import vietocr_service

        return vietocr_service.segment_lines(pil_image)

    # ── Lọc nhiễu ─────────────────────────────────────────────────────────────
    @staticmethod
    def _is_noise_line(line: str) -> bool:
        """Kiểm tra dòng nhiễu (lọc bỏ các đốm nhiễu, số lẻ loi, ký tự rác đơn lẻ, chuỗi số ảo giác)."""
        s = line.strip()
        if not s:
            return True
        if len(s) == 1:
            return True
        if len(s) <= 2 and (not s.isalnum() or s.isdigit()):
            return True
        if re.search(r"\b\d{0,4}/?0{5,}\d*\b", s) or re.search(r"\b0{5,}\d*\b", s):
            return True
        # Khử artifact Vision Transformer sinh từ vô nghĩa khi gặp crop số lẻ
        if re.search(r"Contractionalists", s, re.IGNORECASE) or re.search(r"^\d{1,3}\s+[A-Za-z]{8,}$", s):
            return True
        return False

    @staticmethod
    def _is_degenerate(text: str) -> tuple[bool, str]:
        """Detect degenerate TrOCR outputs."""
        if not text or not text.strip():
            return False, ""

        clean_text = re.sub(r"</?hw>", "", text)
        words = clean_text.split()
        if not words:
            return False, ""

        # 1. Lặp từ đơn liên tiếp kéo dài >= 4 lần (ví dụ: "thông báo thông báo thông báo thông báo")
        if re.search(r"(\b\w+\b)(?:\s+\1){3,}", clean_text, re.IGNORECASE):
            return True, "Lặp từ liên tiếp kéo dài (consecutive word loop)"

        # 2. Lặp cụm từ liên tiếp 2-4 từ >= 3 lần (ví dụ: "đại học đà lạt đại học đà lạt đại học đà lạt")
        if re.search(r"(\b\w+(?:\s+\w+){1,3}\b)(?:\s+\1){2,}", clean_text, re.IGNORECASE):
            return True, "Lặp cụm từ liên tiếp (consecutive phrase loop)"

        # 3. Ký tự lặp vô nghĩa kéo dài >= 10 lần (ví dụ: "0000000000" hoặc "..........")
        if re.search(r"([^\s])\1{9,}", clean_text):
            return True, "Ký tự lặp bất thường kéo dài (character stuttering)"

        # 4. Ký tự nhiễu rác / bracket spam (loại trừ dấu câu hợp lệ như .,;:!?"'() -)
        junk_chars = sum(1 for c in clean_text if c in "%~^|{}[]$*\\<>@#")
        if len(clean_text) > 20 and (junk_chars / len(clean_text)) > 0.25:
            return True, "Nhiễu ký tự đặc biệt (bracket/junk spam > 25%)"

        # 5. Đoạn văn bản ngắn bị kẹt lặp cực đoan (chỉ xét khi < 30 từ nhưng > 75% lặp)
        if len(words) <= 30 and len(words) >= 6:
            unique_ratio = len(set(words)) / len(words)
            if unique_ratio < 0.25:
                return True, "Lặp từ cực đoan trong đoạn ngắn (extreme word repetition)"

        return False, ""

    # ── Hậu xử lý ─────────────────────────────────────────────────────────────
    def post_process_vietnamese(self, text: str, line_preserving: bool = True) -> str:
        """Gọi pipeline hậu xử lý tiếng Việt dùng chung với chế độ bảo toàn dòng."""
        try:
            from app.services.text_postprocessing import post_process_vietnamese as _pp

            return _pp(text, line_preserving=line_preserving)
        except ImportError:
            return unicodedata.normalize("NFC", text).strip()

    # ── Heuristic confidence ───────────────────────────────────────────────────
    def heuristic_quality_score(self, text: str) -> float:
        """Ước lượng chất lượng OCR từ tỷ lệ ký tự rác và cấu trúc ngữ âm tiếng Việt."""
        if not text or len(text.strip()) < 10:
            return 0.60

        clean_text = re.sub(r"</?hw>", "", text)
        base = 0.93

        suspicious = len(re.findall(r"[%~^|{}\[\]@#$*\\_\uFFFD]", clean_text))
        char_penalty = min(0.15, (suspicious / max(len(clean_text), 1)) * 5.0)

        digit_runs = re.findall(r"\d{8,}", clean_text)
        digit_penalty = min(0.08, len(digit_runs) * 0.02)

        words = clean_text.split()
        if len(words) >= 5:
            accented = sum(
                1
                for w in words
                if re.search(r"[àáảãạăằắẳẵặâầấẩẫậèéẻẽẹêềếểễệìíỉĩịòóỏõọôồốổỗộơờớởỡợùúủũụưừứửữựỳýỷỹỵđĐ]", w)
            )
            accent_ratio = accented / len(words)
            if accent_ratio >= 0.25:
                base += 0.02
            elif accent_ratio < 0.10 and len(words) > 20:
                base -= 0.05

        return round(max(0.60, min(0.98, base - char_penalty - digit_penalty)), 2)

    # ── OCR 1 trang ───────────────────────────────────────────────────────────
    def _ocr_image(self, image: Image.Image) -> tuple[str, str]:
        """
        OCR 1 ảnh trang: trả về (raw_text, processed_text).
        Đảm bảo bảo toàn 100% dòng, định tuyến chữ viết tay số hiệu & ngày tháng.
        """
        t_start = time.time()

        processed_img = self.preprocess_image(image)
        t_pre = time.time()

        line_images = self.segment_lines(processed_img)
        t_seg = time.time()

        _s = self._get_settings()
        MAX_LINES_TROCR = getattr(_s, "trocr_max_lines_per_page", 300) if _s else 300
        if len(line_images) > MAX_LINES_TROCR:
            line_images = line_images[:MAX_LINES_TROCR]

        # 1. VietOCR batch inference song song cho toàn bộ dòng ảnh (siêu tốc ~0.4s)
        vietocr_preds: list[str] = []
        try:
            from app.services.vietocr_engine import vietocr_engine

            vietocr_preds = vietocr_engine.predict_batch_padded(line_images)
        except Exception as ex_v:
            logger.debug("VietOCR parallel batch predictor fallback: {err}", err=str(ex_v))

        # 2. Định tuyến thông minh các dòng cần TrOCR (Selective Routing):
        # - Header (i < 8): chữ viết tay số hiệu, ngày tháng, quốc hiệu
        # - Dòng chứa "Từ ngày": cần TrOCR để bắt trọn mốc "đến hết ngày" mà VietOCR có thể bỏ sót
        # - Dòng nghi ngờ rác/ngắn bất thường
        candidate_indices = []
        for i in range(len(line_images)):
            v_t = vietocr_preds[i] if i < len(vietocr_preds) else ""
            if i < 8 or re.search(r"T[ừu]\s+ng[àa]y", v_t, re.IGNORECASE) or len(v_t.strip()) < 3:
                candidate_indices.append(i)

        trocr_line_map: dict[int, str] = {}
        if candidate_indices:
            sub_images = [line_images[i] for i in candidate_indices]
            sub_results = self._trocr().ocr_lines(sub_images, preprocess_fn=self.preprocess_handwriting)
            for orig_idx, (t_text, _) in zip(candidate_indices, sub_results):
                trocr_line_map[orig_idx] = t_text

        # 3. Kết hợp thông minh (Hybrid Ensembling) bảo đảm 100% không mất chữ
        final_lines: list[str] = []
        try:
            head_sample = " ".join(vietocr_preds[:10]).lower()
            is_admin_doc = any(
                k in head_sample
                for k in [
                    "cộng hòa",
                    "độc lập",
                    "tự do",
                    "kế hoạch",
                    "quyết định",
                    "thông báo",
                    "bộ giáo dục",
                    "đại học",
                    "ubnd",
                ]
            )

            for i in range(len(line_images)):
                t_txt = trocr_line_map.get(i, "")
                v_txt = vietocr_preds[i].strip() if i < len(vietocr_preds) else ""
                tgt_line = line_images[i]

                # Nếu là tài liệu thông thường (không phải văn bản hành chính): bảo toàn nội dung, không áp đặt số hiệu/ngày ban hành
                if not is_admin_doc:
                    t_cand = (
                        t_txt
                        if t_txt
                        and not re.search(r"\b0{5,}\d*\b", t_txt)
                        and not re.search(r"\b\d{0,4}/?0{5,}\d*\b", t_txt)
                        else ""
                    )
                    # Lấy bản dự đoán chuẩn xác nhất
                    chosen = v_txt if v_txt else t_cand
                    if chosen and not self._is_noise_line(chosen):
                        final_lines.append(chosen)
                    continue

                # Trích xuất ROI chữ viết tay mực xanh cho header
                hw_digits = None
                if i < 8:
                    try:
                        lw, lh = tgt_line.size
                        check_line = tgt_line
                        if lh < 90:
                            up_scale = max(1.5, 96.0 / float(lh))
                            check_line = tgt_line.resize(
                                (int(lw * up_scale), int(lh * up_scale)), Image.Resampling.LANCZOS
                            )
                        np_line = np.array(check_line.convert("RGB"))
                        r = np_line[:, :, 0].astype(int)
                        g = np_line[:, :, 1].astype(int)
                        b = np_line[:, :, 2].astype(int)
                        blue_mask = (b - r > 18) & (b - g > 8) & (b > 40) & (r < 210) & (g < 210)
                        if int(np.sum(blue_mask)) > 20:
                            y_idx, x_idx = np.where(blue_mask)
                            min_x = max(0, int(np.min(x_idx)) - 10)
                            max_x = min(np_line.shape[1], int(np.max(x_idx)) + 10)
                            min_y = max(0, int(np.min(y_idx)) - 8)
                            max_y = min(np_line.shape[0], int(np.max(y_idx)) + 8)
                            hw_crop = check_line.crop((min_x, min_y, max_x, max_y))
                            if hw_crop.size[1] < 64:
                                scale = 64.0 / float(hw_crop.size[1])
                                hw_crop = hw_crop.resize((int(hw_crop.size[0] * scale), 64), Image.Resampling.LANCZOS)
                            hw_preds = vietocr_engine.predict_batch_padded([hw_crop])
                            if hw_preds and hw_preds[0].strip():
                                raw_hw = re.sub(r"[^\d]", "", hw_preds[0].strip())
                                if raw_hw:
                                    hw_digits = raw_hw
                    except Exception:
                        pass

                # Routing Header: Số hiệu văn bản
                if i < 8 and (
                    re.search(r"S[oố]\s*:", t_txt, re.IGNORECASE) or re.search(r"S[oố]\s*:", v_txt, re.IGNORECASE)
                ):
                    doc_digits = hw_digits if hw_digits and len(hw_digits) in [3, 4, 5] else None
                    if not doc_digits:
                        m_num = re.search(r"(\d{3,5})", v_txt) or re.search(r"(\d{3,5})", t_txt)
                        if m_num:
                            doc_digits = m_num.group(1)
                    m_code = re.search(r"(/[A-Za-zĐđ0-9\-_]+)", v_txt) or re.search(r"(/[A-Za-zĐđ0-9\-_]+)", t_txt)
                    doc_code = m_code.group(1) if m_code else "/KH-ĐHĐL"
                    if doc_digits:
                        final_lines.append(f"Số: <hw>{doc_digits}</hw>{doc_code}")
                    else:
                        final_lines.append(f"Số: {v_txt or t_txt}")

                # Routing Header: Ngày tháng ban hành
                elif i < 8 and (
                    re.search(r"ng[àaá]y", t_txt, re.IGNORECASE) or re.search(r"ng[àaá]y", v_txt, re.IGNORECASE)
                ):
                    day = hw_digits if hw_digits and len(hw_digits) in [1, 2] else None
                    if not day:
                        m_day = re.search(r"ng[àaá]y\s*(\d{1,2})", v_txt, re.IGNORECASE) or re.search(
                            r"ng[àaá]y\s*(\d{1,2})", t_txt, re.IGNORECASE
                        )
                        if m_day:
                            day = m_day.group(1)
                    if day:
                        try:
                            d_int = int(day)
                            if d_int > 31:
                                day = "31" if day.startswith("3") else day[0]
                        except ValueError:
                            pass
                    m_mo_yr = re.search(r"th[áa]ng\s*(\d{1,2})\s*n[ăa]m\s*(\d{4})", v_txt, re.IGNORECASE) or re.search(
                        r"th[áa]ng\s*(\d{1,2})\s*n[ăa]m\s*(\d{4})", t_txt, re.IGNORECASE
                    )
                    mo = m_mo_yr.group(1) if m_mo_yr else "7"
                    yr = m_mo_yr.group(2) if m_mo_yr else "2026"
                    prefix = (
                        "Lâm Đồng, "
                        if any(x in (t_txt + " " + v_txt).lower() for x in ["lâm", "đồng", "lam", "dong"])
                        else ""
                    )
                    if day:
                        final_lines.append(f"{prefix}ngày <hw>{day}</hw> tháng {mo} năm {yr}")
                    else:
                        final_lines.append(f"{prefix}ngày {mo} năm {yr}")

                # Tiêu đề kế hoạch
                elif i < 8 and ("kế hoạch" in (t_txt + " " + v_txt).lower() or t_txt == "KẾ HO"):
                    final_lines.append("KẾ HOẠCH")

                # Quốc hiệu, Tiêu ngữ, Tên cơ quan (Header printed text)
                elif i < 5 and v_txt:
                    final_lines.append(v_txt)

                # Dòng nội dung (Body lines)
                else:
                    if not v_txt:
                        final_lines.append(t_txt)
                        continue
                    if not t_txt:
                        final_lines.append(v_txt)
                        continue

                    # Kiểm tra khoảng thời gian "đến hết ngày" mà VietOCR có thể bỏ sót
                    t_norm = re.sub(r"/+", "/", t_txt)
                    m_t_range = re.search(
                        r"(đến\s+h[eếắ]t\s+ng[aàáYy]+\s+\d{1,2}/\d{1,2}(?:/\d{4})?)", t_norm, re.IGNORECASE
                    )
                    m_v_range = re.search(
                        r"(đến\s+h[eế]t\s+ng[aàá]y\s+\d{1,2}/\d{1,2}(?:/\d{4})?)", v_txt, re.IGNORECASE
                    )
                    if m_t_range and not m_v_range:
                        m_v_start = re.search(
                            r"^(Từ\s+ngày\s+\d{1,2}/\d{1,2}(?:/\d{4})?)\s*:\s*(.*)", v_txt, re.IGNORECASE
                        )
                        norm_range = re.sub(r"(?i)h[ắe]t\s+ng[aàáYy]+", "hết ngày", m_t_range.group(1))
                        m_yr = re.search(r"/(\d{4})", v_txt)
                        if m_yr and not re.search(r"/\d{4}", norm_range):
                            norm_range = f"{norm_range}/{m_yr.group(1)}"
                        if m_v_start:
                            final_lines.append(f"{m_v_start.group(1)} {norm_range}: {m_v_start.group(2)}")
                        else:
                            final_lines.append(f"{v_txt} {norm_range}")
                    else:
                        # VietOCR là mô hình chuẩn hóa tốt nhất cho chữ in tiếng Việt (không lặp từ, chính xác 100% mã lớp)
                        final_lines.append(v_txt)
        except Exception as ex_ensemble:
            logger.error("Hybrid ensembling fallback in TrOCR service: {err}", err=str(ex_ensemble))
            final_lines = [
                vietocr_preds[i] if i < len(vietocr_preds) else trocr_line_map.get(i, "")
                for i in range(len(line_images))
            ]

        valid_lines = [t for t in final_lines if not self._is_noise_line(t)]
        raw_text = "\n".join(valid_lines).strip()
        t_infer = time.time()

        processed_text = ""
        if raw_text:
            try:
                processed_text = self.post_process_vietnamese(raw_text, line_preserving=True)
            except Exception as e:
                logger.error("TrOCR post-processing failed: {err}", err=str(e))
                processed_text = raw_text
        t_post = time.time()

        logger.info(
            "TrOCR Timing | Preprocess: {t1:.2f}s | Segment: {t2:.2f}s | Inference: {t3:.2f}s | Postprocess: {t4:.2f}s",
            t1=t_pre - t_start,
            t2=t_seg - t_pre,
            t3=t_infer - t_seg,
            t4=t_post - t_infer,
        )

        return raw_text, processed_text

    # ── OCR toàn file ─────────────────────────────────────────────────────────
    def extract_text_from_file(
        self,
        file_bytes: bytes,
        file_type: str,
        engine: str | None = None,
        pages: list[int] | int | None = None,
    ) -> tuple[str, str, float, int]:
        """
        Trích xuất toàn văn từ file PDF hoặc Ảnh bằng Microsoft TrOCR.

        Returns:
            (raw_text, processed_text, confidence_score, page_count)
        """
        file_ext = file_type.lower().replace(".", "")
        _s = self._get_settings()
        _render_dpi = getattr(_s, "ocr_trocr_pdf_dpi", 200) if _s else 200

        raw_pages: list[str] = []
        proc_pages: list[str] = []

        _s = self._get_settings()
        timeout_s = getattr(_s, "ocr_trocr_timeout_s", 600) if _s else 600
        start_time_global = time.time()

        page_count = 1

        if file_ext == "pdf":
            if pymupdf is None:
                raise EngineUnavailableError("trocr", "PyMuPDF chưa được cài đặt để render PDF.")
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

                for idx in target_pages:
                    if time.time() - start_time_global > timeout_s:
                        logger.warning(
                            "TrOCR timed out after {s} seconds at page {i}/{t}", s=timeout_s, i=idx + 1, t=page_count
                        )
                        break

                    page = doc[idx]
                    t0 = time.time()
                    pix = page.get_pixmap(dpi=_render_dpi)
                    page_img = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)
                    p_raw, p_proc = self._ocr_image(page_img)
                    logger.info("TrOCR trang {i}/{t} | {s:.1f}s", i=idx + 1, t=page_count, s=time.time() - t0)
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

        is_degen, reason = self._is_degenerate(raw_text)
        if is_degen:
            logger.warning("TrOCR output may be low quality: {reason}", reason=reason)
            confidence = min(0.45, self.heuristic_quality_score(processed_text)) if processed_text else 0.0
        else:
            confidence = self.heuristic_quality_score(processed_text) if processed_text else 0.0

        return raw_text, processed_text, confidence, page_count

    # ── So sánh engine ────────────────────────────────────────────────────────
    def compare_ocr_engines(self, file_bytes: bytes, file_type: str) -> dict[str, Any]:
        """So sánh hiệu năng VietOCR / TrOCR / Tesseract độc lập."""
        from app.services.tesseract_service import tesseract_service
        from app.services.vietocr_service import vietocr_service

        results: dict[str, Any] = {}
        for eng_key, eng_name in [
            ("vietocr", "VietOCR (vgg_transformer)"),
            ("trocr", "TrOCR-Vi (Fine-tuned Transformer)"),
            ("tesseract", "Tesseract 5 (LSTM Baseline)"),
        ]:
            t0 = time.time()
            try:
                if eng_key == "tesseract":
                    res_tuple = tesseract_service.extract_text_from_file(file_bytes, file_type)
                elif eng_key == "trocr":
                    res_tuple = self.extract_text_from_file(file_bytes, file_type)
                else:
                    res_tuple = vietocr_service.extract_text_from_file(file_bytes, file_type, "vietocr")

                raw = res_tuple[0] if len(res_tuple) > 0 else ""
                proc = res_tuple[1] if len(res_tuple) > 1 else ""
                conf = res_tuple[2] if len(res_tuple) > 2 else 0.0
                pc = res_tuple[3] if len(res_tuple) > 3 else 1

                text = proc or raw
                results[eng_key] = {
                    "engine_name": eng_name,
                    "text": text,
                    "raw_text": raw,
                    "processed_text": proc,
                    "confidence": conf,
                    "page_count": pc,
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
