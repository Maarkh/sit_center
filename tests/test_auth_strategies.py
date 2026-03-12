# tests/test_auth_strategies.py
"""Tests for the decomposed auth strategies (core/auth_strategies.py)."""
import pytest
from unittest.mock import patch, MagicMock
from fastapi import HTTPException


class TestEnvAdminAuth:
    def test_valid_env_admin(self):
        from core.auth_strategies import try_env_admin_auth

        with patch("core.auth_strategies.settings") as mock_settings, \
             patch("core.auth_strategies.pwd_context") as mock_pwd:
            mock_settings.ADMIN_USERNAME = "admin"
            mock_settings.ADMIN_PASSWORD = "$2b$12$hash"
            mock_pwd.verify.return_value = True

            token = try_env_admin_auth("admin", "password123")
            assert isinstance(token, str)
            assert len(token) > 0

    def test_wrong_username(self):
        from core.auth_strategies import try_env_admin_auth

        with patch("core.auth_strategies.settings") as mock_settings:
            mock_settings.ADMIN_USERNAME = "admin"

            with pytest.raises(HTTPException) as exc_info:
                try_env_admin_auth("wrong_user", "password123")
            assert exc_info.value.status_code == 401

    def test_wrong_password(self):
        from core.auth_strategies import try_env_admin_auth

        with patch("core.auth_strategies.settings") as mock_settings, \
             patch("core.auth_strategies.pwd_context") as mock_pwd:
            mock_settings.ADMIN_USERNAME = "admin"
            mock_settings.ADMIN_PASSWORD = "$2b$12$hash"
            mock_pwd.verify.return_value = False

            with pytest.raises(HTTPException) as exc_info:
                try_env_admin_auth("admin", "wrong_pass")
            assert exc_info.value.status_code == 401


class TestDbAuth:
    def test_db_user_found(self):
        from core.auth_strategies import try_db_auth

        mock_user_row = {
            "id": 1,
            "username": "dbuser",
            "password_hash": "$2b$12$hash",
            "tenant_id": "tenant1",
            "is_active": True,
            "roles": ["viewer"],
            "permissions": ["read:metrics"],
        }

        with patch("core.auth_strategies.get_engine") as mock_engine, \
             patch("core.auth_strategies.pwd_context") as mock_pwd:
            conn = MagicMock()
            mock_engine.return_value.connect.return_value.__enter__ = MagicMock(return_value=conn)
            mock_engine.return_value.connect.return_value.__exit__ = MagicMock(return_value=False)
            conn.execute.return_value.mappings.return_value.first.return_value = mock_user_row
            mock_pwd.verify.return_value = True

            result = try_db_auth("dbuser", "password")
            assert result is not None
            assert result["username"] == "dbuser"
            assert result["tenant_id"] == "tenant1"
            assert "token" in result

    def test_db_user_not_found(self):
        from core.auth_strategies import try_db_auth

        with patch("core.auth_strategies.get_engine") as mock_engine:
            conn = MagicMock()
            mock_engine.return_value.connect.return_value.__enter__ = MagicMock(return_value=conn)
            mock_engine.return_value.connect.return_value.__exit__ = MagicMock(return_value=False)
            conn.execute.return_value.mappings.return_value.first.return_value = None

            result = try_db_auth("nonexistent", "password")
            assert result is None

    def test_db_wrong_password_raises(self):
        from core.auth_strategies import try_db_auth

        mock_user_row = {
            "id": 1,
            "username": "dbuser",
            "password_hash": "$2b$12$hash",
            "tenant_id": "tenant1",
            "is_active": True,
            "roles": [],
            "permissions": [],
        }

        with patch("core.auth_strategies.get_engine") as mock_engine, \
             patch("core.auth_strategies.pwd_context") as mock_pwd:
            conn = MagicMock()
            mock_engine.return_value.connect.return_value.__enter__ = MagicMock(return_value=conn)
            mock_engine.return_value.connect.return_value.__exit__ = MagicMock(return_value=False)
            conn.execute.return_value.mappings.return_value.first.return_value = mock_user_row
            mock_pwd.verify.return_value = False

            with pytest.raises(HTTPException) as exc_info:
                try_db_auth("dbuser", "wrong_pass")
            assert exc_info.value.status_code == 401


class TestLdapAuth:
    def test_ldap_disabled_returns_none(self):
        from core.auth_strategies import try_ldap_auth

        with patch("core.auth_strategies.settings") as mock_settings:
            mock_settings.LDAP_ENABLED = False
            result = try_ldap_auth("user", "pass")
            assert result is None

    def test_ldap_auth_failure_returns_none(self):
        from core.auth_strategies import try_ldap_auth

        with patch("core.auth_strategies.settings") as mock_settings:
            mock_settings.LDAP_ENABLED = True

            with patch("core.ldap_auth.ldap_authenticator") as mock_ldap:
                mock_ldap.authenticate.return_value = None
                result = try_ldap_auth("user", "wrong_pass")
                assert result is None
