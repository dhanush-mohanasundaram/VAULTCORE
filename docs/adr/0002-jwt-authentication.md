# ADR 0002: JWT Authentication with PyJWT

## Context
The backend needs stateless authentication. The initial implementation used `python-jose[cryptography]` which is poorly maintained and has known security concerns.

## Decision
Use `pyjwt[crypto]` with explicit algorithm allow-list (`HS256` only). SECRET_KEY is validated at startup: must be present, at least 32 characters, and not a default value. Access tokens expire after 30 minutes.

## Alternatives Considered
- **python-jose**: Poorly maintained, cryptographic agility issues.
- **PyJWT**: Actively maintained, explicit algorithm selection, widely used.

## Consequences
- Tokens are signed with HMAC-SHA256.
- Algorithm is fixed to HS256; no algorithm confusion attacks possible.
- Startup fails fast if SECRET_KEY is weak or missing.
- Access tokens are short-lived (30 min); no refresh tokens in MVP (postponed to V2).
