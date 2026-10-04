"""
backend/tests/test_engine_isolation.py — OCR Multi-Engine Isolation & Regression Tests

Tuân thủ AAA Pattern (Arrange - Act - Assert).
Kiểm tra tính độc lập tuyệt đối giữa các OCR engines (vietocr, trocr, tesseract).
"""
import uuid
from unittest.mock import AsyncMock, MagicMock, patch
import pytest
import pytest_asyncio
import httpx
from sqlalchemy import select

from app.core.constants import OCR_ENGINES
from app.core.database import AsyncSessionLocal, init_db
from app.core.exceptions import EngineUnavailableError
from app.models.documents import Document
from app.models.ocr_results import OCRResult
from app.models.processing_jobs import ProcessingJob
from app.services.document_service import DocumentService
from app.worker.tasks import async_process_ocr
from app.models.users import User


@pytest_asyncio.fixture(autouse=True)
async def setup_db():
    await init_db()


async def _get_valid_user_id(session) -> uuid.UUID:
    res = await session.execute(select(User.id).limit(1))
    uid = res.scalar()
    if uid:
        return uid
    # Fallback to creating a test user if none exists
    u = User(
        username="isolation_test_user",
        email="isolation@test.com",
        hashed_password="hash",
        full_name="Isolation User",
        role="STAFF",
        is_active=True,
    )
    session.add(u)
    await session.flush()
    return u.id


@pytest.mark.asyncio
async def test_invalid_engine_validation_422(async_client: httpx.AsyncClient, staff_token: str):
    """Kiểm tra truyền engine không hợp lệ -> 422 Unprocessable Entity."""
    headers = {"Authorization": f"Bearer {staff_token}"}
    fake_id = str(uuid.uuid4())

    # 1. Reprocess with invalid engine
    res_reprocess = await async_client.post(
        f"/api/v1/documents/{fake_id}/reprocess-ocr?engine=unsupported_engine",
        headers=headers,
    )
    assert res_reprocess.status_code == 422
    assert "không hợp lệ" in res_reprocess.json().get("detail", "")

    # 2. Get ocr-results with invalid engine
    res_get = await async_client.get(
        f"/api/v1/documents/{fake_id}/ocr-results/unsupported_engine",
        headers=headers,
    )
    assert res_get.status_code == 422


@pytest.mark.asyncio
async def test_upload_creates_only_default_engine_row():
    """(a) Upload/Xử lý mặc định chỉ tạo duy nhất 1 bản ghi OCRResult cho vietocr (không tự động chạy trocr)."""
    doc_id = uuid.uuid4()

    async with AsyncSessionLocal() as session:
        user_id = await _get_valid_user_id(session)
        now_doc = Document(
            id=doc_id,
            title="Đơn thử nghiệm isolation",
            original_filename="test.pdf",
            file_type="pdf",
            file_size_bytes=1024,
            minio_object_key=f"documents/{doc_id}/test.pdf",
            uploaded_by=user_id,
            ocr_status="PENDING",
        )
        job = ProcessingJob(
            document_id=doc_id,
            status="PENDING",
        )
        session.add(now_doc)
        session.add(job)
        await session.commit()

    with patch("app.services.storage_service.storage_service.get_file", return_value=b"%PDF-1.4 dummy"):
        with patch("app.services.vietocr_service.vietocr_service.extract_text_from_file", return_value=("VietOCR Raw Text", "VietOCR Processed Text", 0.95)):
            with patch("app.services.ai_service.ai_service.extract_smart_fields", new_callable=AsyncMock, return_value={}):
                with patch("app.services.search_index_service.search_index_service.index_document", new_callable=AsyncMock):
                    # Chạy OCR mặc định (engine=None -> vietocr)
                    await async_process_ocr(str(doc_id), engine=None)

    async with AsyncSessionLocal() as session:
        res = await session.execute(
            select(OCRResult).where(OCRResult.document_id == doc_id)
        )
        rows = res.scalars().all()

        assert len(rows) == 1
        assert rows[0].ocr_engine == "vietocr"
        assert rows[0].is_latest is True
        assert rows[0].status == "DONE"
        assert rows[0].raw_text == "VietOCR Raw Text"
        assert rows[0].processing_time_ms is not None
        assert rows[0].processing_time_ms >= 0


@pytest.mark.asyncio
async def test_reprocess_trocr_does_not_overwrite_vietocr():
    """(b) Chạy lại với engine=trocr tạo bản ghi trocr mà không ghi đè is_latest của vietocr."""
    doc_id = uuid.uuid4()

    async with AsyncSessionLocal() as session:
        user_id = await _get_valid_user_id(session)
        doc = Document(
            id=doc_id,
            title="Đơn thử nghiệm reprocess",
            original_filename="test2.pdf",
            file_type="pdf",
            file_size_bytes=1024,
            minio_object_key=f"documents/{doc_id}/test2.pdf",
            uploaded_by=user_id,
            ocr_status="DONE",
        )
        vietocr_row = OCRResult(
            document_id=doc_id,
            ocr_engine="vietocr",
            is_latest=True,
            raw_text="Văn bản gốc VietOCR",
            corrected_text="Văn bản chuẩn VietOCR",
            confidence_score=0.92,
            status="DONE",
        )
        session.add(doc)
        session.add(vietocr_row)
        session.add(ProcessingJob(document_id=doc_id, status="PENDING"))
        await session.commit()

    with patch("app.services.storage_service.storage_service.get_file", return_value=b"%PDF-1.4 dummy"):
        with patch("app.services.trocr_service.trocr_service.extract_text_from_file", return_value=("TrOCR Raw Text", "TrOCR Processed Text", 0.88)):
            with patch("app.services.ai_service.ai_service.extract_smart_fields", new_callable=AsyncMock, return_value={}):
                with patch("app.services.search_index_service.search_index_service.index_document", new_callable=AsyncMock):
                    await async_process_ocr(str(doc_id), engine="trocr")

    async with AsyncSessionLocal() as session:
        res = await session.execute(
            select(OCRResult).where(OCRResult.document_id == doc_id)
        )
        rows = res.scalars().all()

        assert len(rows) == 2
        engine_map = {r.ocr_engine: r for r in rows}

        assert "vietocr" in engine_map
        assert "trocr" in engine_map

        assert engine_map["vietocr"].is_latest is True
        assert engine_map["vietocr"].raw_text == "Văn bản gốc VietOCR"

        assert engine_map["trocr"].is_latest is True
        assert engine_map["trocr"].raw_text == "TrOCR Raw Text"
        assert engine_map["trocr"].status == "DONE"

        # Check get_document_by_id returns all latest engines
        doc_service = DocumentService(session)
        doc_dto = await doc_service.get_document_by_id(doc_id)
        assert len(doc_dto.all_ocr_results) == 2
        engines_in_dto = {r.ocr_engine for r in doc_dto.all_ocr_results}
        assert engines_in_dto == {"vietocr", "trocr"}


