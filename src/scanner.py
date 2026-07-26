"""Windows IPv6 地址扫描器。"""
from __future__ import annotations

import socket
import subprocess
from dataclasses import dataclass

import psutil

from validator import AddressValidator

_VIRTUAL_HINTS = (
    "virtual", "vmware", "hyper-v", "vbox", "virtualbox", "wsl",
    "docker", "zerotier", "tailscale", "tap", "tun", "loopback",
)


@dataclass(frozen=True)
class IPv6Address:
    address: str
    interface_name: str
    is_temporary: bool
    address_type: str
    is_usable: bool
    is_virtual: bool = False

    @property
    def type_label(self) -> str:
        temp_label = "临时地址" if self.is_temporary else "稳定地址"
        return f"{temp_label} · {self.address_type}"


class IPv6Scanner:
    """读取网卡地址，并识别 Windows 隐私临时地址。"""

    def __init__(self) -> None:
        self.validator = AddressValidator()
        self._temporary_addresses: set[str] = set()

    @staticmethod
    def _powershell_flags() -> int:
        return getattr(subprocess, "CREATE_NO_WINDOW", 0)

    def _load_temporary_addresses(self) -> None:
        """查询 SuffixOrigin=Random 的地址；失败时不影响普通扫描。"""
        self._temporary_addresses.clear()
        command = (
            "[Console]::OutputEncoding=[Text.UTF8Encoding]::new();"
            "Get-NetIPAddress -AddressFamily IPv6 -ErrorAction SilentlyContinue | "
            "Where-Object {$_.SuffixOrigin -eq 'Random' -and $_.AddressState -eq 'Preferred'} | "
            "Select-Object -ExpandProperty IPAddress"
        )
        try:
            result = subprocess.run(
                ["powershell", "-NoProfile", "-NonInteractive", "-Command", command],
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=6,
                creationflags=self._powershell_flags(),
                check=False,
            )
            if result.returncode != 0:
                return
            for line in result.stdout.splitlines():
                parsed = self.validator.parse(line)
                if parsed:
                    self._temporary_addresses.add(parsed.compressed.lower())
        except (OSError, subprocess.SubprocessError):
            return

    @staticmethod
    def _is_virtual_interface(name: str) -> bool:
        lowered = name.casefold()
        return any(hint in lowered for hint in _VIRTUAL_HINTS)

    def scan_all_interfaces(self) -> list[IPv6Address]:
        """返回已启用接口上的有效 IPv6 地址，自动去重。"""
        self._load_temporary_addresses()
        try:
            net_if_addrs = psutil.net_if_addrs()
            net_if_stats = psutil.net_if_stats()
        except (OSError, RuntimeError):
            return []

        addresses: list[IPv6Address] = []
        seen: set[tuple[str, str]] = set()
        for interface_name, addrs in net_if_addrs.items():
            stats = net_if_stats.get(interface_name)
            if stats is not None and not stats.isup:
                continue
            for addr in addrs:
                if addr.family != socket.AF_INET6:
                    continue
                parsed = self.validator.parse(addr.address)
                if not parsed:
                    continue
                key = (parsed.compressed.lower(), interface_name.casefold())
                if key in seen:
                    continue
                seen.add(key)
                address_type, is_usable = self.validator.validate(str(parsed))
                addresses.append(
                    IPv6Address(
                        address=parsed.compressed,
                        interface_name=interface_name,
                        is_temporary=parsed.compressed.lower() in self._temporary_addresses,
                        address_type=address_type,
                        is_usable=is_usable,
                        is_virtual=self._is_virtual_interface(interface_name),
                    )
                )
        return addresses

    def get_usable_addresses(self) -> list[IPv6Address]:
        return [address for address in self.scan_all_interfaces() if address.is_usable]

    @staticmethod
    def sort_addresses(addresses: list[IPv6Address]) -> list[IPv6Address]:
        """公网物理网卡优先，其次临时地址，再显示本地/虚拟地址。"""
        return sorted(
            addresses,
            key=lambda item: (
                not item.is_usable,
                item.is_virtual,
                not item.is_temporary,
                item.interface_name.casefold(),
                item.address,
            ),
        )
