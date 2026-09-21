# Docker — Backend Containerization

## Purpose

Huong dan Dockerfile va Docker configuration cho backend service.

## Scope

Multi-stage Dockerfile: builder stage + runtime stage. Docker Compose integration.

## TODO

- [ ] Viet multi-stage Dockerfile (python:3.11-slim)
- [ ] Toi uu image size (pip install --no-cache-dir)
- [ ] Implement health check endpoint (/health)
- [ ] Configure environment variables qua .env
- [ ] Setup non-root user trong container (security best practice)
- [ ] Viet .dockerignore

## References

- docker/README.md
- docker/Compose.md
