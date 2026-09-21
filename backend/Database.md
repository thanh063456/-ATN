# Database — Cau hinh va Schema

## Purpose

Chi tiet cau hinh PostgreSQL, SQLAlchemy engine, Alembic migrations va database schema.

## Scope

SQLAlchemy 2.0 async voi asyncpg driver. Alembic cho migration. PostgreSQL 15.

## TODO

- [ ] Cau hinh async SQLAlchemy engine (create_async_engine)
- [ ] Tao Base model class voi timestamps (created_at, updated_at)
- [ ] Implement tat ca ORM models (User, Document, OCRResult, ProcessingJob)
- [ ] Setup Alembic voi async support
- [ ] Viet initial migration
- [ ] Thiet ke database indexes (btree, gin cho text search)

## References

- .ai/design/ERD.md
- .ai/design/Database.md
- Repository.md
