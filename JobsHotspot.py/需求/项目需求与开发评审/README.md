# Jobs Hotspot · 项目需求与开发评审

![Jobs出品，必属精品](https://picsum.photos/1500/400)

[toc]

---

## 🔥 <span id="前言">前言</span>

| 文档信息 | 内容 |
| --- | --- |
| 项目标识 | JobsHotspot（工程标识） |
| 编制日期 | 2026-11-05 |
| 需求方 | Jobs |
| 开发及验收负责人 |  |
| 发布版本／渠道 |  |

## 一、原始需求 <a href="#前言" style="font-size:17px; color:green;"><b>🔼</b></a> <a href="#🔚" style="font-size:17px; color:green;"><b>🔽</b></a>

以下原文保留用户给出的顺序及资料路径；这些绝对路径只是来源记录，软件运行不依赖它们。

```text
MacOS/WindowsOS都有一个迫切的需求，你需要用Python来写一个双端的App，根据平台打包
1、主要功能就是简单的，本地的硬件数据插头进的电脑这个流量，要利用电脑的wifi做成热点
2、MacOS/WindowsOS双端都要写，但是各个端的具体情况不一样，需要做区分，特别是MacOS的系统因为升级，可能的位置会不一样，但大体应该都是一样的，我之前写了一个关于MacOS的热点分享的文档，你可以参考下：/Users/jobs/Documents/Github/JobsDocs/MacOS配置个人热点🛜.md
3、此功能要简单纯粹，因为这个功能都是集成在一些大型的软件里作为辅助功能出现的，现在我就需要完全的可控，独立出来。无论是对MacOS还是WindowsOS，都是需要GUI，可以最小化退回到系统任务栏/状态栏
4、GUI右上角要有：国际化语言的切换、主题颜色的切换，这个你可以参考下/Users/jobs/Documents/Github/JobsGenesis/JobsPythonTools.py/JobsSSHKeyMgr.py
5、要突出的显示流量进和流量出。这个受限制于当前设备状态，比如：当前电脑本身就利用wifi接受信号，没有实体的数据线接入电脑，那么此功能的数据进口就不可用，进而导致整个功能不可用；如果是当前电脑不具备Wifi模块，那就是只能是USB/普通正常的数据口进，那么此功能的数据出口就不可用，进而导致整个功能不可用；我只是举例，可能现实生产生活中，出现问题的情况可能并不局限于此
6、对于错误（不可用）需要文字+图来进行展示
7、功能不可用那么分享按钮也不可用（分享按钮需要在显眼处圆圈形状，开关都要有不同的图，这个按钮就只要背景图就行）
```

## 二、需求追溯与状态流程 <a href="#前言" style="font-size:17px; color:green;"><b>🔼</b></a> <a href="#🔚" style="font-size:17px; color:green;"><b>🔽</b></a>

| 需求 | 实现与验收方向 | 已确认来源 |
| --- | --- | --- |
| R-001 | 实体以太网／USB 网络输入到 Wi-Fi 热点；不将 Wi-Fi 输入作为可分享来源 | 原文 1、5 |
| R-002 | MacOS／Windows 平台后端分别处理系统能力、权限、配置及设置入口 | 原文 2 |
| R-003 | 独立 GUI、系统托盘／状态栏、窗口隐藏与重新显示 | 原文 3 |
| R-004 | 右上角语言与主题菜单；十种语言、白天／黑夜／系统、保存偏好 | 原文 4 与全局 GUI 规范 |
| R-005 | 突出显示输入／输出、接口类型、速率／累计值及不可用原因 | 原文 5 |
| R-006 | 每个阻断原因有文字和对应图片，提供重新检测／系统设置恢复入口 | 原文 6 |
| R-007 | 显眼圆形纯图片开关；开启、关闭、不可用图形不同；阻断时不启动 | 原文 7 |

状态主流程：检测 → 可用关闭／不可用／未知 → 用户开启 → 系统操作进行中 → 复核真实开启 → 用户停止 → 复核真实关闭。硬件热插拔、网络断开、拒绝授权、超时、原生接口失败都重新进入检测。已开启时即使上游消失，仍保留停止能力；无法确认系统状态不反馈成功。

## 三、技术评审与权限 <a href="#前言" style="font-size:17px; color:green;"><b>🔼</b></a> <a href="#🔚" style="font-size:17px; color:green;"><b>🔽</b></a>

| 项目 | 当前方案及依据 |
| --- | --- |
| 前端路线 | 通用型 Python 跨平台 GUI，用户明确指定；PySide6 延续现有 SSHKeyMgr 风格 |
| 目标平台 | MacOS 与 Windows；具体最低系统／架构以构建依赖和实机验证矩阵填写 |
| 后端／数据库 | 不适用；本机系统控制，无远端服务及业务数据库 |
| MacOS 系统能力 | 系统 Internet Sharing；首次原生配置实体上游、唯一 Wi-Fi 输出、SSID、安全类型及密码，后续定点辅助功能控制并复核；需相关自动化／辅助功能授权。NAT 内部配置格式变化、开关标签／布局变化时禁用启动并回到系统设置 |
| Windows 系统能力 | 系统 Windows PowerShell 5.1 访问 Windows Runtime NetworkOperatorTetheringManager，读取系统能力和操作结果；实体来源须报告 InternetAccess，多块物理 Wi-Fi 时因目标不确定禁用启动 |
| 配置与密码 | Qt 当前用户配置保存语言／主题等偏好；密码不写普通设置或日志；MacOS 热点凭据由系统配置维护 |
| 流量口径 | 接口级收发总量及增量速率，包含主机自身通信；未知不得解释为零 |
| Windows 凭据范围 | SSID 1–32 个 UTF-8 字节；密码 8–63 个可打印 ASCII 字符 |
| 外部素材 | 本地随包资源及来源／许可说明；运行时无需网络下载 |
| 构建与分发 | 各平台本机构建，自包含运行依赖，打包验证后生成最新入口 |

用户有操作 GUI、读取状态、请求系统共享开关的权限；程序不绕过系统授权，不持久安装网络驱动或代理。系统是否允许共享由当前硬件、驱动、策略、配置和权限共同决定。

## 四、<span id="acceptance">三级验收与可运行测试</span> <a href="#前言" style="font-size:17px; color:green;"><b>🔼</b></a> <a href="#🔚" style="font-size:17px; color:green;"><b>🔽</b></a>

目标验收等级：

验收人／期限：

| 用例 | 前置／操作 | 预期 | 证据范围 |
| --- | --- | --- | --- |
| T-001／R-001、R-005 | 仅 Wi-Fi 输入或无实体网络 | 显示输入不可用，启动禁用 | 平台解析器隔离输出；实机步骤另验 |
| T-002／R-005、R-006 | 无 Wi-Fi、无线电关闭、策略禁止 | 对应图文原因；按钮禁用 | 原生能力输出夹具；实机另验 |
| T-003／R-001、R-007 | 实体输入正常，Wi-Fi 及权限准备好，点击启动 | 原生成功且状态复核后才显示开启 | 需目标端真实热点及客户端验收 |
| T-004／R-005、R-007 | 热点运行时拔掉输入，再点击停止 | 显示断线但仍允许请求停止 | 隔离状态用例及实机另验 |
| T-005／R-002、R-006 | 拒绝权限、错误输出、超时、未知设置结构 | 无虚假成功，有恢复入口 | 解析器／操作失败夹具 |
| T-006／R-003 | 最小化／关闭窗口，托盘重新显示，再退出 | 状态可见、窗口可恢复，退出行为明确 | GUI 与原生托盘分别检查 |
| T-007／R-004 | 切换十种语言、三种主题、改变系统外观、重启 | 全界面更新，偏好恢复，系统主题实时响应 | GUI 冒烟与人工查看 |
| T-008／R-005 | 切换接口、计数归零、计数不可读 | 不出现负速率或误导统计 | 计算用例及本机只读采集 |
| T-009／R-002 | 复制工程到中文空格路径并换当前目录构建 | 所有资源、入口、后端随位置解析 | 构建 safety 用例与成品 smoke |
| T-010 | 停止后重新开始、休眠唤醒、跨机安装，客户端上网 | 系统状态与客户端真实访问一致 | 各平台实机验收 |

可运行检查入口见 [工程 README](../../JobsHotspot/README.md)。基础可运行要求主流程和关键错误闭环；可商用另需实际兼容矩阵、权限、完整回归及支持责任；工业化另需长期运行、断线恢复、跨机分发及可维护证据。构建、GUI 冒烟、真实系统开关、客户端传输、签名发布分别记录，不互相替代。

## 五、交付、升级与卸载 <a href="#前言" style="font-size:17px; color:green;"><b>🔼</b></a> <a href="#🔚" style="font-size:17px; color:green;"><b>🔽</b></a>

| 交付项 | 入口／行为 |
| --- | --- |
| MacOS 构建 | [平台打包入口](../../【MacOS】📦生成dmg.command/README.md)，生成完整 APP／DMG |
| Windows 构建 | [平台打包入口](../../【Windows】📦生成exe.bat/README.md)，生成完整 EXE 目录／ZIP |
| 源码与依赖 | [Python 工程](../../JobsHotspot/README.md)，pyproject 声明及资源许可随源码 |
| 日志与版本 | 系统临时目录的 JobsHotspot-build.log；产物目录 build-info.json 和 SHA-256 |
| 安装 | MacOS 将完整 APP 复制到 Applications；Windows 解压完整 ZIP 到自选位置 |
| 升级 | 先明确停止系统热点并退出旧程序，再替换应用；偏好由当前用户设置保管 |
| 卸载与恢复 | 明确关闭系统互联网共享／移动热点，退出应用，移除对应 APP 或完整解压目录；不删除系统网络配置、共享依赖或其它用户数据。撤销不再需要的系统授权由用户在系统设置中处理 |
| 签名与发布 | 本地／临时签名构建；正式 Developer ID、公证、Windows Authenticode 证书及渠道另行配置 |

无服务器部署、数据库、URL、内网穿透或远端自动化任务，不制造对应的空工程及服务脚本。

## 六、不确定项与待补字段 <a href="#前言" style="font-size:17px; color:green;"><b>🔼</b></a> <a href="#🔚" style="font-size:17px; color:green;"><b>🔽</b></a>

| Q 编号 | 有依据的不确定项 | 用户结论 |
| --- | --- | --- |
| Q-001 | <span style="color:#d32f2f;">【不确定 Q-001】MacOS 系统版本及设置控件会变化；当前适配代码不能等同于所有系统／语言均已实际验收，需要在目标 MacOS 上完成授权、配置和开关实测。</span> |  |
| Q-002 | <span style="color:#d32f2f;">【不确定 Q-002】Windows 原生 API 依赖热点硬件、驱动、系统策略与权限，当前 MacOS 开发机不能确认目标 Windows 的真实结果。</span> |  |
| Q-003 | <span style="color:#d32f2f;">【不确定 Q-003】工程以 JobsHotspot 作为中性功能标识，正式产品名称、Bundle 身份、签名证书及发布渠道尚未由需求给出。</span> |  |

| 待补字段 | 内容 |
| --- | --- |
| 最低系统与 CPU 架构清单 |  |
| 正式产品名称／签名账号／证书归属 |  |
| 排期／预算／验收负责人 |  |
| 长期支持、响应时段与发布渠道 |  |

## 七、官方依据与确认记录 <a href="#前言" style="font-size:17px; color:green;"><b>🔼</b></a> <a href="#🔚" style="font-size:17px; color:green;"><b>🔽</b></a>

核验日期：2026-11-05。用户原文及既有热点笔记提供功能来源；系统技术事实不作为用户偏好记录。

- [Apple：互联网共享](https://support.apple.com/guide/mac-help/share-internet-connection-mac-network-users-mchlp1540/mac)：原生以太网等来源与 Wi-Fi 分享配置。
- [Microsoft：NetworkOperatorTetheringManager](https://learn.microsoft.com/en-us/uwp/api/windows.networking.networkoperators.networkoperatortetheringmanager)：热点状态、配置与启停能力，目标系统约束另验。
- [PyInstaller：原生打包边界](https://www.pyinstaller.org/en/stable/)：按目标平台构建，产物包含依赖。
- [Qt for Python](https://doc.qt.io/qtforpython-6/)：当前 GUI 与分发依赖依据。

<a id="🔚" href="#前言" style="font-size:17px; color:green; font-weight:bold;">我是有底线的➤点我回到首页</a>
