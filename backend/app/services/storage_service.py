"""
backend/app/services/storage_service.py — Supabase Storage Service

Thay thế MinIO bằng Supabase Storage (S3-compatible).
Vẫn giữ local fallback khi Supabase offline (môi trường dev không có internet).

API mapping MinIO → Supabase:
  put_object()    → storage.from_(bucket).upload(path, data)
  get_object()    → storage.from_(bucket).download(path)
  remove_object() → storage.from_(bucket).remove([path])
"""
import io
import os
import uuid
from datetime import datetime
from pathlib import Path
from typing import BinaryIO

from loguru import logger

from app.core.config import settings
from app.core.exceptions import StorageException

# Local fallback directory (khi Supabase offline hoặc chạy offline)
LOCAL_STORAGE_DIR = Path(
    os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../uploads"))
)


class StorageService:
    """
    Service lưu trữ file qua Supabase Storage.
    Tự động fallback Local Storage khi Supabase không khả dụng.
    """

    def __init__(self) -> None:
        self.documents_bucket = settings.supabase_storage_bucket_documents
        self.thumbnails_bucket = settings.supabase_storage_bucket_thumbnails
        self._supabase_enabled: bool | None = None
        self._client = None
        self._init_client()

    def _init_client(self) -> None:
        """Khởi tạo Supabase client lazy (chỉ import khi cần)."""
        try:
            from app.core.supabase_client import supabase_admin
            self._client = supabase_admin
            logger.info("Supabase Storage client ready.")
        except Exception as exc:
            logger.warning("Supabase Storage client init failed: {err}", err=str(exc))
            self._client = None

    def _is_supabase_alive(self) -> bool:
        """Kiểm tra nhanh kết nối Supabase Storage."""
        if self._supabase_enabled is False or not self._client:
            return False
        if self._supabase_enabled is True:
            return True
        try:
            # List buckets để kiểm tra kết nối
            self._client.storage.list_buckets()
            self._supabase_enabled = True
            return True
        except Exception:
            self._supabase_enabled = False
            logger.warning("Supabase Storage not reachable, will use local fallback.")
            return False

    def _ensure_bucket_exists(self, bucket_name: str) -> None:
        """Tạo bucket nếu chưa tồn tại trên Supabase."""
        if not self._is_supabase_alive():
            return
        try:
            existing = [b.name for b in self._client.storage.list_buckets()]
            if bucket_name not in existing:
                self._client.storage.create_bucket(bucket_name, options={"public": False})
                logger.info("Created Supabase Storage bucket: {bucket}", bucket=bucket_name)
        except Exception as exc:
            logger.warning("Could not ensure bucket exists: {err}", err=str(exc))

    def generate_object_key(self, original_filename: str, prefix: str = "documents") -> str:
        """
        Sinh object key theo cấu trúc:
        {prefix}/{YYYY}/{MM}/{file_uuid}_{clean_filename}

        Supabase Storage yêu cầu key chỉ chứa ASCII — tên file tiếng Việt/Unicode
        được chuyển sang ASCII (unidecode) trước khi tạo key.
        """
        import unicodedata
        import re

        now = datetime.now()
        file_uuid = uuid.uuid4()

        # Tách tên file và extension
        name_part, _, ext_part = original_filename.rpartition(".")
        if not name_part:
            name_part = original_filename
            ext_part = ""

        # Normalize Unicode → ASCII (NFC → NFKD → loại bỏ combining marks)
        normalized = unicodedata.normalize("NFKD", name_part)
        ascii_name = normalized.encode("ascii", errors="ignore").decode("ascii")

        # Giữ chỉ alphanumeric, dấu gạch dưới, gạch ngang
        ascii_name = re.sub(r"[^\w\-]", "_", ascii_name)
        # Collapse nhiều underscore liên tiếp
        ascii_name = re.sub(r"_+", "_", ascii_name).strip("_")

        # Ghép lại với extension
        clean_name = f"{ascii_name}.{ext_part}" if ext_part else ascii_name
        if not clean_name or clean_name == ".":
            clean_name = "document"

        return f"{prefix}/{now.year}/{now.month:02d}/{file_uuid}_{clean_name}"

    def upload_file(
        self,
        file_data: bytes | BinaryIO,
        filename: str,
        content_type: str = "application/octet-stream",
        bucket_name: str | None = None,
    ) -> str:
        """
        Upload file lên Supabase Storage, fallback local nếu offline.
        Trả về object_key (đường dẫn trong bucket).
        """
        bucket = bucket_name or self.documents_bucket
        object_key = self.generate_object_key(filename)

        # Chuẩn hóa về bytes
        if isinstance(file_data, bytes):
            data_bytes = file_data
        else:
            file_data.seek(0)
            data_bytes = file_data.read()

        # Thử upload lên Supabase Storage
        if self._is_supabase_alive():
            try:
                self._ensure_bucket_exists(bucket)
                self._client.storage.from_(bucket).upload(
                    path=object_key,
                    file=data_bytes,
                    file_options={"content-type": content_type, "upsert": "false"},
                )
                logger.info(
                    "Uploaded to Supabase Storage: bucket={bucket}, key={key}, size={size}B",
                    bucket=bucket,
                    key=object_key,
                    size=len(data_bytes),
                )
                return object_key
            except Exception as exc:
                logger.warning(
                    "Supabase Storage upload failed ({err}). Falling back to local.",
                    err=str(exc),
                )
                self._supabase_enabled = False  # reset để retry lần sau

        # Fallback: lưu local disk
        try:
            local_path = LOCAL_STORAGE_DIR / object_key
            local_path.parent.mkdir(parents=True, exist_ok=True)
            with open(local_path, "wb") as f:
                f.write(data_bytes)
            logger.info(
                "Saved to local storage: path={path}, size={size}B",
                path=str(local_path),
                size=len(data_bytes),
            )
            return object_key
        except Exception as exc:
            logger.error("Failed to save locally: {err}", err=str(exc))
            raise StorageException(f"Lỗi lưu trữ file: {str(exc)}") from exc

    def get_file(self, object_key: str, bucket_name: str | None = None) -> bytes:
        """
        Đọc toàn bộ nội dung file theo object key.
        Ưu tiên local (nếu tồn tại), sau đó Supabase Storage.
        """
        # 1. Kiểm tra local trước
        local_path = LOCAL_STORAGE_DIR / object_key
        if local_path.exists():
            with open(local_path, "rb") as f:
                return f.read()

        # 2. Đọc từ Supabase Storage
        bucket = bucket_name or self.documents_bucket
        if self._client:
            try:
                data = self._client.storage.from_(bucket).download(object_key)
                return data
            except Exception as exc:
                logger.error(
                    "Failed to read {key} from Supabase Storage: {err}",
                    key=object_key,
                    err=str(exc),
                )

        raise StorageException(f"Không tìm thấy file: {object_key}")

    def get_file_stream(self, object_key: str, bucket_name: str | None = None) -> io.BytesIO:
        """Trả về BytesIO stream của file (từ local hoặc Supabase)."""
        data = self.get_file(object_key, bucket_name)
        return io.BytesIO(data)

    def get_public_url(self, object_key: str, bucket_name: str | None = None) -> str | None:
        """
        Lấy public URL của file trên Supabase Storage.
        Chỉ hoạt động nếu bucket có public access.
        """
        bucket = bucket_name or self.documents_bucket
        if self._client:
            try:
                res = self._client.storage.from_(bucket).get_public_url(object_key)
                return res
            except Exception as exc:
                logger.warning("Could not get public URL: {err}", err=str(exc))
        return None

    def get_signed_url(
        self,
        object_key: str,
        expires_in: int = 3600,
        bucket_name: str | None = None,
    ) -> str | None:
        """
        Tạo signed URL để download file (hết hạn sau `expires_in` giây).
        Phù hợp với private bucket.
        """
        bucket = bucket_name or self.documents_bucket
        if self._client:
            try:
                res = self._client.storage.from_(bucket).create_signed_url(
                    object_key, expires_in
                )
                return res.get("signedURL")
            except Exception as exc:
                logger.warning("Could not create signed URL: {err}", err=str(exc))
        return None

    def delete_file(self, object_key: str, bucket_name: str | None = None) -> bool:
        """Xóa file khỏi Supabase Storage và local fallback."""
        # Xóa local
        local_path = LOCAL_STORAGE_DIR / object_key
        if local_path.exists():
            try:
                local_path.unlink()
            except Exception:
                pass

        # Xóa Supabase Storage
        bucket = bucket_name or self.documents_bucket
        if self._client:
            try:
                self._client.storage.from_(bucket).remove([object_key])
                logger.info("Deleted from Supabase Storage: {key}", key=object_key)
                return True
            except Exception as exc:
                logger.warning("Failed to delete from Supabase Storage: {err}", err=str(exc))

        return True


# Singleton instance
storage_service = StorageService()
