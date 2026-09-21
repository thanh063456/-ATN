# Integration Tests — Kiem thu tich hop

## Purpose

Huong dan viet integration tests: API endpoint tests, database, Elasticsearch.

## Scope

httpx.AsyncClient de test FastAPI. Test DB: PostgreSQL test container. Mock ES.

## TODO

- [ ] Viet test cho POST /api/v1/auth/login (success + fail cases)
- [ ] Viet test cho POST /api/v1/documents (upload file)
- [ ] Viet test cho GET /api/v1/documents/{id}
- [ ] Viet test cho GET /api/v1/search?q=...
- [ ] Viet test cho OCR trigger endpoint
- [ ] Test authentication middleware (401 khi khong co token)
- [ ] Test error responses (400, 401, 404, 422, 500)

## References

- UnitTest.md
- PerformanceTest.md
- backend/Testing.md
