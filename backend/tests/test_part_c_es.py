import pytest
from httpx import AsyncClient
from app.core.elasticsearch import INDEX_MAPPINGS, is_es_available
from app.core.doc_types_config import DOC_TYPES_CONFIG


def test_es_mappings_contain_specified_fields():
    props = INDEX_MAPPINGS["properties"]
    expected_fields = [
        "doc_type_code",
        "doc_type_name",
        "doc_group",
        "doc_subtype",
        "doc_type_confidence",
        "doc_type_source",
        "subject",
        "issuing_unit",
        "ocr_scope",
        "page_count",
        "pages_ocr",
        "needs_review",
        # backward compatibility
        "document_type",
    ]
    for field in expected_fields:
        assert field in props, f"Field '{field}' missing from INDEX_MAPPINGS"


@pytest.mark.asyncio
async def test_get_doc_types_endpoint(async_client: AsyncClient):
    response = await async_client.get("/api/v1/doc-types")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == len(DOC_TYPES_CONFIG.types)
    codes = [item["code"] for item in data]
    assert "THONG_BAO" in codes
    assert "QUYET_DINH" in codes
    assert "CONG_VAN" in codes


@pytest.mark.asyncio
async def test_search_facets_and_params(async_client: AsyncClient):
    # Test params doc_type_code and doc_group on search endpoint
    response = await async_client.get("/api/v1/search?q=thong+bao&doc_type_code=THONG_BAO&doc_group=VAN_BAN_HANH_CHINH")
    assert response.status_code == 200
    data = response.json()
    assert "facets" in data
    assert "results" in data
    # Facets should be dictionary with doc_type_code and doc_group keys
    if data["facets"] is not None:
        assert "doc_type_code" in data["facets"]
        assert "doc_group" in data["facets"]


@pytest.mark.asyncio
async def test_list_documents_doctype_filters(async_client: AsyncClient):
    response = await async_client.get("/api/v1/documents?doc_type_code=THONG_BAO&doc_group=VAN_BAN_HANH_CHINH")
    assert response.status_code == 200
    data = response.json()
    assert "items" in data


@pytest.mark.es
def test_es_marker_skips_when_unavailable():
    # If ES is running, this passes; if not, conftest pytest_runtest_setup skips cleanly
    assert is_es_available() is True
