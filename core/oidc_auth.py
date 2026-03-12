# core/oidc_auth.py
from authlib.integrations.starlette_client import OAuth
from config import settings, logger

oauth = OAuth()


def configure_oidc():
    """Register the OIDC provider (Keycloak) with authlib OAuth."""
    if not getattr(settings, "OIDC_ENABLED", False):
        return

    issuer_url = getattr(settings, "OIDC_ISSUER_URL", "")
    client_id = getattr(settings, "OIDC_CLIENT_ID", "")
    client_secret = getattr(settings, "OIDC_CLIENT_SECRET", "")

    if not all([issuer_url, client_id, client_secret]):
        logger.warning("OIDC enabled but missing configuration; skipping")
        return

    oauth.register(
        name="keycloak",
        client_id=client_id,
        client_secret=client_secret,
        server_metadata_url=f"{issuer_url}/.well-known/openid-configuration",
        client_kwargs={"scope": "openid email profile"},
    )
    logger.info("OIDC provider 'keycloak' registered (issuer=%s)", issuer_url)
