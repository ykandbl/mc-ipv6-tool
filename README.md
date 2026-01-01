# IPv6 地址工具

一个 Windows 桌面应用程序，用于获取和管理本机 IPv6 地址。

## 下载

### 方式一：直接下载（推荐）

前往 [Releases](../../releases) 页面下载最新版本的 `IPv6Tool.exe`，双击即可运行。

### 方式二：从源码运行

```bash
# 克隆仓库
git clone https://github.com/你的用户名/ipv6-address-tool.git
cd ipv6-address-tool

# 安装依赖
pip install -r requirements.txt

# 运行程序
cd src
python main.py
```

## 功能

- 🔍 自动扫描所有网络接口的 IPv6 地址
- 🏷️ 区分临时地址和正常地址
- ⚠️ 自动识别不可用地址（如 fe80 链路本地地址）
- 📋 一键复制地址到剪贴板（自动格式化为 `[地址]:` 格式）
- 🌐 快速跳转到 IPv6 测试网站
- 🔄 手动刷新地址列表
- 📐 根据屏幕大小自适应 UI

## 地址类型说明

| 颜色 | 含义 |
|------|------|
| 🔵 蓝色 | 可用于外部通信的全局单播地址 |
| 🔴 红色 | 不可用于外部通信（链路本地、回环等） |

## 打包为 EXE

```bash
# 方式一：使用打包脚本
build.bat

# 方式二：手动打包
pip install -r requirements.txt
pyinstaller build.spec --clean
```

打包完成后，可执行文件位于 `dist/IPv6Tool.exe`。

## 项目结构

```
ipv6-address-tool/
├── src/
│   ├── main.py          # 程序入口
│   ├── scanner.py       # IPv6 扫描器
│   ├── validator.py     # 地址验证器
│   ├── clipboard.py     # 剪贴板处理
│   ├── browser.py       # 浏览器启动
│   └── ui/
│       └── main_window.py  # 主窗口
├── requirements.txt     # 依赖列表
├── build.spec          # PyInstaller 配置
├── build.bat           # 打包脚本
├── LICENSE             # MIT 许可证
└── README.md
```

## 依赖

- Python 3.8+
- PyQt6
- psutil
- PyInstaller (打包用)

## 许可证

[MIT License](LICENSE) © Bole
