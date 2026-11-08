# BrandCanon AI — Production Deployment & Operations Runbook

## Overview
BrandCanon AI is an enterprise-ready intelligent brand governance SaaS platform. This document covers production deployment orchestration, container management, database migrations, backup/restore procedures, healthchecks, and disaster recovery.

---

## 1. Architecture Topology
- **Web Frontend**: Next.js 14 (App Router) in standalone production mode (`port 3000`).
- **API Backend**: FastAPI / Python 3.11 with Uvicorn (`port 8000`).
- **Relational DB & Vector Store**: PostgreSQL 16 + pgvector extension (`port 5432`).
- **In-Memory Cache & Lock Store**: Redis 7 Alpine (`port 6379`).
- **Storage**: Local filesystem or S3-compatible private object store.

---

## 2. Quickstart with Docker Compose

### Step 1: Environment Variables
Create the production environment file:
```bash
cp .env.example .env
# Edit .env and supply production secrets (JWT_SECRET, DATABASE_URL, GEMINI_API_KEY)
```

### Step 2: Build & Start All Services
```bash
docker compose up -d --build
```

### Step 3: Verify Service Health
```bash
# Check container status
docker compose ps

# Inspect backend health endpoint
curl -s http://localhost:8000/api/v1/health | jq .
```
Expected output:
```json
{
  "status": "healthy",
  "app": "BrandCanon AI",
  "environment": "production",
  "version": "1.0.0"
}
```

---

## 3. Database Migrations & Seeding

### Execute Migrations
Alembic automatically runs on container startup via the backend entrypoint:
```bash
docker compose exec backend alembic upgrade head
```

### Seed Initial Admin Workspace (Optional / First-time setup)
```bash
docker compose exec backend python seed.py
```

### Rollback Migration (One step)
```bash
docker compose exec backend alembic downgrade -1
```

---

## 4. Backup & Disaster Recovery

### Automated Database Backup
Run a snapshot backup of the PostgreSQL container:
```bash
docker compose exec db pg_dump -U brandcanon brandcanon_db > backup_$(date +%Y%m%d_%H%M%S).sql
```

### Restoring from Backup
```bash
docker compose exec -T db psql -U brandcanon -d brandcanon_db < backup_file.sql
```

---

## 5. Security & Network Hardening
1. **Security Headers**: Injected automatically by FastAPI middleware:
   - `X-Content-Type-Options: nosniff`
   - `X-Frame-Options: DENY`
   - `X-XSS-Protection: 1; mode=block`
   - `Strict-Transport-Security: max-age=31536000; includeSubDomains`
   - `Referrer-Policy: strict-origin-when-cross-origin`
2. **Tenant Isolation**: Strict organization-scoping enforced on all models and queries via `get_current_tenant` dependency.
3. **Role-Based Access Control (RBAC)**: Distinct permissions enforced for `ADMIN`, `BRAND_MANAGER`, `CREATOR`, and `REVIEWER`.

