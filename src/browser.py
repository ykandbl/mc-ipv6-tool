"""浏览器启动器模块"""
import webbrowser


class BrowserLauncher:
    """浏览器启动器，用于打开 IPv6 测试网站"""
    
    # IPv6 测试网站 URL
    IPV6_TEST_URL = "https://test-ipv6.com/"
    
    @classmethod
    def open_ipv6_test(cls) -> bool:
        """
        打开 IPv6 测试网站
        
        Returns:
            bool: 是否成功打开浏览器
        """
        try:
            webbrowser.open(cls.IPV6_TEST_URL)
            return True
        except Exception:
            return False
    
    @staticmethod
    def open_url(url: str) -> bool:
        """
        打开指定 URL
        
        Args:
            url: 要打开的网址
            
        Returns:
            bool: 是否成功打开浏览器
        """
        try:
            webbrowser.open(url)
            return True
        except Exception:
            return False
