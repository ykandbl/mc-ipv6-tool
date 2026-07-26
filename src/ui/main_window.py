"""主窗口与联机向导界面。"""
from __future__ import annotations

import webbrowser
from collections.abc import Callable

from PyQt6.QtCore import Qt, QThread, QTimer, pyqtSignal
from PyQt6.QtGui import QCloseEvent, QFont
from PyQt6.QtWidgets import (
    QApplication,
    QComboBox,
    QDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from app_version import APP_NAME, APP_VERSION
from clipboard import ClipboardHandler
from connectivity_test import (
    ConnectivityTester,
    combine_direction_results,
)
from firewall import (
    FirewallRuleState,
    get_firewall_rule_state,
    remove_firewall_port,
    set_firewall_port,
    validate_port_spec,
)
from ipv6_readiness import IPv6ReadinessTester, ReadinessResult
from scanner import IPv6Address, IPv6Scanner
from ui.app_icon import create_app_icon
from validator import AddressValidator

THEME = {
    "ink": "#18211B",
    "muted": "#68736B",
    "canvas": "#F3F5F1",
    "card": "#FFFFFF",
    "line": "#DDE3DC",
    "green": "#2F6B48",
    "green_hover": "#24583A",
    "green_soft": "#EAF3ED",
    "lime": "#C7E36C",
    "orange": "#B96625",
    "orange_soft": "#FFF2E8",
    "red": "#B7403A",
    "red_soft": "#FCEDEC",
    "navy": "#1C2921",
}

APP_STYLE = f"""
QWidget {{ color: {THEME['ink']}; font-family: "Microsoft YaHei UI"; font-size: 10pt; }}
QMainWindow, QDialog {{ background: {THEME['canvas']}; }}
QFrame#card {{ background: {THEME['card']}; border: 1px solid {THEME['line']}; border-radius: 16px; }}
QFrame#subcard {{ background: #F8FAF7; border: 1px solid {THEME['line']}; border-radius: 12px; }}
QFrame#hero {{ background: {THEME['navy']}; border: none; border-radius: 18px; }}
QLineEdit, QComboBox {{
    background: white; border: 1px solid #CCD5CC; border-radius: 9px;
    padding: 10px 12px; min-height: 22px; selection-background-color: {THEME['green']};
}}
QLineEdit:focus, QComboBox:focus {{ border: 2px solid {THEME['green']}; padding: 9px 11px; }}
QLineEdit:disabled, QComboBox:disabled {{ color: #7B857D; background: #EEF1ED; }}
QPushButton {{
    border: 1px solid #C9D2C9; border-radius: 9px; padding: 10px 16px;
    background: white; font-weight: 600;
}}
QPushButton:hover:enabled {{ border-color: {THEME['green']}; background: {THEME['green_soft']}; }}
QPushButton:pressed:enabled {{ background: #DDEBE1; }}
QPushButton:disabled {{ color: #929A94; border-color: #DDE2DD; background: #EEF1EE; }}
QPushButton#primary {{ background: {THEME['green']}; color: white; border: none; }}
QPushButton#primary:hover:enabled {{ background: {THEME['green_hover']}; }}
QPushButton#dark {{ background: {THEME['navy']}; color: white; border: none; }}
QPushButton#danger {{ color: {THEME['red']}; border-color: #E5BBB8; background: {THEME['red_soft']}; }}
QPushButton#danger:hover:enabled {{ background: #F7DAD8; }}
QPushButton#primary:disabled, QPushButton#dark:disabled {{
    color: #929A94; border: 1px solid #DDE2DD; background: #E8ECE8;
}}
QPushButton#danger:disabled {{ color: #A8AFAA; border-color: #DDE2DD; background: #EEF1EE; }}
QProgressBar {{ border: none; border-radius: 4px; background: #E3E8E2; text-align: center; min-height: 8px; max-height: 8px; }}
QProgressBar::chunk {{ border-radius: 4px; background: {THEME['green']}; }}
QScrollArea {{ border: none; background: transparent; }}
QScrollBar:vertical {{ background: transparent; width: 10px; margin: 2px; }}
QScrollBar::handle:vertical {{ background: #C9D1CA; border-radius: 4px; min-height: 34px; }}
QScrollBar::handle:vertical:hover {{ background: #AEB9B0; }}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}
QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{ background: transparent; }}
QToolTip {{ background: {THEME['navy']}; color: white; border: none; padding: 6px; }}
"""


class TaskThread(QThread):
    progress = pyqtSignal(int, str)
    result_ready = pyqtSignal(object)
    failed = pyqtSignal(str)

    def __init__(self, operation: Callable, parent=None):
        super().__init__(parent)
        self.operation = operation

    def run(self) -> None:
        try:
            self.result_ready.emit(self.operation(self.progress.emit))
        except Exception as exc:  # noqa: BLE001 - 线程边界必须转换成 UI 信号
            self.failed.emit(str(exc))


def make_title(text: str, size: int = 15) -> QLabel:
    label = QLabel(text)
    label.setFont(QFont("Microsoft YaHei UI", size, QFont.Weight.DemiBold))
    return label


def make_step(number: str, title: str) -> QHBoxLayout:
    row = QHBoxLayout()
    row.setSpacing(10)
    badge = QLabel(number)
    badge.setFixedSize(34, 34)
    badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
    badge.setStyleSheet(
        f"background:{THEME['green_soft']};color:{THEME['green']};"
        "border-radius:9px;font-weight:700;font-size:10pt;"
    )
    row.addWidget(badge)
    row.addWidget(make_title(title, 14), 1)
    return row


def set_copy_feedback(button: QPushButton, original: str) -> None:
    button.setText("已复制")
    button.setEnabled(False)
    QTimer.singleShot(1200, lambda: (button.setText(original), button.setEnabled(True)))


class AddressCard(QFrame):
    def __init__(self, address: IPv6Address, recommended: bool = False, parent=None):
        super().__init__(parent)
        self.address = address
        self.setObjectName("subcard")
        if recommended:
            self.setStyleSheet(f"QFrame#subcard{{border:2px solid {THEME['green']};}}")
        layout = QHBoxLayout(self)
        layout.setContentsMargins(14, 11, 14, 11)
        text = QVBoxLayout()
        value = QLabel(address.address)
        value.setFont(QFont("Consolas", 10, QFont.Weight.DemiBold))
        value.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        text.addWidget(value)
        details = [address.interface_name, "临时" if address.is_temporary else "稳定"]
        if address.is_virtual:
            details.append("虚拟网卡")
        detail = QLabel(" · ".join(details))
        detail.setStyleSheet(f"color:{THEME['muted']};font-size:9pt;")
        text.addWidget(detail)
        layout.addLayout(text, 1)
        if recommended:
            badge = QLabel("推荐分享")
            badge.setStyleSheet(
                f"background:{THEME['green_soft']};color:{THEME['green']};"
                "padding:5px 8px;border-radius:6px;font-weight:600;"
            )
            layout.addWidget(badge)
        copy_button = QPushButton("复制")
        copy_button.clicked.connect(lambda: self._copy(copy_button))
        layout.addWidget(copy_button)

    def _copy(self, button: QPushButton) -> None:
        if ClipboardHandler.copy_to_clipboard(self.address.address):
            set_copy_feedback(button, "复制")


class ConnectivityTestDialog(QDialog):
    """测试“本机 → 对方”，再由用户确认反向测试结果。"""

    def __init__(self, addresses: list[IPv6Address], parent=None):
        super().__init__(parent)
        self.addresses = [address for address in addresses if address.is_usable]
        self.test_thread: TaskThread | None = None
        self.local_result: dict | None = None
        self.outcome_selected = False
        self.tested_source = ""
        self.tested_target = ""
        self.setWindowTitle("双向连通性测试")
        self.setMinimumSize(720, 680)
        self.resize(760, 760)
        self.setStyleSheet(APP_STYLE)
        self._setup_ui()

    def _setup_ui(self) -> None:
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        self.scroll = scroll
        content = QWidget()
        scroll.setWidget(content)
        layout = QVBoxLayout(content)
        layout.setContentsMargins(26, 24, 26, 20)
        layout.setSpacing(14)

        header = QFrame()
        header.setObjectName("hero")
        header_layout = QVBoxLayout(header)
        header_layout.setContentsMargins(22, 18, 22, 18)
        title = make_title("双向连通性测试", 18)
        title.setStyleSheet("color:white;")
        subtitle = QLabel("双方分别完成一次单向测试，再根据对方反馈合并测试结果")
        subtitle.setStyleSheet("color:#C9D5CC;")
        subtitle.setWordWrap(True)
        header_layout.addWidget(title)
        header_layout.addWidget(subtitle)
        layout.addWidget(header)

        direction_note = QLabel(
            "判断原则：本机可访问对方 → 对方具备房主方向条件；对方可访问本机 → 本机具备房主方向条件。Ping 仅用于初步检测。"
        )
        direction_note.setWordWrap(True)
        direction_note.setStyleSheet(
            f"background:{THEME['green_soft']};color:{THEME['green']};"
            "padding:11px 13px;border-radius:9px;font-weight:600;"
        )
        layout.addWidget(direction_note)

        source_card = QFrame()
        source_card.setObjectName("card")
        source_layout = QVBoxLayout(source_card)
        source_layout.setContentsMargins(16, 14, 16, 14)
        source_layout.addWidget(make_title("1. 复制本机地址并发送给对方", 12))
        source_row = QHBoxLayout()
        self.source_combo = QComboBox()
        for address in self.addresses:
            suffix = " · 推荐" if address.is_temporary and not address.is_virtual else ""
            self.source_combo.addItem(f"{address.address} · {address.interface_name}{suffix}", address.address)
        source_row.addWidget(self.source_combo, 1)
        self.copy_address_button = QPushButton("复制本机地址")
        self.copy_address_button.setObjectName("primary")
        self.copy_address_button.clicked.connect(self._copy_my_address)
        source_row.addWidget(self.copy_address_button)
        source_layout.addLayout(source_row)
        layout.addWidget(source_card)

        target_card = QFrame()
        target_card.setObjectName("card")
        target_layout = QVBoxLayout(target_card)
        target_layout.setContentsMargins(16, 14, 16, 14)
        target_layout.addWidget(make_title("2. 输入对方地址，测试本机 → 对方", 12))
        self.remote_input = QLineEdit()
        self.remote_input.setPlaceholderText("对方的 IPv6 地址，例如 2409:xxxx:xxxx::1234")
        self.remote_input.textChanged.connect(self._validate_input)
        target_layout.addWidget(self.remote_input)
        self.validation_label = QLabel("等待输入对方发送的 IPv6 地址")
        self.validation_label.setStyleSheet(f"color:{THEME['muted']};font-size:9pt;")
        target_layout.addWidget(self.validation_label)
        self.test_button = QPushButton("测试本机 → 对方")
        self.test_button.setObjectName("dark")
        self.test_button.setEnabled(False)
        self.test_button.clicked.connect(self._start_test)
        target_layout.addWidget(self.test_button, alignment=Qt.AlignmentFlag.AlignLeft)
        layout.addWidget(target_card)

        self.progress = QProgressBar()
        self.progress.setRange(0, 100)
        self.progress.setVisible(False)
        layout.addWidget(self.progress)
        self.status_label = QLabel("")
        self.status_label.setStyleSheet(f"color:{THEME['muted']};")
        layout.addWidget(self.status_label)

        self.result_frame = QFrame()
        self.result_frame.setObjectName("card")
        result_layout = QVBoxLayout(self.result_frame)
        result_layout.setContentsMargins(16, 15, 16, 15)
        self.direction_title = make_title("", 13)
        self.direction_message = QLabel("")
        self.direction_message.setWordWrap(True)
        result_layout.addWidget(self.direction_title)
        result_layout.addWidget(self.direction_message)
        divider = QFrame()
        divider.setFixedHeight(1)
        divider.setStyleSheet(f"background:{THEME['line']};border:none;margin:6px 0;")
        result_layout.addWidget(divider)
        result_layout.addWidget(make_title("3. 请选择对方的反向测试结果", 12))
        feedback_note = QLabel("请对方测试本机地址，并根据对方反馈选择相应结果。")
        feedback_note.setWordWrap(True)
        feedback_note.setStyleSheet(f"color:{THEME['muted']};")
        result_layout.addWidget(feedback_note)
        feedback_row = QHBoxLayout()
        friend_can_connect = QPushButton("对方可以连接本机")
        friend_can_connect.setObjectName("primary")
        friend_can_connect.clicked.connect(lambda: self._combine_results(True))
        friend_cannot_connect = QPushButton("对方无法连接本机")
        friend_cannot_connect.setObjectName("danger")
        friend_cannot_connect.clicked.connect(lambda: self._combine_results(False))
        feedback_row.addWidget(friend_can_connect)
        feedback_row.addWidget(friend_cannot_connect)
        result_layout.addLayout(feedback_row)
        self.final_result = QLabel("")
        self.final_result.setWordWrap(True)
        self.final_result.setVisible(False)
        result_layout.addWidget(self.final_result)
        self.result_frame.setVisible(False)
        layout.addWidget(self.result_frame)
        layout.addStretch()
        outer.addWidget(scroll, 1)

        footer = QFrame()
        footer.setStyleSheet(f"background:white;border-top:1px solid {THEME['line']};")
        footer_layout = QHBoxLayout(footer)
        footer_layout.setContentsMargins(26, 12, 26, 12)
        footer_layout.addStretch()
        self.close_button = QPushButton("完成并关闭")
        self.close_button.clicked.connect(self.close)
        footer_layout.addWidget(self.close_button)
        outer.addWidget(footer)

    def _copy_my_address(self) -> None:
        address = str(self.source_combo.currentData() or "")
        if address and ClipboardHandler.copy_to_clipboard(address):
            set_copy_feedback(self.copy_address_button, "复制本机地址")

    def _validate_input(self) -> None:
        valid, clean, _ = AddressValidator.clean_user_input(self.remote_input.text())
        self.test_button.setEnabled(valid and bool(self.addresses) and not self._is_running())
        if not self.remote_input.text().strip():
            text, color = "等待输入对方发送的 IPv6 地址", THEME["muted"]
        elif valid:
            text, color = f"地址格式正确：{clean}", THEME["green"]
        else:
            text, color = "地址格式不正确，请重新复制完整 IPv6 地址", THEME["red"]
        self.validation_label.setText(text)
        self.validation_label.setStyleSheet(f"color:{color};font-size:9pt;")

    def _is_running(self) -> bool:
        return bool(self.test_thread and self.test_thread.isRunning())

    def _start_test(self) -> None:
        valid, remote_address, _ = AddressValidator.clean_user_input(self.remote_input.text())
        if not valid:
            return
        self.tested_source = str(self.source_combo.currentData())
        self.tested_target = remote_address
        self.local_result = None
        self.test_button.setEnabled(False)
        self.close_button.setEnabled(False)
        self.source_combo.setEnabled(False)
        self.remote_input.setEnabled(False)
        self.result_frame.setVisible(False)
        self.final_result.setVisible(False)
        self.progress.setVisible(True)
        self.progress.setValue(0)
        self.status_label.setText("正在准备测试…")
        tester = ConnectivityTester()
        self.test_thread = TaskThread(
            lambda progress: tester.test_bidirectional(self.tested_source, self.tested_target, progress), self
        )
        self.test_thread.progress.connect(self._on_progress)
        self.test_thread.result_ready.connect(self._on_result)
        self.test_thread.failed.connect(self._on_error)
        self.test_thread.start()

    def _on_progress(self, value: int, message: str) -> None:
        self.progress.setValue(value)
        self.status_label.setText(message)

    def _finish_test_ui(self) -> None:
        self.progress.setVisible(False)
        self.close_button.setEnabled(True)
        self.source_combo.setEnabled(True)
        self.remote_input.setEnabled(True)
        self.test_button.setEnabled(True)
        self.test_button.setText("重新测试本机 → 对方")

    def _on_result(self, result: dict) -> None:
        self.local_result = result
        self._finish_test_ui()
        success = result["local_to_remote"]["success"]
        self.result_frame.setVisible(True)
        self.direction_title.setText("本机 → 对方：连接正常" if success else "本机 → 对方：未收到响应")
        color = THEME["green"] if success else THEME["orange"]
        self.direction_title.setStyleSheet(f"color:{color};")
        direction = result["local_to_remote"]
        message = (
            f"本机运营商（按 IPv6 前缀推测）：{result['local_isp']}\n"
            f"对方运营商（按 IPv6 前缀推测）：{result['remote_isp']}\n"
            f"连接测试：本机 → 对方 · {direction['message']}。\n"
        )
        message += "对方的房主方向已通过初步检测。" if success else "该结果不足以判断本机房主方向，仍需参考对方的反向测试。"
        if result["cross_isp"]:
            message += "\n双方运营商不同，两个方向出现不同结果的概率会更高。"
        self.direction_message.setText(message)
        self.status_label.setText("等待对方完成反向测试后，请选择对应结果")
        QTimer.singleShot(0, lambda: self.scroll.verticalScrollBar().setValue(self.scroll.verticalScrollBar().maximum()))

    def _on_error(self, message: str) -> None:
        self._finish_test_ui()
        self.status_label.setText(f"测试失败：{message}")

    def _combine_results(self, remote_success: bool) -> None:
        if not self.local_result:
            return
        outcome = combine_direction_results(
            self.local_result["local_to_remote"]["success"], remote_success
        )
        self.final_result.setText(f"<h3>{outcome['title']}</h3><p>{outcome['message']}</p>")
        self.final_result.setStyleSheet(
            f"background:{THEME['green_soft']};padding:13px;border-radius:9px;color:{THEME['ink']};"
        )
        self.final_result.setVisible(True)
        self.outcome_selected = True

    def closeEvent(self, event: QCloseEvent) -> None:
        if self._is_running():
            event.ignore()
            self.status_label.setText("测试正在进行，请等待几秒后再关闭")
            return
        event.accept()


class PortTestDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.thread: TaskThread | None = None
        self.setWindowTitle("房主端口连通性测试")
        self.setMinimumWidth(590)
        self.setStyleSheet(APP_STYLE)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(26, 24, 26, 24)
        layout.setSpacing(13)
        layout.addWidget(make_title("房主实际 TCP 端口测试", 16))
        note = QLabel(
            "它会尝试建立 IPv6 TCP 连接。通过表示地址、路由、防火墙和端口监听基本正常，"
            "但不保证 Minecraft 版本、模组、白名单或登录验证一定通过。"
        )
        note.setWordWrap(True)
        note.setStyleSheet(f"color:{THEME['muted']};")
        layout.addWidget(note)
        self.input = QLineEdit()
        self.input.setPlaceholderText("完整加入地址，例如 [2409:xxxx::1234]:25565")
        self.input.textChanged.connect(self._validate)
        layout.addWidget(self.input)
        self.result = QLabel("请输入房主提供的完整连接地址")
        self.result.setWordWrap(True)
        self.result.setStyleSheet(f"background:#F8FAF7;color:{THEME['muted']};padding:12px;border-radius:9px;")
        layout.addWidget(self.result)
        buttons = QHBoxLayout()
        self.test_button = QPushButton("建立 TCP 连接")
        self.test_button.setObjectName("primary")
        self.test_button.setEnabled(False)
        self.test_button.clicked.connect(self._start)
        self.close_button = QPushButton("关闭")
        self.close_button.clicked.connect(self.close)
        buttons.addWidget(self.test_button)
        buttons.addWidget(self.close_button)
        layout.addLayout(buttons)

    def _validate(self) -> None:
        valid, _, port = AddressValidator.clean_user_input(self.input.text())
        running = bool(self.thread and self.thread.isRunning())
        self.test_button.setEnabled(valid and port is not None and not running)

    def _start(self) -> None:
        valid, address, port = AddressValidator.clean_user_input(self.input.text())
        if not valid or port is None:
            return
        self.test_button.setEnabled(False)
        self.close_button.setEnabled(False)
        self.result.setText("正在尝试建立 TCP 连接…")
        tester = ConnectivityTester()
        self.thread = TaskThread(lambda progress: tester.test_port(address, port, progress), self)
        self.thread.result_ready.connect(self._done)
        self.thread.failed.connect(lambda error: self._done({"success": False, "message": error}))
        self.thread.start()

    def _done(self, result: dict) -> None:
        color = THEME["green"] if result["success"] else THEME["orange"]
        suffix = (
            "\n\n注意：这不是 Minecraft 登录测试，仍可能受版本、模组、白名单等因素影响。"
            if result["success"]
            else ""
        )
        self.result.setText(result["message"] + suffix)
        self.result.setStyleSheet(f"background:#F8FAF7;color:{color};font-weight:600;padding:12px;border-radius:9px;")
        self.test_button.setEnabled(True)
        self.close_button.setEnabled(True)

    def closeEvent(self, event: QCloseEvent) -> None:
        if self.thread and self.thread.isRunning():
            event.ignore()
            self.result.setText("端口测试正在进行，请稍候")
        else:
            event.accept()


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.scanner = IPv6Scanner()
        self.addresses: list[IPv6Address] = []
        self.readiness_thread: TaskThread | None = None
        self.firewall_thread: TaskThread | None = None
        self.rule_state_thread: TaskThread | None = None
        self.firewall_state = FirewallRuleState(False, False)
        self.recommended_address = ""
        self.step_labels: list[QLabel] = []
        self.completed_steps: set[int] = set()
        self._initial_started = False
        self._closing = False
        self.rule_timer = QTimer(self)
        self.rule_timer.setInterval(3500)
        self.rule_timer.timeout.connect(lambda: self._refresh_firewall_state(silent=True))
        self.setWindowTitle(f"{APP_NAME} · v{APP_VERSION}")
        self.setMinimumSize(820, 620)
        self.resize(1040, 760)
        self.setStyleSheet(APP_STYLE)
        self._setup_ui()

    def _setup_ui(self) -> None:
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        canvas = QWidget()
        scroll.setWidget(canvas)
        self.setCentralWidget(scroll)
        outer = QHBoxLayout(canvas)
        outer.setContentsMargins(22, 20, 22, 20)
        content = QWidget()
        content.setMaximumWidth(1120)
        outer.addStretch()
        outer.addWidget(content, 1)
        outer.addStretch()
        layout = QVBoxLayout(content)
        layout.setSpacing(15)

        header = QFrame()
        header.setObjectName("hero")
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(24, 20, 24, 20)
        logo = QLabel()
        logo.setFixedSize(52, 52)
        logo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        logo.setPixmap(create_app_icon().pixmap(52, 52))
        header_layout.addWidget(logo)
        brand = QVBoxLayout()
        title = make_title("买块 IPv6 联机工具", 19)
        title.setStyleSheet("color:white;")
        subtitle = QLabel("Minecraft Java · IPv6 直连配置与诊断")
        subtitle.setStyleSheet("color:#BFCBC2;")
        brand.addWidget(title)
        brand.addWidget(subtitle)
        header_layout.addLayout(brand, 1)
        admin_badge = QLabel("管理员模式")
        admin_badge.setStyleSheet(
            "background:#304238;color:#D9E5DB;padding:7px 11px;border-radius:8px;font-size:9pt;font-weight:600;"
        )
        version = QLabel(f"v{APP_VERSION}")
        version.setStyleSheet("color:#9FB0A3;")
        header_layout.addWidget(admin_badge)
        header_layout.addWidget(version)
        layout.addWidget(header)

        guide = QHBoxLayout()
        guide.setSpacing(8)
        for number, text in (("01", "网络检测"), ("02", "双向测试"), ("03", "创建或加入游戏")):
            label = QLabel()
            label.setProperty("step_number", number)
            label.setProperty("step_text", text)
            label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.step_labels.append(label)
            guide.addWidget(label, 1)
        layout.addLayout(guide)
        self._update_step_guide(active_step=1)

        self.network_card = self._build_network_card()
        layout.addWidget(self.network_card)

        self.address_panel = QFrame()
        self.address_panel.setObjectName("card")
        self.address_layout = QVBoxLayout(self.address_panel)
        self.address_layout.setContentsMargins(18, 16, 18, 16)
        self.address_layout.setSpacing(9)
        self.address_panel.setVisible(False)
        layout.addWidget(self.address_panel)

        lower = QHBoxLayout()
        lower.setSpacing(15)
        lower.addWidget(self._build_friend_card(), 1)
        lower.addWidget(self._build_host_card(), 1)
        layout.addLayout(lower)

        footer = QHBoxLayout()
        footer_label = QLabel("本工具不提供中转服务；双向测试结果由双方自行确认")
        footer_label.setStyleSheet(f"color:{THEME['muted']};font-size:9pt;")
        github_button = QPushButton("GitHub")
        github_button.clicked.connect(lambda: webbrowser.open("https://github.com/ykandbl/mc-ipv6-tool"))
        footer.addWidget(footer_label)
        footer.addStretch()
        footer.addWidget(github_button)
        layout.addLayout(footer)
        layout.addStretch()

    def _update_step_guide(self, active_step: int, completed_steps: set[int] | None = None) -> None:
        completed = self.completed_steps if completed_steps is None else completed_steps
        for index, label in enumerate(self.step_labels, start=1):
            number = str(label.property("step_number"))
            text = str(label.property("step_text"))
            if index in completed:
                label.setText(f"完成  {text}")
                label.setStyleSheet(
                    f"background:{THEME['green_soft']};border:1px solid #C9DECF;padding:9px;"
                    f"border-radius:9px;color:{THEME['green']};font-weight:700;"
                )
            elif index == active_step:
                label.setText(f"{number}  {text}")
                label.setStyleSheet(
                    f"background:{THEME['navy']};border:1px solid {THEME['navy']};padding:9px;"
                    "border-radius:9px;color:white;font-weight:700;"
                )
            else:
                label.setText(f"{number}  {text}")
                label.setStyleSheet(
                    f"background:white;border:1px solid {THEME['line']};padding:9px;border-radius:9px;"
                    f"color:{THEME['muted']};font-weight:600;"
                )

    def _build_network_card(self) -> QFrame:
        card = QFrame()
        card.setObjectName("card")
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(20, 18, 20, 18)
        card_layout.setSpacing(10)
        top = QHBoxLayout()
        left = QVBoxLayout()
        left.addLayout(make_step("01", "检测本机 IPv6"))
        self.network_title = QLabel("等待检测")
        self.network_title.setStyleSheet(f"color:{THEME['muted']};font-size:12pt;font-weight:700;margin-top:4px;")
        self.network_summary = QLabel("自动检查公网地址、IPv6 默认路由和纯 IPv6 互联网访问")
        self.network_summary.setWordWrap(True)
        self.network_summary.setStyleSheet(f"color:{THEME['muted']};")
        left.addWidget(self.network_title)
        left.addWidget(self.network_summary)
        top.addLayout(left, 1)
        self.check_button = QPushButton("重新检测")
        self.check_button.setObjectName("primary")
        self.check_button.clicked.connect(self._start_readiness_check)
        top.addWidget(self.check_button, alignment=Qt.AlignmentFlag.AlignTop)
        card_layout.addLayout(top)
        self.network_progress = QProgressBar()
        self.network_progress.setRange(0, 0)
        self.network_progress.setVisible(False)
        card_layout.addWidget(self.network_progress)
        self.checks_layout = QVBoxLayout()
        self.checks_layout.setSpacing(5)
        card_layout.addLayout(self.checks_layout)
        self.quick_address_frame = QFrame()
        self.quick_address_frame.setObjectName("subcard")
        quick_layout = QHBoxLayout(self.quick_address_frame)
        quick_layout.setContentsMargins(13, 9, 13, 9)
        quick_text = QVBoxLayout()
        quick_title = QLabel("推荐分享地址")
        quick_title.setStyleSheet(f"color:{THEME['muted']};font-size:9pt;")
        self.quick_address_value = QLabel("")
        self.quick_address_value.setFont(QFont("Consolas", 10, QFont.Weight.DemiBold))
        self.quick_address_value.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        quick_text.addWidget(quick_title)
        quick_text.addWidget(self.quick_address_value)
        quick_layout.addLayout(quick_text, 1)
        self.quick_copy_button = QPushButton("复制地址")
        self.quick_copy_button.setObjectName("primary")
        self.quick_copy_button.clicked.connect(self._copy_recommended_address)
        quick_layout.addWidget(self.quick_copy_button)
        self.quick_address_frame.setVisible(False)
        card_layout.addWidget(self.quick_address_frame)
        self.address_toggle = QPushButton("查看本机地址")
        self.address_toggle.setVisible(False)
        self.address_toggle.clicked.connect(self._toggle_addresses)
        card_layout.addWidget(self.address_toggle, alignment=Qt.AlignmentFlag.AlignLeft)
        return card

    def _build_friend_card(self) -> QFrame:
        card = QFrame()
        card.setObjectName("card")
        layout = QVBoxLayout(card)
        layout.setContentsMargins(20, 18, 20, 18)
        layout.setSpacing(11)
        layout.addLayout(make_step("02", "执行双向连通性测试"))
        desc = QLabel("双方分别完成一个方向的测试，并根据对方反馈合并测试结果。")
        desc.setWordWrap(True)
        desc.setStyleSheet(f"color:{THEME['muted']};")
        layout.addWidget(desc)
        flow = QLabel("本机 → 对方    ＋    对方 → 本机    ＝    主机选择建议")
        flow.setAlignment(Qt.AlignmentFlag.AlignCenter)
        flow.setStyleSheet(
            f"background:{THEME['green_soft']};color:{THEME['green']};"
            "padding:12px;border-radius:9px;font-weight:700;"
        )
        layout.addWidget(flow)
        for number, instruction in (
            ("1", "复制本机地址并发送给对方"),
            ("2", "双方分别完成一次单向测试"),
            ("3", "根据对方反馈选择测试结果"),
        ):
            item = QHBoxLayout()
            item.setSpacing(9)
            bullet = QLabel(number)
            bullet.setFixedSize(24, 24)
            bullet.setAlignment(Qt.AlignmentFlag.AlignCenter)
            bullet.setStyleSheet(
                f"background:#F0F3EF;color:{THEME['muted']};border-radius:7px;font-size:9pt;font-weight:700;"
            )
            item.addWidget(bullet)
            instruction_label = QLabel(instruction)
            instruction_label.setStyleSheet(f"color:{THEME['muted']};font-size:9pt;")
            item.addWidget(instruction_label, 1)
            layout.addLayout(item)
        layout.addStretch()
        self.friend_button = QPushButton("开始双向测试")
        self.friend_button.setObjectName("primary")
        self.friend_button.setEnabled(False)
        self.friend_button.clicked.connect(self._open_connectivity_test)
        layout.addWidget(self.friend_button)
        return card

    def _build_host_card(self) -> QFrame:
        card = QFrame()
        card.setObjectName("card")
        layout = QVBoxLayout(card)
        layout.setContentsMargins(20, 18, 20, 18)
        layout.setSpacing(10)
        layout.addLayout(make_step("03", "创建或加入游戏"))
        heading = QHBoxLayout()
        host_title = QLabel("作为房主")
        host_title.setStyleSheet("font-weight:700;")
        self.rule_badge = QLabel("正在读取防火墙…")
        self.rule_badge.setStyleSheet(
            f"background:#EEF1EE;color:{THEME['muted']};padding:5px 8px;border-radius:7px;font-size:9pt;"
        )
        heading.addWidget(host_title)
        heading.addStretch()
        heading.addWidget(self.rule_badge)
        layout.addLayout(heading)
        host_note = QLabel("在游戏“对局域网开放”后，输入画面显示的单个端口。")
        host_note.setWordWrap(True)
        host_note.setStyleSheet(f"color:{THEME['muted']};font-size:9pt;")
        layout.addWidget(host_note)
        port_row = QHBoxLayout()
        self.port_input = QLineEdit()
        self.port_input.setPlaceholderText("例如 25565")
        self.port_input.textChanged.connect(self._validate_port)
        self.set_port_button = QPushButton("设置规则")
        self.set_port_button.setObjectName("primary")
        self.set_port_button.setEnabled(False)
        self.set_port_button.clicked.connect(self._set_firewall_port)
        port_row.addWidget(self.port_input, 1)
        port_row.addWidget(self.set_port_button)
        layout.addLayout(port_row)
        self.delete_rule_button = QPushButton("删除现有规则")
        self.delete_rule_button.setObjectName("danger")
        self.delete_rule_button.setEnabled(False)
        self.delete_rule_button.setVisible(False)
        self.delete_rule_button.clicked.connect(self._delete_firewall_rule)
        layout.addWidget(self.delete_rule_button, alignment=Qt.AlignmentFlag.AlignLeft)
        self.firewall_status = QLabel("正在按规则名称检查 Windows 防火墙")
        self.firewall_status.setWordWrap(True)
        self.firewall_status.setStyleSheet(f"color:{THEME['muted']};font-size:9pt;")
        layout.addWidget(self.firewall_status)
        divider = QFrame()
        divider.setFixedHeight(1)
        divider.setStyleSheet(f"background:{THEME['line']};border:none;margin:3px 0;")
        layout.addWidget(divider)
        join_title = QLabel("加入对方游戏")
        join_title.setStyleSheet("font-weight:700;")
        layout.addWidget(join_title)
        port_test_button = QPushButton("测试对方的实际 TCP 端口")
        port_test_button.clicked.connect(self._open_port_test)
        layout.addWidget(port_test_button, alignment=Qt.AlignmentFlag.AlignLeft)
        return card

    def start_initial_checks(self) -> None:
        if self._initial_started:
            return
        self._initial_started = True
        self._start_readiness_check()
        self._refresh_firewall_state()
        self.rule_timer.start()

    def _start_readiness_check(self) -> None:
        if self.readiness_thread and self.readiness_thread.isRunning():
            return
        self.check_button.setEnabled(False)
        self.check_button.setText("检测中…")
        self.network_progress.setVisible(True)
        self.network_title.setText("正在检查地址、路由和 IPv6 互联网连接…")
        self.network_summary.setText("通常需要 2–6 秒")
        self.readiness_thread = TaskThread(lambda _progress: IPv6ReadinessTester(self.scanner).run(), self)
        self.readiness_thread.result_ready.connect(self._show_readiness_result)
        self.readiness_thread.failed.connect(self._readiness_failed)
        self.readiness_thread.start()

    def _clear_layout(self, target: QVBoxLayout) -> None:
        while target.count():
            item = target.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

    def _show_readiness_result(self, result: ReadinessResult) -> None:
        self.network_progress.setVisible(False)
        self.check_button.setEnabled(True)
        self.check_button.setText("重新检测")
        self.addresses = result.addresses
        color = {
            "available": THEME["green"],
            "degraded": THEME["orange"],
            "unavailable": THEME["red"],
        }[result.status]
        self.network_title.setText(result.title)
        self.network_title.setStyleSheet(f"color:{color};font-weight:700;font-size:12pt;margin-top:4px;")
        self.network_summary.setText(result.summary)
        self._clear_layout(self.checks_layout)
        symbols = {"pass": "通过", "warn": "注意", "fail": "失败"}
        colors = {"pass": THEME["green"], "warn": THEME["orange"], "fail": THEME["red"]}
        for check in result.checks:
            label = QLabel(
                f"<b style='color:{colors[check.status]}'>{symbols[check.status]} · {check.label}</b>　{check.detail}"
            )
            label.setWordWrap(True)
            self.checks_layout.addWidget(label)
        has_usable_address = any(address.is_usable for address in self.addresses)
        self.friend_button.setEnabled(has_usable_address)
        self.address_toggle.setVisible(bool(self.addresses))
        self.recommended_address = result.recommended_address
        self.quick_address_value.setText(self.recommended_address)
        self.quick_address_frame.setVisible(bool(self.recommended_address))
        self._render_addresses(result.recommended_address)
        if has_usable_address:
            self.completed_steps.add(1)
            self._update_step_guide(active_step=2)
        else:
            self.completed_steps.discard(1)
            self._update_step_guide(active_step=1)

    def _readiness_failed(self, message: str) -> None:
        self.network_progress.setVisible(False)
        self.check_button.setEnabled(True)
        self.check_button.setText("重新检测")
        self.network_title.setText("检测过程出现错误")
        self.network_title.setStyleSheet(f"color:{THEME['red']};font-weight:700;")
        self.network_summary.setText(message)
        self.quick_address_frame.setVisible(False)
        self.completed_steps.discard(1)
        self._update_step_guide(active_step=1)

    def _render_addresses(self, recommended: str) -> None:
        self._clear_layout(self.address_layout)
        self.address_layout.addWidget(make_title("本机 IPv6 地址", 12))
        for address in self.addresses:
            self.address_layout.addWidget(AddressCard(address, address.address == recommended))

    def _toggle_addresses(self) -> None:
        visible = not self.address_panel.isVisible()
        self.address_panel.setVisible(visible)
        self.address_toggle.setText("收起本机地址" if visible else "查看本机地址")

    def _copy_recommended_address(self) -> None:
        if self.recommended_address and ClipboardHandler.copy_to_clipboard(self.recommended_address):
            set_copy_feedback(self.quick_copy_button, "复制地址")

    def _open_connectivity_test(self) -> None:
        usable = IPv6Scanner.sort_addresses([address for address in self.addresses if address.is_usable])
        if not usable:
            QMessageBox.warning(self, "没有可用地址", "请先完成 IPv6 网络检测。")
            return
        dialog = ConnectivityTestDialog(usable, self)
        dialog.exec()
        if dialog.outcome_selected:
            self.completed_steps.update({1, 2})
            self._update_step_guide(active_step=3)

    def _open_port_test(self) -> None:
        PortTestDialog(self).exec()

    def _firewall_busy(self) -> bool:
        return bool(self.firewall_thread and self.firewall_thread.isRunning())

    def _refresh_firewall_state(self, silent: bool = False) -> None:
        if self._closing:
            return
        if self.rule_state_thread and self.rule_state_thread.isRunning():
            return
        if not silent:
            self.rule_badge.setText("检查中…")
        self.rule_state_thread = TaskThread(lambda _progress: get_firewall_rule_state(), self)
        self.rule_state_thread.result_ready.connect(self._apply_firewall_state)
        self.rule_state_thread.failed.connect(
            lambda error: self._apply_firewall_state(FirewallRuleState(False, False, error=error))
        )
        self.rule_state_thread.start()

    def _apply_firewall_state(self, state: FirewallRuleState) -> None:
        previous_exists = self.firewall_state.exists
        self.firewall_state = state
        if not state.query_succeeded:
            self.rule_badge.setText("读取失败")
            self.rule_badge.setStyleSheet(
                f"background:{THEME['red_soft']};color:{THEME['red']};padding:5px 8px;border-radius:7px;font-size:9pt;"
            )
            self.port_input.setEnabled(False)
            self.set_port_button.setVisible(True)
            self.set_port_button.setEnabled(False)
            self.delete_rule_button.setVisible(False)
            self.delete_rule_button.setEnabled(False)
            self.firewall_status.setText(state.error)
            return
        if state.exists:
            self.rule_badge.setText(f"规则已存在 · {state.port or '未知端口'}")
            self.rule_badge.setStyleSheet(
                f"background:{THEME['green_soft']};color:{THEME['green']};padding:5px 8px;border-radius:7px;font-size:9pt;font-weight:600;"
            )
            if state.port:
                self.port_input.setText(state.port)
            self.port_input.setEnabled(False)
            self.set_port_button.setVisible(False)
            self.set_port_button.setEnabled(False)
            self.delete_rule_button.setVisible(True)
            self.delete_rule_button.setEnabled(not self._firewall_busy())
            self.firewall_status.setText("如需更换端口，请先删除现有规则，再设置新的端口。")
            self.firewall_status.setStyleSheet(f"color:{THEME['green']};font-size:9pt;")
            return
        if previous_exists:
            self.port_input.clear()
        self.rule_badge.setText("尚未设置")
        self.rule_badge.setStyleSheet(
            f"background:#EEF1EE;color:{THEME['muted']};padding:5px 8px;border-radius:7px;font-size:9pt;"
        )
        self.port_input.setEnabled(not self._firewall_busy())
        self.set_port_button.setVisible(True)
        self.delete_rule_button.setVisible(False)
        self.delete_rule_button.setEnabled(False)
        self._validate_port()

    def _validate_port(self) -> None:
        if self.firewall_state.exists:
            self.set_port_button.setEnabled(False)
            return
        valid, error, normalized = validate_port_spec(self.port_input.text())
        self.set_port_button.setEnabled(valid and not self._firewall_busy() and self.firewall_state.query_succeeded)
        if self.port_input.text() and not valid:
            text, color = error, THEME["red"]
        elif valid:
            text, color = f"将创建本工具专用规则并开放 TCP {normalized}", THEME["muted"]
        else:
            text, color = "每次只能设置一个端口；应用会持续检查规则是否存在。", THEME["muted"]
        self.firewall_status.setText(text)
        self.firewall_status.setStyleSheet(f"color:{color};font-size:9pt;")

    def _set_firewall_port(self) -> None:
        if self.firewall_state.exists:
            self.firewall_status.setText("规则已经存在，请先删除旧规则。")
            return
        valid, error, normalized = validate_port_spec(self.port_input.text())
        if not valid:
            self.firewall_status.setText(error)
            return
        self._run_firewall_task(lambda: set_firewall_port(normalized), "正在创建 Windows 防火墙规则…")

    def _delete_firewall_rule(self) -> None:
        if not self.firewall_state.exists:
            return
        reply = QMessageBox.question(
            self,
            "删除防火墙规则",
            f"确定删除本工具创建的规则吗？\n当前端口：{self.firewall_state.port or '未知'}",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            self._run_firewall_task(remove_firewall_port, "正在删除 Windows 防火墙规则…")

    def _run_firewall_task(self, operation: Callable, status: str) -> None:
        self.port_input.setEnabled(False)
        self.set_port_button.setEnabled(False)
        self.delete_rule_button.setEnabled(False)
        self.firewall_status.setText(status)
        self.firewall_status.setStyleSheet(f"color:{THEME['green']};font-size:9pt;font-weight:600;")
        self.firewall_thread = TaskThread(lambda _progress: operation(), self)
        self.firewall_thread.result_ready.connect(self._firewall_done)
        self.firewall_thread.failed.connect(lambda error: self._firewall_done((False, error)))
        self.firewall_thread.start()

    def _firewall_done(self, result: tuple) -> None:
        success, message = result[0], result[1]
        color = THEME["green"] if success else THEME["red"]
        self.firewall_status.setText(message)
        self.firewall_status.setStyleSheet(f"color:{color};font-size:9pt;font-weight:600;")
        if success and len(result) == 3:
            port = result[2].get("本地端口", "")
            address = next((item.address for item in self.addresses if item.is_usable), "")
            if port and address:
                join_text = f"[{address}]:{port}"
                ClipboardHandler.copy_to_clipboard(join_text)
                self.firewall_status.setText(f"规则设置完成，加入地址已复制：{join_text}")
        if not self._closing:
            QTimer.singleShot(200, self._refresh_firewall_state)

    def _active_background_tasks(self) -> list[str]:
        tasks: list[str] = []
        if self.readiness_thread and self.readiness_thread.isRunning():
            tasks.append("IPv6 网络检测")
        if self.rule_state_thread and self.rule_state_thread.isRunning():
            tasks.append("读取防火墙状态")
        if self.firewall_thread and self.firewall_thread.isRunning():
            tasks.append("修改防火墙规则")
        return tasks

    def _finish_close_when_idle(self) -> None:
        if self._active_background_tasks():
            QTimer.singleShot(100, self._finish_close_when_idle)
            return
        QApplication.quit()

    def closeEvent(self, event: QCloseEvent) -> None:
        self.rule_timer.stop()
        active_tasks = self._active_background_tasks()
        if not active_tasks:
            event.accept()
            return

        # 阻塞操作无法安全地强杀；立即隐藏窗口，待有超时保护的工作线程结束后退出进程。
        self._closing = True
        self.statusBar().showMessage("正在结束：" + "、".join(active_tasks))
        self.hide()
        event.ignore()
        QTimer.singleShot(0, self._finish_close_when_idle)
