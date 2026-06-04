"""Routing logic for notification channels — pure predicate, no network/DB."""
from core.notification_channels import channel_matches


def _ch(event_types, min_priority="info", enabled=True):
    return {"event_types": event_types, "min_priority": min_priority, "enabled": enabled}


def test_event_type_subscription():
    ch = _ch(["alert", "incident"])
    assert channel_matches(ch, "alert", "info")
    assert channel_matches(ch, "incident", "info")
    assert not channel_matches(ch, "predictive", "info")


def test_all_matches_every_event():
    ch = _ch(["all"])
    for et in ("alert", "incident", "escalation", "predictive", "situation", "system"):
        assert channel_matches(ch, et, "info")


def test_min_priority_gate():
    ch = _ch(["alert"], min_priority="warning")
    assert not channel_matches(ch, "alert", "info")
    assert channel_matches(ch, "alert", "warning")
    assert channel_matches(ch, "alert", "critical")


def test_critical_channel_only_critical():
    ch = _ch(["all"], min_priority="critical")
    assert not channel_matches(ch, "alert", "warning")
    assert channel_matches(ch, "alert", "critical")


def test_disabled_never_matches():
    ch = _ch(["all"], enabled=False)
    assert not channel_matches(ch, "alert", "critical")


def test_empty_subscription_silent():
    ch = _ch([])
    assert not channel_matches(ch, "alert", "critical")
