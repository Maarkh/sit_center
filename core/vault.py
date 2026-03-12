# core/vault.py
"""
HashiCorp Vault integration for secret management.

Usage:
  - Set VAULT_ENABLED=true, VAULT_ADDR, VAULT_ROLE, VAULT_SECRET_PATH in .env
  - In Kubernetes: uses Vault Agent Sidecar (annotations in Helm chart)
  - Standalone: uses AppRole or Token auth to fetch secrets at startup

Secrets from Vault override corresponding env vars in Settings.
"""
import os
import logging
from typing import Dict, Optional

logger = logging.getLogger(__name__)

VAULT_ENABLED = os.getenv("VAULT_ENABLED", "false").lower() == "true"
VAULT_ADDR = os.getenv("VAULT_ADDR", "https://vault.example.com")
VAULT_TOKEN = os.getenv("VAULT_TOKEN", "")
VAULT_ROLE_ID = os.getenv("VAULT_ROLE_ID", "")
VAULT_SECRET_ID = os.getenv("VAULT_SECRET_ID", "")
VAULT_SECRET_PATH = os.getenv("VAULT_SECRET_PATH", "secret/data/sit-center")
VAULT_MOUNT = os.getenv("VAULT_MOUNT", "secret")


def fetch_secrets() -> Dict[str, str]:
    """Fetch secrets from Vault and return as dict of env-var-compatible keys."""
    if not VAULT_ENABLED:
        return {}

    try:
        import requests
    except ImportError:
        logger.warning("requests library required for Vault integration")
        return {}

    token = _get_vault_token()
    if not token:
        logger.error("Could not obtain Vault token")
        return {}

    try:
        headers = {"X-Vault-Token": token}
        resp = requests.get(
            f"{VAULT_ADDR}/v1/{VAULT_SECRET_PATH}",
            headers=headers,
            timeout=10,
        )
        resp.raise_for_status()
        data = resp.json().get("data", {}).get("data", {})
        logger.info("Fetched %d secrets from Vault", len(data))
        return data
    except Exception as e:
        logger.error("Failed to fetch secrets from Vault: %s", e)
        return {}


def _get_vault_token() -> Optional[str]:
    """Get Vault token via direct token, AppRole, or Kubernetes auth."""
    if VAULT_TOKEN:
        return VAULT_TOKEN

    # Kubernetes Service Account auth
    sa_token_path = "/var/run/secrets/kubernetes.io/serviceaccount/token"
    if os.path.exists(sa_token_path):
        return _k8s_auth(sa_token_path)

    # AppRole auth
    if VAULT_ROLE_ID and VAULT_SECRET_ID:
        return _approle_auth()

    return None


def _k8s_auth(sa_token_path: str) -> Optional[str]:
    """Authenticate to Vault using Kubernetes service account."""
    try:
        import requests

        with open(sa_token_path) as f:
            jwt = f.read().strip()

        role = os.getenv("VAULT_ROLE", "sit-center")
        resp = requests.post(
            f"{VAULT_ADDR}/v1/auth/kubernetes/login",
            json={"jwt": jwt, "role": role},
            timeout=10,
        )
        resp.raise_for_status()
        return resp.json()["auth"]["client_token"]
    except Exception as e:
        logger.error("Vault Kubernetes auth failed: %s", e)
        return None


def _approle_auth() -> Optional[str]:
    """Authenticate to Vault using AppRole."""
    try:
        import requests

        resp = requests.post(
            f"{VAULT_ADDR}/v1/auth/approle/login",
            json={"role_id": VAULT_ROLE_ID, "secret_id": VAULT_SECRET_ID},
            timeout=10,
        )
        resp.raise_for_status()
        return resp.json()["auth"]["client_token"]
    except Exception as e:
        logger.error("Vault AppRole auth failed: %s", e)
        return None


def inject_vault_secrets():
    """Fetch secrets from Vault and inject into os.environ (before Settings init)."""
    secrets = fetch_secrets()
    for key, value in secrets.items():
        env_key = key.upper()
        if env_key not in os.environ:
            os.environ[env_key] = str(value)
            logger.debug("Injected Vault secret: %s", env_key)
        else:
            logger.debug("Vault secret %s skipped (already in env)", env_key)
