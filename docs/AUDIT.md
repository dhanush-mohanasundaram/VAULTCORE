# VAULTCORE — Phase 0 Audit

Generated from reading the current repo at `E:\MY GOAL\PROJECTS\VAULTCORE`.

## Known issues (a–k)

| # | Issue | File(s) | Severity | Phase |
|---|---|---|---|---|
| a | **Idempotency race**: `checkout()` checks `idempotency_keys` table *before* taking row locks. Two identical requests can both pass; the second waits on the lock, then finds the cart empty instead of returning the first order. | `backend/app/services/order_service.py` lines 7–16 | Critical | 1 |
| b | **Two idempotency mechanisms**: `orders.idempotency_key` column AND `idempotency_keys` table. Redundant. Not scoped per user (`UNIQUE(user_id, key)` missing). No request-body hash. No 422 on same key + different body. | `backend/app/models.py` lines 130, 151–158; `backend/app/services/order_service.py` line 70 | Critical | 1 |
| c | **Deadlock risk**: `with_for_update()` on products and inventory are two separate queries without `order_by(id)`. PostgreSQL acquires row locks in whatever order the scan returns rows — not guaranteed ascending id. Two transactions touching the same rows in different scan order can deadlock. | `backend/app/services/order_service.py` lines 26–39 | Critical | 1 |
| d | **Stock decrement not conditional**: `inv.quantity = inv.quantity - qty` executed in Python after loading the row, not `UPDATE ... SET quantity = quantity - :n WHERE product_id = :id AND quantity >= :n` with rowcount check. `CHECK (quantity >= 0)` exists but is only a second line of defence. | `backend/app/services/order_service.py` lines 68–69; `backend/app/models.py` line 92 | Critical | 1 |
| e | **No order status state machine**: `orders.status` is a free-text `String(50)`. Any value can be written. No enforced transitions (pending → paid → shipped → completed, plus cancellation). | `backend/app/models.py` line 128; `backend/app/services/admin_service.py` line 50; `backend/app/api/admin.py` line 48 | High | 1 |
| f | **Roles partially trusted from JWT**: `require_role()` does re-query the DB (good), but `get_current_user()` returns the user without re-verifying roles are still assigned, and the JWT itself embeds `roles`. A revoked admin could still hold a valid JWT containing "admin". Authorization decisions must load roles from the DB on every request. | `backend/app/deps.py` lines 20–38; `backend/app/security.py` line 23 | High | 2 |
| g | **Unmaintained deps**: `python-jose` and `passlib` are poorly maintained. Replace with PyJWT (explicit algorithm allow-list) and `argon2-cffi`. | `backend/app/security.py` lines 2–9; `backend/pyproject.toml` lines 13, 18 | High | 2 |
| h | **Seed endpoint with hardcoded admin password**: `POST /api/products/seed` hardcodes sample data and is an HTTP endpoint. Should be a CLI command reading `VAULTCORE_ADMIN_PASSWORD` from env. | `backend/app/api/products.py` lines 76–101 | Medium | 3 |
| i | **Missing endpoints**: no product search (`q` param), no admin stock-adjustment endpoint with audit row, low-stock threshold hardcoded to 5 instead of config. | `backend/app/api/products.py` line 29; `backend/app/services/product_service.py` lines 89–95 | Medium | 3 |
| j | **No pagination** on list endpoints (`/api/products`, `/api/admin/orders`, `/api/admin/users`). Default limit 20, max 100 missing. | `backend/app/api/products.py` line 29; `backend/app/api/admin.py` lines 10, 28 | Medium | 3 |
| k | **Doc errors in spec/README**: table count says 12 but schema has 11; section 11 duplicated; code tree mis-indented; concurrency test mentions both 20 customers and 5 buyer accounts. | `README.md`; `tests/test_core.py` line 210 | Low | 6 |

## Additional issues found during read

