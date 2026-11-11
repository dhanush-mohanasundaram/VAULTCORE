# ADR 0004: Frontend Auth Token Storage (sessionStorage)

## Context
The frontend needs to store the JWT access token so it can be sent with authenticated API requests. Options: localStorage, sessionStorage, or httpOnly cookie.

## Decision
Store JWT in `sessionStorage` under key `"token"`.

## Alternatives Considered
- **localStorage**: Persists across browser restarts; higher XSS risk surface.
- **httpOnly cookie**: Most secure against XSS but requires backend cookie handling and CSRF protection; more complex for MVP.
- **sessionStorage**: Chosen; cleared on tab close, reducing long-lived token exposure. Accessible via JavaScript so no backend cookie changes needed.

## Consequences
- Token is vulnerable to XSS if the frontend has XSS bugs; mitigate with CSP and sanitized outputs.
- Token is cleared when the browser tab closes; acceptable for MVP.
- Admin route protection on the frontend is UI-only; backend enforces RBAC on every request.
