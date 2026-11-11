# VAULTCORE Interview Notes

Use this document to prepare for SDE backend interviews. Each section explains a technical decision, the problem it solves, and the trade-offs.

## 1. Inventory Overselling Prevention

**Problem:** Two customers buy the last item simultaneously. Without protection, both succeed and inventory goes negative.

**Solution:**
- `SELECT ... FOR UPDATE` row-level locks on product and inventory rows, acquired in ascending ID order.
- Conditional SQL update: `UPDATE inventory SET quantity = quantity - n WHERE product_id = ? AND quantity >= n`.
- CHECK constraint `quantity >= 0` as database-level defense.

**Trade-offs:**
- Row locks reduce concurrency under high contention (serializes access to hot products).
- Conditional UPDATE is slightly slower than unconditional but prevents overselling.

**Interview talking point:** "We use pessimistic locking with deterministic lock ordering to prevent deadlocks, plus a conditional update as a defense-in-depth measure."

## 2. Duplicate Checkout Prevention (Idempotency)

**Problem:** Customer double-clicks "Place order" or network retry causes duplicate orders.

**Solution:**
- `idempotency_keys` table with `UNIQUE(user_id, key)`.
- Fast-path check before locks, post-lock re-check inside transaction.
- Same key + same body → returns existing order.
- Same key + different body → 429 conflict.

**Interview talking point:** "We use idempotency keys scoped per user, stored with a request body hash. If two requests arrive with the same key, the second returns the first order without side effects."

## 3. Database Schema Decisions

**Money:** Stored as `NUMERIC(12,2)`, never float. Floating-point cannot represent 0.1 + 0.2 exactly.

**Soft deletes:** Products use `is_active = false` instead of hard delete. Preserves order/cart history.

**Integer columns:** `is_active` uses `1/0` instead of boolean because PostgreSQL doesn't allow `integer = boolean` comparisons.

**Interview talking point:** "We chose NUMERIC for money to avoid floating-point rounding errors, and soft deletes to preserve referential integrity with historical orders."

## 4. Concurrency Control

**Scenario:** 50 buyers, 1 item in stock.

**Expected result:** Exactly 1 order succeeds, 49 get out-of-stock (409), inventory ends at 0.

**Mechanism:** Row-level locks + idempotency keys + conditional stock decrement.

**Interview talking point:** "Under concurrency, we serialize access to the hot product row using SELECT FOR UPDATE in ascending ID order. The first buyer wins, the rest get 409. No negative stock, no duplicate orders."

## 5. Why Not Redis/Microservices?

Redis adds operational complexity (another service to monitor, backup, upgrade). For an MVP, PostgreSQL handles transactions, locking, and idempotency natively. Microservices add network latency and distributed transaction complexity without current scale justification.

## 6. Security Decisions

- Argon2id for password hashing (memory-hard, resistant to GPU attacks).
- JWT with HS256, 30-minute expiry.
- SECRET_KEY validated at startup (32+ chars, not default).
- RBAC checked from database on every request (not trusted from JWT alone).
- Login rate limiting: 5 failures per 5 minutes per (IP, email).

## 7. Scaling Considerations

**Current:** Monolithic FastAPI + PostgreSQL on a single server.

**10x scale:** Add read replicas for read-heavy catalog queries, add Redis for rate limiting and session caching.

**100x scale:** Consider read-heavy sharding by product ID, introduce message queue for async order processing, split auth service.

## 8. What We Didn't Build (and Why)

- **Real payment gateway:** Requires PCI compliance; simulated in MVP.
- **Redis:** Not needed for MVP scale; PostgreSQL handles locking natively.
- **Email notifications:** Requires SMTP infrastructure; postponed.
- **Microservices:** Monolith is simpler to deploy and debug at current scale.
- **Double-entry ledger:** Complex accounting; not needed for MVP.
