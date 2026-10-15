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
        import torch
        _s = self._get_settings()
        model_name = getattr(_s, "trocr_model_name", "microsoft/trocr-base-printed") if _s else "microsoft/trocr-base-printed"
        req_device = getattr(_s, "trocr_device", "cuda")                                if _s else "cuda"

        device = "cpu"
        if req_device in ("cuda", "auto"):
            if torch.cuda.is_available():
                device = "cuda"
            else:
                logger.warning("CUDA không khả dụng trên hệ thống, tự động fallback sang CPU cho TrOCR")

        # Nếu model đã được load nhưng đang ở thiết bị khác, tự động migrate sang device mới
        if self._model is not None and self._image_processor is not None and self._tokenizer is not None:
            if self._device != device or str(self._model.device) != device:
                logger.info("Migrating TrOCR model from {old} to {new}...", old=self._device, new=device)
                self._model = self._model.to(device)
                self._device = device
            return self._image_processor, self._tokenizer, self._model

        if self._model is None or self._image_processor is None or self._tokenizer is None:
            try:
                from transformers import VisionEncoderDecoderModel, ViTImageProcessor, AutoTokenizer, RobertaTokenizer

                self._device = device

                if not os.path.exists(model_name) and not model_name.startswith("microsoft/"):
                    repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
                    cand = os.path.join(repo_root, model_name.lstrip("./\\"))
                    if os.path.exists(cand):
                        model_name = cand

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
                if hasattr(self._model, "generation_config") and self._model.generation_config is not None:
                    self._model.generation_config.max_length = None
                self._model.eval()
                self._init_error = None
                logger.info("Initialized Microsoft TrOCR Vision Transformer successfully")
            except Exception as exc:
                self._init_error = str(exc)
                logger.warning("TrOCR model initialization failed: {err}", err=str(exc))
                self._image_processor = None
                self._tokenizer = None
                self._model = None
                self._device = None
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
            device = self._device or ("cuda" if torch.cuda.is_available() else "cpu")

            rgb_images = [img.convert("RGB") if img.mode != "RGB" else img for img in images]
            pixel_values = image_processor(images=rgb_images, return_tensors="pt").pixel_values.to(device)

            with torch.inference_mode():
                generated_ids = model.generate(
                    pixel_values, 
                    max_new_tokens=64,
                    num_beams=2,
                    early_stopping=True,
                    do_sample=False
                )

            generated_texts = tokenizer.batch_decode(generated_ids, skip_special_tokens=True)
            cleaned_texts = []
            for t in generated_texts:
                s = str(t).strip()
                # Repair broken multi-byte BPE token decodings (\ufffd)
                s = re.sub(r'(?i)\bh\ufffd\b', 'hệ', s)
                s = re.sub(r'(?i)\bc\ufffda\b', 'của', s)
                s = re.sub(r'(?i)\bs\ufffd\b', 'số', s)
                s = re.sub(r'(?i)\bL\ufffd\b', 'Lễ', s)
                s = re.sub(r'(?i)TH\ufffdC\b', 'THỨC', s)
                s = re.sub(r'(?i)\bt\ufffdp\b', 'tập', s)
                s = re.sub(r'(?i)\bs\ufffdng\b', 'sáng', s)
                s = re.sub(r'(?i)\bnh\ufffdp\b', 'nhập', s)
                s = s.replace('\ufffd', '')
                cleaned_texts.append(s)
            return cleaned_texts

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
        OCR danh sách ảnh dòng bằng TrOCR (batch predict trực tiếp, không cắt nhỏ chunk).
        """
        if not line_images:
            return []

        _s = self._get_settings()
        _max_lines  = getattr(_s, "trocr_max_lines_per_page", 60) if _s else 60
        _batch_size = getattr(_s, "trocr_batch_size", 4)         if _s else 4

        imgs = line_images[:_max_lines] if _max_lines > 0 else line_images
        cleaned = [preprocess_fn(li) if preprocess_fn else li for li in imgs]
        total_lines = len(cleaned)
        line_results: list[tuple[str, float]] = []

        logger.info("[TrOCR] Bắt đầu nhận diện {total} dòng văn bản...", total=total_lines)

        for i in range(0, total_lines, _batch_size):
            batch = cleaned[i: i + _batch_size]
            preds = self.predict_batch(batch)
            for txt in preds:
                txt = txt.strip()
                if txt:
                    bad = len(re.findall(r'[%~^|<>{}\[\]\\]', txt))
                    conf = max(0.60, 0.95 - (bad / max(len(txt), 1)) * 3)
                    line_results.append((txt, round(conf, 2)))

        return line_results


# Singleton
trocr_engine = TrOCREngine()
