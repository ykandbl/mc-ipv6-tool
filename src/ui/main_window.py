"""主窗口模块"""
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QScrollArea, QFrame, QMessageBox, QApplication,
    QLineEdit, QGroupBox, QProgressBar, QDialog, QTextEdit
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QFont, QPalette, QColor

from scanner import IPv6Scanner, IPv6Address
from clipboard import ClipboardHandler
from browser import BrowserLauncher
from firewall import set_firewall_port, remove_firewall_port
from connectivity_test import ConnectivityTester


# 主题颜色 - 现代深蓝配色方案
THEME = {
    "primary": "#1e3c72",
    "primary_dark": "#152a52",
    "primary_light": "#2a5298",
    "accent": "#4CAF50",
    "accent_hover": "#43A047",
    "success": "#4CAF50",
    "danger": "#E53935",
    "warning": "#FF9800",
    "bg": "#f0f2f5",
    "card_bg": "#ffffff",
    "text": "#2c3e50",
    "text_secondary": "#7f8c8d",
    "border": "#dfe6e9",
    "recommend": "#FF9800",
    "shadow": "rgba(0, 0, 0, 0.1)"
}


def get_scale_factor() -> float:
    """根据屏幕大小计算缩放因子"""
    screen = QApplication.primaryScreen()
    if screen is None:
        return 1.0
    size = screen.size()
    base_width = 1920
    scale = size.width() / base_width
    return max(0.8, min(1.5, scale))


class TestThread(QThread):
    """测试线程"""
    progress = pyqtSignal(int, str)
    finished = pyqtSignal(dict)
    
    def __init__(self, local_addr, remote_addr):
        super().__init__()
        self.local_addr = local_addr
        self.remote_addr = remote_addr
        self.tester = ConnectivityTester()
    
    def run(self):
        result = self.tester.test_bidirectional(
            self.local_addr,
            self.remote_addr,
            callback=self.progress.emit
        )
        self.finished.emit(result)


class ConnectivityTestDialog(QDialog):
    """连通性测试对话框"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("IPv6 连通性测试")
        self.setFixedSize(500, 400)
        self._setup_ui()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        
        # 说明
        info_label = QLabel("💡 测试你和对方的 IPv6 连通性，自动判断谁适合当房主\n\n⚠️ 注意：双方都需要先用工具获取自己的 IPv6 地址并互相交换")
        info_label.setWordWrap(True)
        info_label.setStyleSheet(f"color: {THEME['text_secondary']}; padding: 10px; background-color: #F5F5F5; border-radius: 4px;")
        layout.addWidget(info_label)
        
        # 输入区域
        input_group = QGroupBox("输入对方的 IPv6 地址")
        input_layout = QVBoxLayout(input_group)
        
        self.remote_input = QLineEdit()
        self.remote_input.setPlaceholderText("如: 2409:890d:380:18a3:5ad:de6b:8552:ff6a")
        self.remote_input.setStyleSheet(f"""
            QLineEdit {{
                border: 1px solid {THEME['border']};
                border-radius: 4px;
                padding: 8px;
                font-size: 10pt;
            }}
        """)
        input_layout.addWidget(self.remote_input)
        layout.addWidget(input_group)
        
        # 进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setStyleSheet(f"""
            QProgressBar {{
                border: 1px solid {THEME['border']};
                border-radius: 4px;
                text-align: center;
            }}
            QProgressBar::chunk {{
                background-color: {THEME['primary']};
            }}
        """)
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)
        
        # 状态标签
        self.status_label = QLabel("")
        self.status_label.setStyleSheet(f"color: {THEME['text_secondary']};")
        self.status_label.setVisible(False)
        layout.addWidget(self.status_label)
        
        # 结果显示
        self.result_text = QTextEdit()
        self.result_text.setReadOnly(True)
        self.result_text.setStyleSheet(f"""
            QTextEdit {{
                border: 1px solid {THEME['border']};
                border-radius: 4px;
                padding: 10px;
                background-color: {THEME['card_bg']};
            }}
        """)
        self.result_text.setVisible(False)
        layout.addWidget(self.result_text)
        
        # 按钮
        btn_layout = QHBoxLayout()
        
        self.test_btn = QPushButton("🔍 开始测试")
        self.test_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {THEME['primary']};
                color: white;
                border: none;
                border-radius: 4px;
                padding: 10px 20px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {THEME['primary_dark']};
            }}
            QPushButton:disabled {{
                background-color: {THEME['border']};
            }}
        """)
        self.test_btn.clicked.connect(self.start_test)
        btn_layout.addWidget(self.test_btn)
        
        close_btn = QPushButton("关闭")
        close_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {THEME['card_bg']};
                border: 1px solid {THEME['border']};
                border-radius: 4px;
                padding: 10px 20px;
            }}
        """)
        close_btn.clicked.connect(self.close)
        btn_layout.addWidget(close_btn)
        
        layout.addLayout(btn_layout)
    
    def start_test(self):
        remote_addr = self.remote_input.text().strip()
        
        if not remote_addr:
            QMessageBox.warning(self, "提示", "请输入对方的 IPv6 地址")
            return
        
        # 获取本地地址
        from scanner import IPv6Scanner
        scanner = IPv6Scanner()
        addresses = scanner.scan_all_interfaces()
        usable_addrs = [addr for addr in addresses if addr.is_usable]
        
        if not usable_addrs:
            QMessageBox.warning(self, "错误", "未找到可用的 IPv6 地址")
            return
        
        local_addr = usable_addrs[0].address
        
        # 开始测试
        self.test_btn.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        self.status_label.setVisible(True)
        self.result_text.setVisible(False)
        
        self.test_thread = TestThread(local_addr, remote_addr)
        self.test_thread.progress.connect(self.on_progress)
        self.test_thread.finished.connect(self.on_finished)
        self.test_thread.start()
    
    def on_progress(self, value, message):
        self.progress_bar.setValue(value)
        self.status_label.setText(message)
    
    def on_finished(self, result):
        self.test_btn.setEnabled(True)
        self.progress_bar.setVisible(False)
        self.status_label.setVisible(False)
        self.result_text.setVisible(True)
        
        # 显示结果
        text = f"""
