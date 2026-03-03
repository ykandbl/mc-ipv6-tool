"""启动画面模块"""
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QProgressBar, QApplication
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont, QPainter, QLinearGradient, QColor, QPen


class SplashScreen(QWidget):
    """启动画面"""
    
    def __init__(self):
        super().__init__()
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint | 
            Qt.WindowType.WindowStaysOnTopHint
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFixedSize(500, 280)
        
        # 居中显示
        screen = QApplication.primaryScreen().geometry()
        x = (screen.width() - self.width()) // 2
        y = (screen.height() - self.height()) // 2
        self.move(x, y)
        
        self._setup_ui()
        
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # 主容器
        container = QWidget()
        container.setStyleSheet("""
            QWidget {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #1e3c72, stop:1 #2a5298);
                border-radius: 20px;
                border: 2px solid rgba(255,255,255,0.2);
            }
        """)
        container_layout = QVBoxLayout(container)
        container_layout.setContentsMargins(40, 40, 40, 40)
        container_layout.setSpacing(20)
        
        # 图标和标题
        title = QLabel("🎮 我的世界 IPv6 联机工具")
        title.setFont(QFont("Microsoft YaHei", 18, QFont.Weight.Bold))
        title.setStyleSheet("color: white; background: transparent;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        container_layout.addWidget(title)
        
        # 副标题
        subtitle = QLabel("Minecraft IPv6 Connection Tool")
        subtitle.setFont(QFont("Arial", 10))
        subtitle.setStyleSheet("color: rgba(255,255,255,0.7); background: transparent;")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        container_layout.addWidget(subtitle)
        
        container_layout.addSpacing(10)
        
        # 状态文字
        self.status_label = QLabel("正在初始化...")
        self.status_label.setFont(QFont("Microsoft YaHei", 10))
        self.status_label.setStyleSheet("color: rgba(255,255,255,0.9); background: transparent;")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        container_layout.addWidget(self.status_label)
        
        # 进度条
        self.progress = QProgressBar()
        self.progress.setFixedHeight(10)
        self.progress.setTextVisible(False)
        self.progress.setStyleSheet("""
            QProgressBar {
                background-color: rgba(255,255,255,0.2);
                border-radius: 5px;
                border: 1px solid rgba(255,255,255,0.3);
            }
            QProgressBar::chunk {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #4CAF50, stop:1 #8BC34A);
                border-radius: 5px;
            }
        """)
        self.progress.setValue(0)
        container_layout.addWidget(self.progress)
        
        # 版本信息
        version_label = QLabel("v1.2.2")
        version_label.setFont(QFont("Arial", 8))
        version_label.setStyleSheet("color: rgba(255,255,255,0.5); background: transparent;")
        version_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        container_layout.addWidget(version_label)
        
        layout.addWidget(container)
    
    def set_progress(self, value: int, status: str = None):
        """设置进度"""
        self.progress.setValue(value)
        if status:
            self.status_label.setText(status)
        QApplication.processEvents()
