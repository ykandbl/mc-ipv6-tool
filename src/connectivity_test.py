"""IPv6 连通性测试模块"""
import subprocess
import socket
import threading
from typing import Tuple


def ping_ipv6(address: str, count: int = 3, timeout: int = 5000) -> Tuple[bool, str, int]:
    """
    Ping IPv6 地址
    
    Returns:
        (成功与否, 详细信息, 平均延迟ms)
    """
    try:
        result = subprocess.run(
            ["ping", "-6", "-n", str(count), "-w", str(timeout), address],
            capture_output=True,
            text=True,
            encoding='gbk',
            errors='ignore',
            timeout=count * (timeout / 1000) + 5
        )
        
        output = result.stdout
        
        # 解析丢包率
        if "100% 丢失" in output or "100% loss" in output:
            return False, "无法连接（100% 丢包）", 0
        
        # 解析平均延迟
        avg_time = 0
        if "平均 =" in output:
            try:
                avg_str = output.split("平均 =")[1].split("ms")[0].strip()
                avg_time = int(avg_str)
            except:
                pass
        
        if result.returncode == 0:
            return True, f"连接正常（平均延迟 {avg_time}ms）", avg_time
        else:
            return False, "连接失败", 0
            
    except subprocess.TimeoutExpired:
        return False, "连接超时", 0
    except Exception as e:
        return False, f"测试失败: {str(e)}", 0


def test_tcp_port(address: str, port: int, timeout: int = 5) -> Tuple[bool, str]:
    """
    测试 TCP 端口连通性
    
    Returns:
        (成功与否, 详细信息)
    """
    try:
        sock = socket.socket(socket.AF_INET6, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        
        result = sock.connect_ex((address, port))
        sock.close()
        
        if result == 0:
            return True, f"端口 {port} 可以连接"
        else:
            return False, f"端口 {port} 无法连接"
            
    except socket.timeout:
        return False, f"端口 {port} 连接超时"
    except Exception as e:
        return False, f"测试失败: {str(e)}"


def get_isp_info(ipv6_address: str) -> str:
    """根据 IPv6 前缀判断运营商"""
    prefix = ipv6_address.split(':')[0]
    
    isp_map = {
        '240e': '中国电信',
        '2408': '中国联通',
        '2409': '中国移动',
        '2001': '国际',
        '2400': '亚太',
    }
    
    for key, value in isp_map.items():
        if prefix.startswith(key):
            return value
    
    return '未知运营商'


class ConnectivityTester:
    """连通性测试器"""
    
    def __init__(self):
        self.is_testing = False
        self.result = None
    
    def test_bidirectional(self, local_addr: str, remote_addr: str, 
                          callback=None) -> dict:
        """
        双向连通性测试
        
        Args:
            local_addr: 本地 IPv6 地址
            remote_addr: 对方 IPv6 地址
            callback: 进度回调函数 callback(progress, message)
        
        Returns:
            测试结果字典
        """
        result = {
            'local_isp': get_isp_info(local_addr),
            'remote_isp': get_isp_info(remote_addr),
            'local_to_remote': {'success': False, 'message': '', 'latency': 0},
            'cross_isp': False,
            'recommendation': ''
        }
        
        # 判断是否跨运营商
        result['cross_isp'] = result['local_isp'] != result['remote_isp']
        
        if callback:
            callback(20, f"检测运营商: 你是{result['local_isp']}，对方是{result['remote_isp']}")
        
        # 测试本地到对方
        if callback:
            callback(40, "测试连接到对方...")
        
        success, message, latency = ping_ipv6(remote_addr)
        result['local_to_remote'] = {
            'success': success,
            'message': message,
            'latency': latency
        }
        
        if callback:
            callback(100, "测试完成")
        
        # 生成建议
        if result['local_to_remote']['success']:
            result['recommendation'] = "✅ 你可以连接到对方，建议对方当房主开房，你去加入"
        else:
            if result['cross_isp']:
                result['recommendation'] = "⚠️ 你连不到对方（跨运营商），建议你当房主开房，让对方来连你"
            else:
                result['recommendation'] = "❌ 你连不到对方，建议你当房主开房，或检查对方网络"
        
        return result
    
    def test_port(self, address: str, port: int, callback=None) -> dict:
        """
        测试指定端口
        
        Returns:
            测试结果字典
        """
        if callback:
            callback(50, f"测试端口 {port}...")
        
        success, message = test_tcp_port(address, port)
        
        if callback:
            callback(100, "测试完成")
        
        return {
            'success': success,
            'message': message,
            'port': port
        }
