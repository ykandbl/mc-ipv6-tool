"""Windows 防火墙入站规则管理。"""
from __future__ import annotations

import json
import re
import subprocess
from dataclasses import dataclass

from privileges import is_admin

RULE_ID = "MCIPv6Tool.Host.TCP"
RULE_NAME = "买块联机工具 - Minecraft Java TCP"
LEGACY_RULE_NAME = "买块房主规则"


@dataclass(frozen=True)
class FirewallRuleState:
    """本工具防火墙规则的当前状态。"""

    query_succeeded: bool
    exists: bool
    port: str = ""
    display_name: str = ""
    error: str = ""


def validate_port_spec(value: str) -> tuple[bool, str, str]:
    """只接受一个 Minecraft Java TCP 端口。"""
    text = re.sub(r"\s+", "", value or "")
    if not text:
        return False, "请输入游戏中显示的端口", ""
    if not text.isascii() or not text.isdigit():
        return False, "端口只能是 1–65535 之间的单个数字", ""
    port = int(text)
    if not 1 <= port <= 65535:
        return False, "端口必须在 1–65535 之间", ""
    return True, "", str(port)


def _run_powershell(command: str, timeout: int = 20) -> tuple[bool, str]:
    if not is_admin():
        return False, "该操作需要管理员权限"
    wrapped = "[Console]::OutputEncoding=[Text.UTF8Encoding]::new();$ErrorActionPreference='Stop';" + command
    try:
        result = subprocess.run(
            ["powershell", "-NoProfile", "-NonInteractive", "-Command", wrapped],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
            check=False,
        )
        output = (result.stdout + result.stderr).strip()
        return result.returncode == 0, output
    except subprocess.TimeoutExpired:
        return False, "Windows 防火墙响应超时"
    except OSError as exc:
        return False, str(exc)


def get_firewall_rule_state() -> FirewallRuleState:
    """按规则名称查询状态及当前端口，不按端口反查。"""
    command = (
        f"$rule=Get-NetFirewallRule -Name '{RULE_ID}' -ErrorAction SilentlyContinue | Select-Object -First 1;"
        f"if (-not $rule) {{$rule=Get-NetFirewallRule -DisplayName '{LEGACY_RULE_NAME}' "
        "-ErrorAction SilentlyContinue | Select-Object -First 1};"
        "if (-not $rule) {[pscustomobject]@{exists=$false;port='';display_name=''} | ConvertTo-Json -Compress} "
        "else {$filter=$rule | Get-NetFirewallPortFilter | Select-Object -First 1;"
        "[pscustomobject]@{exists=$true;port=[string]$filter.LocalPort;display_name=[string]$rule.DisplayName} "
        "| ConvertTo-Json -Compress}"
    )
    success, output = _run_powershell(command, timeout=8)
    if not success:
        return FirewallRuleState(False, False, error=output or "无法读取 Windows 防火墙")
    try:
        data = json.loads(output)
        return FirewallRuleState(
            True,
            bool(data.get("exists")),
            str(data.get("port") or ""),
            str(data.get("display_name") or ""),
        )
    except (json.JSONDecodeError, AttributeError, TypeError) as exc:
        return FirewallRuleState(False, False, error=f"无法解析防火墙状态：{exc}")


def check_rule_exists() -> bool:
    """兼容旧调用；新界面应使用 ``get_firewall_rule_state``。"""
    return get_firewall_rule_state().exists


def get_rule_info(port: str = "") -> dict:
    info = {
        "名称": RULE_NAME,
        "方向": "入站",
        "协议": "TCP（Minecraft Java）",
        "操作": "允许连接",
        "网络": "专用、公用",
    }
    if port:
        info["本地端口"] = port
    return info


def set_firewall_port(port: str) -> tuple[bool, str, dict]:
    """创建规则；已存在同名规则时拒绝覆盖，必须先删除。"""
    valid, error, normalized = validate_port_spec(port)
    if not valid:
        return False, error, {}
    command = (
        f"$existing=Get-NetFirewallRule -Name '{RULE_ID}' -ErrorAction SilentlyContinue | Select-Object -First 1;"
        f"if (-not $existing) {{$existing=Get-NetFirewallRule -DisplayName '{LEGACY_RULE_NAME}' "
        "-ErrorAction SilentlyContinue | Select-Object -First 1};"
        "if ($existing) {$filter=$existing | Get-NetFirewallPortFilter | Select-Object -First 1;"
        "Write-Output ('blocked|' + [string]$filter.LocalPort)} else {"
        f"New-NetFirewallRule -Name '{RULE_ID}' -DisplayName '{RULE_NAME}' "
        f"-Description '由买块 IPv6 联机工具创建；结束联机后可安全删除。' "
        f"-Direction Inbound -Protocol TCP -LocalPort '{normalized}' "
        "-Action Allow -Profile Private,Public -Enabled True | Out-Null;Write-Output 'created'}"
    )
    success, output = _run_powershell(command)
    if not success:
        return False, f"设置防火墙失败：{output or '未知错误'}", {}
    blocked = next((line for line in output.splitlines() if line.startswith("blocked|")), "")
    if blocked:
        current_port = blocked.partition("|")[2] or "未知"
        return False, f"规则已经存在（端口 {current_port}），请先删除旧规则", {}
    if "created" not in output:
        return False, "Windows 未确认规则创建成功，请刷新后重试", {}
    return True, "Minecraft Java 入站规则已设置", get_rule_info(normalized)


def remove_firewall_port() -> tuple[bool, str]:
    command = (
        f"$rules=@(Get-NetFirewallRule -Name '{RULE_ID}' -ErrorAction SilentlyContinue);"
        f"$rules+=@(Get-NetFirewallRule -DisplayName '{LEGACY_RULE_NAME}' -ErrorAction SilentlyContinue);"
        "if ($rules.Count -eq 0) {Write-Output 'missing'} "
        "else {$rules | Remove-NetFirewallRule;Write-Output 'removed'}"
    )
    success, output = _run_powershell(command)
    if not success:
        return False, f"删除防火墙规则失败：{output or '未知错误'}"
    if "missing" in output:
        return True, "没有找到本工具创建的规则"
    return True, "已删除本工具创建的防火墙规则"
