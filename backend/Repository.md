# Repository Pattern — Data Access Layer

## Purpose

Huong dan implement Repository pattern: SQLAlchemy repositories, async queries, transaction.

## Scope

Abstract BaseRepository[T] -> Concrete Repositories. Async SQLAlchemy 2.0 voi asyncpg.

## TODO

- [ ] Implement BaseRepository[T] generic class (CRUD methods)
- [ ] Implement DocumentRepository
- [ ] Implement UserRepository
- [ ] Implement OCRResultRepository
- [ ] Implement Unit of Work pattern cho transaction
- [ ] Xu ly database transaction (commit/rollback)
- [ ] Implement soft delete (deleted_at timestamp)

## References

- https://www.sqlalchemy.org/
- Database.md
- FastAPI.md
