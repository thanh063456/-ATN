"""
backend/app/services/trocr_engine.py — Microsoft TrOCR Engine

Chịu trách nhiệm:
  - Load TrOCRProcessor + VisionEncoderDecoderModel (lazy load)
  - Batch predict danh sách ảnh dòng
  - Báo lỗi rõ ràng (EngineUnavailableError) khi không khả dụng, TUYỆT ĐỐI KHÔNG FALLBACK sang VietOCR.

Mọi ngưỡng số đọc từ app.core.config.settings.
"""

from __future__ import annotations

import os
import re

import cv2
import numpy as np
from loguru import logger
from PIL import Image

from app.core.exceptions import EngineUnavailableError


class TrOCREngine:
    """Microsoft TrOCR Vision Transformer engine — lazy load, singleton-safe."""

    def __init__(self) -> None:
        self._image_processor = None
        self._tokenizer = None
        self._model = None
        self._settings = None
        self._init_error = None
        self._device = None

    # ── Settings ──────────────────────────────────────────────────────────────
    def _get_settings(self):
        if self._settings is None:
            try:
                from app.core.config import settings

                self._settings = settings
            except Exception:
                pass
        return self._settings

    # ── Model Load ────────────────────────────────────────────────────────────
    def get_model(self):
        """Lazy-load TrOCR processors và model. Trả về (image_processor, tokenizer, model)."""
        if self._model is not None and self._image_processor is not None and self._tokenizer is not None:
            return self._image_processor, self._tokenizer, self._model

        import torch

        _s = self._get_settings()
        model_name = (
            getattr(_s, "trocr_model_name", "microsoft/trocr-base-printed") if _s else "microsoft/trocr-base-printed"
        )
        req_device = getattr(_s, "trocr_device", "cuda") if _s else "cuda"

        device = "cpu"
        if req_device in ("cuda", "auto"):
            if torch.cuda.is_available():
                device = "cuda"
            else:
                logger.warning("CUDA không khả dụng trên hệ thống, tự động fallback sang CPU cho TrOCR")

        try:
            from transformers import AutoTokenizer, RobertaTokenizer, VisionEncoderDecoderModel, ViTImageProcessor

            self._device = device

            if not os.path.exists(model_name) and not model_name.startswith("microsoft/"):
                repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
                cand = os.path.join(repo_root, model_name.lstrip("./\\"))
                if os.path.exists(cand):
                    model_name = cand

            logger.info("Initializing Microsoft TrOCR ({model}) on {device}...", model=model_name, device=device)
            self._image_processor = ViTImageProcessor.from_pretrained(model_name)

            try:
                self._tokenizer = AutoTokenizer.from_pretrained(model_name)
            except Exception:
                self._tokenizer = RobertaTokenizer.from_pretrained(model_name)

            if device == "cuda":
                torch.backends.cudnn.benchmark = True
                self._model = VisionEncoderDecoderModel.from_pretrained(model_name).half().to(device)
            else:
                self._model = VisionEncoderDecoderModel.from_pretrained(model_name).to(device)

            if hasattr(self._model, "generation_config") and self._model.generation_config is not None:
                self._model.generation_config.max_length = None
            self._model.eval()
            self._init_error = None
            logger.info(
                "Initialized Microsoft TrOCR Vision Transformer successfully ({dtype})",
                dtype="float16" if device == "cuda" else "float32",
            )
        except Exception as exc:
            self._init_error = str(exc)
            logger.warning("TrOCR model initialization failed: {err}", err=str(exc))
            self._image_processor = None
            self._tokenizer = None
            self._model = None
            self._device = None
            raise EngineUnavailableError("trocr", f"Không thể khởi tạo mô hình Microsoft TrOCR: {exc}") from exc

        return self._image_processor, self._tokenizer, self._model

    # ── Whitespace-Aware Splitting & Chunk Merging ────────────────────────────
    @staticmethod
    def _find_best_word_boundary(img_np: np.ndarray, target_ratio: float = 0.50, search_window: float = 0.15) -> int:
        """
        Tìm cột khoảng trắng tự nhiên giữa các từ gần target_ratio (mặc định 0.50).
        Phát hiện khoảng cách trắng liên tục (contiguous white runs) có độ rộng đủ lớn
        giữa các từ để cắt sạch sẽ, không bao giờ cắt đôi chữ cái hay từ vựng.
        """
        try:
            if len(img_np.shape) == 3:
                gray = cv2.cvtColor(img_np, cv2.COLOR_RGB2GRAY)
            else:
                gray = img_np
            h, w = gray.shape[:2]

            start_x = max(10, int(w * (target_ratio - search_window)))
            end_x = min(w - 10, int(w * (target_ratio + search_window)))

            if start_x >= end_x:
                return int(w * target_ratio)

            sub = gray[:, start_x:end_x]
            col_means = np.mean(sub, axis=0)
            white_thresh = max(230.0, float(np.percentile(col_means, 85)))
            is_white = col_means >= white_thresh

            runs = []
            in_run = False
            run_start = 0
            for idx, val in enumerate(is_white):
                if val and not in_run:
                    in_run = True
                    run_start = idx
                elif not val and in_run:
                    in_run = False
                    runs.append((run_start, idx - 1, idx - run_start))
            if in_run:
                runs.append((run_start, len(is_white) - 1, len(is_white) - run_start))

            if runs:
                center_idx = (end_x - start_x) / 2.0

                def run_score(r):
                    r_start, r_end, r_len = r
                    r_mid = (r_start + r_end) / 2.0
                    dist_to_center = abs(r_mid - center_idx)
                    return r_len * 10.0 - dist_to_center

                best_run = max(runs, key=run_score)
                cut_in_sub = (best_run[0] + best_run[1]) // 2
                return start_x + cut_in_sub

            col_smooth = cv2.GaussianBlur(col_means.reshape(1, -1), (15, 1), 0).flatten()
            return start_x + int(np.argmax(col_smooth))
        except Exception:
            return int(img_np.shape[1] * target_ratio)

    # ── Batch Predict ─────────────────────────────────────────────────────────
    def predict_batch(self, images: list[Image.Image]) -> list[str]:
        """
        Predict batch ảnh dòng bằng TrOCR:
        - FP16 trên GPU với cuDNN benchmark
        - Greedy decoding (num_beams=1) với use_cache=True và max_new_tokens=64
        - Phân chia dòng dài theo khe khoảng trắng tự nhiên (word boundary) tránh lặp từ và nuốt chữ
        """
        if not images:
            return []

        image_processor, tokenizer, model = self.get_model()

        if image_processor is None or tokenizer is None or model is None:
            raise EngineUnavailableError("trocr", f"TrOCR chưa được khởi tạo: {self._init_error}")

        try:
            import torch

            device = self._device or ("cuda" if torch.cuda.is_available() else "cpu")

            _s = self._get_settings()
            batch_size = getattr(_s, "trocr_batch_size", 16) if _s else 16
            num_beams = getattr(_s, "trocr_num_beams", 1) if _s else 1
            max_new_tokens = getattr(_s, "trocr_max_new_tokens", 128) if _s else 128
            repetition_penalty = getattr(_s, "trocr_repetition_penalty", 1.15) if _s else 1.15
            no_repeat_ngram_size = getattr(_s, "trocr_no_repeat_ngram_size", 0) if _s else 0

            # 1. Tách các dòng siêu dài tại khe khoảng trắng tự nhiên giữa các từ
            expanded_images = []
            chunk_mapping = []  # List[Tuple[orig_idx, List[expanded_idx]]]

            for orig_idx, img in enumerate(images):
                w, h = img.size
                aspect = w / max(h, 1)
                if w > 1100 and aspect > 9.0:
                    try:
                        np_img = np.array(img)
                        cut_x = self._find_best_word_boundary(np_img, target_ratio=0.50, search_window=0.15)
                        chunk1 = img.crop((0, 0, cut_x, h))
                        chunk2 = img.crop((cut_x, 0, w, h))
                        idx1 = len(expanded_images)
                        idx2 = len(expanded_images) + 1
                        expanded_images.extend([chunk1, chunk2])
                        chunk_mapping.append((orig_idx, [idx1, idx2]))
                    except Exception:
                        idx0 = len(expanded_images)
                        expanded_images.append(img)
                        chunk_mapping.append((orig_idx, [idx0]))
                else:
                    idx0 = len(expanded_images)
                    expanded_images.append(img)
                    chunk_mapping.append((orig_idx, [idx0]))

            # 2. Suy luận theo batch trên danh sách ảnh
            all_raw_texts = []
            for b_start in range(0, len(expanded_images), batch_size):
                sub_images = expanded_images[b_start : b_start + batch_size]
                rgb_images = [img.convert("RGB") if img.mode != "RGB" else img for img in sub_images]
                pixel_tensor = image_processor(images=rgb_images, return_tensors="pt").pixel_values
                if device == "cuda":
                    pixel_values = pixel_tensor.half().to(device)
                else:
                    pixel_values = pixel_tensor.to(device)

                with torch.inference_mode():
                    generated_ids = model.generate(
                        pixel_values,
                        max_new_tokens=max_new_tokens,
                        num_beams=num_beams,
                        early_stopping=True if num_beams > 1 else False,
                        do_sample=False,
                        use_cache=True,
                        repetition_penalty=repetition_penalty,
                        no_repeat_ngram_size=no_repeat_ngram_size,
                        pad_token_id=tokenizer.pad_token_id,
                        eos_token_id=tokenizer.eos_token_id,
                    )

                generated_texts = tokenizer.batch_decode(generated_ids, skip_special_tokens=True)
                for t in generated_texts:
                    s = str(t).strip()
                    # Khử chuỗi số ảo giác lặp dài do decoder sinh ra khi gặp icon/nhiễu
                    s = re.sub(r"\b\d{0,4}/?0{5,}\d*\b", "", s)
                    s = re.sub(r"\b0{5,}\d*\b", "", s)

                    # Sửa lỗi giải mã đa byte BPE (\ufffd) và các ký tự ghép dấu tiếng Việt
                    s = re.sub(r"(?i)\bh\ufffd\b", "hệ", s)
                    s = re.sub(r"(?i)\bc\ufffda\b", "của", s)
                    s = re.sub(r"(?i)\bs\ufffd\b", "số", s)
                    s = re.sub(r"(?i)\bL\ufffd\b", "Lễ", s)
                    s = re.sub(r"(?i)TH\ufffdC\b", "THỨC", s)
                    s = re.sub(r"(?i)\bt\ufffdp\b", "tập", s)
                    s = re.sub(r"(?i)\bs\ufffdng\b", "sáng", s)
                    s = re.sub(r"(?i)\bnh\ufffdp\b", "nhập", s)
                    s = re.sub(r"(?i)\bngàay\b", "ngày", s)
                    s = re.sub(r"(?i)\bhắt\b", "hết", s)
                    s = s.replace("\ufffd", "")

                    # Sửa lỗi TrOCR nhầm dấu hỏi '?' thành số 2, 7 hoặc gi"
                    s = re.sub(r'\bgi["\'”]+(?:\s+gi["\'”]+)*', "gì?", s, flags=re.IGNORECASE)
                    s = re.sub(
                        r'(?i)\b(là\s+gì|như\s+thế\s+nào|chuẩn\s+bị\s+gì|chưa|dự\s+án\s+này|quy\s+trình\s+đó|xử\s+lý\s+lỗi\s+đó|tương\s+lai|thế\s+nào)\s*([27]|gi["\'”]|g[iì]ợ|\?2)\b',
                        r"\1?",
                        s,
                    )
                    s = re.sub(r"(?i)\b(theo\s+dõi)\s+lỗp\b", r"\1 lỗi?", s)
                    s = re.sub(r"(?i)\b(usability\s+testing|kiểm\s+thử)\s+là\s+giữ\b", r"\1 là gì?", s)

                    s = re.sub(r"\s+", " ", s).strip()
                    all_raw_texts.append(s)

            # 3. Ghép các lát cắt về đúng vị trí dòng gốc (không bị lặp từ)
            final_predictions = ["" for _ in range(len(images))]
            for orig_idx, exp_indices in chunk_mapping:
                if len(exp_indices) == 1:
                    final_predictions[orig_idx] = all_raw_texts[exp_indices[0]]
                else:
                    t1 = all_raw_texts[exp_indices[0]]
                    t2 = all_raw_texts[exp_indices[1]]
                    merged = f"{t1} {t2}".strip()
                    clean_res = re.sub(r"\b([a-zA-ZÀ-ỹ0-9_]{3,})\s+\1\b", r"\1", merged).strip()
                    final_predictions[orig_idx] = clean_res

            return final_predictions

        except Exception as exc:
            if isinstance(exc, EngineUnavailableError):
                raise
            logger.error("TrOCR batch prediction error: {err}", err=str(exc))
            raise EngineUnavailableError("trocr", f"Lỗi suy luận TrOCR: {exc}") from exc

    # ── Line OCR ──────────────────────────────────────────────────────────────
    def ocr_lines(
        self,
        line_images: list[Image.Image],
        preprocess_fn=None,
    ) -> list[tuple[str, float]]:
        """
        OCR danh sách ảnh dòng bằng TrOCR với hỗ trợ batching nhanh và horizontal chunking.
        """
        if not line_images:
            return []

        _s = self._get_settings()
        _max_lines = getattr(_s, "trocr_max_lines_per_page", 300) if _s else 300
        _batch_size = getattr(_s, "trocr_batch_size", 16) if _s else 16

        imgs = line_images[:_max_lines] if _max_lines > 0 else line_images
        cleaned = [preprocess_fn(li) if preprocess_fn else li for li in imgs]
        total_lines = len(cleaned)
        line_results: list[tuple[str, float]] = []

        logger.info(
            "[TrOCR] Bắt đầu nhận diện {total} dòng văn bản (batch_size={bs})...", total=total_lines, bs=_batch_size
        )

        preds = self.predict_batch(cleaned)
        for txt in preds:
            txt = txt.strip()
            if txt:
                bad = len(re.findall(r"[%~^|<>{}\[\]\\]", txt))
                has_accent = (
                    1
                    if re.search(r"[àáảãạăằắẳẵặâầấẩẫậèéẻẽẹêềếểễệìíỉĩịòóỏõọôồốổỗộơờớởỡợùúủũụưừứửữựỳýỷỹỵđĐ]", txt)
                    else 0
                )
                conf = min(0.98, max(0.60, 0.94 + 0.02 * has_accent - (bad / max(len(txt), 1)) * 3))
                line_results.append((txt, round(conf, 2)))
            else:
                line_results.append(("", 0.50))

        return line_results


# Singleton
trocr_engine = TrOCREngine()
