"""IPv6 地址验证器模块"""
from typing import Tuple


class AddressValidator:
    """IPv6 地址验证器，用于判断地址类型和可用性"""
    
    # 地址类型标签
    LABEL_LINK_LOCAL = "链路本地地址（不可用于外部通信）"
    LABEL_LOOPBACK = "本地回环地址"
    LABEL_GLOBAL_UNICAST = "可用于通信"
    LABEL_UNIQUE_LOCAL = "唯一本地地址"
    LABEL_UNKNOWN = "未知类型"
    
    @staticmethod
    def is_link_local(address: str) -> bool:
        """检查是否为链路本地地址 (fe80::)"""
        normalized = address.lower().strip()
        return normalized.startswith("fe80")
    
    @staticmethod
    def is_loopback(address: str) -> bool:
        """检查是否为回环地址 (::1)"""
        normalized = address.strip()
        return normalized == "::1" or normalized == "0:0:0:0:0:0:0:1"
    
    @staticmethod
    def is_global_unicast(address: str) -> bool:
        """检查是否为全局单播地址 (2xxx:: 或 3xxx::)"""
        normalized = address.lower().strip()
        if not normalized:
            return False
        first_char = normalized[0]
        return first_char in ('2', '3')
    
    @staticmethod
    def is_unique_local(address: str) -> bool:
        """检查是否为唯一本地地址 (fc00:: 或 fd00::)"""
        normalized = address.lower().strip()
        return normalized.startswith("fc") or normalized.startswith("fd")
    
    @classmethod
    def validate(cls, address: str) -> Tuple[str, bool]:
        """
        验证地址类型
        
        Args:
            address: IPv6 地址字符串
            
        Returns:
            Tuple[str, bool]: (类型标签, 是否可用于外部通信)
        """
        if cls.is_loopback(address):
            return (cls.LABEL_LOOPBACK, False)
        
        if cls.is_link_local(address):
            return (cls.LABEL_LINK_LOCAL, False)
        
        if cls.is_global_unicast(address):
            return (cls.LABEL_GLOBAL_UNICAST, True)
        
        if cls.is_unique_local(address):
            return (cls.LABEL_UNIQUE_LOCAL, False)
        
        return (cls.LABEL_UNKNOWN, False)
