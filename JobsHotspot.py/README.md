# Jobs Hotspot · 独立双端热点

![Jobs出品，必属精品](https://picsum.photos/1500/400)

[toc]

---

## 🔥 <span id="前言">前言</span>

[**Python**](https://www.python.org/) 独立桌面热点工具：把已连接的以太网、USB 网卡或 USB 网络共享输入，分享为电脑的 Wi-Fi 热点。界面突出显示输入、输出、可用性、适配器速率和累计流量，提供图文故障说明、圆形图片分享开关、系统托盘／状态栏、十种语言和三种主题。

| 入口 | 用途 |
| --- | --- |
| [MacOS 打包脚本](./【MacOS】📦生成dmg.command/README.md) | 在 MacOS 本机生成 APP 与 DMG |
| [Windows 打包脚本](./【Windows】📦生成exe.bat/README.md) | 在 Windows 本机生成 EXE 完整目录与 ZIP |
| [源码与代码地图](./JobsHotspot/README.md) | 模块、运行、诊断与测试 |
| [需求与开发评审](./需求/项目需求与开发评审/README.md) | 原始需求、平台边界及验收用例 |

平台成品携带 Python、Qt 及本地图片资源；普通用户运行成品无需安装 Python。源码构建仍需要 Python 3.11+ 和对应平台工具。

## 一、使用流程与流量含义 <a href="#前言" style="font-size:17px; color:green;"><b>🔼</b></a> <a href="#🔚" style="font-size:17px; color:green;"><b>🔽</b></a>

- 先插入具有网络功能的实体连接，例如以太网、USB 以太网或手机 USB 网络共享。普通充电线和无网络驱动的 USB 设备不能作为网络入口。
- Wi-Fi 硬件必须存在、无线电打开，且驱动及系统策略允许创建热点。仅通过 Wi-Fi 接入互联网时，本应用不提供 Wi-Fi 转 Wi-Fi 中继。
- 启动应用后选择输入，查看线路图和图文诊断。条件不满足时，圆形分享按钮禁用；已经运行的热点仍保留停止入口。
- 在 Windows 设置热点名称及密码后开启。MacOS 首次在系统的“互联网共享”中选择输入接口、Wi-Fi 输出、安全类型、热点名称及密码，应用沿用该配置。
- 最小化／关闭窗口时，有可用托盘／状态栏则隐藏窗口。通过托盘菜单重新显示或退出；退出与热点停止按应用实际提示执行，关闭窗口不能视为停止系统热点。

显示的是所选网络适配器的流量，包含电脑自身通信，并非热点客户端独占流量；缺少可信计数时显示未知值，不伪造为零。接口变化、断线或统计计数重置后重新建立速率基线。

## 二、平台能力与权限边界 <a href="#前言" style="font-size:17px; color:green;"><b>🔼</b></a> <a href="#🔚" style="font-size:17px; color:green;"><b>🔽</b></a>

| 平台 | 控制方式 | 初次准备及失败处理 |
| --- | --- | --- |
| MacOS | 系统 Internet Sharing 配置与定点辅助功能自动化 | 按 [Apple 官方说明](https://support.apple.com/guide/mac-help/share-internet-connection-mac-network-users-mchlp1540/mac)配置；首次操作可能需要“自动化”与“辅助功能”权限。系统设置位置及控件可能随系统版本／语言变化；无法可靠确认目标控件或配置时保持禁用并打开系统设置处理，不改写系统私有 plist 或强制启动守护进程 |
| Windows | 系统 PowerShell 调用 [NetworkOperatorTetheringManager](https://learn.microsoft.com/en-us/uwp/api/windows.networking.networkoperators.networkoperatortetheringmanager) | 需要系统移动热点能力、可用 Wi-Fi 适配器和相关策略许可。操作结果按原生状态复核；策略限制、驱动问题、WinRT 不可用和超时均显示错误，可进入系统设置排查 |

MacOS 的按钮控制不等同于 Apple 提供稳定的公开热点开关 API；控件适配无法覆盖尚未验证的系统版本。Windows 不使用旧式 `netsh hostednetwork`。具体兼容性以目标机器的硬件、驱动、系统 API、权限和实测结果为准。

MacOS 首次需要在系统设置中配置匹配的实体来源及唯一 Wi-Fi 输出；配置读取涉及系统内部 NAT plist 格式，缺失、无法解析或格式变化都会保持启动禁用。开启状态同时核对配置与共享进程，不仅凭某个桥接接口存在判断。切换只定位唯一、明确标注的互联网共享开关，不自动处理通用确认按钮或管理员密码；系统需要确认时由用户处理。当前物理链路、IPv4 和路由正常也不能证明上游 ISP 或认证门户已经放行。

Windows 目标为 Windows 10／11，使用系统 Windows PowerShell 5.1 和 WinRT。当前同时存在多块物理 Wi-Fi 网卡时禁用启动，避免无法确定系统默认输出；SSID 限 1–32 个 UTF-8 字节，密码限 8–63 个可打印 ASCII 字符。输入还需对应 WinRT 网络配置报告 InternetAccess。入口掉线后，只要可重新取得运行中热点管理器仍可停止；全部配置消失而无法确认状态时，进入系统设置处理。

## 三、语言、主题与离线行为 <a href="#前言" style="font-size:17px; color:green;"><b>🔼</b></a> <a href="#🔚" style="font-size:17px; color:green;"><b>🔽</b></a>

右上角的语言与主题入口参考 SSHKeyMgr 的紧凑图文菜单：简体中文、繁体中文、藏文、英文、日文、法文、西班牙文、德文、俄罗斯文、韩文；主题包含白天、黑夜、跟随系统。选择保存到当前用户设置，跟随系统时响应系统外观变化。动态网络输入列表提供无数据提示及重新检测入口。

应用为本机硬件工具，所有状态和写操作通过系统后端处理，不依赖远端 API。离线演示 `--demo` 使用明确标识的模拟状态，无法改变系统热点；真实系统查询失败时显示未知／不可用，不把演示状态自动用于真实开关。图片资源随包读取，运行时不请求网络图片。

## 四、工程与打包交付 <a href="#前言" style="font-size:17px; color:green;"><b>🔼</b></a> <a href="#🔚" style="font-size:17px; color:green;"><b>🔽</b></a>

```text
JobsHotspot.py/
├── README.md
├── 【MacOS】📦生成dmg.command/
├── 【Windows】📦生成exe.bat/
├── 需求/项目需求与开发评审/README.md
├── JobsHotspot/
│   ├── pyproject.toml
│   ├── src/jobs_hotspot/
│   ├── tests/
│   └── scripts/
└── dist/YYYY.MM.DD HH-mm-ss/  # 本机成功构建时生成
```

构建前逐项检查资源和依赖，再仅清理本工具固定 `dist` 的旧产物。成功后验证成品 GUI 冒烟、分发包与 SHA-256，更新外层相对快捷链接／`.lnk`，打开本次目录再启动 APP／EXE。成品数据读取不依赖构建机路径；复制软件时，MacOS 复制完整 APP，Windows 解压完整 ZIP，不能只拿 EXE。

构建日志为系统临时目录中的 `JobsHotspot-build.log`。发布目录的 `build-info.json` 记录构建平台、架构、依赖版本和分发包摘要。用户设置由 Qt 当前用户配置存储管理；热点密码不应写入日志或普通偏好文件，系统热点配置由系统保管。

## 五、版本、许可与验证范围 <a href="#前言" style="font-size:17px; color:green;"><b>🔼</b></a> <a href="#🔚" style="font-size:17px; color:green;"><b>🔽</b></a>

本工具随当前 Python 工具集管理，未创建独立 Git 仓库或新增子模块；此目录没有自己的 `.gitmodules`。APP 为本地／临时签名构建，尚不代表 Developer ID 公证；Windows 包未做 Authenticode 签名。MacOS 另一 CPU 架构及 Windows 包分别在对应系统／架构生成并验收。

2026-11-05 统计口径：业务窗口按应用主界面计一处；需求覆盖见七条需求追溯表。运行依赖一项 PySide6（按 `pyproject.toml` 直接依赖计，Qt 随 wheel 自带），构建依赖 PyInstaller；没有服务器、业务数据库、远端接口或第三方云账号。源码文件及代码行数为开发中动态值，不把未完成统计写成发布规模。

本机 MacOS ARM64 的 APP／DMG 已生成，见第一层 `JobsHotspot.app` 与 `JobsHotspot.dmg` 最新入口。2026-11-05：56 项隔离自动测试、冻结 GUI 冒烟、DMG 完整性与移入中文空格临时目录后的工程外运行通过；构建基线为 Python 3.15.2、PySide6 6.12.0、PyInstaller 6.22.3，实际记录见产物目录 `build-info.json`。

源码、解析器与构建安全检查和 GUI 冒烟属于有限验证；没有连接热点客户端实际传输的环境，不能声称真实热点端到端通过。MacOS 27.2 已做本机只读网络／共享状态检查，开关脚本只做编译及隔离用例验证，未执行真实开关。Windows 原生运行、MacOS 其它系统版本、授权后真实开关、断线恢复、休眠唤醒及跨机分发仍需按 [验收用例](./需求/项目需求与开发评审/README.md#acceptance)实测。

<a id="🔚" href="#前言" style="font-size:17px; color:green; font-weight:bold;">我是有底线的➤点我回到首页</a>
