# ADR 0003: Idempotency Keys for Checkout

## Context
Duplicate checkout requests (e.g., double-click, network retry) could create multiple orders for the same cart. We need idempotency: submitting the same key twice must return the same order without side effects.

## Decision
- Single `idempotency_keys` table with `UNIQUE(user_id, key)` constraint.
- Each key stores `request_body_hash` (SHA-256), `order_id`, `response_status_code`, `response_body`.
- Checkout flow: fast-path key check → row-level locks on products/inventory → re-check key inside transaction → validate stock → write order + key atomically.
- On unique-constraint violation (concurrent same-key requests), return the existing order.

## Alternatives Considered
- **Key only on orders table**: Insufficient; doesn't capture request body or response, can't detect same-key-different-body.
- **Separate idempotency table**: Chosen; cleanly separates concerns and allows querying retry history.

## Consequences
- Same key + same body → returns existing order (no duplicate).
- Same key + different body → 429 conflict.
- Different key → new order as normal.
- Idempotency keys are scoped per user.
