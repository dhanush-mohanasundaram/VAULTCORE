# VAULTCORE — Secure, Transaction-Safe E-Commerce Management Platform

Full-stack e-commerce platform with transaction-safe order processing (simplified Amazon/Flipkart MVP).

## Stack

- Frontend: React + TypeScript + Tailwind CSS (Vite)
- Backend: FastAPI + Python (SQLAlchemy, Alembic, JWT/Argon2)
- Database: PostgreSQL
- Tests: Pytest

## Layout

```
VAULTCORE/
├── backend/            # FastAPI app, models, services, routers, tests, migrations
└── frontend/           # Vite + React + TypeScript + Tailwind SPA
```

## Backend quickstart

```powershell
cd backend
uv sync                 # or uv add <deps> if lockfile missing
cp .env.example .env    # optional; defaults point at local PostgreSQL
uv run alembic upgrade head
uv run uvicorn app.main:app --reload
```

API docs: http://localhost:8000/docs

Seed demo data (creates `admin@vaultcore.local` / `admin123`):

```powershell
uv run scripts/seed.py
```

Run tests:

```powershell
uv run pytest
```

## Frontend quickstart

```powershell
cd frontend
npm install
npm run dev        # http://localhost:5173, proxies /api to localhost:8000
npm run build
```

## Key engineering implemented

- **ACID order processing**: checkout runs inside one PostgreSQL transaction.
- **Row-level locking**: products and inventory rows are locked with `SELECT ... FOR UPDATE` during checkout, so concurrent buyers cannot oversell stock.
- **Idempotency**: `IdempotencyKey` table makes repeated checkout with the same key return the existing order — no duplicates.
- **Backend-validated pricing**: order totals are computed from database prices, never trusted from the frontend.
- **RBAC**: `customer` / `admin` roles enforced with FastAPI dependencies on every mutating endpoint.
- **Tests**: registration/login, product admin RBAC, cart, happy-path checkout, idempotency, 20-way concurrent checkout (exactly one success, no negative stock), admin stats and low-stock.

## Demo accounts

- Admin: `admin@vaultcore.local` / `admin123`
- Customers: register via the storefront.
