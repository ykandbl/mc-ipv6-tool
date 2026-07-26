"""双向连通性初步检测与实际游戏端口测试。"""
from __future__ import annotations

import ipaddress
import locale
import re
import socket
import subprocess


def _creation_flags() -> int:
    return getattr(subprocess, "CREATE_NO_WINDOW", 0)


def ping_ipv6(
    address: str,
    count: int = 3,
    timeout: int = 2500,
    source_address: str | None = None,
) -> tuple[bool, str, int]:
    """使用 Windows Ping 检测“本机 → 对方”的 ICMPv6 可达性。"""
    try:
        target = ipaddress.IPv6Address(address).compressed
        command = ["ping", "-6", "-n", str(count), "-w", str(timeout)]
        if source_address:
            command.extend(["-S", ipaddress.IPv6Address(source_address).compressed])
        command.append(target)
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            encoding=locale.getpreferredencoding(False),
            errors="replace",
            timeout=count * (timeout / 1000) + 4,
            creationflags=_creation_flags(),
            check=False,
        )
        output = f"{result.stdout}\n{result.stderr}"
        if result.returncode != 0:
            if re.search(r"100%\s*(?:丢失|loss)", output, re.IGNORECASE):
                return False, "未收到对方响应（100% 丢包）", 0
            return False, "暂时无法访问对方", 0

        average = 0
        match = re.search(r"(?:平均|Average)\s*[=:]\s*<?(\d+)\s*ms", output, re.IGNORECASE)
        if match:
            average = max(1, int(match.group(1)))
        if average:
            return True, f"连接正常（平均延迟 {average}ms）", average
        return True, "连接正常", 0
    except subprocess.TimeoutExpired:
        return False, "测试超时，未收到对方响应", 0
    except (OSError, ValueError) as exc:
        return False, f"无法执行测试：{exc}", 0


def test_tcp_port(address: str, port: int, timeout: int = 5) -> tuple[bool, str]:
    """测试 Minecraft Java 服务端口是否真的处于监听状态。"""
    if not 1 <= int(port) <= 65535:
        return False, "端口必须在 1–65535 之间"
    try:
        with socket.socket(socket.AF_INET6, socket.SOCK_STREAM) as sock:
            sock.settimeout(timeout)
            result = sock.connect_ex((ipaddress.IPv6Address(address).compressed, int(port)))
        if result == 0:
            return True, f"端口 {port} 接受了 TCP 连接，基础网络路径正常"
        return False, f"端口 {port} 暂时无法连接；请确认房主已创建游戏并完成防火墙配置"
    except TimeoutError:
        return False, f"端口 {port} 连接超时"
    except (OSError, ValueError) as exc:
        return False, f"端口测试失败：{exc}"


def get_isp_info(ipv6_address: str) -> str:
    """对中国大陆家宽常见公网前缀作提示性识别。"""
    try:
        first = ipaddress.IPv6Address(ipv6_address).exploded.split(":", 1)[0]
    except ValueError:
        return "未知运营商"
    return {
        "240e": "中国电信",
        "2408": "中国联通",
        "2409": "中国移动",
    }.get(first, "其他或未知运营商")


def combine_direction_results(local_success: bool, remote_success: bool) -> dict:
    """合并两个人各自执行的一次单向测试。"""
    if local_success and remote_success:
        return {
            "code": "both",
            "title": "双方均通过主机方向初步检测",
            "message": "两个方向均收到响应，可选择任意一方作为房主；创建游戏后建议继续测试实际 TCP 端口。",
            "local_can_host": True,
            "remote_can_host": True,
        }
    if local_success and not remote_success:
        return {
            "code": "remote_only",
            "title": "建议由对方作为房主",
            "message": "本机可以访问对方，但对方未能访问本机。对方作为房主的连接成功率更高，创建游戏后建议测试实际端口。",
            "local_can_host": False,
            "remote_can_host": True,
        }
    if not local_success and remote_success:
        return {
            "code": "local_only",
            "title": "建议由本机用户作为房主",
            "message": "对方可以访问本机，但本机未能访问对方。本机用户作为房主的连接成功率更高，创建游戏后建议测试实际端口。",
            "local_can_host": True,
            "remote_can_host": False,
        }
    return {
        "code": "neither",
        "title": "两个 Ping 方向都未收到响应",
        "message": "该结果可能由网络链路异常或 ICMPv6 被拦截导致。房主创建游戏后仍可尝试实际端口测试。",
        "local_can_host": False,
        "remote_can_host": False,
    }


class ConnectivityTester:
    """运行耗时网络操作，调用方应放到工作线程中。"""

    def test_bidirectional(self, local_addr: str, remote_addr: str, callback=None) -> dict:
        """保留旧 API 名称；本方法只完成“本机 → 对方”的一半测试。"""
        local_isp = get_isp_info(local_addr)
        remote_isp = get_isp_info(remote_addr)
        known = {"中国电信", "中国联通", "中国移动"}
        cross_isp = local_isp in known and remote_isp in known and local_isp != remote_isp

        if callback:
            callback(20, "正在确认双方网络信息…")
        if callback:
            callback(45, "正在测试本机至对方的连通性…")
        success, message, latency = ping_ipv6(remote_addr, source_address=local_addr)
        if callback:
            callback(100, "本方向测试完成")
        return {
            "local_isp": local_isp,
            "remote_isp": remote_isp,
            "cross_isp": cross_isp,
            "local_to_remote": {
                "success": success,
                "message": message,
                "latency": latency,
            },
        }

    def test_port(self, address: str, port: int, callback=None) -> dict:
        if callback:
            callback(40, f"正在连接 [{address}]:{port}…")
        success, message = test_tcp_port(address, port)
        if callback:
            callback(100, "端口测试完成")
        return {"success": success, "message": message, "port": port}
