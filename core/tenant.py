# core/tenant.py
from contextvars import ContextVar

_current_tenant: ContextVar[str] = ContextVar("current_tenant", default="default")


def get_current_tenant() -> str:
    return _current_tenant.get()


def set_current_tenant(tenant_id: str) -> None:
    _current_tenant.set(tenant_id)
