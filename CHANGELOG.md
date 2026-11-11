# CHANGELOG

## [1.0.0] — Pending

### Phase 1 — Correctness Core (done)
- Unified idempotency: single `idempotency_keys` table with `UNIQUE(user_id, key)`, `request_body_hash`, response fields; removed redundant `orders.idempotency_key` column
- Checkout: fast-path idempotency check, post-lock re-check; products and inventory locked in ascending id order; conditional stock decrement via `UPDATE ... WHERE quantity >= n` with rowcount check
- Order status state machine: pending→paid→shipped→completed, plus cancellation; enforced in service layer
- Money as NUMERIC(12,2) with CHECK constraints; composite index on `orders(user_id, created_at)`
- Product soft-delete (`is_active=false`) instead of hard delete, preserving order/cart history
- Product search (`search` param, ILIKE on name/description) and pagination (limit/offset, default 20, max 100)
- Admin stock adjustment endpoint with `inventory_audit_log` audit rows
- Configurable low-stock threshold (`VAULTCORE_LOW_STOCK_THRESHOLD` env, default 5)
- Alembic migrations regenerated on clean DB; 12 tables
- Tests: 6 passed

### Phase 2 — Security & Auth (planned)
- Replace python-jose/passlib with PyJWT + argon2-cffi
- SECRET_KEY fail-fast at startup (missing, <32 chars, or default value)
- CORS origins from config (no wildcard with credentials)
- Login rate limiting per IP and per email
- Password policy (min 8 chars)
- DB-backed role loading on every request (revoked admin loses access immediately)

### Phase 3 — API Quality (planned)
- Unified error format, request-ID middleware, structured JSON logs, generic 500 handler
- Thin routers, pydantic-settings config, OpenAPI examples
- Pagination on admin list endpoints

### Phase 4 — Tests (planned)
- Deterministic barrier concurrency tests (50 buyers/stock 10, 20 same-key, deadlock)
- Price tampering, RBAC, migration tests, unit tests for pure logic

### Phase 5 — Frontend (planned)
- Strict TypeScript, typed API client, loading/empty/error states
- Idempotency key in sessionStorage, in-flight submit disable

### Phase 6 — Docs/CI/Release (planned)
- README, ADRs, RUNBOOK, SECURITY, INTERVIEW_NOTES, PowerShell scripts, GitHub Actions, v1.0.0 tag

### Phase 5 — Frontend (done)
- Strict TypeScript, no `any` types in API client
- Typed API client module with structured error handling (ApiError class)
- Product catalog with server-side search, pagination (limit/offset, default 20, max 100)
- Cart page with in-flight disable on quantity/remove buttons, idempotency key in sessionStorage
- Checkout page with sessionStorage idempotency key, retry with new key, duplicate request protection
- Admin dashboard with stats, low-stock alerts, order management
- Admin product management with create form
- Admin order management with status update (state machine enforced)
- Admin product form with validation
- Navbar with JWT-based admin detection (decodes JWT for UI-only gating; backend enforces RBAC)
- Tests: Vitest + React Testing Library for API client, cart page, checkout page
