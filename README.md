# VAULTCORE — Secure, Transaction-Safe E-Commerce Management Platform

Full-stack e-commerce platform with transaction-safe order processing (simplified Amazon/Flipkart MVP). Built as a portfolio-grade SDE project with engineering depth you can defend in an interview.

## Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| Frontend | React + TypeScript + Tailwind CSS + Vite | Storefront + Admin Dashboard |
| Backend | FastAPI + Python 3.14 | REST API, business logic |
| ORM / DB | SQLAlchemy 2.0 + Alembic + PostgreSQL 16 | Relational data, ACID transactions |
| Auth | JWT (PyJWT) + Argon2id (argon2-cffi) | Stateless auth, password hashing |
| Tests | Pytest (backend) + Vitest + RTL (frontend) | 13 backend + frontend component tests |
| CI | GitHub Actions | ruff, mypy, backend tests, frontend build |

## Layout

```
VAULTCORE/
├── backend/            # FastAPI app, models, services, routers, tests, migrations
├── frontend/           # Vite + React + TypeScript + Tailwind SPA
├── scripts/            # dev.ps1, test.ps1 (PowerShell)
├── docs/               # ARCHITECTURE, RUNBOOK, SECURITY, TESTING, ROADMAP, INTERVIEW_NOTES, ADRs
└── .github/workflows/  # CI: ruff, mypy, backend tests (PostgreSQL service), frontend build
```

## Backend Quickstart

```powershell
cd E:\MY GOAL\PROJECTS\VAULTCORE\backend
uv sync
cp .env.example .env          # edit SECRET_KEY (32+ chars)
uv run alembic upgrade head
PYTHONPATH=. uv run scripts/seed.py   # creates admin@vaultcore.local / admin123
uv run uvicorn app.main:app --reload --port 8000
```

API docs: http://localhost:8000/docs

Run tests:
```powershell
cd backend
export SECRET_KEY="your-32-char-secret"
uv run pytest          # 13 tests passing
```

## Frontend Quickstart

```powershell
cd E:/MY GOAL\PROJECTS\VAULTCORE\frontend
npm install
npm run dev        # http://localhost:5173 (proxies /api to localhost:8000)
npm run build
```

## Key Engineering (Interview-Ready)

| Concept | Implementation |
|---------|---------------|
| **ACID order processing** | Checkout runs in one PostgreSQL transaction; all-or-nothing |
| **Row-level locking** | `SELECT ... FOR UPDATE` on product + inventory rows, ascending ID order to prevent deadlocks |
| **Idempotency** | `idempotency_keys` table with `UNIQUE(user_id, key)` + SHA-256 body hash; same key returns same order |
| **Conditional stock decrement** | `UPDATE inventory SET quantity = quantity - n WHERE product_id = ? AND quantity >= n`; rowcount checked |
| **Backend-validated pricing** | Order totals computed from DB prices; frontend prices ignored |
| **RBAC** | `customer` / `admin` roles loaded from DB on every request |
| **Order state machine** | pending→paid→shipped→completed, plus cancellation; enforced in service layer |
| **Soft delete** | Products set `is_active=false`, preserving order/cart history |
| **Security** | SECRET_KEY fail-fast at startup, CORS from config (no wildcard), login rate limiting (5 fails/5min → 429) |

## Demo Credentials

- Admin: `admin@vaultcore.local` / `admin123`
- Customer: register at `/register`

## Documentation

| Doc | Contents |
|-----|----------|
| `docs/ARCHITECTURE.md` | System diagram, data flow, module responsibilities |
| `docs/INTERVIEW_NOTES.md` | 5 hardest problems explained for interview defense |
| `docs/RUNBOOK.md` | Setup, seed, test, reset database, common errors |
| `docs/SECURITY.md` | Auth, authorization, rate limiting, CORS, data protection |
| `docs/TESTING.md` | Backend + frontend test strategy |
| `docs/ROADMAP.md` | Postponed features (V2) |
| `docs/adr/` | ADR 0001 Argon2, 0002 JWT, 0003 Idempotency, 0004 Token storage |

## Scripts

| Script | Purpose |
|--------|---------|
| `scripts/dev.ps1` | Start backend with env vars (PowerShell) |
| `scripts/test.ps1` | Run backend tests (PowerShell) |

## CI

GitHub Actions runs on every push: `ruff` lint, `mypy` type check, backend tests against a PostgreSQL service container, frontend build.
