# Coding Rules — Quy tắc lập trình

## Purpose

Quy tắc viết code bắt buộc cho toàn bộ dự án: naming convention, code structure,
error handling, logging, documentation, testing.

## Scope

Áp dụng cho: Python (backend, training), JavaScript/TypeScript (frontend),
SQL (database), YAML (config), Markdown (docs).

---

## 1. Naming Conventions

### Python (Backend)

| Loại | Convention | Ví dụ |
|------|-----------|-------|
| Biến, hàm, file, module | `snake_case` | `user_id`, `get_document()`, `document_service.py` |
| Class, Pydantic model | `PascalCase` | `DocumentService`, `UserCreate` |
| Hằng số | `UPPER_SNAKE_CASE` | `MAX_FILE_SIZE_MB`, `OCR_TIMEOUT_SECONDS` |
| Private method/attr | `_snake_case` | `_validate_file_type()` |
| Type alias | `PascalCase` | `DocumentList = list[Document]` |

### Pydantic Schema

Đặt tên theo pattern `<Entity><Action>`:

| Schema | Dùng khi | Ví dụ |
|--------|---------|-------|
| `<Entity>Create` | Body của POST endpoint | `DocumentCreate`, `UserCreate` |
| `<Entity>Update` | Body của PATCH/PUT endpoint | `DocumentUpdate` |
| `<Entity>Response` | Response trả về client | `DocumentResponse`, `UserResponse` |
| `<Entity>Request` | Request body phức tạp (không phải CRUD đơn giản) | `SearchRequest` |
| `<Entity>Filter` | Query params cho list endpoint | `DocumentFilter` |

### JavaScript / TypeScript (Frontend)

| Loại | Convention | Ví dụ |
|------|-----------|-------|
| Biến, hàm | `camelCase` | `userId`, `fetchDocuments()` |
| Component | `PascalCase` | `DocumentCard`, `SearchBar` |
| Hằng số / enum | `UPPER_SNAKE_CASE` | `API_BASE_URL` |
| File component | `PascalCase.tsx` | `DocumentCard.tsx` |
| File utility | `camelCase.ts` | `formatDate.ts` |

---

## 2. Cấu trúc Router FastAPI

**Quy tắc: 1 file router = 1 resource.**

```
backend/app/routers/
├── auth.py           # /auth/login, /auth/logout, /auth/refresh
├── documents.py      # /documents/ (CRUD)
├── ocr.py            # /ocr/trigger, /ocr/result/{id}
├── search.py         # /search/
├── users.py          # /users/
└── health.py         # /health
```

**Template chuẩn cho một route:**

```python
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.users import User
from app.schemas.documents import DocumentCreate, DocumentResponse
from app.services.document_service import DocumentService

router = APIRouter(prefix="/documents", tags=["documents"])


@router.post("/", response_model=DocumentResponse, status_code=status.HTTP_201_CREATED)
async def create_document(
    payload: DocumentCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> DocumentResponse:
    """Tạo document mới."""
    service = DocumentService(db)
    return await service.create(payload, uploaded_by=current_user.id)
```

---

## 3. Exception Handling

**Quy tắc cốt lõi:**
- Service layer chỉ raise custom exception — **KHÔNG raise `HTTPException`** trực tiếp.
- Router layer bắt custom exception và chuyển thành `HTTPException`.
- Handler toàn cục đăng ký trong `main.py`.

```python
# app/core/exceptions.py
class AppException(Exception):
    """Base exception cho toàn bộ ứng dụng."""
    def __init__(self, message: str, status_code: int = 500):
        self.message = message
        self.status_code = status_code
        super().__init__(message)

class DocumentNotFoundException(AppException):
    def __init__(self, document_id: str):
        super().__init__(f"Không tìm thấy tài liệu: {document_id}", status_code=404)

class OCRProcessingException(AppException):
    def __init__(self, detail: str):
        super().__init__(f"Lỗi xử lý OCR: {detail}", status_code=500)

class PermissionDeniedException(AppException):
    def __init__(self):
        super().__init__("Không có quyền thực hiện thao tác này", status_code=403)
```

```python
# Trong router — bắt và chuyển đổi
from app.core.exceptions import AppException

@app.exception_handler(AppException)
async def app_exception_handler(request: Request, exc: AppException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.message},
    )
```

---

## 4. Testing — Pytest AAA Pattern

**Quy tắc:**
- Mỗi service có file test riêng: `tests/unit/test_document_service.py`
- Mock toàn bộ external dependency (DB, MinIO, ES, Celery).
- Dùng pattern **Arrange → Act → Assert** rõ ràng.
- Test name: `test_<function>_<scenario>_<expected_result>`

```python
# tests/unit/test_document_service.py
import pytest
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

from app.services.document_service import DocumentService
from app.core.exceptions import DocumentNotFoundException


@pytest.mark.asyncio
async def test_get_document_exists_returns_document():
    # Arrange
    mock_db = AsyncMock()
    mock_document = MagicMock(id=uuid4(), title="Test Doc")
    mock_db.get.return_value = mock_document
    service = DocumentService(db=mock_db)

    # Act
    result = await service.get_by_id(mock_document.id)

    # Assert
    assert result.id == mock_document.id
    assert result.title == "Test Doc"


@pytest.mark.asyncio
async def test_get_document_not_found_raises_exception():
    # Arrange
    mock_db = AsyncMock()
    mock_db.get.return_value = None
    service = DocumentService(db=mock_db)

    # Act & Assert
    with pytest.raises(DocumentNotFoundException):
        await service.get_by_id(uuid4())
```

---

## 5. Logging

Dùng **Loguru** (đã có trong requirements). Format chuẩn:

```python
from loguru import logger

# Không dùng f-string trong logger — dùng lazy formatting
logger.info("Document uploaded: id={doc_id}, user={user_id}", doc_id=doc.id, user_id=user.id)
logger.error("OCR failed: doc_id={doc_id}, error={error}", doc_id=doc_id, error=str(exc))

# Log với context
with logger.contextualize(request_id=request_id, user_id=user_id):
    logger.info("Processing document")
```

---

## 6. Commit Message (Conventional Commits)

Format: `<type>(<scope>): <subject>`

| Type | Dùng khi |
|------|---------|
| `feat` | Thêm tính năng mới |
| `fix` | Sửa bug |
| `docs` | Thay đổi tài liệu |
| `refactor` | Refactor không thêm feature, không fix bug |
| `test` | Thêm/sửa test |
| `chore` | Build, CI, config |
| `perf` | Cải thiện hiệu năng |

Ví dụ:
```
feat(documents): add soft delete endpoint
fix(ocr): handle empty page_texts from VietOCR
docs(api): update search endpoint documentation
test(document-service): add unit tests for upload flow
```

---

## References

- `pyproject.toml` (ruff, mypy config)
- `.editorconfig`
- `.ai/AGENTS.md`
- `.ai/DECISIONS.md`