@pytest.mark.asyncio
async def test_tesseract_engine_never_calls_vietocr_service():
    """(c) Chạy engine=tesseract gọi tesseract_service và TUYỆT ĐỐI KHÔNG gọi vietocr_service."""
    doc_id = uuid.uuid4()

    async with AsyncSessionLocal() as session:
        user_id = await _get_valid_user_id(session)
        doc = Document(
            id=doc_id,
            title="Đơn thử nghiệm tesseract",
            original_filename="test3.pdf",
            file_type="pdf",
            file_size_bytes=1024,
            minio_object_key=f"documents/{doc_id}/test3.pdf",
            uploaded_by=user_id,
            ocr_status="PENDING",
        )
        session.add(doc)
        session.add(ProcessingJob(document_id=doc_id, status="PENDING"))
        await session.commit()

    mock_tess = MagicMock(return_value=("Tesseract Raw Text", "Tesseract Processed Text", 0.75))
    mock_viet = MagicMock(return_value=("VietOCR Text", "VietOCR Processed", 0.99))

    with patch("app.services.storage_service.storage_service.get_file", return_value=b"%PDF-1.4 dummy"):
        with patch("app.services.tesseract_service.tesseract_service.extract_text_from_file", mock_tess):
            with patch("app.services.vietocr_service.vietocr_service.extract_text_from_file", mock_viet):
                with patch("app.services.ai_service.ai_service.extract_smart_fields", new_callable=AsyncMock, return_value={}):
                    with patch("app.services.search_index_service.search_index_service.index_document", new_callable=AsyncMock):
                        await async_process_ocr(str(doc_id), engine="tesseract")

    # Assert tesseract was called, vietocr was NEVER called for text extraction
    mock_tess.assert_called_once()
    mock_viet.assert_not_called()

    async with AsyncSessionLocal() as session:
        res = await session.execute(
            select(OCRResult).where(OCRResult.document_id == doc_id, OCRResult.ocr_engine == "tesseract")
        )
        row = res.scalars().first()
        assert row is not None
        assert row.status == "DONE"
        assert row.raw_text == "Tesseract Raw Text"


@pytest.mark.asyncio
async def test_trocr_failure_reports_failed_and_never_copies_vietocr():
    """(e) Khi TrOCR bị lỗi, lưu trạng thái FAILED với error_message và TUYỆT ĐỐI KHÔNG copy text của VietOCR."""
    doc_id = uuid.uuid4()

    async with AsyncSessionLocal() as session:
        user_id = await _get_valid_user_id(session)
        doc = Document(
            id=doc_id,
            title="Đơn test TrOCR lỗi",
            original_filename="test4.pdf",
            file_type="pdf",
            file_size_bytes=1024,
            minio_object_key=f"documents/{doc_id}/test4.pdf",
            uploaded_by=user_id,
            ocr_status="DONE",
        )
        vietocr_row = OCRResult(
            document_id=doc_id,
            ocr_engine="vietocr",
            is_latest=True,
            raw_text="VietOCR Valid Text",
            corrected_text="VietOCR Valid Text",
            confidence_score=0.95,
            status="DONE",
        )
        session.add(doc)
        session.add(vietocr_row)
        session.add(ProcessingJob(document_id=doc_id, status="PENDING"))
        await session.commit()

    with patch("app.services.storage_service.storage_service.get_file", return_value=b"%PDF-1.4 dummy"):
        with patch(
            "app.services.trocr_service.trocr_service.extract_text_from_file",
            side_effect=EngineUnavailableError("Model weights for TrOCR not found"),
        ):
            with patch("app.services.ai_service.ai_service.extract_smart_fields", new_callable=AsyncMock, return_value={}):
                with patch("app.services.search_index_service.search_index_service.index_document", new_callable=AsyncMock):
                    # async_process_ocr handles exception for non-default engine and marks OCRResult as FAILED
                    await async_process_ocr(str(doc_id), engine="trocr")

    async with AsyncSessionLocal() as session:
        res = await session.execute(
            select(OCRResult).where(OCRResult.document_id == doc_id, OCRResult.ocr_engine == "trocr")
        )
        trocr_row = res.scalars().first()

        assert trocr_row is not None
        assert trocr_row.status == "FAILED"
        assert "Model weights for TrOCR not found" in trocr_row.error_message
        assert trocr_row.raw_text == ""  # Did NOT copy VietOCR
        assert trocr_row.corrected_text == ""
