# Deployment Diagram — Sơ đồ Triển khai

## Purpose

Mô tả kiến trúc triển khai hạ tầng phần cứng, các container Docker, các nút (Nodes), mạng nội bộ và cổng giao tiếp cho hệ thống Student-Document-OCR.

## Scope

Kiến trúc triển khai Production / Staging dựa trên Docker Compose stack.

---

## 1. Topo Triển khai Container (Docker Compose Stack)

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                                 HOST SERVER / VM NODE                                  │
│                          (Ubuntu 22.04 LTS / Docker Engine)                            │
│                                                                                        │
│   ┌────────────────────────────────────────────────────────────────────────────────┐   │
│   │                        PUBLIC NETWORK / INTERNET                               │   │
│   └───────────────────────────────────────┬────────────────────────────────────────┘   │
│                                           │ HTTPS (Port 443) / HTTP (Port 80)          │
│                                           ▼                                            │
│   ┌────────────────────────────────────────────────────────────────────────────────┐   │
│   │                     REVERSE PROXY LAYER (Nginx Container)                      │   │
│   │   - Nginx (Port 80 -> 3000 / 8000)                                             │   │
│   │   - SSL/TLS Termination                                                        │   │
│   └───────────────────┬──────────────────────────────────────┬─────────────────────┘   │
│                       │ Port 3000                            │ Port 8000               │
│                       ▼                                      ▼                         │
│   ┌───────────────────────────────┐      ┌─────────────────────────────────────────┐   │
│   │   FRONTEND CONTAINER          │      │    BACKEND SERVICE CONTAINER            │   │
│   │   - React SPA (Static Build)  │      │    - FastAPI / Uvicorn (Port 8000)      │   │
│   │   - Nginx Web Server          │      │    - Python 3.11 Runtime                │   │
│   └───────────────────────────────┘      └───────────────────┬─────────────────────┘   │
│                                                              │                         │
│                                           ┌──────────────────┴─────────────────────┐   │
│                                           │  DOCKER INTERNAL NETWORK (ocr_net)     │   │
│                                           └──────────────────┬─────────────────────┘   │
│                                                              │                         │
│         ┌───────────────────────┬────────────────────────────┼─────────────────────────┼──────────────────────┐
│         │                       │                            │                         │                      │
│         ▼                       ▼                            ▼                         ▼                      ▼
│ ┌───────────────┐       ┌───────────────┐            ┌───────────────┐         ┌───────────────┐      ┌───────────────┐
│ │  CELERY       │       │  POSTGRESQL   │            │ ELASTICSEARCH │         │ MINIO OBJECT  │      │ REDIS BROKER  │
│ │  WORKER       │       │  CONTAINER    │            │ CONTAINER     │         │ STORAGE       │      │ CONTAINER     │
│ │  - VietOCR    │       │ - Postgres 15 │            │ - ES 8.12.0   │         │ - MinIO S3    │      │ - Redis 7     │
│ │  - PyTorch    │       │ - Port 5432   │            │ - Port 9200   │         │ - Port 9000   │      │ - Port 6379   │
│ └───────────────┘       └───────────────┘            └───────────────┘         └───────────────┘      └───────────────┘
│                                 │                            │                         │
│                                 ▼                            ▼                         ▼
│                         ┌───────────────┐            ┌───────────────┐         ┌───────────────┐
│                         │ Postgres Vol  │            │ ES Data Vol   │         │ MinIO Vol     │
│                         │ (Persistent)  │            │ (Persistent)  │         │ (Persistent)  │
│                         └───────────────┘            └───────────────┘         └───────────────┘
└────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Danh sách Containers & Tài nguyên Cấu hình

| Service Container | Image Base | Internal Port | External Port | Volume Mount | CPU/RAM Recommendation |
|-------------------|------------|---------------|---------------|--------------|------------------------|
| `nginx_proxy` | `nginx:1.25-alpine` | 80, 443 | 80, 443 | `./docker/nginx.conf` | 0.5 Core, 256MB RAM |
| `frontend` | Custom (Node->Nginx) | 80 | 3000 (dev) | N/A (Static Files) | 0.5 Core, 256MB RAM |
| `backend` | Custom (`python:3.11-slim`) | 8000 | 8000 | `./backend:/app` (dev) | 1.0 Core, 1GB RAM |
| `celery_worker` | Custom (`python:3.11-slim`) | N/A | N/A | `./models:/app/models` | 2.0 Cores, 2GB RAM |
| `postgres` | `postgres:15-alpine` | 5432 | 5432 (dev) | `postgres_data:/var/lib/postgresql/data` | 1.0 Core, 1GB RAM |
| `elasticsearch` | `elasticsearch:8.12.0` | 9200 | 9200 (dev) | `es_data:/usr/share/elasticsearch/data` | 1.0 Core, 2GB RAM |
| `minio` | `minio/minio:latest` | 9000, 9001 | 9000, 9001 | `minio_data:/data` | 0.5 Core, 512MB RAM |
| `redis` | `redis:7-alpine` | 6379 | 6379 (dev) | `redis_data:/data` | 0.5 Core, 256MB RAM |
| `flower` | Custom (`python:3.11-slim`) | 5555 | 5555 (dev) | N/A | 0.2 Core, 128MB RAM |

---

## 3. Mạng & Chuẩn Giao tiếp (Networking Spec)

- **Docker Bridge Network**: Khởi tạo mạng nội bộ tên `ocr_net`. Tất cả container kết nối vào chung một subnet.
- **Port Binding (Production)**:
  - Chỉ mở duy nhất cổng **80 / 443** (Nginx Proxy) ra ngoài Internet.
  - Các cổng 5432 (PostgreSQL), 9200 (ES), 6379 (Redis), 9000 (MinIO) **chỉ cho phép truy cập nội bộ** trong `ocr_net`.
- **Environment Variables**: Tất cả cấu hình nhạy cảm (DB Passwords, JWT Secret, MinIO Keys) được quản lý tập trung qua file `.env`.

---

## TODO

- [ ] Hoàn thiện file `docker-compose.yml` gốc và `docker-compose.prod.yml`.
- [ ] Viết hướng dẫn triển khai Production từng bước trong `docker/Deployment.md`.

## References

- ARCHITECTURE.md
- docker-compose.yml
- TECH_STACK.md
