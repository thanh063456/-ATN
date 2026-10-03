"""
backend/app/services/trocr_engine.py — Microsoft TrOCR Engine

Chịu trách nhiệm:
  - Load TrOCRProcessor + VisionEncoderDecoderModel (lazy load)
  - Batch predict danh sách ảnh dòng
  - Fallback sang VietOCR nếu TrOCR không khả dụng

Mọi ngưỡng số đọc từ app.core.config.settings.
"""
import re

from loguru import logger
from PIL import Image


class TrOCREngine:
    """Microsoft TrOCR Vision Transformer engine — lazy load, singleton-safe."""

    def __init__(self) -> None:
        self._processor = None
        self._model = None
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

    # ── Model Load ────────────────────────────────────────────────────────────
    def get_model(self):
        """Lazy-load TrOCR processor và model. Trả về (processor, model)."""
        if self._model is None or self._processor is None:
            try:
                import torch
                from transformers import TrOCRProcessor, VisionEncoderDecoderModel, ViTImageProcessor, RobertaTokenizer

                _s = self._get_settings()
                # Dùng trocr-base-printed với RobertaTokenizer đầy đủ vocab
                model_name = getattr(_s, "trocr_model_name", "microsoft/trocr-base-printed") if _s else "microsoft/trocr-base-printed"
                device     = getattr(_s, "trocr_device", "cpu")                                if _s else "cpu"

                logger.info("Initializing Microsoft TrOCR ({model}) on {device}...",
                            model=model_name, device=device)
                image_processor = ViTImageProcessor.from_pretrained(model_name)
                tokenizer = RobertaTokenizer.from_pretrained(model_name)
                self._processor = TrOCRProcessor(image_processor=image_processor, tokenizer=tokenizer)
                self._model = (
                    VisionEncoderDecoderModel.from_pretrained(model_name).to(device)
                )
                self._model.eval()
                logger.info("Initialized Microsoft TrOCR Vision Transformer successfully")
            except Exception as exc:
                logger.warning("TrOCR model initialization failed: {err}", err=str(exc))
                self._processor = None
                self._model = None

        return self._processor, self._model

    # ── Batch Predict ─────────────────────────────────────────────────────────
    def predict_batch(self, images: list[Image.Image]) -> list[str]:
        """
        Predict batch ảnh dòng bằng TrOCR.
        """
        if not images:
            return []

        proc, model = self.get_model()

        if proc is None or model is None:
            logger.warning("TrOCR is completely unavailable. Returning empty results.")
            return [""] * len(images)

        try:
            import torch
            _s = self._get_settings()
            device = getattr(_s, "trocr_device", "cpu") if _s else "cpu"

            rgb_images = [img.convert("RGB") if img.mode != "RGB" else img for img in images]
            pixel_values = proc(images=rgb_images, return_tensors="pt").pixel_values.to(device)

            with torch.no_grad():
                generated_ids = model.generate(pixel_values, max_new_tokens=64)

            generated_texts = proc.batch_decode(generated_ids, skip_special_tokens=True)
            return [str(t).strip() for t in generated_texts]

        except Exception as exc:
            logger.warning("TrOCR batch prediction error: {err}", err=str(exc))
            from app.services.vietocr_engine import vietocr_engine
            return vietocr_engine.predict_batch_padded(images)

    # ── Line OCR ──────────────────────────────────────────────────────────────
    def ocr_lines(
        self,
        line_images: list[Image.Image],
        preprocess_fn=None,
    ) -> list[tuple[str, float]]:
        """
        OCR danh sách ảnh dòng bằng TrOCR.

        Args:
            line_images: Danh sách ảnh đã segment từ segment_lines().
            preprocess_fn: Hàm tiền xử lý từng dòng (preprocess_handwriting),
                           nếu None thì bỏ qua.

        Returns:
            list[(text, confidence)] — chỉ trả về dòng có nội dung.
        """
        if not line_images:
            return []

        _s = self._get_settings()
        _max_lines  = getattr(_s, "ocr_max_lines_per_page", 300) if _s else 300
        _batch_size = getattr(_s, "trocr_batch_size", 8)         if _s else 8

        imgs = line_images[:_max_lines] if _max_lines > 0 else line_images
        cleaned = [preprocess_fn(li) if preprocess_fn else li for li in imgs]
        total_lines = len(cleaned)
        line_results: list[tuple[str, float]] = []
        try:
            for i in range(0, total_lines, _batch_size):
                batch = cleaned[i: i + _batch_size]
                logger.info("[TrOCR] Đang xử lý dòng {start}-{end}/{total}...",
                            start=i + 1, end=min(i + _batch_size, total_lines), total=total_lines)
                texts = self.predict_batch(batch)
                for txt in texts:
                    txt = str(txt).strip() if txt else ""
                    if txt:
                        bad  = len(re.findall(r'[%~^|<>{}\\[\]\\\\]', txt))
                        conf = max(0.60, 0.95 - (bad / max(len(txt), 1)) * 3)
                        line_results.append((txt, round(conf, 2)))
        except Exception as e:
            logger.debug("TrOCR line prediction failed: {err}", err=str(e))

        return line_results


# Singleton
trocr_engine = TrOCREngine()
