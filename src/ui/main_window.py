"""主窗口模块"""
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QScrollArea, QFrame, QMessageBox, QApplication
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

from scanner import IPv6Scanner, IPv6Address
from clipboard import ClipboardHandler
from browser import BrowserLauncher


def get_scale_factor() -> float:
    """根据屏幕大小计算缩放因子"""
    screen = QApplication.primaryScreen()
    if screen is None:
        return 1.0
    
    size = screen.size()
    # 基准：1920x1080 = 1.0
    base_width = 1920
    scale = size.width() / base_width
    
    # 限制缩放范围 0.8 ~ 1.5
    return max(0.8, min(1.5, scale))


class AddressCard(QFrame):
    """单个地址卡片组件"""
    
    def __init__(self, ipv6_addr: IPv6Address, scale: float = 1.0, parent=None):
        super().__init__(parent)
        self.ipv6_addr = ipv6_addr
        self.scale = scale
        self._setup_ui()
    
    def _setup_ui(self):
        self.setFrameStyle(QFrame.Shape.Box | QFrame.Shadow.Raised)
        self.setLineWidth(1)
        
        layout = QHBoxLayout(self)
        margin = int(10 * self.scale)
        layout.setContentsMargins(margin, int(8 * self.scale), margin, int(8 * self.scale))
        
        # 左侧信息区域
        info_layout = QVBoxLayout()
        
        # 地址显示
        addr_label = QLabel(self.ipv6_addr.address)
        addr_font = QFont()
        addr_font.setFamily("Consolas")
        addr_font.setPointSize(int(11 * self.scale))
        addr_label.setFont(addr_font)
        
        # 根据可用性设置颜色
        if self.ipv6_addr.is_usable:
            addr_label.setStyleSheet("color: #1565c0;")
        else:
            addr_label.setStyleSheet("color: #c62828;")
        
        info_layout.addWidget(addr_label)
        
        # 接口名称和类型
        temp_label = "临时地址" if self.ipv6_addr.is_temporary else "正常地址"
        detail_text = f"接口: {self.ipv6_addr.interface_name} | {temp_label} | {self.ipv6_addr.address_type}"
        detail_label = QLabel(detail_text)
        detail_font_size = int(10 * self.scale)
        detail_label.setStyleSheet(f"color: #666; font-size: {detail_font_size}px;")
        info_layout.addWidget(detail_label)
        
        layout.addLayout(info_layout, 1)
        
        # 复制按钮
        copy_btn = QPushButton("复制")
        copy_btn.setFixedWidth(int(60 * self.scale))
        copy_btn.clicked.connect(self._copy_address)
        layout.addWidget(copy_btn)
    
    def _copy_address(self):
        formatted_address = f"[{self.ipv6_addr.address}]:"
        if ClipboardHandler.copy_to_clipboard(formatted_address):
            QMessageBox.information(self, "成功", f"已复制: {formatted_address}")
        else:
            QMessageBox.warning(self, "错误", "复制失败，请重试")


class MainWindow(QMainWindow):
    """主窗口"""
    
    def __init__(self):
        super().__init__()
        self.scanner = IPv6Scanner()
        self.scale = get_scale_factor()
        self._setup_ui()
        self._refresh_addresses()
    
    def _setup_ui(self):
        self.setWindowTitle("IPv6 地址工具")
        
        # 根据屏幕大小设置窗口尺寸
        base_width, base_height = 600, 500
        width = int(base_width * self.scale)
        height = int(base_height * self.scale)
        min_width = int(500 * self.scale)
        min_height = int(400 * self.scale)
        
        self.setMinimumSize(min_width, min_height)
        self.resize(width, height)
        
        # 中央部件
        central = QWidget()
        self.setCentralWidget(central)
        
        margin = int(15 * self.scale)
        spacing = int(10 * self.scale)
        
        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(margin, margin, margin, margin)
        main_layout.setSpacing(spacing)
        
        # 顶部按钮区域
        btn_layout = QHBoxLayout()
        
        btn_font = QFont()
        btn_font.setPointSize(int(10 * self.scale))
        
        refresh_btn = QPushButton("🔄 刷新地址")
        refresh_btn.setFont(btn_font)
        refresh_btn.clicked.connect(self._refresh_addresses)
        btn_layout.addWidget(refresh_btn)
        
        test_btn = QPushButton("🌐 IPv6 连通性测试")
        test_btn.setFont(btn_font)
        test_btn.clicked.connect(self._open_ipv6_test)
        btn_layout.addWidget(test_btn)
        
        btn_layout.addStretch()
        main_layout.addLayout(btn_layout)
        
        # 状态标签
        self.status_label = QLabel("正在扫描...")
        status_font = QFont()
        status_font.setPointSize(int(10 * self.scale))
        self.status_label.setFont(status_font)
        main_layout.addWidget(self.status_label)
        
        # 地址列表滚动区域
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        
        self.list_widget = QWidget()
        self.list_layout = QVBoxLayout(self.list_widget)
        self.list_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.list_layout.setSpacing(int(8 * self.scale))
        
        scroll.setWidget(self.list_widget)
        main_layout.addWidget(scroll, 1)
        
        # 底部说明
        legend_font_size = int(10 * self.scale)
        legend = QLabel("🔵 蓝色 = 可用于外部通信  🔴 红色 = 不可用于外部通信")
        legend.setStyleSheet(f"color: #666; font-size: {legend_font_size}px;")
        legend.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(legend)
    
    def _refresh_addresses(self):
        """刷新地址列表"""
        while self.list_layout.count():
            item = self.list_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        addresses = self.scanner.scan_all_interfaces()
        addresses.sort(key=lambda x: (not x.is_usable, x.interface_name))
        
        if not addresses:
            self.status_label.setText("未找到 IPv6 地址")
            no_addr_label = QLabel("当前系统没有可用的 IPv6 地址")
            no_addr_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            no_addr_label.setStyleSheet("color: #999; padding: 20px;")
            self.list_layout.addWidget(no_addr_label)
            return
        
        usable_count = sum(1 for addr in addresses if addr.is_usable)
        self.status_label.setText(
            f"找到 {len(addresses)} 个 IPv6 地址，其中 {usable_count} 个可用于外部通信"
        )
        
        for addr in addresses:
            card = AddressCard(addr, self.scale)
            self.list_layout.addWidget(card)
    
    def _open_ipv6_test(self):
        """打开 IPv6 测试网站"""
        if not BrowserLauncher.open_ipv6_test():
            QMessageBox.warning(
                self, 
                "错误", 
                f"无法打开浏览器\n请手动访问: {BrowserLauncher.IPV6_TEST_URL}"
            )
