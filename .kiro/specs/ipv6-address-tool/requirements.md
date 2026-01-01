# Requirements Document

## Introduction

一个 Windows 桌面应用程序，用于自动获取本机 IPv6 地址（包括临时地址和正常地址），提供地址有效性检测和一键复制功能。最终可打包为 exe 安装文件。

## Glossary

- **IPv6_Tool**: 主应用程序，负责获取和显示 IPv6 地址
- **IPv6_Address**: 本机的 IPv6 网络地址
- **Temporary_Address**: Windows 系统生成的临时 IPv6 地址，用于隐私保护
- **Permanent_Address**: 固定的 IPv6 地址（非临时）
- **Link_Local_Address**: 以 fe80 开头的链路本地地址，仅用于本地网络通信
- **Clipboard_Manager**: 系统剪贴板管理组件

## Requirements

### Requirement 1: IPv6 地址获取

**User Story:** 作为用户，我想要自动获取本机所有 IPv6 地址，以便了解当前网络配置。

#### Acceptance Criteria

1. WHEN the application starts, THE IPv6_Tool SHALL automatically scan and display all IPv6 addresses on the system
2. WHEN multiple network interfaces exist, THE IPv6_Tool SHALL display IPv6 addresses from all active interfaces
3. WHEN an IPv6 address is a temporary address, THE IPv6_Tool SHALL label it as "临时地址"
4. WHEN an IPv6 address is a permanent address, THE IPv6_Tool SHALL label it as "正常地址"
5. WHEN no IPv6 address is found, THE IPv6_Tool SHALL display a message indicating no IPv6 addresses are available

### Requirement 2: 地址有效性检测

**User Story:** 作为用户，我想要知道哪些 IPv6 地址可以用于实际通信，以便选择正确的地址。

#### Acceptance Criteria

1. WHEN an IPv6 address starts with "fe80", THE IPv6_Tool SHALL mark it as "链路本地地址（不可用于外部通信）"
2. WHEN an IPv6 address starts with "::1", THE IPv6_Tool SHALL mark it as "本地回环地址"
3. WHEN an IPv6 address is a valid global unicast address, THE IPv6_Tool SHALL mark it as "可用于通信"
4. THE IPv6_Tool SHALL visually distinguish usable addresses from unusable addresses using different colors or icons

### Requirement 3: 一键复制功能

**User Story:** 作为用户，我想要快速复制选中的 IPv6 地址到剪贴板，以便在其他应用中使用。

#### Acceptance Criteria

1. WHEN a user clicks the copy button next to an address, THE Clipboard_Manager SHALL copy that IPv6 address to the system clipboard
2. WHEN the copy operation succeeds, THE IPv6_Tool SHALL display a brief success notification
3. IF the copy operation fails, THEN THE IPv6_Tool SHALL display an error message explaining the failure

### Requirement 4: 地址刷新功能

**User Story:** 作为用户，我想要手动刷新地址列表，以便获取最新的网络配置。

#### Acceptance Criteria

1. WHEN a user clicks the refresh button, THE IPv6_Tool SHALL rescan all network interfaces
2. WHEN refreshing, THE IPv6_Tool SHALL update the address list with current information
3. WHILE refreshing is in progress, THE IPv6_Tool SHALL display a loading indicator

### Requirement 5: 用户界面

**User Story:** 作为用户，我想要一个简洁易用的界面，以便快速完成操作。

#### Acceptance Criteria

1. THE IPv6_Tool SHALL display a main window with a clear list of all IPv6 addresses
2. THE IPv6_Tool SHALL provide a copy button for each displayed address
3. THE IPv6_Tool SHALL provide a global refresh button
4. THE IPv6_Tool SHALL display the network interface name for each address

### Requirement 6: IPv6 连通性测试跳转

**User Story:** 作为用户，我想要快速跳转到 IPv6 测试网站，以便验证我的 IPv6 网络是否正常工作。

#### Acceptance Criteria

1. THE IPv6_Tool SHALL provide a button to open an IPv6 test website
2. WHEN a user clicks the test button, THE IPv6_Tool SHALL open the default browser with the IPv6 test URL
3. THE IPv6_Tool SHALL use a reliable IPv6 test website (e.g., test-ipv6.com or ipv6-test.com)

### Requirement 7: 可打包为 EXE 安装文件

**User Story:** 作为用户，我想要将应用打包为 exe 文件，以便在其他 Windows 电脑上安装使用。

#### Acceptance Criteria

1. THE IPv6_Tool SHALL be packaged as a standalone Windows executable file
2. WHEN the executable runs, THE IPv6_Tool SHALL not require Python to be installed on the target system
3. THE IPv6_Tool SHALL include all necessary dependencies in the package
