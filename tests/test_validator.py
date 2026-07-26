import pytest

from validator import AddressValidator


@pytest.mark.parametrize(
    ("value", "expected", "port"),
    [
        ("2409:8000::1", "2409:8000::1", None),
        ("[2409:8000::1]", "2409:8000::1", None),
        ("[2409:8000::1]:", "2409:8000::1", None),
        ("[2409:8000::1]:25565", "2409:8000::1", 25565),
    ],
)
def test_clean_user_input_accepts_common_copy_formats(value, expected, port):
    assert AddressValidator.clean_user_input(value) == (True, expected, port)


@pytest.mark.parametrize(
    "value",
    ["", "not-an-ip", "[2409::1", "[2409::1]:0", "[2409::1]:65536"],
)
def test_clean_user_input_rejects_invalid_values(value):
    assert AddressValidator.clean_user_input(value)[0] is False


def test_validate_uses_full_link_local_range():
    label, usable = AddressValidator.validate("febf::1")
    assert "链路本地" in label
    assert usable is False


def test_invalid_prefix_is_not_treated_as_global():
    assert AddressValidator.validate("2-not-ipv6")[1] is False


def test_documentation_prefix_is_not_recommended():
    assert AddressValidator.validate("2001:db8::1")[1] is False


def test_real_global_unicast_is_usable():
    assert AddressValidator.validate("2409:8000::1")[1] is True
