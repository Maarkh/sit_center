"""H-2: get_current_user re-resolves authz from the DB in production (TESTING off)."""
import os
from unittest.mock import patch, MagicMock
from datetime import timedelta

import pytest
from fastapi import HTTPException

from api.auth import get_current_user, create_access_token, _USER_ABSENT


def _tok(username="bob", tenant="default", roles=("admin",)):
    return create_access_token(
        data={"sub": username, "scopes": ["admin"], "tenant_id": tenant,
              "roles": list(roles), "permissions": ["read:metrics"]},
        expires_delta=timedelta(minutes=5),
    )


def test_reresolve_overrides_token_claims():
    req = MagicMock()
    with patch.dict(os.environ, {"TESTING": ""}), \
         patch("api.auth._resolve_user_grants", return_value=("acme", ["viewer"], ["read:metrics"])):
        td = get_current_user(request=req, token=_tok("bob", "default", ["admin"]))
    # the DB grants win over the (possibly forged) claims
    assert td.tenant_id == "acme"
    assert td.roles == ["viewer"]
    assert "admin" not in td.scopes


def test_reresolve_absent_user_rejected():
    req = MagicMock()
    with patch.dict(os.environ, {"TESTING": ""}), \
         patch("api.auth._resolve_user_grants", return_value=_USER_ABSENT):
        with pytest.raises(HTTPException) as ei:
            get_current_user(request=req, token=_tok("ghost"))
    assert ei.value.status_code == 401


def test_reresolve_db_error_falls_back_to_claims():
    req = MagicMock()
    with patch.dict(os.environ, {"TESTING": ""}), \
         patch("api.auth._resolve_user_grants", return_value=None):
        td = get_current_user(request=req, token=_tok("bob", "default", ["admin"]))
    assert td.tenant_id == "default"  # token claims preserved on DB blip


def test_testing_mode_trusts_claims():
    req = MagicMock()
    with patch.dict(os.environ, {"TESTING": "1"}), \
         patch("api.auth._resolve_user_grants") as resolver:
        td = get_current_user(request=req, token=_tok("bob", "default", ["admin"]))
    resolver.assert_not_called()       # re-resolution skipped under TESTING
    assert td.tenant_id == "default"
