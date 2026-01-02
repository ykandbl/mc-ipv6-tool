"""Windows 防火墙入站规则管理模块"""
import subprocess
import ctypes
import sys


RULE_NAME = "买块房主规则"


def is_admin() -> bool:
    """检查是否以管理员权限运行"""
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False


def run_as_admin(command: str) -> tuple[bool, str]:
    """以管理员权限运行 PowerShell 命令"""
    try:
        # 使用 PowerShell 执行命令
        result = subprocess.run(
            ["powershell", "-Command", command],
            capture_output=True,
            text=True,
            encoding='gbk',
            errors='ignore'
        )
        success = result.returncode == 0
        output = result.stdout + result.stderr
        return success, output
    except Exception as e:
        return False, str(e)


def check_rule_exists() -> bool:
    """检查入站规则是否存在"""
    command = f'Get-NetFirewallRule -DisplayName "{RULE_NAME}" -ErrorAction SilentlyContinue'
    success, output = run_as_admin(command)
    return success and RULE_NAME in output


def create_firewall_rule(port: str) -> tuple[bool, str]:
    """创建新的入站规则"""
    command = f'''
    New-NetFirewallRule -DisplayName "{RULE_NAME}" `
        -Direction Inbound `
        -Protocol TCP `
        -LocalPort {port} `
        -Action Allow `
        -Profile Domain,Private,Public `
        -Enabled True
    '''
    return run_as_admin(command)


def update_firewall_rule(port: str) -> tuple[bool, str]:
    """更新现有入站规则的端口"""
    command = f'Set-NetFirewallRule -DisplayName "{RULE_NAME}" -LocalPort {port}'
    return run_as_admin(command)


def delete_firewall_rule() -> tuple[bool, str]:
    """删除入站规则"""
    command = f'Remove-NetFirewallRule -DisplayName "{RULE_NAME}"'
    return run_as_admin(command)


def get_rule_info() -> dict:
    """获取规则详细信息"""
    return {
        "名称": RULE_NAME,
        "方向": "入站",
        "协议": "TCP",
        "操作": "允许连接",
        "配置文件": "域、专用、公用",
        "已启用": "是"
    }


def set_firewall_port(port: str) -> tuple[bool, str, dict]:
    """
    设置防火墙入站规则端口
    如果规则存在则更新，不存在则创建
    
    Args:
        port: 端口号，如 "8080" 或 "80,443" 或 "5000-5010"
    
    Returns:
        (成功与否, 消息, 规则信息)
    """
    # 验证端口格式
    port = port.strip()
    if not port:
        return False, "端口号不能为空", {}
    
    # 简单验证端口格式（数字、逗号、横杠）
    valid_chars = set("0123456789,-")
    if not all(c in valid_chars for c in port):
        return False, "端口格式无效，请输入数字，多个端口用逗号分隔，范围用横杠", {}
    
    try:
        rule_info = get_rule_info()
        rule_info["本地端口"] = port
        
        if check_rule_exists():
            success, output = update_firewall_rule(port)
            if success:
                return True, f"已更新规则 '{RULE_NAME}'", rule_info
            else:
                return False, f"更新规则失败: {output}", {}
        else:
            success, output = create_firewall_rule(port)
            if success:
                return True, f"已创建规则 '{RULE_NAME}'", rule_info
            else:
                return False, f"创建规则失败: {output}", {}
    except Exception as e:
        return False, f"操作失败: {str(e)}", {}


def remove_firewall_port() -> tuple[bool, str]:
    """
    删除防火墙入站规则
    
    Returns:
        (成功与否, 消息)
    """
    try:
        if not check_rule_exists():
            return False, f"规则 '{RULE_NAME}' 不存在"
        
        success, output = delete_firewall_rule()
        if success:
            return True, f"已删除规则 '{RULE_NAME}'"
        else:
            return False, f"删除规则失败: {output}"
    except Exception as e:
        return False, f"操作失败: {str(e)}"
