# Testing — Chien luoc kiem thu Backend

## Purpose

Huong dan viet va chay tests cho backend: unit tests, integration tests, mocking, coverage.

## Scope

pytest + pytest-asyncio. httpx.AsyncClient cho API tests. pytest-cov cho coverage.

## TODO

- [ ] Setup pytest fixtures (db session, async client, auth headers)
- [ ] Viet unit tests cho service layer (mock repositories)
- [ ] Viet integration tests cho API endpoints (httpx.AsyncClient)
- [ ] Mock external services (OCR engine, Elasticsearch, MinIO)
- [ ] Setup test database (test-specific PostgreSQL DB)
- [ ] Dat coverage >= 80% cho service layer
- [ ] Setup CI test pipeline

## References

- tests/README.md
- tests/UnitTest.md
- tests/IntegrationTest.md
