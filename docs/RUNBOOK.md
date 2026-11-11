# VAULTCORE Runbook

## Prerequisites
- Python 3.14+ with uv
- Node.js 26+ with npm
- PostgreSQL 16 running locally

## Backend Setup

### 1. Create the database
```bash
psql -U postgres -c "create database vaultcore;"
```

### 2. Configure environment
```bash
cd E:\MY GOAL\PROJECTS\VAULTCORE\backend
cp .env.example .env
# Edit .env: set SECRET_KEY (32+ chars, not a default value)
```

### 3. Install dependencies
```bash
uv sync
```

### 4. Run migrations
```bash
uv run alembic upgrade head
```

### 5. Seed demo data
```bash
PYTHONPATH=. uv run scripts/seed.py
```
Creates: admin@vaultcore.local / admin123

### 6. Start the server
```bash
uv run uvicorn app.main:app --reload --port 8000
```
API docs: http://localhost:8000/docs

## Frontend Setup

### 1. Install dependencies
```bash
cd E:\MY GOAL\PROJECTS\VAULTCORE\frontend
npm install
```

### 2. Start dev server
```bash
npm run dev
```
Frontend: http://localhost:5173

## Running Tests

### Backend
```bash
cd E:\MY GOAL\PROJECTS\VAULTCORE\backend
export SECRET_KEY="your-32-char-secret"
uv run pytest
```

### Frontend
```bash
cd E:\MY GOAL\PROJECTS\VAULTCORE\frontend
npm install -D vitest @testing-library/react @testing-library/jest-dom jsdom
npm test
```

## Reset Database
```bash
psql -U postgres -d vaultcore -c "DROP SCHEMA public CASCADE; CREATE SCHEMA public;"
uv run alembic upgrade head
PYTHONPATH=. uv run scripts/seed.py
```

## Common Issues

| Issue | Fix |
|-------|-----|
| SECRET_KEY missing | Set SECRET_KEY env var (32+ chars) |
| Port 8000 in use | Kill existing uvicorn process or use --port 8001 |
| ModuleNotFoundError: app | Run from backend/ directory with PYTHONPATH=. |
| Alembic revision errors | Delete alembic/versions/*.py, regenerate |

## Demo Credentials
- Admin: admin@vaultcore.local / admin123
- Customer: Register at /register
