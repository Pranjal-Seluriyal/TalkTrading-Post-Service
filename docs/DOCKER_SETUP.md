# Docker Setup & Operation Guide for Post Service

## Prerequisites
- Docker Engine & Docker Compose (v2+)
- Port `8004` (host) available
- Clean checkout of `post-service-feature-post-module`

---

## 1. Environment Configuration

Copy the example environment template:
```bash
cp .env.example .env
```
Ensure `SECRET_KEY` is configured with a secure random string (at least 32 characters in production) and `POSTGRES_PASSWORD` is set.

---

## 2. Docker Compose Commands

### Validate Compose Configuration
```bash
docker compose config
```

### Build Image
```bash
docker compose build
```

### Start Services in Background
```bash
docker compose up -d
```
This starts both `post_service_postgres` and `post_service_app`. The application automatically waits for PostgreSQL readiness and applies Alembic migrations on startup via `docker-entrypoint.sh`.

### Check Running Containers
```bash
docker compose ps
```

### Inspect Container Logs
```bash
docker compose logs -f post-service
```
To view database logs:
```bash
docker compose logs -f postgres
```

### Verify Container Health
```bash
curl -f http://localhost:8004/api/v1/health/live
curl -f http://localhost:8004/api/v1/health/ready
```

### Run Migrations Manually (if required)
```bash
docker compose exec post-service alembic upgrade head
```

### Stop Services
```bash
docker compose down
```

### Reset Disposable Development Data
To completely purge PostgreSQL and local media volumes:
```bash
docker compose down -v
```
