"""IPv6 扫描器模块"""
import socket
import subprocess
import re
from dataclasses import dataclass
from typing import List, Dict, Set
import psutil

from validator import AddressValidator


@dataclass
class IPv6Address:
    """IPv6 地址数据模型"""
    address: str           # IPv6 地址字符串
    interface_name: str    # 网络接口名称
    is_temporary: bool     # 是否为临时地址
    address_type: str      # 地址类型标签
    is_usable: bool        # 是否可用于外部通信
    
    @property
    def type_label(self) -> str:
        """获取完整的类型标签"""
        temp_label = "临时地址" if self.is_temporary else "正常地址"
        return f"{temp_label} - {self.address_type}"


class IPv6Scanner:
    """IPv6 地址扫描器"""
    
    def __init__(self):
        self.validator = AddressValidator()
        self._temporary_addresses: Set[str] = set()
        self._load_temporary_addresses()
    
    def _load_temporary_addresses(self):
        """通过 PowerShell 命令获取临时地址列表"""
        try:
            import os
            # 获取脚本路径
            script_dir = os.path.dirname(os.path.abspath(__file__))
            script_path = os.path.join(script_dir, 'get_temp_ipv6.ps1')
            
            # 如果脚本不存在，创建它
            if not os.path.exists(script_path):
                with open(script_path, 'w') as f:
                    f.write('Get-NetIPAddress -AddressFamily IPv6 | Where-Object {$_.SuffixOrigin -eq 5} | Select-Object -ExpandProperty IPAddress\n')
            
            result = subprocess.run(
                ['powershell', '-ExecutionPolicy', 'Bypass', '-File', script_path],
                capture_output=True,
                text=True,
                encoding='utf-8',
                errors='ignore',
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            
            for line in result.stdout.strip().split('\n'):
                addr = line.strip().split('%')[0].lower()
                if addr:
                    self._temporary_addresses.add(addr)
        except Exception:
            pass
    
    def scan_all_interfaces(self) -> List[IPv6Address]:
        """扫描所有网络接口，返回 IPv6 地址列表"""
        addresses = []
        
        # 重新加载临时地址信息
        self._temporary_addresses.clear()
        self._load_temporary_addresses()
        
        try:
            net_if_addrs = psutil.net_if_addrs()
        except Exception:
            return addresses
        
        for interface_name, addrs in net_if_addrs.items():
            for addr in addrs:
                if addr.family == socket.AF_INET6:
                    ipv6_addr = self._create_ipv6_address(
                        addr.address, 
                        interface_name
                    )
                    if ipv6_addr:
                        addresses.append(ipv6_addr)
        
        return addresses
    
    def _create_ipv6_address(self, address: str, interface_name: str) -> IPv6Address:
        """创建 IPv6Address 对象"""
        clean_address = address.split('%')[0]
        address_type, is_usable = self.validator.validate(clean_address)
        is_temporary = self._is_temporary_address(clean_address)
        
        return IPv6Address(
            address=clean_address,
            interface_name=interface_name,
            is_temporary=is_temporary,
            address_type=address_type,
            is_usable=is_usable
        )
    
    def _is_temporary_address(self, address: str) -> bool:
        """判断是否为临时地址"""
        if self.validator.is_link_local(address) or self.validator.is_loopback(address):
            return False
        
        # 检查是否在临时地址集合中
        addr_lower = address.lower()
        return addr_lower in self._temporary_addresses
    
    def get_usable_addresses(self) -> List[IPv6Address]:
        """获取所有可用于外部通信的地址"""
        return [addr for addr in self.scan_all_interfaces() if addr.is_usable]
