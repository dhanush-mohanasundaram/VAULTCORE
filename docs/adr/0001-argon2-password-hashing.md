# ADR 0001: Password Hashing with Argon2

## Context
The VAULTCORE backend needs to securely hash user passwords. The initial implementation used `passlib[argon2]`, which is a Python wrapper around libargon2 but is poorly maintained and has known compatibility issues with newer argon2-cffi versions (the `verify()` argument order differs from passlib).

## Decision
Replace `passlib[argon2]` with `argon2-cffi` directly, using the `PasswordHasher` class with default parameters (Argon2id, 64 MiB memory, 3 iterations, 4 parallel lanes).

## Alternatives Considered
- **bcrypt**: Widely supported but limited to 72-character passwords and no memory-hardness configuration.
- **scrypt**: Memory-hard but less widely adopted and slower to verify.
- **passlib[argon2]**: Convenience wrapper but poorly maintained; caused verification bugs in production.

## Consequences
- Passwords are hashed with Argon2id, the winner of the Password Hashing Competition.
- Verification uses `pwd_context.verify(hashed_password, plain_password)` — note the argument order (hash first, password second).
- Dependency is actively maintained (`argon2-cffi` on PyPI).
- Migration path: existing passlib hashes would need re-hashing on next login; acceptable for MVP.
