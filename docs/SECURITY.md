# VAULTCORE Security

## Authentication
- Passwords hashed with Argon2id (argon2-cffi).
- JWT access tokens signed with HS256, 30-minute expiry.
- SECRET_KEY validated at startup: required, 32+ characters, not a default value.
- No refresh tokens in MVP (postponed to V2).

## Authorization
- Role-Based Access Control (RBAC): customer and admin roles.
- Roles loaded from database on every request — revoked admins lose access immediately.
- Admin endpoints require `admin` role; customer endpoints require `customer` role.
- Frontend AdminOnly component is UI-only; backend enforces RBAC on every request.

## Rate Limiting
- Login endpoint rate-limited: 5 failed attempts per 300 seconds per (IP, email) pair → 429 response.
- In-process limiter; documented as MVP limitation (Redis-based rate limiting postponed to V2).

## CORS
- Origins configured via CORS_ORIGINS environment variable.
- No wildcard origin when credentials are enabled.
- Default: http://localhost:5173

## Data Protection
- Prices stored as NUMERIC(12,2) — never float.
- Order totals computed server-side from database prices; frontend prices ignored.
- Idempotency keys scoped per user with SHA-256 request body hash.
- CHECK constraints on database: quantity >= 0, price >= 0, total >= 0, cart quantity 1-99.

## Secrets Management
- SECRET_KEY provided via environment variable, never committed to git.
- .env.example provided with placeholder values.
- .env is in .gitignore.

## Known Limitations
- In-process login rate limiter (not distributed; resets on restart).
- JWT tokens not revocable before expiry (short 30-min window mitigates).
- No refresh token rotation.
- No password reset flow in MVP.