| # | Issue | File(s) | Severity | Phase |
|---|---|---|---|---|
| l | **SECRET_KEY default value**: `.env` uses `dev-secret-change-me`. No startup fail-fast if missing, shorter than 32 chars, or still the default. | `backend/app/security.py` line 5 | Critical | 2 |
| m | **CORS wildcard with credentials**: `allow_origins=["*"]` + `allow_credentials=True`. Browsers reject this; it's a security misconfiguration. | `backend/app/main.py` lines 9–13 | High | 2 |
| n | **No generic 500 handler**: unhandled exceptions may leak stack traces. | `backend/app/main.py` | Medium | 3 |
| o | **No request ID / structured logging**: no correlation ID, no JSON logs with route/status/latency. | `backend/app/main.py` | Medium | 3 |
| p | **No login rate limiting**: login endpoint has no per-IP / per-email throttling. | `backend/app/api/auth.py` | Medium | 2 |
| q | **No password policy**: registration accepts any length password. | `backend/app/services/auth_service.py` | Low | 2 |
| r | **Product hard delete**: `delete_product` removes the row and its inventory, breaking order history references. Should be soft delete (`is_active = false`). | `backend/app/services/product_service.py` lines 60–69 | Medium | 1 |
| s | **Money type**: `Numeric(10,2)` is acceptable (not float) but spec wants a documented, consistent choice. Prefer `NUMERIC(12,2)` and an ADR documenting why (exact decimal arithmetic, no float). | `backend/app/models.py` lines 74, 129, 145 | Low | 1 |
| t | **Timezone**: `server_default=func.now()` on `DateTime(timezone=True)` — DB server time, not explicitly UTC. | `backend/app/models.py` lines 35, 77, 102, 131 | Low | 1 |
| u | **Test count mismatch**: concurrency test uses 5 buyers but spec says 50 buyers / stock 10 / exactly 10 successes. Need deterministic `threading.Barrier` tests. | `backend/tests/test_core.py` lines 210–275 | High | 4 |
| v | **Test DB not isolated**: tests mutate the shared `vaultcore` database directly instead of creating/dropping a test database per run. | `backend/tests/test_core.py` lines 14–16 | High | 4 |

## Schema count check

The spec lists 12 tables. Current models define 11:

1. roles
2. users
3. user_roles
4. categories
5. products
6. inventory
7. carts
8. cart_items
9. orders
10. order_items
11. idempotency_keys

Missing relative to spec's intent: no separate table was actually missing — the count discrepancy is a doc error (spec says 12, code has 11). The audit treats this as documentation only unless an `order_audit_log` table is added for stock adjustments (issue i).

## Plan

- **Phase 1** — Correctness core: fix idempotency race (a,b), lock ordering (c), conditional stock decrement (d), status state machine (e), soft delete (r), money/UTC ADR (s,t), schema unification (b), pagination scaffolding (j).
- **Phase 2** — Security/auth: replace jose/passlib (g), SECRET_KEY fail-fast (l), CORS origins (m), login rate limiting (p), password policy (q), DB-backed roles (f).
- **Phase 3** — API quality: error format (one place), request ID + structured logging (o), generic 500 (n), thin routers, config via pydantic-settings, OpenAPI examples, pagination (j), search (i), stock adjustment + audit (i), CLI seed (h).
- **Phase 4** — Tests: real PostgreSQL test DB, deterministic barrier concurrency (50 buyers / stock 10 / 10 successes; 20 same-key requests / 1 order; deadlock test), price tampering, RBAC, migrations, unit tests for totals/state machine/fingerprinting.
- **Phase 5** — Frontend: strict TS, typed API client, loading/empty/error states, idempotency key in sessionStorage, in-flight disable, admin route hiding, a11y, ADR for token storage.
- **Phase 6** — Docs/CI/release: README, ARCHITECTURE, TESTING, RUNBOOK, SECURITY, ROADMAP, INTERVIEW_NOTES, PowerShell scripts, GitHub Actions, CHANGELOG, v1.0.0 tag.

Each phase ends with: full test suite, CHANGELOG update, commit, short report.
