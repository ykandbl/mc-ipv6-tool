"""剪贴板处理器模块"""
from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QClipboard


class ClipboardHandler:
    """剪贴板处理器，用于复制文本到系统剪贴板"""
    
    @staticmethod
    def copy_to_clipboard(text: str) -> bool:
        """
        复制文本到剪贴板
        
        Args:
            text: 要复制的文本
            
        Returns:
            bool: 是否成功
        """
        try:
            clipboard = QApplication.clipboard()
            if clipboard is None:
                return False
            clipboard.setText(text, QClipboard.Mode.Clipboard)
            return True
        except Exception:
            return False
    
    @staticmethod
    def get_clipboard_text() -> str:
        """
        获取剪贴板文本
        
        Returns:
            str: 剪贴板中的文本
        """
        try:
            clipboard = QApplication.clipboard()
            if clipboard is None:
                return ""
            return clipboard.text(QClipboard.Mode.Clipboard)
        except Exception:
            return ""
