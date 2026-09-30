"""
backend/app/core/config.py — Application Settings

Đọc toàn bộ biến môi trường từ .env bằng pydantic-settings.
Ref: .env.example, .ai/CODING_RULES.md (không hardcode credentials)
"""
from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


def _find_env_file() -> str:
    """Tìm .env từ thư mục hiện tại hoặc thư mục cha."""
    for p in [Path(".env"), Path("../.env"), Path("../../.env")]:
        if p.exists():
            return str(p)
    return ".env"  # fallback — sẽ dùng env vars từ shell


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=_find_env_file(),
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ── App ──────────────────────────────────────────────────────────────────
    app_name: str = "student-document-ocr"
    app_env: Literal["development", "staging", "production"] = "development"
    app_debug: bool = True
    app_secret_key: str = Field(default="CHANGE_ME_TO_A_RANDOM_SECRET_KEY")
    app_port: int = 8000
    app_host: str = "0.0.0.0"

    # ── Database ──────────────────────────────────────────────────────
    # asyncpg URL — Supabase / PostgreSQL Connection
    database_url: str = Field(
        default="postgresql+asyncpg://postgres:YOUR_PASSWORD@localhost:5432/postgres"
    )
    # psycopg2 URL — Alembic migration (Direct connection)
    alembic_database_url: str = Field(
        default="postgresql+psycopg2://postgres:YOUR_PASSWORD@localhost:5432/postgres"
    )

    # Connection pool
    db_pool_size: int = 5
    db_max_overflow: int = 10
    db_pool_timeout: int = 30

    # ── Supabase ──────────────────────────────────────────────────
    supabase_url: str = Field(default="https://YOUR_PROJECT_REF.supabase.co")
    supabase_anon_key: str = Field(default="")
    supabase_service_key: str = Field(default="")
    supabase_storage_bucket_documents: str = "documents"
    supabase_storage_bucket_thumbnails: str = "thumbnails"

    # ── Elasticsearch ─────────────────────────────────────────────────────────
    es_host: str = "localhost"
    es_port: int = 9200
    es_index_documents: str = "documents"
    es_username: str = "elastic"
    es_password: str = ""

    @property
    def es_url(self) -> str:
        return f"http://{self.es_host}:{self.es_port}"

    # ── MinIO (kept for backward compat reference) ───────────────────
    # Supabase Storage replaces MinIO — these are only kept for fallback
    minio_endpoint: str = "localhost:9000"
    minio_access_key: str = "DISABLED"
    minio_secret_key: str = "DISABLED"
    minio_bucket_documents: str = "documents"
    minio_bucket_thumbnails: str = "thumbnails"
    minio_use_ssl: bool = False

    # ── Redis ─────────────────────────────────────────────────────────────────
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_password: str = ""
    redis_db: int = 0

    @property
    def redis_url(self) -> str:
        if self.redis_password:
            return f"redis://:{self.redis_password}@{self.redis_host}:{self.redis_port}/{self.redis_db}"
        return f"redis://{self.redis_host}:{self.redis_port}/{self.redis_db}"

    # ── Celery ────────────────────────────────────────────────────────────────
    celery_broker_url: str = "redis://localhost:6379/0"
    celery_result_backend: str = "redis://localhost:6379/1"

    # ── OCR Engine ────────────────────────────────────────────────────────────
    ocr_engine: Literal["vietocr", "paddleocr"] = "vietocr"
    ocr_model_path: str = "./models/vietocr_transformer.pth"
    ocr_device: str = "cpu"

    # DPI render PDF scan (200 DPI: cân bằng tối ưu giữa độ nét và tốc độ xử lý)
    ocr_pdf_dpi_default: int = 200
    ocr_pdf_dpi_table_region: int = 300     # Render cao hơn cho vùng phát hiện bảng
    ocr_pdf_dpi_fast: int = 150             # DPI nhanh dùng khi ocr_fast_mode=True
    ocr_fast_mode: bool = False

    # VietOCR Transformer decoder settings
    # Mặc định False (Greedy search) khi chạy CPU để tăng tốc độ gấp 4-6 lần (từ ~70s xuống ~12s/trang)
    ocr_beamsearch_enabled: bool = False
    ocr_beam_size: int = 4                  # Beam size khi beamsearch=True
    ocr_beam_width: int = 4                 # Backward compat alias
    ocr_batch_size: int = 16                # Batch size predict_batch() với Padded Batching
    ocr_max_lines_per_page: int = 60       # Giới hạn dòng/trang để tránh quá tải
    ocr_extract_tables: bool = True         # Bóc tách cấu trúc bảng biểu nếu có lưới bảng rõ ràng

    # Morphology kernel sizes cho phát hiện đường kẻ bảng
    ocr_morph_kernel_horiz: int = 25       # Kernel ngang phát hiện đường kẻ ngang
    ocr_morph_kernel_vert: int = 25        # Kernel dọc phát hiện đường kẻ dọc

    # MSSV pattern — cấu hình được, không hardcode "2[0-3]" trong service
    # Ví dụ: "2[0-3]" = chấp nhận MSSV bắt đầu bằng 20, 21, 22, 23
    mssv_year_prefix_pattern: str = r"2[0-3]"
    mssv_length_min: int = 7
    mssv_length_max: int = 8

    # Admin dictionary path (cho text_postprocessing module)
    ocr_admin_dict_path: str = "./data/admin_dictionary_vi.json"

    # ── AI Enhancement & Smart Entity Extraction ─────────────────────────────
    # Hỗ trợ Gemini, OpenAI, Ollama (Local) hoặc auto fallback
    ai_provider: Literal["auto", "gemini", "openai", "ollama", "none"] = "auto"
    gemini_api_key: str = Field(default="")
    gemini_model: str = "gemini-1.5-flash"
    openai_api_key: str = Field(default="")
    openai_model: str = "gpt-4o-mini"
    openai_base_url: str = "https://api.openai.com/v1"
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "qwen2.5:7b"
    ai_timeout_seconds: float = 20.0

    # ── JWT ───────────────────────────────────────────────────────────────────
    jwt_secret_key: str = Field(default="CHANGE_ME_TO_A_JWT_SECRET")
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 60
    jwt_refresh_token_expire_days: int = 7

    # ── CORS ──────────────────────────────────────────────────────────────────
    cors_allowed_origins: str = "http://localhost:3000,http://localhost:5173"

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.cors_allowed_origins.split(",") if o.strip()]

    # ── Logging ───────────────────────────────────────────────────────────────
    log_level: str = "INFO"
    log_file: str = "./logs/app.log"

    # ── File upload limits ────────────────────────────────────────────────────
    max_file_size_mb: int = 50
    allowed_file_types: list[str] = ["pdf", "jpg", "jpeg", "png", "tiff"]

    @property
    def max_file_size_bytes(self) -> int:
        return self.max_file_size_mb * 1024 * 1024

    @property
    def is_production(self) -> bool:
        return self.app_env == "production"


@lru_cache
def get_settings() -> Settings:
    """
    Cached singleton — chỉ đọc .env một lần.
    Dùng trong FastAPI Depends: Depends(get_settings)
    """
    return Settings()


# Convenience alias — dùng trực tiếp trong code nội bộ
settings: Settings = get_settings()
