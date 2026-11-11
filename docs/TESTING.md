# VAULTCORE Testing

## Backend Tests (Pytest)
Location: `backend/tests/test_core.py`

All integration tests run against a real PostgreSQL database (`vaultcore`). SQLite is deliberately NOT used because `FOR UPDATE` row locks and CHECK constraints behave differently.

### Test Categories
- **Auth & RBAC**: Registration, login, password policy (min 8 chars), rate limiting (5 failures → 429), admin/customer RBAC, revoked admin loses access immediately.
- **Cart & Checkout**: Add to cart, checkout flow, inventory decrement, cart cleared after checkout.
- **Idempotency**: Same key returns same order; exactly one order row; inventory decremented once.
- **Price Tampering**: Server computes totals from database prices; client prices ignored.
- **Concurrency**: 5 buyers on 1 unit stock → exactly 1 success, 4 out-of-stock (409), stock ends at 0.
- **Deadlock Prevention**: Two carts with opposite lock ordering → no deadlock, exactly one succeeds.
- **Migrations**: Downgrade then upgrade cycle preserves all tables.

### Running Tests
```bash
cd backend
export SECRET_KEY="your-32-char-secret"
uv run pytest
```

## Frontend Tests (Vitest + React Testing Library)
Location: `frontend/src/**/*.test.tsx`

### Test Categories
- **API Client**: Idempotency key handling, product input validation, ApiError shape.
- **Cart Page**: Loading state, cart display, quantity update, checkout flow.
- **Checkout Page**: Idempotency key display, new key generation, order placement, error handling.

### Running Tests
```bash
cd frontend
npm install -D vitest @testing-library/react @testing-library/jest-dom jsdom
npx vitest run
```

## Coverage Philosophy
Tests cover critical paths: authentication, authorization, concurrency safety, idempotency, and data integrity. Tests are not written purely for coverage numbers.
