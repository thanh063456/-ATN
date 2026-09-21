# Deploy Scripts — Script trien khai

## Purpose

Mo ta va huong dan cac script trien khai he thong: build, deploy, rollback, backup.

## Scope

Scripts: deploy.sh, rollback.sh, health_check.sh, backup.sh, create_es_index.py.

## TODO

- [ ] Viet deploy.sh (git pull + docker compose up -d --build)
- [ ] Viet rollback.sh (quay ve version truoc)
- [ ] Viet health_check.sh (kiem tra tat ca services tra ve OK)
- [ ] Viet backup_db.sh (pg_dump + tar.gz + upload MinIO)
- [ ] Viet create_es_index.py (idempotent - chay nhieu lan van OK)
- [ ] Document tung script voi usage examples

## References

- docker/Deployment.md
- Makefile
