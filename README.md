# 🎮 我的世界 IPv6 联机工具

帮助我的世界房主快速获取 IPv6 地址并配置防火墙，让小白玩家轻松联机！

## ✨ 功能特点

- 🔍 自动扫描本机所有 IPv6 地址
- ⭐ 智能推荐临时地址（更安全）
- 🔥 一键配置 Windows 防火墙入站规则
- 📋 一键复制地址，格式化为 `[地址]:` 方便粘贴
- 🌐 快速测试 IPv6 连通性
- 🎨 美观的启动画面和现代化 UI

## 📥 下载安装

### 方式一：直接下载（推荐）

前往 [Releases](../../releases) 页面下载最新版本的 `IPv6Tool.exe`，双击即可运行。

> ⚠️ 首次运行需要管理员权限（用于配置防火墙）

### 方式二：从源码运行

```bash
# 克隆仓库
git clone https://github.com/ykandbl/mc-ipv6-tool.git
cd mc-ipv6-tool

# 安装依赖
pip install -r requirements.txt

# 运行程序
cd src
python main.py
```

## 🎯 使用说明

### 房主操作步骤

1. **以管理员身份运行** IPv6Tool.exe
2. 在地址列表中找到带 ⭐推荐 标签的地址，点击 **复制**
3. 输入游戏端口号，点击 **设置端口**
4. 把复制的地址发给玩家，让他们直接连接
5. **联机结束后**，务必点击 **删除规则** 关闭端口

### 玩家操作

玩家无需安装此工具，直接在游戏中输入房主提供的地址即可连接。

## 🔧 打包为 EXE

```bash
# 使用打包脚本
build.bat

# 或手动打包
pip install -r requirements.txt
pyinstaller build.spec --clean
```

打包完成后，可执行文件位于 `dist/IPv6Tool.exe`。

## 📁 项目结构

```
mc-ipv6-tool/
├── src/
│   ├── main.py           # 程序入口
│   ├── scanner.py        # IPv6 扫描器
│   ├── validator.py      # 地址验证器
│   ├── clipboard.py      # 剪贴板处理
│   ├── browser.py        # 浏览器启动
│   ├── firewall.py       # 防火墙规则管理
│   └── ui/
│       ├── main_window.py   # 主窗口
│       └── splash.py        # 启动画面
├── requirements.txt      # 依赖列表
├── build.spec           # PyInstaller 配置
├── build.bat            # 打包脚本
└── README.md
```

## 📋 依赖

- Python 3.8+
- PyQt6
- psutil
- PyInstaller (打包用)

## 📄 许可证

[MIT License](LICENSE) © Bole

## 🙏 致谢

感谢所有使用和支持这个项目的玩家！
