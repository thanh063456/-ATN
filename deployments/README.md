# Deployments — Infrastructure va Deployment Config

## Purpose

Cau hinh va script cho viec trien khai len cac moi truong khac nhau.

## Scope

Moi truong: development (Docker Compose local), staging (VPS), production. Config: nginx, CI/CD.

## TODO

- [ ] Viet nginx.conf cho production (reverse proxy + SSL termination)
- [ ] Viet docker-compose.prod.yml (production overrides)
- [ ] Thiet lap CI/CD pipeline (GitHub Actions: test + build + deploy)
- [ ] Viet deployment checklist (pre-deploy, deploy, post-deploy verification)
- [ ] Huong dan SSL certificate voi Let's Encrypt va Certbot
- [ ] Huong dan monitoring setup (Prometheus + Grafana + Alertmanager)

## References

- docker/Deployment.md
- scripts/Deploy.md
- docker/README.md
