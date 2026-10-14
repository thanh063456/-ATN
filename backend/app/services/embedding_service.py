"""
backend/app/services/embedding_service.py — Text Embedding Service for Hybrid Search

Cung cấp vector nhúng 768 chiều cho tài liệu và truy vấn tìm kiếm:
1. Thử nghiệm sinh vector qua Google Gemini text-embedding-004 (hoặc OpenAI text-embedding-3-small) nếu có API key.
2. Fallback sang Term-Hashing n-gram vectorizer chuẩn hóa L2 (chạy offline 100% không cần Internet).
"""
import hashlib
import math
import re
from typing import Any
import httpx
try:
    from loguru import logger
except ImportError:
    import logging
    logger = logging.getLogger("embedding_service")
logger: Any = logger

from app.core.config import settings

EMBEDDING_DIM = 768


class EmbeddingService:
    """Service sinh vector 768 chiều phục vụ kNN Vector & Hybrid Search trên Elasticsearch 8."""

    def __init__(self) -> None:
        self.dim = EMBEDDING_DIM

    async def get_embedding(self, text: str) -> list[float]:
        """Sinh vector nhúng 768 chiều cho đoạn văn bản."""
        if not text or not text.strip():
            return [0.0] * self.dim

        clean_text = text.strip()[:2000]

        # 1. Thử nghiệm gọi Gemini Embedding API nếu có key
        if settings.gemini_api_key:
            try:
                url = f"https://generativelanguage.googleapis.com/v1beta/models/text-embedding-004:embedContent?key={settings.gemini_api_key}"
                payload = {
                    "model": "models/text-embedding-004",
                    "content": {"parts": [{"text": clean_text}]},
                }
                async with httpx.AsyncClient(timeout=5.0) as client:
                    resp = await client.post(url, json=payload)
                if resp.status_code == 200:
                    vec = resp.json().get("embedding", {}).get("values", [])
                    if len(vec) == self.dim:
                        return vec
            except Exception as exc:
                logger.debug(f"Gemini embedding fallback to local vectorizer: {exc}")

        # 2. Local Deterministic Feature Hashing Vectorizer (Chạy offline, cực nhanh, không phụ thuộc mạng)
        return self._generate_local_vector(clean_text)

    def _generate_local_vector(self, text: str) -> list[float]:
        """Tạo vector ngữ nghĩa 768 chiều dựa trên feature hashing và n-grams tiếng Việt."""
        vec = [0.0] * self.dim
        words = re.findall(r"\w+", text.lower())

        if not words:
            return vec

        # Chiếu các từ và bi-grams vào không gian 768 chiều
        tokens = list(words)
        for i in range(len(words) - 1):
            tokens.append(f"{words[i]}_{words[i+1]}")

        for tok in tokens:
            h = int(hashlib.md5(tok.encode("utf-8")).hexdigest(), 16)
            idx = h % self.dim
            sign = 1.0 if ((h >> 16) % 2 == 0) else -1.0
            vec[idx] += sign

        # Chuẩn hóa L2 Norm (Unit vector) để tối ưu Cosine Similarity
        norm = math.sqrt(sum(x * x for x in vec))
        if norm > 0:
            vec = [round(x / norm, 6) for x in vec]

        return vec


embedding_service = EmbeddingService()
