# Unit Tests — Kiem thu don vi

## Purpose

Huong dan viet unit tests cho tung layer: service, repository, utility, schema.

## Scope

pytest + pytest-asyncio. Mocking: unittest.mock, pytest-mock. Test isolation.

## TODO

- [ ] Viet test cho AuthService (login, token generation, refresh)
- [ ] Viet test cho DocumentService (create, get, list, delete)
- [ ] Viet test cho OCRService (trigger, parse result)
- [ ] Viet test cho SearchService (query builder, result mapping)
- [ ] Viet test cho Pydantic schemas (validation, serialization)
- [ ] Viet test cho utility functions (file processing, pagination)
- [ ] Dat coverage >= 80% cho service layer

## References

- IntegrationTest.md
- backend/Testing.md
