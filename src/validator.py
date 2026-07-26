"""IPv6 地址解析、清理与分类。"""
from __future__ import annotations

import ipaddress
import re


class AddressValidator:
    """集中处理所有 IPv6 输入，避免 UI 和扫描器各自实现一套规则。"""

    LABEL_LINK_LOCAL = "链路本地地址（不可用于互联网联机）"
    LABEL_LOOPBACK = "本地回环地址"
    LABEL_GLOBAL_UNICAST = "公网 IPv6 地址"
    LABEL_UNIQUE_LOCAL = "唯一本地地址"
    LABEL_MULTICAST = "组播地址"
    LABEL_UNSPECIFIED = "未指定地址"
    LABEL_RESERVED = "保留或特殊用途地址"
    LABEL_INVALID = "无效 IPv6 地址"

    @staticmethod
    def parse(address: str) -> ipaddress.IPv6Address | None:
        """解析 IPv6，允许 Windows 接口返回的 ``%scope`` 后缀。"""
        if not address:
            return None
        clean = address.strip().split("%", 1)[0]
        try:
            return ipaddress.IPv6Address(clean)
        except (ipaddress.AddressValueError, ValueError):
            return None

    @classmethod
    def clean_user_input(cls, value: str) -> tuple[bool, str, int | None]:
        """清理用户粘贴的 IPv6 或 ``[IPv6]:端口``。

        兼容工具旧版本复制出的 ``[IPv6]:`` 占位格式。
        返回 ``(是否合法, 规范地址, 可选端口)``。
        """
        text = (value or "").strip()
        if not text:
            return False, "", None

        port = None
        address = text
        if text.startswith("["):
            closing = text.find("]")
            if closing < 0:
                return False, text, None
            address = text[1:closing].strip()
            suffix = text[closing + 1 :].strip()
            if suffix:
                if not suffix.startswith(":"):
                    return False, address, None
                port_text = suffix[1:].strip()
                if port_text:
                    if not re.fullmatch(r"\d{1,5}", port_text):
                        return False, address, None
                    port = int(port_text)
                    if not 1 <= port <= 65535:
                        return False, address, None
        elif text.count(":") < 2:
            return False, text, None

        parsed = cls.parse(address)
        if parsed is None:
            return False, address, port
        return True, parsed.compressed, port

    @classmethod
    def is_link_local(cls, address: str) -> bool:
        parsed = cls.parse(address)
        return bool(parsed and parsed.is_link_local)

    @classmethod
    def is_loopback(cls, address: str) -> bool:
        parsed = cls.parse(address)
        return bool(parsed and parsed.is_loopback)

    @classmethod
    def is_global_unicast(cls, address: str) -> bool:
        parsed = cls.parse(address)
        if not parsed:
            return False
        # Minecraft 公网直连需要 2000::/3。ipaddress.is_global 在不同
        # Python 版本对特殊用途网段的口径不同，因此额外限制正式 GUA 范围。
        return parsed in ipaddress.IPv6Network("2000::/3") and not parsed.is_private

    @classmethod
    def is_unique_local(cls, address: str) -> bool:
        parsed = cls.parse(address)
        return bool(parsed and parsed in ipaddress.IPv6Network("fc00::/7"))

    @classmethod
    def validate(cls, address: str) -> tuple[str, bool]:
        """返回 ``(地址类型, 是否适合公网联机)``。"""
        parsed = cls.parse(address)
        if parsed is None:
            return cls.LABEL_INVALID, False
        if parsed.is_loopback:
            return cls.LABEL_LOOPBACK, False
        if parsed.is_unspecified:
            return cls.LABEL_UNSPECIFIED, False
        if parsed.is_link_local:
            return cls.LABEL_LINK_LOCAL, False
        if parsed.is_multicast:
            return cls.LABEL_MULTICAST, False
        if parsed in ipaddress.IPv6Network("fc00::/7"):
            return cls.LABEL_UNIQUE_LOCAL, False
        if cls.is_global_unicast(str(parsed)):
            return cls.LABEL_GLOBAL_UNICAST, True
        return cls.LABEL_RESERVED, False
