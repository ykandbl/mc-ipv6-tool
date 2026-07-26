"""买块 IPv6 联机工具入口。"""
from __future__ import annotations

import os
import sys

if getattr(sys, "frozen", False):
    application_path = sys._MEIPASS
else:
    application_path = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, application_path)
sys.path.insert(0, os.path.join(application_path, "ui"))

from PyQt6.QtCore import QTimer
from PyQt6.QtWidgets import QApplication, QMessageBox

from app_version import APP_NAME, APP_VERSION
from privileges import is_admin, relaunch_as_admin
from ui.app_icon import create_app_icon


def main() -> None:
    if os.name == "nt" and not is_admin():
        success, message = relaunch_as_admin(sys.argv[1:])
        if success:
            return
        app = QApplication(sys.argv)
        QMessageBox.critical(None, "需要管理员权限", f"本工具需要管理员权限才能运行。\n\n{message}")
        return

    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    app.setApplicationVersion(APP_VERSION)
    app.setOrganizationName("Bole")
    app.setStyle("Fusion")
    app.setWindowIcon(create_app_icon())

    from ui.main_window import MainWindow
    from ui.splash import SplashScreen

    splash = SplashScreen()
    splash.show()
    splash.set_progress(25, "正在准备网络检测…")

    window = MainWindow()
    splash.set_progress(100, "准备完成")

    def show_window() -> None:
        splash.close()
        window.show()
        window.start_initial_checks()

    QTimer.singleShot(220, show_window)
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
