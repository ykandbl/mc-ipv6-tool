# Implementation Plan: IPv6 Address Tool

## Overview

基于 Python + PyQt6 实现 IPv6 地址获取工具，采用增量开发方式，先搭建核心功能，再完善 UI 和打包。

## Tasks

- [x] 1. 项目初始化和依赖配置
  - 创建项目目录结构
  - 创建 requirements.txt 包含 PyQt6, psutil, pyinstaller
  - 创建 src/__init__.py 和 tests/__init__.py
  - _Requirements: 7.3_

- [x] 2. 实现地址验证器 (AddressValidator)
  - [x] 2.1 创建 src/validator.py 实现 AddressValidator 类
    - 实现 is_link_local() 检测 fe80 开头地址
    - 实现 is_loopback() 检测 ::1 地址
    - 实现 is_global_unicast() 检测全局单播地址
    - 实现 validate() 返回地址类型和可用性
    - _Requirements: 2.1, 2.2, 2.3_

  - [ ]* 2.2 编写属性测试：链路本地地址识别
    - **Property 2: 链路本地地址识别**
    - **Validates: Requirements 2.1**

  - [ ]* 2.3 编写属性测试：全局单播地址识别
    - **Property 3: 全局单播地址识别**
    - **Validates: Requirements 2.3**

- [x] 3. 实现 IPv6 扫描器 (IPv6Scanner)
  - [x] 3.1 创建 src/scanner.py 实现 IPv6Scanner 类
    - 定义 IPv6Address 数据类
    - 实现 scan_all_interfaces() 扫描所有接口
    - 区分临时地址和正常地址
    - 集成 AddressValidator 进行地址验证
    - _Requirements: 1.1, 1.2, 1.3, 1.4_

  - [ ]* 3.2 编写属性测试：地址类型标签正确性
    - **Property 1: 地址类型标签正确性**
    - **Validates: Requirements 1.3, 1.4**

- [x] 4. Checkpoint - 核心逻辑验证
  - 确保所有测试通过，如有问题请告知

- [x] 5. 实现剪贴板处理器 (ClipboardHandler)
  - [x] 5.1 创建 src/clipboard.py 实现 ClipboardHandler 类
    - 使用 PyQt6 的 QClipboard 实现复制功能
    - 实现 copy_to_clipboard() 方法
    - _Requirements: 3.1_

  - [ ]* 5.2 编写属性测试：剪贴板复制往返一致性
    - **Property 4: 剪贴板复制往返一致性**
    - **Validates: Requirements 3.1**

- [x] 6. 实现浏览器启动器 (BrowserLauncher)
  - [x] 6.1 创建 src/browser.py 实现 BrowserLauncher 类
    - 使用 webbrowser 模块打开默认浏览器
    - 配置 IPv6 测试网站 URL
    - _Requirements: 6.1, 6.2, 6.3_

- [x] 7. 实现主窗口 UI (MainWindow)
  - [x] 7.1 创建 src/ui/main_window.py 实现 MainWindow 类
    - 创建主窗口布局
    - 实现地址列表显示组件
    - 为每个地址添加复制按钮
    - 添加刷新按钮
    - 添加 IPv6 测试按钮
    - 实现地址可用性的颜色区分
    - _Requirements: 5.1, 5.2, 5.3, 5.4, 2.4_

  - [x] 7.2 创建 src/main.py 程序入口
    - 初始化 QApplication
    - 创建并显示 MainWindow
    - _Requirements: 1.1_

- [x] 8. Checkpoint - 功能集成验证
  - 运行程序验证所有功能正常工作
  - 确保所有测试通过，如有问题请告知

- [x] 9. 打包配置
  - [x] 9.1 创建 PyInstaller 配置文件 build.spec
    - 配置单文件打包
    - 包含所有依赖
    - 设置 Windows 图标（可选）
    - _Requirements: 7.1, 7.2, 7.3_

  - [x] 9.2 创建打包脚本和说明
    - 创建 build.bat 一键打包脚本
    - 更新 README.md 包含使用和打包说明
    - _Requirements: 7.1_

- [x] 10. Final Checkpoint - 最终验证
  - 确保所有测试通过
  - 验证 exe 打包流程
  - 如有问题请告知

## Notes

- 标记 `*` 的任务为可选测试任务，可跳过以加快 MVP 开发
- 每个任务都关联了具体的需求编号以便追溯
- Checkpoint 任务用于阶段性验证
- 属性测试验证核心逻辑的正确性
