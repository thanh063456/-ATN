# Docker Compose — Cau hinh chi tiet

## Purpose

Chi tiet cau hinh docker-compose.yml: service definitions, env vars, health checks.

## Scope

Giai thich tung service trong docker-compose.yml, best practices, common issues.

## TODO

- [ ] Document tung service: image, ports, volumes, env vars
- [ ] Huong dan health check configuration cho moi service
- [ ] Huong dan service dependencies (depends_on + condition: service_healthy)
- [ ] Huong dan restart policies (unless-stopped cho production)
- [ ] Huong dan resource limits (deploy.resources.limits cho production)
- [ ] Document environment variable mapping (.env -> service env)

## References

- docker-compose.yml (root)
- Network.md
- Volumes.md
- .env.example
