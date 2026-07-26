"""与主界面一致的轻量启动画面。"""
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import (
    QApplication,
    QHBoxLayout,
    QLabel,
    QProgressBar,
    QVBoxLayout,
    QWidget,
)

from app_version import APP_VERSION
from ui.app_icon import create_app_icon


class SplashScreen(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFixedSize(520, 270)
        screen = QApplication.primaryScreen()
        if screen is not None:
            area = screen.availableGeometry()
            self.move(area.center().x() - self.width() // 2, area.center().y() - self.height() // 2)
        self._setup_ui()

    def _setup_ui(self) -> None:
        outer = QVBoxLayout(self)
        outer.setContentsMargins(8, 8, 8, 8)
        container = QWidget()
        container.setStyleSheet(
            "QWidget{background:#1C2921;border:1px solid #34463A;border-radius:20px;}"
            "QLabel{border:none;background:transparent;color:white;}"
            "QProgressBar{border:none;background:#34463A;border-radius:4px;min-height:8px;max-height:8px;}"
            "QProgressBar::chunk{background:#C7E36C;border-radius:4px;}"
        )
        layout = QVBoxLayout(container)
        layout.setContentsMargins(34, 30, 34, 28)
        layout.setSpacing(18)
        brand = QHBoxLayout()
        logo = QLabel()
        logo.setFixedSize(54, 54)
        logo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        logo.setPixmap(create_app_icon().pixmap(54, 54))
        brand.addWidget(logo)
        text = QVBoxLayout()
        title = QLabel("买块 IPv6 联机工具")
        title.setFont(QFont("Microsoft YaHei UI", 17, QFont.Weight.DemiBold))
        subtitle = QLabel("Minecraft Java · IPv6 直连配置与诊断")
        subtitle.setStyleSheet("color:#BFCBC2;")
        text.addWidget(title)
        text.addWidget(subtitle)
        brand.addLayout(text, 1)
        version = QLabel(f"v{APP_VERSION}")
        version.setStyleSheet("color:#9FB0A3;")
        brand.addWidget(version, alignment=Qt.AlignmentFlag.AlignTop)
        layout.addLayout(brand)
        layout.addStretch()
        self.status_label = QLabel("正在初始化…")
        self.status_label.setStyleSheet("color:#D2DDD4;")
        layout.addWidget(self.status_label)
        self.progress = QProgressBar()
        self.progress.setTextVisible(False)
        self.progress.setValue(0)
        layout.addWidget(self.progress)
        outer.addWidget(container)

    def set_progress(self, value: int, status: str | None = None) -> None:
        self.progress.setValue(value)
        if status:
            self.status_label.setText(status)
        QApplication.processEvents()
