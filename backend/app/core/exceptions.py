"""
backend/app/core/exceptions.py — Custom exception hierarchy

Ref: .ai/CODING_RULES.md §3
Quy tắc:
  - Service layer raise custom exception (KHÔNG raise HTTPException).
  - Router/handler chuyển sang HTTPException.
  - AppException handler đăng ký toàn cục trong main.py.
"""
from __future__ import annotations


class AppException(Exception):
    """
    Base exception cho toàn bộ ứng dụng.
    Tất cả custom exception phải kế thừa từ đây.
    """

    def __init__(self, message: str, status_code: int = 500) -> None:
        self.message = message
        self.status_code = status_code
        super().__init__(message)

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(status={self.status_code}, message={self.message!r})"


# ── 400 Bad Request ────────────────────────────────────────────────────────────

class ValidationException(AppException):
    """Dữ liệu đầu vào không hợp lệ (nghiệp vụ, không phải Pydantic)."""

    def __init__(self, message: str) -> None:
        super().__init__(message, status_code=400)


class FileTooLargeException(AppException):
    """File upload vượt quá giới hạn cho phép."""

    def __init__(self, size_mb: float, max_mb: int) -> None:
        super().__init__(
            f"File quá lớn: {size_mb:.1f}MB (tối đa {max_mb}MB)",
            status_code=400,
        )


class UnsupportedFileTypeException(AppException):
    """Định dạng file không được hỗ trợ."""

    def __init__(self, file_type: str) -> None:
        super().__init__(
            f"Định dạng file không hỗ trợ: {file_type}. Chỉ chấp nhận PDF, JPG, PNG, TIFF.",
            status_code=400,
        )


# ── 401 Unauthorized ──────────────────────────────────────────────────────────

class UnauthorizedException(AppException):
    """Chưa xác thực (token thiếu hoặc hết hạn)."""

    def __init__(self, message: str = "Vui lòng đăng nhập để tiếp tục") -> None:
        super().__init__(message, status_code=401)


class InvalidCredentialsException(AppException):
    """Sai username hoặc password."""

    def __init__(self) -> None:
        super().__init__("Tên đăng nhập hoặc mật khẩu không đúng", status_code=401)


class TokenExpiredException(AppException):
    """Token JWT đã hết hạn."""

    def __init__(self) -> None:
        super().__init__("Phiên đăng nhập đã hết hạn, vui lòng đăng nhập lại", status_code=401)


# ── 403 Forbidden ─────────────────────────────────────────────────────────────

class PermissionDeniedException(AppException):
    """Không đủ quyền thực hiện hành động này."""

    def __init__(self, action: str | None = None) -> None:
        msg = "Không có quyền thực hiện thao tác này"
        if action:
            msg = f"Không có quyền: {action}"
        super().__init__(msg, status_code=403)


# ── 404 Not Found ─────────────────────────────────────────────────────────────

class NotFoundException(AppException):
    """Resource không tìm thấy (base)."""

    def __init__(self, resource: str, resource_id: str | None = None) -> None:
        msg = f"Không tìm thấy {resource}"
        if resource_id:
            msg = f"Không tìm thấy {resource}: {resource_id}"
        super().__init__(msg, status_code=404)


class DocumentNotFoundException(NotFoundException):
    def __init__(self, document_id: str) -> None:
        super().__init__("tài liệu", document_id)


class UserNotFoundException(NotFoundException):
    def __init__(self, user_id: str) -> None:
        super().__init__("người dùng", user_id)


# ── 409 Conflict ──────────────────────────────────────────────────────────────

class DuplicateResourceException(AppException):
    """Resource đã tồn tại."""

    def __init__(self, resource: str, field: str, value: str) -> None:
        super().__init__(
            f"{resource} với {field}='{value}' đã tồn tại",
            status_code=409,
        )


# ── 422 Unprocessable ─────────────────────────────────────────────────────────

class DocumentNotReadyException(AppException):
    """Tài liệu chưa hoàn thành OCR, không thể thực hiện thao tác."""

    def __init__(self, document_id: str, current_status: str) -> None:
        super().__init__(
            f"Tài liệu {document_id} chưa sẵn sàng (trạng thái: {current_status})",
            status_code=422,
        )


# ── 500 Internal ──────────────────────────────────────────────────────────────

class OCRProcessingException(AppException):
    """Lỗi trong quá trình xử lý OCR."""

    def __init__(self, detail: str) -> None:
        super().__init__(f"Lỗi xử lý OCR: {detail}", status_code=500)


class StorageException(AppException):
    """Lỗi khi thao tác với MinIO."""

    def __init__(self, detail: str) -> None:
        super().__init__(f"Lỗi lưu trữ file: {detail}", status_code=500)


class SearchIndexException(AppException):
    """Lỗi khi index/query Elasticsearch."""

    def __init__(self, detail: str) -> None:
        super().__init__(f"Lỗi tìm kiếm: {detail}", status_code=500)
