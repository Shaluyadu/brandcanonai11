# BrandCanon AI — Enterprise-Ready Intelligent Brand Governance SaaS

> **BrandCanon AI** is an intelligent pre-publication assurance and content compliance SaaS platform. It serves as an evidence-grounded brand governance engine for marketing teams, content creators, brand managers, and legal reviewers.

---

## 🚀 Implemented Capabilities (Phases 1–7 Verified)

### 1. Multi-Tenant Workspace & Security Isolation (Phase 1)
- **Tenant Scoping**: All queries, ORM relationships, services, and APIs are scoped to an authenticated organization workspace (`X-Organisation-Id` header resolution).
- **Zero Cross-Tenant Leakage**: Tested and verified that users belonging to Organization A cannot access Organization B's workspace or members (enforces `403 FORBIDDEN: TENANT_ACCESS_FORBIDDEN`).
- **Cryptographic Security**: PBKDF2-HMAC-SHA256 password hashing with salt, constant-time comparison, and RFC 7519 HS256 JWT sessions.

### 2. Role-Based Access Control (RBAC) (Phase 1)
Enforces a 4-tier enterprise role matrix across backend API dependencies and frontend UI:
1. **Workspace Admin**: Full authority over workspace settings, inviting members, role assignment, and audit logs.
2. **Brand Owner / Brand Manager**: Authority over brand guidelines, verified claims, terminology rules, and human knowledge approvals.
3. **Content Creator**: Authority over permitted submissions, running reviews, and accepting/dismissing suggestions.
4. **Reviewer (Legal / Compliance)**: Authority over review queue, evaluating evidence, and recording final approval or rejection decisions.

### 3. Brand Knowledge Hub & Ingestion (Phase 2)
- **Guidelines Ingestion**: Document parser supporting `.docx` and `.pdf` files with metadata extraction.
- **Brand Facts & Claims**: Lifecycle management for verified enterprise brand claims with manager approval flows.
- **Terminology Engine**: Whole-word and phrase deterministic matchers with case sensitivity options for preferred and prohibited terms.

### 4. Content Submissions & AI Governance Review (Phases 3–5)
- **Submission Engine**: Multi-channel draft management with full revision history.
- **Agentic AI Reviewer**: Multi-layer compliance engine combining deterministic terminology rules with semantic evidence grounding.
- **Interactive Review Studio**: Split-screen editor allowing creators to review suggestions, accept/reject diffs, and submit for compliance approval.
- **Compliance Queue**: Dedicated queue for Legal/Compliance reviewers to inspect evidence and issue final approval decisions.

### 5. Empirical Governance Analytics (Phase 6)
- Compliance score aggregation and recurring violation category heatmaps.
- Channel-by-channel risk distribution and team throughput benchmarks.

### 6. Responsive Next.js Enterprise Design System & Deployment (Phase 7)
- Built with **Next.js 14 (App Router)**, **TypeScript**, **Tailwind CSS**, and **Lucide icons**.
- Clean, light-first enterprise design with restrained orange identity accent (`#EA580C`), dark navy typography (`#0F172A`), and clear status indicators.
- **Role-aware collapsible navigation**: Dynamically surfaces permitted tools per role.
- **Dynamic Quick-Login selector**: Pre-configured for NovaTech demonstration personas.
- **Production Docker Compose & Render**: Ready for full-stack Docker deployment and Render Blueprint hosting.

---

## 👥 Fictional Demonstration Accounts (NovaTech)

Pre-seeded into the database for immediate testing:

| Role | Email | Password | Primary Authority |
| :--- | :--- | :--- | :--- |
| **Workspace Admin** | `admin@novatech.io` | `NovaTech@2026!` | Workspace configuration, member roles, audit logs |
| **Brand Manager** | `brand@novatech.io` | `NovaTech@2026!` | Brand guidelines, approved facts, terminology |
| **Content Creator** | `creator@novatech.io` | `NovaTech@2026!` | Content drafting & pre-publication reviews |
| **Reviewer / Legal** | `reviewer@novatech.io` | `NovaTech@2026!` | Review queue, approving or rejecting submissions |

---

## 🛠️ Local Development & Execution Commands

### Prerequisites
- Node.js 18+ (tested with Node v26)
- Python 3.10+ (tested with Python 3.14)

### 1. Backend Setup & Run

```bash
cd backend

# (Optional) Activate your Python virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run initial database migration & seed NovaTech demo accounts
alembic upgrade head
python3 seed.py

# Start the FastAPI development server (runs on port 8000)
python3 -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

- API Base URL: `http://127.0.0.1:8000`
- Interactive OpenAPI Docs: `http://127.0.0.1:8000/docs`
- ReDoc Documentation: `http://127.0.0.1:8000/redoc`

### 2. Frontend Setup & Run

```bash
cd frontend

# Install dependencies (already installed)
npm install

# Run the development server (runs on port 3000)
npm run dev

# Or build and test the production bundle
npm run build
npm start
```

- Web Application: `http://localhost:3000`

### 3. Running Automated Tests

```bash
# Run backend pytest suite (62 test cases across all modules, 100% pass)
cd backend
python3 -m pytest -v

# Run frontend TypeScript type checking
cd frontend
npm run typecheck
```

---

## ☁️ Render Blueprint Deployment

Deploy both Frontend and Backend seamlessly on Render via the included `render.yaml` blueprint:

1. Sign in to [Render.com](https://render.com) and go to **Blueprints**.
2. Click **New Blueprint Instance** and connect this repository (`BrandCanon_AI`).
3. Render automatically provisions:
   - **`brandcanon-backend`**: FastAPI Web Service with Python 3.11, automatic database migrations, and seed data.
   - **`brandcanon-frontend`**: Next.js 14 Web Service connected to the backend.
4. Click **Apply** to deploy both services with one click.

---

## 🚢 Docker Compose Production Setup

To run the complete production stack (PostgreSQL + pgvector, Redis, FastAPI Backend, and Next.js Frontend):

```bash
docker compose up --build
```

---

## 📋 Status Overview: Phases 1–7 Complete

| Module / Milestone | Status | Description |
| :--- | :---: | :--- |
| **Phase 1: Foundation & RBAC** | ✅ Complete | Multi-tenant auth, workspace onboarding, 4-tier RBAC, DB migrations, tenant isolation, and audit logging. |
| **Phase 2: Brand Knowledge Hub** | ✅ Complete | Guidelines ingestion (DOCX/PDF), claim extraction, verified facts lifecycle, terminology rule matching, and manager approvals. |
| **Phase 3: Content Submissions** | ✅ Complete | Submission manager, multi-channel drafting, version history, automated rule checks, and async processing. |
| **Phase 4: Agentic AI Review** | ✅ Complete | Review orchestrator, deterministic terminology matcher, pgvector/mock embeddings RAG, and evidence grounding layer. |
| **Phase 5: Governance & Approvals** | ✅ Complete | Split-screen Review Studio, creator revision workflows, reviewer decision queues, and audit trail generation. |
| **Phase 6: Governance Analytics** | ✅ Complete | Empirical compliance metrics, recurring violation pattern heatmaps, team benchmarks, and performance dashboards. |
| **Phase 7: Deployment & Hardening** | ✅ Complete | Production Docker Compose (Postgres, pgvector, Redis), Render Blueprint deployment, TLS/security hardening, and 62 passing tests. |

# BrandCanon_AI
