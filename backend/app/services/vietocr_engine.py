"""
backend/app/services/vietocr_engine.py — VietOCR Engine (vgg_transformer)

Chịu trách nhiệm:
  - Load VietOCR Predictor (lazy, thread-safe)
  - Padded Batch Predict (tối ưu throughput CPU gấp 3-5x)
  - OCR từng dòng ảnh với line_results trả về list[(text, confidence)]

Mọi ngưỡng số đọc từ app.core.config.settings.
"""
import glob
import os
import re

from loguru import logger
from PIL import Image


class VietOCREngine:
    """VietOCR vgg_transformer Seq2Seq engine — lazy load, singleton-safe."""

    def __init__(self) -> None:
        self._predictor = None
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
    def get_predictor(self):
        """Lazy-load VietOCR predictor. Tìm fine-tuned weights nếu có."""
        if self._predictor is not None:
            return self._predictor

        orig_requests_get = None
        try:
            import urllib3
            urllib3.disable_warnings()
            import requests
            from vietocr.tool import utils as vocr_utils

            orig_requests_get = requests.get

            def _scoped_get(*args, **kwargs):
                kwargs["verify"] = False
                return orig_requests_get(*args, **kwargs)

            vocr_utils.requests.get = _scoped_get

            import torch
            torch.set_num_threads(min(8, os.cpu_count() or 4))

            from vietocr.tool.config import Cfg
            from vietocr.tool.predictor import Predictor

            config = Cfg.load_config_from_name("vgg_transformer")

            _s = self._get_settings()
            _device     = getattr(_s, "ocr_device", "cpu")           if _s else "cpu"
            _beamsearch = getattr(_s, "ocr_beamsearch_enabled", False) if _s else False
            _beam_size  = getattr(_s, "ocr_beam_size", 4)             if _s else 4
            _fast_mode  = getattr(_s, "ocr_fast_mode", False)         if _s else False

            if _fast_mode:
                _beamsearch = False

            config["device"] = _device
            config["predictor"]["beamsearch"] = _beamsearch
            if _beamsearch:
                config["predictor"]["beam_size"] = _beam_size
                logger.info("VietOCR beamsearch=True beam_size={bs}", bs=_beam_size)
            else:
                logger.info("VietOCR beamsearch=False (greedy, faster)")

            # Tìm model fine-tune tốt nhất
            candidate_patterns = [
                "/app/models/*_best.pth",
                "models/*_best.pth",
                "../models/*_best.pth",
                os.path.join(os.path.dirname(__file__), "../../../models/*_best.pth"),
                os.path.join(os.path.dirname(__file__), "../../models/*_best.pth"),
            ]
            custom_models: list[str] = []
            for pat in candidate_patterns:
                custom_models.extend(glob.glob(pat))
            custom_models = sorted(set(custom_models))

            if custom_models:
                best_weights = custom_models[-1]
                logger.info("Loading fine-tuned VietOCR weights: {path}", path=best_weights)
                config["weights"] = best_weights

            self._predictor = Predictor(config)

            # Quantization tùy chọn (INT8 dynamic) — tăng tốc ~1.5x trên CPU không có AVX512
            # Chỉ áp dụng khi ocr_quantize=True (mặc định False để giữ độ chính xác)
            _quantize = getattr(_s, "ocr_quantize", False) if _s else False
            if _quantize:
                try:
                    import torch
                    torch.backends.quantized.engine = "fbgemm"  # tốt cho Intel x86
                    self._predictor.model = torch.quantization.quantize_dynamic(
                        self._predictor.model,
                        {torch.nn.Linear, torch.nn.LSTM},
                        dtype=torch.qint8,
                    )
                    logger.info("VietOCR quantized (INT8 dynamic) — inference nhanh hơn trên CPU")
                except Exception as qe:
                    logger.warning("Quantization thất bại (bỏ qua): {err}", err=str(qe))

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

    # ── Batch Predict ─────────────────────────────────────────────────────────
    def predict_batch_padded(self, images: list[Image.Image]) -> list[str]:
        """
        Pad tất cả ảnh dòng về cùng h=32, w=max_w rồi predict 1 batch duy nhất.
        Tăng throughput CPU gấp 3-5x so với predict từng ảnh đơn lẻ.
        """
        predictor = self.get_predictor()
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
            outs = []
            for img in images:
                try:
                    outs.append(str(predictor.predict(img)).strip())
                except Exception:
                    outs.append("")
            return outs

    # ── Line OCR ─────────────────────────────────────────────────────────────
    def ocr_lines(
        self,
        line_images: list[Image.Image],
        preprocess_fn=None,
    ) -> list[tuple[str, float]]:
        """
        OCR danh sách ảnh dòng bằng VietOCR.

        Tối ưu (Bước 2): Sort-by-width batching — sắp xếp dòng theo chiều rộng
        trước khi batch để giảm overhead padding trong mỗi batch.
        Các dòng có độ rộng gần nhau sẽ cùng batch → max_w nhỏ hơn → nhanh hơn.
        Kết quả được unsort để trả về đúng thứ tự dòng gốc.

        Args:
            line_images: Danh sách ảnh đã segment từ segment_lines().
            preprocess_fn: Hàm tiền xử lý từng dòng (preprocess_handwriting).

        Returns:
            list[(text, confidence)] theo đúng thứ tự dòng gốc.
        """
        predictor = self.get_predictor()
        if not predictor or not line_images:
            return []

        _s = self._get_settings()
        _max_lines  = getattr(_s, "ocr_max_lines_per_page", 300) if _s else 300
        _batch_size = getattr(_s, "ocr_batch_size", 32)          if _s else 32  # 16 -> 32

        imgs = line_images[:_max_lines] if _max_lines > 0 else line_images

        # Tiền xử lý từng dòng
        cleaned: list[Image.Image] = [
            preprocess_fn(li) if preprocess_fn else li for li in imgs
        ]
        total_lines = len(cleaned)

        # Sort-by-width: nhóm dòng có độ rộng gần nhau vào cùng batch
        # Lưu index gốc để unsort sau
        indexed = sorted(enumerate(cleaned), key=lambda iv: iv[1].size[0])
        orig_indices  = [i for i, _ in indexed]
        sorted_images = [img for _, img in indexed]

        # OCR theo batch (sorted by width)
        sorted_texts: dict[int, str] = {}
        for batch_start in range(0, total_lines, _batch_size):
            batch     = sorted_images[batch_start: batch_start + _batch_size]
            batch_idx = orig_indices[batch_start: batch_start + _batch_size]
            logger.info(
                "[VietOCR] Dòng {s}-{e}/{t} (w={wmin}-{wmax}px)",
                s=batch_start + 1,
                e=min(batch_start + _batch_size, total_lines),
                t=total_lines,
                wmin=batch[0].size[0],
                wmax=batch[-1].size[0],
            )
            texts = self.predict_batch_padded(batch)
            for orig_i, txt in zip(batch_idx, texts):
                sorted_texts[orig_i] = str(txt).strip() if txt else ""

        # Tổng hợp kết quả theo đúng thứ tự dòng gốc
        line_results: list[tuple[str, float]] = []
        for i in range(total_lines):
            txt = sorted_texts.get(i, "")
            if txt:
                bad  = len(re.findall(r'[%~^|<>{}\\[\]\\\\]', txt))
                conf = max(0.60, 0.95 - (bad / max(len(txt), 1)) * 3)
                line_results.append((txt, round(conf, 2)))

        return line_results


# Singleton
vietocr_engine = VietOCREngine()
