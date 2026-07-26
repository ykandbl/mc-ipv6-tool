# 买块 IPv6 联机工具

面向 Minecraft Java 版的 Windows IPv6 联机工具，可检测本机 IPv6 网络、辅助双方完成双向连通性测试，并为房主配置游戏端口。

## 下载

请从 [GitHub Releases](https://github.com/ykandbl/mc-ipv6-tool/releases/latest) 下载最新的 `IPv6Tool-v<版本号>.exe`。程序适用于 64 位 Windows 10/11，每次启动会请求管理员权限，以读取和配置本工具创建的 Windows 防火墙规则。

## 主要功能

- 原生 IPv6 环境检测，无需跳转测试网页
  - 检查公网 IPv6 地址和默认路由
  - 通过两个独立的纯 IPv6 HTTPS 服务验证真实外网连接
  - 区分“没有地址”和“有地址但无法联网”
- 双向连通性测试
  - 双方分别执行一次“本机 → 对方”测试
  - 展示双方 IPv6 前缀推测的运营商、连接结果与延迟
  - 收到对方的反向测试反馈后，选择对应结果
  - 合并两个方向后说明谁更适合当房主，不依赖公网中转服务器
  - 对跨运营商连接给出明确提示
- 地址管理
  - 识别临时地址、稳定地址和虚拟网卡
  - 自动推荐适合分享的公网地址
- 房主工具
  - 启动时请求管理员权限，以便持续读取 Windows 防火墙状态
  - 按本工具固定规则名称检测，不使用端口号反查
  - 已存在规则时只能删除，删除后才能设置新的单个端口
  - 联机结束后一键删除工具创建的规则
- 加入者工具
  - 在房主创建游戏后测试实际 TCP 端口

## 使用方法

### 1. 双方检查 IPv6

双方打开工具，等待第 1 步显示“IPv6 连接正常”。进入双向连通性测试后，可直接复制本机地址并发送给对方。

### 2. 双方各测试一次

双方分别输入对方地址并执行测试。对方完成反向测试后，根据对方反馈在界面中选择相应结果。

工具本身不负责在两个客户端之间同步数据，也不会将对方地址上传到服务器。

工具会给出以下结论之一：

- 双方均通过主机方向初步检测
- 建议由本机用户作为房主
- 建议由对方作为房主
- 两个 Ping 方向均未收到响应

### 3. 房主创建游戏

房主在 Minecraft Java 中“对局域网开放”，记下游戏显示的端口，在工具第 3 步设置防火墙。程序每次启动都会请求管理员权限。

如果界面显示本工具的规则已经存在，只能先删除旧规则；规则删除后才能输入并设置新的端口。

设置成功后，工具会复制完整加入地址：

```text
[2409:xxxx:xxxx:xxxx::1234]:25565
```

加入者也可以使用“测试对方的实际 TCP 端口”。测试通过仅表示 IPv6 TCP 连接能够建立，不能保证 Minecraft 版本、模组、白名单及登录验证等条件一定兼容。

联机结束后，房主应删除本工具创建的防火墙规则。

## 从源码运行

需要 Windows 10/11 和 Python 3.10+：

```powershell
git clone https://github.com/ykandbl/mc-ipv6-tool.git
cd mc-ipv6-tool
python -m pip install -r requirements.txt
python src/main.py
```

## 测试与打包

```powershell
python -m pip install -r requirements-dev.txt
python -m pytest -q
build.bat
```

打包产物会自动包含 `src\app_version.py` 中定义的版本号，格式为 `dist\IPv6Tool-v<版本号>.exe`。每次构建新版都会生成新的文件名，不覆盖旧版本。

## 隐私说明

IPv6 环境检测会直接访问 `api6.ipify.org` 和 `6.ident.me`，用于确认纯 IPv6 HTTPS 是否可用并读取当前公网 IPv6。检测不会上传本地文件、对方地址或游戏端口。

## 项目结构

```text
src/
├── app_version.py          应用名称与版本号
├── main.py                 程序入口
├── ipv6_readiness.py       原生 IPv6 环境检测
├── scanner.py              本机地址扫描
├── validator.py            IPv6 输入与类型验证
├── connectivity_test.py    双向连通性与实际端口测试
├── firewall.py             Windows 防火墙管理
├── privileges.py           启动 UAC 提权
└── ui/
    ├── app_icon.py         点对点连接图标
    ├── main_window.py      主流程界面
    └── splash.py           启动画面
```

## 许可证

[MIT License](LICENSE) © Bole
