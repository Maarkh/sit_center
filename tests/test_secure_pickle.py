"""HMAC-signed pickle (core/secure_pickle.py) — H-4: refuse tampered/forged blobs."""
import base64
import io

import pytest

from core.secure_pickle import dumps_signed, loads_signed


def test_roundtrip():
    obj = {"a": [1, 2, 3], "b": "x"}
    assert loads_signed(dumps_signed(obj)) == obj


def test_tampered_payload_rejected():
    raw = bytearray(base64.b64decode(dumps_signed({"x": 1})))
    raw[-1] ^= 0xFF  # flip a payload byte → HMAC no longer matches
    with pytest.raises(ValueError):
        loads_signed(base64.b64encode(bytes(raw)).decode())


def test_forged_blob_without_valid_sig_rejected():
    import joblib
    buf = io.BytesIO()
    joblib.dump({"evil": 1}, buf)
    forged = base64.b64encode(b"\x00" * 32 + buf.getvalue()).decode()
    with pytest.raises(ValueError):
        loads_signed(forged)  # never reaches joblib.load


def test_none_and_short_rejected():
    with pytest.raises(ValueError):
        loads_signed(None)
    with pytest.raises(ValueError):
        loads_signed(base64.b64encode(b"short").decode())
