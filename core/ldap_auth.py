# core/ldap_auth.py
from typing import Optional, Dict, List
from dataclasses import dataclass
from config import settings, logger, mask_secrets
from sqlalchemy import text
from core.database import get_engine


@dataclass
class LDAPUser:
    username: str
    email: Optional[str]
    display_name: Optional[str]
    groups: List[str]


class LDAPAuthenticator:
    def __init__(self):
        self.url = getattr(settings, "LDAP_URL", "")
        self.base_dn = getattr(settings, "LDAP_BASE_DN", "")
        self.bind_dn = getattr(settings, "LDAP_BIND_DN", "")
        self.bind_password = getattr(settings, "LDAP_BIND_PASSWORD", "")
        self.user_search_filter = getattr(settings, "LDAP_USER_SEARCH_FILTER", "(sAMAccountName={username})")
        self.group_role_map: Dict[str, str] = getattr(settings, "LDAP_GROUP_ROLE_MAP", {})

    def authenticate(self, username: str, password: str) -> Optional[LDAPUser]:
        try:
            import ldap3
            server = ldap3.Server(self.url, get_info=ldap3.ALL)

            # Bind with service account to search
            conn = ldap3.Connection(server, user=self.bind_dn, password=self.bind_password, auto_bind=True)

            search_filter = self.user_search_filter.replace("{username}", ldap3.utils.conv.escape_filter_chars(username))
            conn.search(
                self.base_dn,
                search_filter,
                attributes=["sAMAccountName", "mail", "displayName", "memberOf"],
            )

            if not conn.entries:
                logger.info("LDAP: user '%s' not found", username)
                return None

            entry = conn.entries[0]
            user_dn = entry.entry_dn

            # Verify user password
            user_conn = ldap3.Connection(server, user=user_dn, password=password)
            if not user_conn.bind():
                logger.info("LDAP: invalid password for '%s'", username)
                return None

            groups = [str(g) for g in entry.memberOf] if hasattr(entry, "memberOf") else []
            user_conn.unbind()
            conn.unbind()

            return LDAPUser(
                username=str(entry.sAMAccountName),
                email=str(entry.mail) if hasattr(entry, "mail") else None,
                display_name=str(entry.displayName) if hasattr(entry, "displayName") else None,
                groups=groups,
            )

        except ImportError:
            logger.error("ldap3 library not installed")
            return None
        except Exception as e:
            logger.error("LDAP authentication error: %s", mask_secrets(str(e)))
            return None

    def get_roles_for_groups(self, groups: List[str]) -> List[str]:
        roles = []
        for group in groups:
            cn = group.split(",")[0].replace("CN=", "") if "CN=" in group else group
            mapped_role = self.group_role_map.get(cn)
            if mapped_role:
                roles.append(mapped_role)
        return roles or ["viewer"]

    def sync_user_to_db(self, ldap_user: LDAPUser, tenant_id: str = "default") -> None:
        engine = get_engine()
        try:
            with engine.begin() as conn:
                conn.execute(
                    text("""
                        INSERT INTO users (username, email, tenant_id, auth_provider, is_active)
                        VALUES (:username, :email, :tenant_id, 'ldap', true)
                        ON CONFLICT (username) DO UPDATE SET
                            email = EXCLUDED.email,
                            auth_provider = 'ldap',
                            is_active = true,
                            updated_at = NOW()
                    """),
                    {
                        "username": ldap_user.username,
                        "email": ldap_user.email,
                        "tenant_id": tenant_id,
                    },
                )
            logger.info("LDAP user '%s' synced to DB", ldap_user.username)
        except Exception as e:
            logger.error("Failed to sync LDAP user: %s", mask_secrets(str(e)))


ldap_authenticator = LDAPAuthenticator()
