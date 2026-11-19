"""
backend/tests/test_access_log_filter.py — Unit test for token masking in access log
"""
import logging
from app.main import MaskTokenAccessLogFilter, setup_access_log_filter


def test_mask_token_access_log_filter_tuple_args():
    flt = MaskTokenAccessLogFilter()
    record = logging.LogRecord(
        name="uvicorn.access",
        level=logging.INFO,
        pathname="",
        lineno=0,
        msg='%s - "%s %s HTTP/%s" %d',
        args=(
            "127.0.0.1:54369",
            "GET",
            "/api/v1/documents/41e6f99e-1e5f-4a42-be23-cd2b49dddd8f/file?token=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.test.jwt",
            "1.1",
            200,
        ),
        exc_info=None,
    )

    assert flt.filter(record) is True
    formatted = record.getMessage()
    assert "token=***" in formatted
    assert "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9" not in formatted


def test_mask_token_in_middle_of_query():
    flt = MaskTokenAccessLogFilter()
    record = logging.LogRecord(
        name="uvicorn.access",
        level=logging.INFO,
        pathname="",
        lineno=0,
        msg='%s - "%s %s HTTP/%s" %d',
        args=(
            "127.0.0.1:54369",
            "GET",
            "/api/v1/documents/123/file?download=true&token=SECRET_JWT_TOKEN&format=pdf",
            "1.1",
            200,
        ),
        exc_info=None,
    )

    assert flt.filter(record) is True
    formatted = record.getMessage()
    assert "download=true&token=***&format=pdf" in formatted
    assert "SECRET_JWT_TOKEN" not in formatted


def test_no_token_remains_unchanged():
    flt = MaskTokenAccessLogFilter()
    path = "/api/v1/documents/123/file?download=true&format=pdf"
    record = logging.LogRecord(
        name="uvicorn.access",
        level=logging.INFO,
        pathname="",
        lineno=0,
        msg='%s - "%s %s HTTP/%s" %d',
        args=("127.0.0.1:54369", "GET", path, "1.1", 200),
        exc_info=None,
    )

    assert flt.filter(record) is True
    formatted = record.getMessage()
    assert path in formatted
    assert "token" not in formatted


def test_mask_token_in_record_msg():
    flt = MaskTokenAccessLogFilter()
    record = logging.LogRecord(
        name="uvicorn.access",
        level=logging.INFO,
        pathname="",
        lineno=0,
        msg='GET /api/v1/documents/123/file?token=SECRET_TOKEN HTTP/1.1 200',
        args=(),
        exc_info=None,
    )

    assert flt.filter(record) is True
    formatted = record.getMessage()
    assert "token=***" in formatted
    assert "SECRET_TOKEN" not in formatted


def test_setup_access_log_filter_registers_successfully():
    setup_access_log_filter()
    logger = logging.getLogger("uvicorn.access")
    assert any(isinstance(f, MaskTokenAccessLogFilter) for f in logger.filters)
