"""
backend/app/services/trocr_engine.py — Microsoft TrOCR Engine

Chịu trách nhiệm:
  - Load TrOCRProcessor + VisionEncoderDecoderModel (lazy load)
  - Batch predict danh sách ảnh dòng
  - Báo lỗi rõ ràng (EngineUnavailableError) khi không khả dụng, TUYỆT ĐỐI KHÔNG FALLBACK sang VietOCR.

Mọi ngưỡng số đọc từ app.core.config.settings.
"""
from __future__ import annotations

import re

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
        if self._model is None or self._image_processor is None or self._tokenizer is None:
            try:
                import torch
                from transformers import VisionEncoderDecoderModel, ViTImageProcessor, AutoTokenizer, RobertaTokenizer

                _s = self._get_settings()
                model_name = getattr(_s, "trocr_model_name", "microsoft/trocr-base-printed") if _s else "microsoft/trocr-base-printed"
                device     = getattr(_s, "trocr_device", "cpu")                                if _s else "cpu"

                logger.info("Initializing Microsoft TrOCR ({model}) on {device}...",
                            model=model_name, device=device)
                self._image_processor = ViTImageProcessor.from_pretrained(model_name)
                
                try:
                    self._tokenizer = AutoTokenizer.from_pretrained(model_name)
                except Exception:
                    self._tokenizer = RobertaTokenizer.from_pretrained(model_name)
                self._model = (
                    VisionEncoderDecoderModel.from_pretrained(model_name).to(device)
                )
                self._model.eval()
                if device == "cpu":
                    self._model = torch.quantization.quantize_dynamic(
                        self._model, {torch.nn.Linear}, dtype=torch.qint8
                    )
                self._init_error = None
                logger.info("Initialized Microsoft TrOCR Vision Transformer successfully")
            except Exception as exc:
                self._init_error = str(exc)
                logger.warning("TrOCR model initialization failed: {err}", err=str(exc))
                self._image_processor = None
                self._tokenizer = None
                self._model = None
                raise EngineUnavailableError(
                    "trocr",
                    f"Không thể khởi tạo mô hình Microsoft TrOCR: {exc}"
                ) from exc

        return self._image_processor, self._tokenizer, self._model

    # ── Batch Predict ─────────────────────────────────────────────────────────
    def predict_batch(self, images: list[Image.Image]) -> list[str]:
        """
        Predict batch ảnh dòng bằng TrOCR.
        Không bao giờ fallback sang VietOCR.
        """
        if not images:
            return []

        image_processor, tokenizer, model = self.get_model()

        if image_processor is None or tokenizer is None or model is None:
            raise EngineUnavailableError("trocr", f"TrOCR chưa được khởi tạo: {self._init_error}")

        try:
            import torch
            _s = self._get_settings()
            device = getattr(_s, "trocr_device", "cpu") if _s else "cpu"

            rgb_images = [img.convert("RGB") if img.mode != "RGB" else img for img in images]
            pixel_values = image_processor(images=rgb_images, return_tensors="pt").pixel_values.to(device)

            with torch.inference_mode():
                # Scale max_new_tokens to crop width if possible, but here we just use a safe upper bound
                # since we already chunked the images to 3:1 aspect ratio.
                generated_ids = model.generate(
                    pixel_values, 
                    max_new_tokens=40,
                    no_repeat_ngram_size=3,
                    repetition_penalty=1.2,
                    num_beams=1,
                    do_sample=False
                )

            generated_texts = tokenizer.batch_decode(generated_ids, skip_special_tokens=True)
            return [str(t).strip() for t in generated_texts]

        except Exception as exc:
            if isinstance(exc, EngineUnavailableError):
                raise
            logger.error("TrOCR batch prediction error: {err}", err=str(exc))
            raise EngineUnavailableError("trocr", f"Lỗi suy luận TrOCR: {exc}") from exc

    # ── Line OCR ──────────────────────────────────────────────────────────────
    def _chunk_and_pad(self, img: Image.Image) -> list[Image.Image]:
        """Chunk long lines and pad with white."""
        from app.services.trocr_vi_utils import pad_image_to_square
        import numpy as np

        w, h = img.size
        if h <= 0 or w <= 0:
            return []

        # If aspect ratio <= 3.5, pad directly to square
        if w <= int(h * 3.5):
            return [pad_image_to_square(img, target_size=384)]

        # If long line, split into segments of max width ~3.5*h at whitespace columns
        target_chunk_w = max(1, int(h * 3.5))
        gray = np.array(img.convert("L"))
        chunks = []
        curr_x = 0

        while curr_x < w:
            end_x = min(w, curr_x + target_chunk_w)
            if end_x >= w:
                chunks.append(img.crop((curr_x, 0, w, h)))
                break

            # Search for the whitest column (inter-word gap) in [end_x - 0.25*target, end_x + 0.15*target]
            search_start = max(curr_x + int(h * 1.5), end_x - int(target_chunk_w * 0.25))
            search_end = min(w - 1, end_x + int(target_chunk_w * 0.15))

            best_split = end_x
            if search_end > search_start:
                window = gray[:, search_start:search_end]
                col_means = window.mean(axis=0)
                best_split = search_start + int(np.argmax(col_means))

            chunks.append(img.crop((curr_x, 0, best_split, h)))
            curr_x = best_split

        if not chunks:
            chunks = [img]

        return [pad_image_to_square(c_img, target_size=384) for c_img in chunks]

    def ocr_lines(
        self,
        line_images: list[Image.Image],
        preprocess_fn=None,
    ) -> list[tuple[str, float]]:
        """
        OCR danh sách ảnh dòng bằng TrOCR.
        """
        if not line_images:
            return []

        _s = self._get_settings()
        _max_lines  = getattr(_s, "trocr_max_lines_per_page", 60) if _s else 60
        _batch_size = getattr(_s, "trocr_batch_size", 8)         if _s else 8

        imgs = line_images[:_max_lines] if _max_lines > 0 else line_images
        cleaned = [preprocess_fn(li) if preprocess_fn else li for li in imgs]
        total_lines = len(cleaned)
        line_results: list[tuple[str, float]] = []

        # Process line by line to handle chunks properly
        for i, line_img in enumerate(cleaned):
            logger.info("[TrOCR] Đang xử lý dòng {start}/{total}...",
                        start=i + 1, total=total_lines)
            chunks = self._chunk_and_pad(line_img)
            
            chunk_texts = []
            for j in range(0, len(chunks), _batch_size):
                batch = chunks[j: j + _batch_size]
                chunk_texts.extend(self.predict_batch(batch))
                
            txt = " ".join([t for t in chunk_texts if t]).strip()
            if txt:
                bad  = len(re.findall(r'[%~^|<>{}\[\]\\]', txt))
                conf = max(0.60, 0.95 - (bad / max(len(txt), 1)) * 3)
                line_results.append((txt, round(conf, 2)))

        return line_results


# Singleton
trocr_engine = TrOCREngine()
