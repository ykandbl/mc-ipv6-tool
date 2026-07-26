import pytest

import firewall
from firewall import (
    FirewallRuleState,
    get_firewall_rule_state,
    set_firewall_port,
    validate_port_spec,
)


@pytest.mark.parametrize(
    ("value", "normalized"),
    [
        ("25565", "25565"),
        (" 443 ", "443"),
    ],
)
def test_validate_port_spec_accepts_valid_values(value, normalized):
    assert validate_port_spec(value) == (True, "", normalized)


@pytest.mark.parametrize(
    "value",
    ["", "0", "65536", "80-81", "80,443", "80;Remove-Item", "２５５６５"],
)
def test_validate_port_spec_rejects_invalid_values(value):
    assert validate_port_spec(value)[0] is False


def test_rule_state_is_parsed_by_rule_query(monkeypatch):
    monkeypatch.setattr(
        firewall,
        "_run_powershell",
        lambda command, **kwargs: (True, '{"exists":true,"port":"25565","display_name":"rule"}'),
    )
    assert get_firewall_rule_state() == FirewallRuleState(True, True, "25565", "rule")


def test_rule_state_reports_query_failure(monkeypatch):
    monkeypatch.setattr(firewall, "_run_powershell", lambda command, **kwargs: (False, "denied"))
    assert get_firewall_rule_state().error == "denied"


def test_setting_refuses_to_replace_existing_rule(monkeypatch):
    monkeypatch.setattr(firewall, "_run_powershell", lambda command: (True, "blocked|19132"))
    success, message, info = set_firewall_port("25565")
    assert success is False
    assert "19132" in message
    assert info == {}
