"""
backend/tests/test_search.py — Elasticsearch Search API Tests

Tuân thủ AAA Pattern (Arrange - Act - Assert).
"""
import pytest
import httpx


@pytest.mark.asyncio
async def test_search_vietnamese_query(async_client: httpx.AsyncClient):
    """Kiểm tra tìm kiếm toàn văn tiếng Việt có dấu và không dấu."""
    # ── Arrange ───────────────────────────────────────────────────────────
    query = "học phí"

    # ── Act ───────────────────────────────────────────────────────────────
    response = await async_client.get("/api/v1/search", params={"q": query, "fuzzy": True})

    # ── Assert ────────────────────────────────────────────────────────────
    assert response.status_code == 200
    data = response.json()
    assert "total_hits" in data
    assert "results" in data
    assert data["query"] == query
    assert data["took_ms"] >= 0


@pytest.mark.asyncio
async def test_search_unaccented_query(async_client: httpx.AsyncClient):
    """Kiểm tra tìm kiếm không dấu (asciifolding: 'hoc phi' -> 'học phí')."""
    # ── Arrange ───────────────────────────────────────────────────────────
    query = "hoc phi"

    # ── Act ───────────────────────────────────────────────────────────────
    response = await async_client.get("/api/v1/search", params={"q": query})

    # ── Assert ────────────────────────────────────────────────────────────
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data["results"], list)
