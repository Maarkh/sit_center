# core/passwords.py
"""Password hashing/verification via the `bcrypt` library directly.

passlib (1.7.4, last released 2020) is abandoned and breaks with modern bcrypt
(>= 4.x raise on >72-byte secrets, and bcrypt 4.1+ dropped the __about__ attr
passlib reads), which silently broke ALL login paths. These helpers talk to
bcrypt directly. Existing `$2b$...` hashes (incl. ones created by passlib) remain
verifiable, since they're standard bcrypt.
"""
import bcrypt

# bcrypt has a hard 72-byte limit on the secret. passlib historically truncated
# to 72 bytes; bcrypt >= 4 raises instead. Truncate defensively to keep behaviour
# stable and backward-compatible with previously-stored hashes.
_MAX_BCRYPT_BYTES = 72


def hash_password(password: str) -> str:
    pw = password.encode("utf-8")[:_MAX_BCRYPT_BYTES]
    return bcrypt.hashpw(pw, bcrypt.gensalt()).decode("utf-8")


def verify_password(password: str, password_hash: str) -> bool:
    if not password_hash:
        return False
    try:
        pw = password.encode("utf-8")[:_MAX_BCRYPT_BYTES]
        return bcrypt.checkpw(pw, password_hash.encode("utf-8"))
    except (ValueError, TypeError):
        return False
