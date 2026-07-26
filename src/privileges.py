"""Windows UAC 权限工具。"""
from __future__ import annotations

import ctypes
import os
import subprocess
import sys
from collections.abc import Sequence


def is_admin() -> bool:
    try:
        return bool(ctypes.windll.shell32.IsUserAnAdmin())
    except (AttributeError, OSError):
        return False


def relaunch_as_admin(arguments: Sequence[str] = ()) -> tuple[bool, str]:
    """以管理员身份重新启动当前程序。"""
    try:
        if getattr(sys, "frozen", False):
            executable = sys.executable
            parameters = subprocess.list2cmdline(list(arguments))
        else:
            executable = sys.executable
            parameters = subprocess.list2cmdline([os.path.abspath(sys.argv[0]), *arguments])
        result = ctypes.windll.shell32.ShellExecuteW(
            None, "runas", executable, parameters, None, 1
        )
        if int(result) <= 32:
            return False, f"Windows 拒绝了提权请求（错误代码 {int(result)}）"
        return True, "已请求管理员权限"
    except (AttributeError, OSError, ValueError) as exc:
        return False, f"无法请求管理员权限：{exc}"
