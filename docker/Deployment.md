# Deployment — Huong dan trien khai

## Purpose

Huong dan deploy len production: prerequisites, steps, health check, rollback.

## Scope

Production deployment: build images, push to registry, pull on server, run with prod config.

## TODO

- [ ] Viet production docker-compose.prod.yml
- [ ] Huong dan setup server (Ubuntu 22.04 LTS)
- [ ] Huong dan SSL/TLS voi Let's Encrypt + Certbot + Nginx
- [ ] Huong dan database backup (pg_dump + cron)
- [ ] Huong dan rollback strategy
- [ ] Huong dan log monitoring (docker compose logs + Grafana)

## References

- Compose.md
- Network.md
- deployments/README.md
