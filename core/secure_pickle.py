# core/secure_pickle.py
# joblib/pickle deserialization is RCE-on-load. ML models are cached in Redis and read
# back, so anyone who can write that key (Redis compromise, key-injection) could plant a
# malicious pickle. Sign the blob with HMAC-SHA256(SECRET_KEY) on store and verify it
# BEFORE deserializing on load — a tampered/forged blob is rejected, never unpickled.
# Base64 framing also keeps it safe through a decode_responses=True Redis client.
import base64
import hashlib
import hmac
import io

from config import settings


def _key() -> bytes:
    return settings.secret_key.encode()


def dumps_signed(obj) -> str:
    import joblib
    buf = io.BytesIO()
    joblib.dump(obj, buf)
    blob = buf.getvalue()
    sig = hmac.new(_key(), blob, hashlib.sha256).digest()
    return base64.b64encode(sig + blob).decode("ascii")


def loads_signed(data):
    import joblib
    if data is None:
        raise ValueError("no signed pickle data")
    if isinstance(data, str):
        data = data.encode("ascii")
    raw = base64.b64decode(data)
    if len(raw) < 32:
        raise ValueError("signed pickle too short")
    sig, blob = raw[:32], raw[32:]
    if not hmac.compare_digest(sig, hmac.new(_key(), blob, hashlib.sha256).digest()):
        raise ValueError("signed pickle HMAC mismatch — refusing to deserialize")
    return joblib.load(io.BytesIO(blob))
