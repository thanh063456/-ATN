# Docker Volumes — Quan ly du lieu

## Purpose

Mo ta Docker volume strategy: named volumes, bind mounts, data persistence, backup.

## Scope

Named volumes: postgres_data, elasticsearch_data, minio_data, redis_data.

## TODO

- [ ] Document tat ca named volumes va muc dich
- [ ] Huong dan backup postgres_data (pg_dump)
- [ ] Huong dan backup elasticsearch_data (snapshot API)
- [ ] Huong dan backup minio_data (mc mirror)
- [ ] Huong dan reset toan bo volume (clean start)
- [ ] CANH BAO: Xoa volume se mat toan bo du lieu production

## References

- Compose.md
- Deployment.md
