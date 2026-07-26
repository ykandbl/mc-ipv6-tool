"""面向 Minecraft 联机的原生 IPv6 环境检测。"""
from __future__ import annotations

import ipaddress
import json
import subprocess
import time
import urllib.request
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field

from scanner import IPv6Address, IPv6Scanner


@dataclass(frozen=True)
class ReadinessCheck:
    key: str
    label: str
    status: str  # pass / warn / fail
    detail: str


@dataclass
class ReadinessResult:
    status: str  # available / degraded / unavailable
    title: str
    summary: str
    checks: list[ReadinessCheck] = field(default_factory=list)
    addresses: list[IPv6Address] = field(default_factory=list)
    recommended_address: str = ""
    public_ipv6: str = ""
    latency_ms: int = 0
    route_interface: str = ""


class IPv6ReadinessTester:
    """检测本机公网地址、默认路由和纯 IPv6 HTTPS 可达性。"""

    ENDPOINTS = (
        ("ipify", "https://api6.ipify.org?format=json", "json"),
        ("ident.me", "https://6.ident.me", "text"),
    )

    def __init__(
        self,
        scanner: IPv6Scanner | None = None,
        fetcher: Callable[[str, str, float], tuple[str, int]] | None = None,
    ) -> None:
        self.scanner = scanner or IPv6Scanner()
        self.fetcher = fetcher or self._fetch_public_ipv6

    @staticmethod
    def _powershell_flags() -> int:
        return getattr(subprocess, "CREATE_NO_WINDOW", 0)

    def _get_default_route_interface(self) -> str:
        command = (
            "[Console]::OutputEncoding=[Text.UTF8Encoding]::new();"
            "Get-NetRoute -AddressFamily IPv6 -DestinationPrefix '::/0' "
            "-ErrorAction SilentlyContinue | "
            "Where-Object {$_.Publish -ne 'No' -or $_.NextHop -ne '::'} | "
            "Sort-Object RouteMetric,InterfaceMetric | "
            "Select-Object -First 1 -ExpandProperty InterfaceAlias"
        )
        try:
            result = subprocess.run(
                ["powershell", "-NoProfile", "-NonInteractive", "-Command", command],
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=5,
                creationflags=self._powershell_flags(),
                check=False,
            )
            if result.returncode == 0:
                return result.stdout.strip()
        except (OSError, subprocess.SubprocessError):
            pass
        return ""

    @staticmethod
    def _fetch_public_ipv6(url: str, response_type: str, timeout: float) -> tuple[str, int]:
        """绕过系统代理访问纯 IPv6 HTTPS 服务。"""
        opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
        request = urllib.request.Request(
            url,
            headers={"User-Agent": "MC-IPv6-Tool/1.4 (+readiness-check)"},
        )
        started = time.perf_counter()
        with opener.open(request, timeout=timeout) as response:
            payload = response.read(2048).decode("utf-8", errors="strict").strip()
        latency_ms = max(1, round((time.perf_counter() - started) * 1000))
        if response_type == "json":
            payload = str(json.loads(payload).get("ip", ""))
        parsed = ipaddress.IPv6Address(payload)
        if not parsed.is_global:
            raise ValueError("服务未返回公网 IPv6 地址")
        return parsed.compressed, latency_ms

    def _probe_endpoints(self) -> list[tuple[str, str, int]]:
        successes: list[tuple[str, str, int]] = []
        with ThreadPoolExecutor(max_workers=len(self.ENDPOINTS)) as executor:
            futures = {
                executor.submit(self.fetcher, url, response_type, 5.0): name
                for name, url, response_type in self.ENDPOINTS
            }
            for future in as_completed(futures):
                name = futures[future]
                try:
                    address, latency = future.result()
                    successes.append((name, address, latency))
                except (OSError, ValueError, UnicodeError):
                    pass
        return successes

    def run(self) -> ReadinessResult:
        addresses = self.scanner.sort_addresses(self.scanner.scan_all_interfaces())
        usable = [address for address in addresses if address.is_usable]
        physical = [address for address in usable if not address.is_virtual]
        recommended = (physical or usable)[0].address if usable else ""
        checks: list[ReadinessCheck] = []

        if not usable:
            checks.append(
                ReadinessCheck("address", "公网 IPv6 地址", "fail", "没有找到可用于互联网联机的 IPv6 地址")
            )
            return ReadinessResult(
                status="unavailable",
                title="IPv6 暂不可用",
                summary="请检查光网络终端（光猫）、路由器及运营商网络是否已启用 IPv6。",
                checks=checks,
                addresses=addresses,
            )

        address_detail = f"找到 {len(usable)} 个公网地址"
        if not physical:
            address_detail += "，但都来自虚拟网卡或隧道"
            address_status = "warn"
        else:
            address_status = "pass"
        checks.append(ReadinessCheck("address", "公网 IPv6 地址", address_status, address_detail))

        route_interface = self._get_default_route_interface()
        checks.append(
            ReadinessCheck(
                "route",
                "IPv6 默认路由",
                "pass" if route_interface else "warn",
                f"通过 {route_interface} 访问互联网" if route_interface else "未能确认默认路由，将继续实际联网测试",
            )
        )

        probes = self._probe_endpoints()
        if not probes:
            checks.append(
                ReadinessCheck(
                    "internet",
                    "IPv6 互联网连接",
                    "fail",
                    "两个独立的纯 IPv6 服务均连接失败",
                )
            )
            return ReadinessResult(
                status="degraded",
                title="IPv6 地址存在，但无法联网",
                summary="可能是路由器、VPN 或运营商 IPv6 临时异常。关闭 VPN 后可重新检测。",
                checks=checks,
                addresses=addresses,
                recommended_address=recommended,
                route_interface=route_interface,
            )

        fastest = min(probes, key=lambda item: item[2])
        public_ipv6 = fastest[1]
        latency_ms = fastest[2]
        checks.append(
            ReadinessCheck(
                "internet",
                "IPv6 互联网连接",
                "pass",
                f"{len(probes)}/{len(self.ENDPOINTS)} 个服务成功，最快 {latency_ms}ms",
            )
        )

        local_values = {ipaddress.IPv6Address(item.address).compressed for item in usable}
        if public_ipv6 in local_values:
            checks.append(ReadinessCheck("public_ip", "公网地址一致性", "pass", "外部服务检测到的地址与本机网卡一致"))
        else:
            checks.append(
                ReadinessCheck(
                    "public_ip",
                    "公网地址一致性",
                    "warn",
                    "外部地址与网卡列表不同，可能经过 VPN、隧道或 NAT66",
                )
            )

        return ReadinessResult(
            status="available" if physical else "degraded",
            title="IPv6 连接正常" if physical else "IPv6 可联网，但需要留意虚拟网络",
            summary="可继续交换地址并执行双向连通性测试。",
            checks=checks,
            addresses=addresses,
            recommended_address=recommended,
            public_ipv6=public_ipv6,
            latency_ms=latency_ms,
            route_interface=route_interface,
        )