【测试结果】

运营商信息：
  你的运营商: {result['local_isp']}
  对方运营商: {result['remote_isp']}
  {'⚠️ 跨运营商连接（可能单向不通）' if result['cross_isp'] else '✅ 同运营商（连接稳定）'}

连通性测试：
  你 → 对方: {result['local_to_remote']['message']}

【建议】
{result['recommendation']}

💡 提示：
• Ping 通不代表 100% 能连上游戏，还需要房主正确设置防火墙端口
• 如果 Ping 不通，基本无法连接，建议换方向或使用 VPN
"""
        self.result_text.setText(text.strip())


class AddressCard(QFrame):
    """单个地址卡片组件"""
    
    def __init__(self, ipv6_addr: IPv6Address, scale: float = 1.0, is_recommended: bool = False, parent=None):
        super().__init__(parent)
        self.ipv6_addr = ipv6_addr
        self.scale = scale
        self.is_recommended = is_recommended
        self._setup_ui()
    
    def _setup_ui(self):
        border_color = THEME['recommend'] if self.is_recommended else THEME['border']
        border_width = 3 if self.is_recommended else 2
        
        self.setStyleSheet(f"""
            AddressCard {{
                background-color: {THEME['card_bg']};
                border: {border_width}px solid {border_color};
                border-radius: 10px;
            }}
            AddressCard:hover {{
                border-color: {THEME['primary']};
                background-color: #fafbfc;
            }}
        """)
        
        layout = QHBoxLayout(self)
        margin = int(15 * self.scale)
        layout.setContentsMargins(margin, int(12 * self.scale), margin, int(12 * self.scale))
        
        info_layout = QVBoxLayout()
        info_layout.setSpacing(int(6 * self.scale))
        
        addr_label = QLabel(self.ipv6_addr.address)
        addr_font = QFont("Consolas", int(11 * self.scale))
        addr_font.setBold(True)
        addr_label.setFont(addr_font)
        
        if self.ipv6_addr.is_usable:
            addr_label.setStyleSheet(f"color: {THEME['primary']};")
        else:
            addr_label.setStyleSheet(f"color: {THEME['danger']};")
        
        info_layout.addWidget(addr_label)
        
        temp_label = "临时地址" if self.ipv6_addr.is_temporary else "正常地址"
        usable_label = "可用于通信" if self.ipv6_addr.is_usable else "不可用于通信"
        detail_text = f"接口: {self.ipv6_addr.interface_name} | {temp_label} | {usable_label}"
        detail_label = QLabel(detail_text)
        detail_label.setStyleSheet(f"color: {THEME['text_secondary']}; font-size: {int(9 * self.scale)}pt;")
        info_layout.addWidget(detail_label)
        
        layout.addLayout(info_layout, 1)
        
        # 推荐标签
        if self.is_recommended:
            recommend_label = QLabel("⭐ 推荐")
            recommend_label.setStyleSheet(f"""
                background-color: {THEME['recommend']};
                color: white;
                border-radius: 5px;
                padding: 5px 12px;
                font-weight: bold;
                font-size: {int(9 * self.scale)}pt;
            """)
            layout.addWidget(recommend_label)
        
        copy_btn = QPushButton("📋 复制")
        copy_btn.setFixedWidth(int(80 * self.scale))
        copy_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {THEME['primary']};
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 14px;
                font-weight: bold;
                font-size: {int(9 * self.scale)}pt;
            }}
            QPushButton:hover {{
                background-color: {THEME['primary_dark']};
            }}
        """)
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
        self.setWindowTitle("🎮 我的世界 IPv6 联机工具")
        
        # 设置更大的窗口尺寸，确保内容不被挤压
        base_width, base_height = 850, 950
        width = int(base_width * self.scale)
        height = int(base_height * self.scale)
        self.setMinimumSize(int(800 * self.scale), int(850 * self.scale))
        self.resize(width, height)
        
        self.setStyleSheet(f"QMainWindow {{ background-color: {THEME['bg']}; }}")
        
        central = QWidget()
        self.setCentralWidget(central)
        
        margin = int(20 * self.scale)
        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(margin, margin, margin, margin)
        main_layout.setSpacing(int(12 * self.scale))
        
        # 标题区域 - 增加高度和间距
        title_frame = QFrame()
        title_frame.setFixedHeight(int(140 * self.scale))
        title_frame.setStyleSheet(f"""
            QFrame {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 {THEME['primary']}, stop:1 {THEME['primary_light']});
                border-radius: 12px;
                border: 1px solid rgba(255,255,255,0.1);
            }}
        """)
        title_layout = QVBoxLayout(title_frame)
        title_layout.setSpacing(int(10 * self.scale))
        title_layout.setContentsMargins(20, 20, 20, 20)
        
        title_label = QLabel("🎮 我的世界 IPv6 联机工具")
        title_label.setStyleSheet(f"color: white; font-size: {int(20 * self.scale)}pt; font-weight: bold;")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_layout.addWidget(title_label)
        
        subtitle_label = QLabel("Minecraft IPv6 Connection Tool")
        subtitle_label.setStyleSheet(f"color: rgba(255,255,255,0.8); font-size: {int(10 * self.scale)}pt;")
        subtitle_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_layout.addWidget(subtitle_label)
        
        desc_label = QLabel("💡 房主和玩家都需要使用此工具进行测试")
        desc_label.setStyleSheet(f"color: rgba(255,255,255,0.95); font-size: {int(11 * self.scale)}pt;")
        desc_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        desc_label.setWordWrap(True)
        title_layout.addWidget(desc_label)
        
        main_layout.addWidget(title_frame)
        
        # 使用步骤提示 - 增加高度和更好的布局
        warning_frame = QFrame()
        warning_frame.setMinimumHeight(int(100 * self.scale))
        warning_frame.setStyleSheet(f"""
            QFrame {{
                background-color: #E8F5E9;
                border: 2px solid {THEME['accent']};
                border-radius: 10px;
            }}
        """)
        warning_layout = QVBoxLayout(warning_frame)
        warning_layout.setContentsMargins(20, 12, 20, 12)
        warning_layout.setSpacing(int(10 * self.scale))
        
        warning_title = QLabel("📋 使用步骤")
        warning_title.setStyleSheet(f"color: {THEME['accent']}; font-size: {int(12 * self.scale)}pt; font-weight: bold;")
        warning_layout.addWidget(warning_title)
        
        warning_label = QLabel("1️⃣ 双方交换 IPv6 地址 → 2️⃣ 点击「连通性测试」判断谁当房主 → 3️⃣ 房主设置端口并开房 → 4️⃣ 结束后删除规则")
        warning_label.setStyleSheet(f"color: {THEME['text']}; font-size: {int(10 * self.scale)}pt; line-height: 1.5;")
        warning_label.setWordWrap(True)
        warning_layout.addWidget(warning_label)
        main_layout.addWidget(warning_frame)
        
        # 顶部按钮区域 - 增加间距
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(int(12 * self.scale))
        btn_style = f"""
            QPushButton {{
                background-color: {THEME['card_bg']};
                border: 2px solid {THEME['border']};
                border-radius: 8px;
                padding: {int(12 * self.scale)}px {int(20 * self.scale)}px;
                font-size: {int(10 * self.scale)}pt;
                min-height: {int(40 * self.scale)}px;
                color: {THEME['text']};
                font-weight: 500;
            }}
            QPushButton:hover {{
                background-color: {THEME['primary']};
                color: white;
                border-color: {THEME['primary']};
                transform: translateY(-2px);
            }}
        """
        
        refresh_btn = QPushButton("🔄 刷新地址")
        refresh_btn.setStyleSheet(btn_style)
        refresh_btn.clicked.connect(self._refresh_addresses)
        btn_layout.addWidget(refresh_btn)
        
        test_btn = QPushButton("🌐 IPv6 连通性测试")
        test_btn.setStyleSheet(btn_style)
        test_btn.clicked.connect(self._open_ipv6_test)
        btn_layout.addWidget(test_btn)
        
        connectivity_btn = QPushButton("🔍 连通性测试")
        connectivity_btn.setStyleSheet(btn_style)
        connectivity_btn.clicked.connect(self._open_connectivity_test)
        btn_layout.addWidget(connectivity_btn)
        
        btn_layout.addStretch()
        main_layout.addLayout(btn_layout)
        
        # 防火墙设置区域
        firewall_group = QGroupBox("🔥 防火墙端口设置（仅房主需要）")
        firewall_group.setStyleSheet(f"""
            QGroupBox {{
                font-size: 11pt;
                font-weight: bold;
                color: {THEME['text']};
                background-color: {THEME['card_bg']};
                border: 2px solid {THEME['border']};
                border-radius: 10px;
                margin-top: 12px;
                padding-top: 12px;
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 20px;
                padding: 0 10px;
                background-color: {THEME['card_bg']};
            }}
        """)
        firewall_layout = QHBoxLayout(firewall_group)
        firewall_layout.setContentsMargins(20, 25, 20, 20)
        firewall_layout.setSpacing(int(12 * self.scale))
        
        port_label = QLabel("端口:")
        port_label.setStyleSheet(f"color: {THEME['text']}; font-weight: normal; font-size: 10pt;")
        firewall_layout.addWidget(port_label)
        
        self.port_input = QLineEdit()
        self.port_input.setPlaceholderText("如: 8080 或 80,443 或 5000-5010")
        self.port_input.setFixedWidth(int(220 * self.scale))
        self.port_input.setStyleSheet(f"""
            QLineEdit {{
                border: 2px solid {THEME['border']};
                border-radius: 6px;
                padding: 8px 12px;
                font-size: 10pt;
                background-color: white;
            }}
            QLineEdit:focus {{
                border-color: {THEME['primary']};
            }}
        """)
        firewall_layout.addWidget(self.port_input)
        
        set_port_btn = QPushButton("✅ 设置端口")
        set_port_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {THEME['success']};
                color: white;
                border: none;
                border-radius: 6px;
                padding: 10px 20px;
                font-weight: bold;
                font-size: 10pt;
            }}
            QPushButton:hover {{
                background-color: {THEME['accent_hover']};
            }}
        """)
        set_port_btn.clicked.connect(self._set_firewall_port)
        firewall_layout.addWidget(set_port_btn)
        
        delete_rule_btn = QPushButton("🗑️ 删除规则")
        delete_rule_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {THEME['danger']};
                color: white;
                border: none;
                border-radius: 6px;
                padding: 10px 20px;
                font-weight: bold;
                font-size: 10pt;
            }}
            QPushButton:hover {{
                background-color: #C62828;
            }}
        """)
        delete_rule_btn.clicked.connect(self._delete_firewall_rule)
        firewall_layout.addWidget(delete_rule_btn)
        
        firewall_layout.addStretch()
        main_layout.addWidget(firewall_group)
        
        # 状态标签
        self.status_label = QLabel("正在扫描...")
        self.status_label.setStyleSheet(f"color: {THEME['text_secondary']}; font-size: 10pt;")
        main_layout.addWidget(self.status_label)
        
        # 地址列表滚动区域
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setStyleSheet(f"""
            QScrollArea {{
                border: 1px solid {THEME['border']};
                border-radius: 8px;
                background-color: {THEME['card_bg']};
            }}
        """)
        scroll.setMinimumHeight(int(250 * self.scale))
        
        self.list_widget = QWidget()
        self.list_widget.setStyleSheet(f"background-color: {THEME['card_bg']};")
        self.list_layout = QVBoxLayout(self.list_widget)
        self.list_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.list_layout.setSpacing(int(8 * self.scale))
        self.list_layout.setContentsMargins(10, 10, 10, 10)
        
        scroll.setWidget(self.list_widget)
        main_layout.addWidget(scroll, 1)
        
        # 底部说明
        legend = QLabel("🔵 蓝色 = 可用于外部通信  🔴 红色 = 不可用于外部通信  ⭐ 推荐 = 临时地址（更安全）")
        legend.setStyleSheet(f"color: {THEME['text_secondary']}; font-size: 9pt;")
        legend.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(legend)
        
        # 作者信息
        footer_layout = QHBoxLayout()
        footer_layout.setContentsMargins(0, 5, 0, 0)
        
        author_label = QLabel("作者: Bole")
        author_label.setStyleSheet(f"color: {THEME['text_secondary']}; font-size: 9pt;")
        footer_layout.addWidget(author_label)
        
        footer_layout.addStretch()
        
        github_btn = QPushButton("📦 GitHub")
        github_btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                color: {THEME['primary']};
                border: none;
                font-size: 9pt;
                text-decoration: underline;
            }}
            QPushButton:hover {{
                color: {THEME['primary_dark']};
            }}
        """)
        github_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        github_btn.clicked.connect(self._open_github)
        footer_layout.addWidget(github_btn)
        
        main_layout.addLayout(footer_layout)
    
    def _open_github(self):
        """打开 GitHub 项目页面"""
        import webbrowser
        webbrowser.open("https://github.com/ykandbl/mc-ipv6-tool")
    
    def _open_connectivity_test(self):
        """打开连通性测试对话框"""
        dialog = ConnectivityTestDialog(self)
        dialog.exec()
    
    def _sort_addresses(self, addresses):
        """排序地址：临时地址 > 正常地址 > 本地地址"""
        def sort_key(addr):
            # 优先级：可用临时地址(0) > 可用正常地址(1) > 不可用地址(2)
            if addr.is_usable and addr.is_temporary:
                return (0, addr.interface_name)
            elif addr.is_usable and not addr.is_temporary:
                return (1, addr.interface_name)
            else:
                return (2, addr.interface_name)
        return sorted(addresses, key=sort_key)
    
    def _refresh_addresses(self):
        """刷新地址列表"""
        while self.list_layout.count():
            item = self.list_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        addresses = self.scanner.scan_all_interfaces()
        addresses = self._sort_addresses(addresses)
        
        if not addresses:
            self.status_label.setText("未找到 IPv6 地址")
            no_addr_label = QLabel("当前系统没有可用的 IPv6 地址")
            no_addr_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            no_addr_label.setStyleSheet(f"color: {THEME['text_secondary']}; padding: 20px;")
            self.list_layout.addWidget(no_addr_label)
            return
        
        usable_count = sum(1 for addr in addresses if addr.is_usable)
        self.status_label.setText(
            f"📡 找到 {len(addresses)} 个 IPv6 地址，其中 {usable_count} 个可用于外部通信"
        )
        
        for addr in addresses:
            # 临时地址且可用的标记为推荐
            is_recommended = addr.is_usable and addr.is_temporary
            card = AddressCard(addr, self.scale, is_recommended)
            self.list_layout.addWidget(card)
    
    def _open_ipv6_test(self):
        """打开 IPv6 测试网站"""
        if not BrowserLauncher.open_ipv6_test():
            QMessageBox.warning(
                self, "错误", 
                f"无法打开浏览器\n请手动访问: {BrowserLauncher.IPV6_TEST_URL}"
            )
    
    def _set_firewall_port(self):
        """设置防火墙入站规则端口"""
        port = self.port_input.text().strip()
        
        if not port:
            QMessageBox.warning(self, "提示", "请输入端口号")
            return
        
        success, message, rule_info = set_firewall_port(port)
        
        if success:
            info_text = "✅ 规则设置成功！\n\n📋 规则详情：\n"
            info_text += "─" * 30 + "\n"
            for key, value in rule_info.items():
                info_text += f"  {key}: {value}\n"
            info_text += "─" * 30 + "\n"
            info_text += "\n💡 玩家现在可以通过此端口连接到你的游戏了！"
            info_text += "\n\n⚠️ 结束联机后请务必点击「删除规则」！"
            QMessageBox.information(self, "设置成功", info_text)
        else:
            QMessageBox.warning(self, "设置失败", message)
    
    def _delete_firewall_rule(self):
        """删除防火墙入站规则"""
        reply = QMessageBox.question(
            self, "确认删除",
            "确定要删除「买块房主规则」入站规则吗？\n\n删除后玩家将无法通过此端口连接。",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply != QMessageBox.StandardButton.Yes:
            return
        
        success, message = remove_firewall_port()
        
        if success:
            QMessageBox.information(self, "删除成功", f"✅ {message}\n\n端口已关闭，网络安全已恢复。")
        else:
            QMessageBox.warning(self, "删除失败", message)
