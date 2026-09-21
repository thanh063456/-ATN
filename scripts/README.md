# Scripts — Utility Scripts

## Purpose

Tập hợp các script tiện ích cho development, data processing, deployment và maintenance.
Tất cả script đều phải có `--help` flag và usage examples trong docstring.

## Scope

Gồm 4 nhóm script, mỗi nhóm được document trong file `.md` tương ứng:

| File | Nội dung |
|------|----------|
| `Dataset.md` | Scripts thu thập, làm sạch, split và augment dataset |
| `Training.md` | Scripts chạy training, resume, export model |
| `Deploy.md` | Scripts deploy, rollback, health check, backup |
| _(planned)_ `seed_db.py` | Tạo user admin và data mẫu |
| _(planned)_ `create_es_index.py` | Tạo Elasticsearch index (idempotent) |
| _(planned)_ `setup_env.sh` | Copy `.env.example` → `.env`, kiểm tra dependencies |

> **Lưu ý**: Các file `_*.py` và `_*.ps1` (tiền tố underscore) là scripts nội bộ
> và được liệt vào `.gitignore` — không commit lên repository.

## TODO

- [ ] Viết `setup_env.sh` (tạo .env từ .env.example, check Python/Docker version)
- [ ] Viết `seed_db.py` (tạo user admin và data mẫu cho dev)
- [ ] Viết `create_es_index.py` (tạo ES index mapping, idempotent)
- [ ] Viết `process_dataset.py` (chạy preprocessing pipeline đầy đủ)
- [ ] Viết `backup_db.sh` (pg_dump + compress + upload to MinIO)
- [ ] Viết `health_check.sh` (kiểm tra tất cả services trả về OK)
- [ ] Đảm bảo tất cả script có `--help` và ví dụ sử dụng

## References

- Dataset.md
- Training.md
- Deploy.md
- Makefile
- docker/Deployment.md
