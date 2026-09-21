# Docker — Containerization Guide

## Purpose

Hướng dẫn toàn bộ Docker setup cho hệ thống Student-Document-OCR:
services, networking, volumes, và cấu hình cho development vs production.

## Scope

Docker Compose stack gồm **8 services**:

| Service | Image | Port | Mô tả |
|---------|-------|------|-------|
| `backend` | custom (FastAPI) | 8000 | REST API |
| `frontend` | custom (nginx) | 3000 | React SPA |
| `postgres` | postgres:15-alpine | 5432 | Relational DB |
| `elasticsearch` | elastic:8.12.0 | 9200 | Search engine |
| `minio` | minio/minio | 9000/9001 | Object storage |
| `redis` | redis:7-alpine | 6379 | Cache + Queue broker |
| `celery_worker` | custom (backend) | — | Async OCR tasks |
| `flower` | custom (backend) | 5555 | Celery monitor UI |

## Khởi động nhanh

```bash
# Development stack
docker compose up -d

# Xem logs tất cả services
docker compose logs -f

# Chỉ backend + postgres + redis
docker compose up -d backend postgres redis

# Dừng và xóa containers (giữ volumes)
docker compose down

# Dừng VÀ xóa volumes (mất data!)
docker compose down -v
```

## TODO

- [ ] Viết `backend/Dockerfile` (multi-stage: python:3.11-slim)
- [ ] Viết `frontend/Dockerfile` (multi-stage: node → nginx)
- [ ] Viết `backend/.dockerignore`
- [ ] Viết `frontend/.dockerignore`
- [ ] Thêm health checks vào tất cả services trong docker-compose.yml
- [ ] Viết `docker-compose.prod.yml` (production overrides)
- [ ] Viết `docker/nginx.conf` (reverse proxy + SSL)
- [ ] Test toàn bộ stack end-to-end trên máy sạch

## References

- Compose.md
- Network.md
- Volumes.md
- Deployment.md
- docker-compose.yml (root)
- .env.example
- deployments/README.md
