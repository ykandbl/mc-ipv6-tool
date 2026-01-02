"""IPv6 地址工具 - 程序入口"""
import sys
import os
import ctypes

# 添加 src 目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PyQt6.QtWidgets import QApplication, QMessageBox
from PyQt6.QtCore import QTimer


def is_admin() -> bool:
    """检查是否以管理员权限运行"""
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False


def run_as_admin():
    """以管理员身份重新启动程序"""
    try:
        if getattr(sys, 'frozen', False):
            script = sys.executable
            params = ""
        else:
            script = sys.executable
            params = f'"{os.path.abspath(__file__)}"'
        
        ctypes.windll.shell32.ShellExecuteW(
            None, "runas", script, params, None, 1
        )
        return True
    except Exception as e:
        return False


def main():
    """程序主入口"""
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    
    # 检查管理员权限
    if not is_admin():
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Icon.Warning)
        msg.setWindowTitle("需要管理员权限")
        msg.setText("此程序需要管理员权限才能修改防火墙规则。")
        msg.setInformativeText("是否以管理员身份重新启动？")
        msg.setStandardButtons(
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        msg.setDefaultButton(QMessageBox.StandardButton.Yes)
        
        result = msg.exec()
        
        if result == QMessageBox.StandardButton.Yes:
            if run_as_admin():
                sys.exit(0)
            else:
                QMessageBox.critical(
                    None, "错误", 
                    "无法以管理员身份启动程序。\n请右键点击程序，选择「以管理员身份运行」。"
                )
                sys.exit(1)
        else:
            sys.exit(0)
    
    # 显示启动画面
    from ui.splash import SplashScreen
    splash = SplashScreen()
    splash.show()
    app.processEvents()
    
    # 模拟加载过程
    splash.set_progress(10, "正在初始化...")
    app.processEvents()
    
    splash.set_progress(30, "正在加载模块...")
    from ui.main_window import MainWindow
    app.processEvents()
    
    splash.set_progress(50, "正在扫描网络...")
    app.processEvents()
    
    splash.set_progress(70, "正在准备界面...")
    window = MainWindow()
    app.processEvents()
    
    splash.set_progress(90, "即将完成...")
    app.processEvents()
    
    splash.set_progress(100, "启动完成！")
    app.processEvents()
    
    # 延迟关闭启动画面并显示主窗口
    QTimer.singleShot(300, lambda: (splash.close(), window.show()))
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
