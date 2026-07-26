from ipv6_readiness import IPv6ReadinessTester
from scanner import IPv6Address, IPv6Scanner


def make_address(address="2409:8000::1234", virtual=False):
    return IPv6Address(
        address=address,
        interface_name="以太网" if not virtual else "Test Virtual Adapter",
        is_temporary=True,
        address_type="公网 IPv6 地址",
        is_usable=True,
        is_virtual=virtual,
    )


def test_readiness_reports_available_without_real_network(monkeypatch):
    scanner = IPv6Scanner()
    monkeypatch.setattr(scanner, "scan_all_interfaces", lambda: [make_address()])
    tester = IPv6ReadinessTester(
        scanner=scanner,
        fetcher=lambda _url, _kind, _timeout: ("2409:8000::1234", 42),
    )
    monkeypatch.setattr(tester, "_get_default_route_interface", lambda: "以太网")
    result = tester.run()
    assert result.status == "available"
    assert result.public_ipv6 == "2409:8000::1234"
    assert result.recommended_address == "2409:8000::1234"


def test_readiness_distinguishes_address_from_internet_failure(monkeypatch):
    scanner = IPv6Scanner()
    monkeypatch.setattr(scanner, "scan_all_interfaces", lambda: [make_address()])

    def fail(*_args):
        raise OSError("offline")

    tester = IPv6ReadinessTester(scanner=scanner, fetcher=fail)
    monkeypatch.setattr(tester, "_get_default_route_interface", lambda: "以太网")
    result = tester.run()
    assert result.status == "degraded"
    assert any(check.key == "internet" and check.status == "fail" for check in result.checks)


def test_readiness_without_global_address_is_unavailable(monkeypatch):
    scanner = IPv6Scanner()
    monkeypatch.setattr(scanner, "scan_all_interfaces", list)
    result = IPv6ReadinessTester(scanner=scanner).run()
    assert result.status == "unavailable"
