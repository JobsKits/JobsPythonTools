# `JobsPythonTools.py`

![Jobs出品，必属精品](https://picsum.photos/1500/400)

<!-- jobs-toc:start -->
<!-- jobs-toc:source {"v":2,"token":"[toc]"} -->
<details>
<summary>📚 目录（点击展开 / 收起）</summary>

- [🔥 前言](#jobs-toc-heading-1)
- [一、工具总览](#jobs-toc-heading-2)
- [二、目录结构](#jobs-toc-heading-3)
- [三、运行与打包](#jobs-toc-heading-4)
  - [3.1、macOS](#jobs-toc-heading-5)
  - [3.2、Windows](#jobs-toc-heading-6)
  - [3.3、Windows 系统与架构矩阵](#windows-compatibility)
- [四、输出与忽略规则](#jobs-toc-heading-8)
- [五、风险边界](#jobs-toc-heading-9)
- [六、维护说明](#jobs-toc-heading-10)
- [七、上传 README 演示视频](#jobs-toc-heading-11)
- [八、单仓管理与文档目录](#single-repository-management)
- [九、本仓目录与脚本入口](#repository-layout-and-entrypoints)
  - [【MacOS】📦生成dmg.command](#jobs-toc-heading-14)
  - [【Windows】📦生成exe.bat](#jobs-toc-heading-15)

</details>
<!-- jobs-toc:end -->

---

## <span id="jobs-toc-heading-1" data-jobs-toc="v2">🔥 <font id=前言>前言</font></span><!-- jobs-toc:heading-end -->

**最低支持系统：** [**Windows**](https://www.microsoft.com/windows) **10 64 位（x64）**。这是当前最低支持目标；具体最低 build 尚未锁定，完整实机兼容性仍待验证。

`JobsPythonTools.py` 是 Jobs 本地 [**Python**](https://www.python.org) 桌面工具集合，覆盖文件共享、Mock API、IPA 静态分析、按 App 流量监控、整机监控、浏览器远程协助、Codex 账户切换及 Token 用量监控。各工具的当前能力和详细操作入口见下方总览。

**系统兼容范围：** 当前 EXE 以 [**Windows**](https://www.microsoft.com/windows) 10 / 11 x64 为主要构建与测试目标；Windows 打包入口不代表 XP、Vista、7、8、8.1 或所有 CPU 架构通用。多数工具使用 [**Qt 6**](https://doc.qt.io/qt-6/)，`JobsRemoteHost` 的 [**Tkinter**](https://docs.python.org/3.11/library/tkinter.html) 路线另有依赖边界，详见 [Windows 系统与架构矩阵](#windows-compatibility)。目前尚无覆盖各 Windows 版本与架构的完整实机验收结果。

多数工具采用“外层交付目录 + 内层 Python 工程”结构：外层放总说明、双击入口和 `dist/YYYY.MM.DD HH-mm-ss/` 产物，内层放源码、依赖、资源、测试与构建配置；具体布局以各工具 README 为准。

独立 `.command` 入口先显示内置自述：标题红色加粗，编号正文蓝色且不加粗，非彩色终端显示纯文本；在终端回车确认后执行，`Ctrl+C` 取消，缺少可交互输入时停止。各工具的源码、文档与版本统一由本仓 [**Git**](https://git-scm.com/) 管理，日常维护见 [单仓管理与文档目录](#single-repository-management)。

脚本规范覆盖、验证与待处理项见[脚本统一审查](./项目相关报告/脚本统一审查.md)。

## <span id="jobs-toc-heading-2" data-jobs-toc="v2">一、工具总览 <a href="#前言" style="font-size:17px; color:green;"><b>🔼</b></a> <a href="#🔚" style="font-size:17px; color:green;"><b>🔽</b></a></span><!-- jobs-toc:heading-end -->

| 工具 | 目录 | 核心用途 | 主要入口 |
| --- | --- | --- | --- |
| `LANFileServer` | [功能与操作](./LANFileServer.py/README.md) | 临时 Python / 非临时 Nginx 文件共享、浏览器预览 / 下载、可选上传、二维码、项目聊天室与访问记录。 | [macOS](./LANFileServer.py/【MacOS】📦生成dmg.command/【MacOS】📦生成dmg.command) / [Windows](./LANFileServer.py/【Windows】📦生成exe.bat/【Windows】📦生成exe.bat) 打包 |
| `JobsMockTool` | [功能与操作](./JobsMockTool.py/README.md) | 多接口、单端口 / 独立端口、query / body / headers 条件响应、JSON 树形编辑、内置请求测试与配置保存。 | [macOS](./JobsMockTool.py/【MacOS】📦生成dmg.command/【MacOS】📦生成dmg.command) / [Windows](./JobsMockTool.py/【Windows】📦生成exe.bat/【Windows】📦生成exe.bat)；[构建脚本](./JobsMockTool.py/【MacOS】build_macos.command/README.md) |
| `JobsReverseIPA` | [功能与操作](./JobsReverseIPA.py/README.md) | 授权 IPA 静态分析、环境体检、资源 / 敏感字符串扫描，输出 HTML / JSON / Markdown 报告。 | [macOS](./JobsReverseIPA.py/【MacOS】📦生成dmg.command/【MacOS】📦生成dmg.command) / [Windows](./JobsReverseIPA.py/【Windows】📦生成exe.bat/【Windows】📦生成exe.bat) 打包 |
| `JobsAppTrafficMonitor` | [功能与操作](./JobsAppTrafficMonitor.py/README.md) | macOS 用 nettop、Windows 用 ETW 按 App / 进程统计速率与收发字节；Windows 采集需管理员权限。 | [macOS](./JobsAppTrafficMonitor.py/【MacOS】📦生成dmg.command/【MacOS】📦生成dmg.command) / [Windows](./JobsAppTrafficMonitor.py/【Windows】📦生成exe.bat/【Windows】📦生成exe.bat) 打包 |
| `JobsSystemMonitor` | [功能与操作](./JobsSystemMonitor.py/README.md) | CPU / GPU / 内存 / 上下行速率、历史趋势、网卡选择、刷新间隔；macOS 菜单栏与 Windows 监控条 / 托盘。 | 双端打包入口，Windows 桌面行为需目标机验收 |
| `JobsRemoteHost` | [功能与操作](./JobsRemoteHost.py/README.md) | 浏览器发起观看 / 控制申请，本机弹窗授权；局域网地址 / 临时公网链接、菜单栏 / 托盘驻留及停止服务。 | 双端打包、源码运行及协议自检入口见功能说明 |
| `JobsCodexAccountSwitcher` | `./JobsCodexAccountSwitcher.py/` | 保存 Codex 文件登录态（口令保护可选）、退出后切换与重启；桌面兼容需核验。 | [说明](./JobsCodexAccountSwitcher.py/README.md)、双端打包入口 |
| `JobsCodexTokenMonitor` | `./JobsCodexTokenMonitor.py/` | 独立显示 Codex 每轮输入 / 输出 Token；主面板常驻“窗口置顶”复选框，主题及会话联动统一从 `⋯ → 设置…` 进入。 | [说明](./JobsCodexTokenMonitor.py/README.md)、双端打包入口 |
| `JobsSSHKeyMgr` | [功能与操作](./JobsSSHKeyMgr.py/README.md) | 可编辑邮箱、GitHub SSH 生成 / 复用与配置、agent、GitHub 登记和验证；十语言、三主题、主页面公钥复制面板、算法推荐、独立 SSH 重测及 Token 网页。 | 双端源码运行与打包入口，Windows 原生桌面验收待执行 |
| `JobsHotspot` | [功能与操作](./JobsHotspot.py/README.md) | 有线／USB 网络转 Wi-Fi 热点，突出入口／出口流量、图文诊断、圆形开关、状态栏／托盘及十语言三主题。 | [MacOS](./JobsHotspot.py/【MacOS】📦生成dmg.command/README.md) / [Windows](./JobsHotspot.py/【Windows】📦生成exe.bat/README.md) 本机打包；真实启停需目标机验收 |

个人 SSH 图形工具与 `JobsCommand@Gits` 的 MacOS / WindowsOS 黑窗脚本分开维护；GUI 内嵌跨端实现，不依赖 Gits 仓库位置；本工具由总仓作为普通源码目录管理。默认邮箱为 `295060456@qq.com`，用户可编辑；已有保存邮箱优先恢复。

账户切换与 Token 监控是两个独立 Python 工程，各有源码、依赖、测试、APP / EXE 和分发包。Token 工具不依赖账户工具；可以只安装其中一个。各工具均为本总仓的普通源码目录；独立构建、安装和运行能力保留，版本统一在总仓审阅与提交。

## <span id="jobs-toc-heading-3" data-jobs-toc="v2">二、目录结构 <a href="#前言" style="font-size:17px; color:green;"><b>🔼</b></a> <a href="#🔚" style="font-size:17px; color:green;"><b>🔽</b></a></span><!-- jobs-toc:heading-end -->

```text
.
├── README.md
├── .gitignore
├── icon.png
├── LANFileServer.py/
├── JobsMockTool.py/
├── JobsReverseIPA.py/
├── JobsAppTrafficMonitor.py/
├── JobsCodexAccountSwitcher.py/
├── JobsCodexTokenMonitor.py/
├── JobsSSHKeyMgr.py/
└── JobsHotspot.py/
```

- `./README.md`：当前整库说明和工具索引。
- `./.gitignore`：整库唯一的 Git 忽略规则入口，覆盖各工具的虚拟环境、缓存、构建产物和功能专属忽略路径。
- `./icon.png`：仓库级图标资源。
- `./*/README.md`：每个工具自己的完整说明，包含运行方式、输出目录、日志位置和风险边界。

## <span id="jobs-toc-heading-4" data-jobs-toc="v2">三、运行与打包 <a href="#前言" style="font-size:17px; color:green;"><b>🔼</b></a> <a href="#🔚" style="font-size:17px; color:green;"><b>🔽</b></a></span><!-- jobs-toc:heading-end -->

### <span id="jobs-toc-heading-5" data-jobs-toc="v2">3.1、macOS <a href="#前言" style="font-size:17px; color:green;"><b>🔼</b></a> <a href="#🔚" style="font-size:17px; color:green;"><b>🔽</b></a></span><!-- jobs-toc:heading-end -->

macOS 安装包必须在 macOS 本机生成。进入目标工具目录后，双击或执行对应入口：

```shell
./【MacOS】📦生成dmg.command/【MacOS】📦生成dmg.command
```

脚本通常会创建或复用 `.venv` / `.venv-universal2`，按需安装依赖，再通过 [**PyInstaller**](https://pyinstaller.org/) 生成 `.app` 和 `.dmg`。涉及清理旧 `build` / `dist` 的脚本，会在内部自述里提示影响范围，部分工具要求输入 `YES` 才继续。

### <span id="jobs-toc-heading-6" data-jobs-toc="v2">3.2、Windows <a href="#前言" style="font-size:17px; color:green;"><b>🔼</b></a> <a href="#🔚" style="font-size:17px; color:green;"><b>🔽</b></a></span><!-- jobs-toc:heading-end -->

Windows 可执行程序必须在 Windows 本机生成或启动。进入目标工具目录后，双击或执行对应入口：

```shell
./【Windows】📦生成exe.bat/【Windows】📦生成exe.bat
```

本仓 10 个自维护 BAT 入口在 `setlocal` 范围内限定 Python 使用 UTF-8；安装、构建与源码运行的子进程继承该设置，退出后不改用户或系统环境。三个 Python 内层构建器也为直接调用、标准流重定向和日志设置 UTF-8，避免 GBK 无法输出符号或路径导致中断。

不同工具的 Windows 入口行为略有差异：`JobsMockTool`、`JobsReverseIPA`、`JobsAppTrafficMonitor` 以打包 `.exe` 为主；`LANFileServer` 默认启动图形界面，内部保留 `build-exe` 打包模式。

### 3.3、<span id="windows-compatibility">Windows 系统与架构矩阵</span> <a href="#前言" style="font-size:17px; color:green;"><b>🔼</b></a> <a href="#🔚" style="font-size:17px; color:green;"><b>🔽</b></a>

下表依据各工具当前的 `pyproject.toml`、`requirements*.txt` 和 Windows 构建入口整理；Python 版本列表示源码 / 构建要求，不能单独作为成品最低 Windows 版本。

| 工具 | Python / GUI 依赖边界 | Windows 成品目标与限制 |
| --- | --- | --- |
| [LANFileServer](./LANFileServer.py/README.md) | 声明 Python `>=3.9`、[**PySide6**](https://doc.qt.io/qtforpython-6/) `>=6.7` | Windows 10 / 11 x64；旧系统不在当前 Qt 6 分发范围。 |
| [JobsMockTool](./JobsMockTool.py/README.md) | 未单独声明 Python 下限；PySide6 `>=6.7`，含 QtWebEngine | Windows 10 / 11 x64；实际 Python 与图形依赖须同时满足构建要求。 |
| [JobsReverseIPA](./JobsReverseIPA.py/README.md) | 声明 Python `>=3.10`、PySide6 `>=6.6` | Windows 10 / 11 x64；工具链与各分析能力另按本工具说明核对。 |
| [JobsAppTrafficMonitor](./JobsAppTrafficMonitor.py/README.md) | 声明 Python `>=3.11`、PySide6 `>=6.8,<7`；ETW 只用标准库 / 系统 API | Windows 10 / 11 x64 为打包目标；按进程采集需管理员权限，原生回环、图形界面与成品打包分别验收。 |
| [JobsSystemMonitor](./JobsSystemMonitor.py/README.md) | Python `>=3.11`、PySide6 `>=6.8,<7` | Windows 10 / 11 x64；任务栏、托盘与 GPU 统计需目标机验收。 |
| [JobsCodexAccountSwitcher](./JobsCodexAccountSwitcher.py/README.md) | Python `>=3.11`、PySide6 `>=6.8,<7` | Windows 10 / 11 x64；还需目标环境中实际可用的桌面应用及对应授权入口。 |
| [JobsCodexTokenMonitor](./JobsCodexTokenMonitor.py/README.md) | Python `>=3.11`、PySide6 `>=6.8,<7` | Windows 10 / 11 x64；日志读取与桌面交互按目标环境验收。 |
| [JobsSSHKeyMgr](./JobsSSHKeyMgr.py/README.md) | Python `>=3.11`、PySide6 `>=6.8,<7`；OpenSSH 为业务依赖，GitHub CLI 可选 | Windows 10 / 11 x64 为目标；系统工具、agent 服务、字体及窗口行为需目标机验收。 |
| [JobsRemoteHost](./JobsRemoteHost.py/README.md) | Python `>=3.11`、Tkinter；其他 Python 依赖未锁精确版本，cloudflared 使用最新下载 | Windows 10 / 11 为当前测试目标；Windows 8.1 仅可作为固定依赖后的探索项，尚未验证或承诺支持。 |

[**Qt 6.8 官方 Windows 配置**](https://doc.qt.io/qt-6.8/windows.html)列出 Windows 10 **1809 起**及 Windows 11 的 x64 环境，并列出 ARM64 配置。这是对应 Qt 版本的上游边界；本仓多个依赖使用 `>=` 范围，实际安装的 Qt / Python / 原生库可能提高系统要求，因此没有适用于所有构建产物的统一最低 Windows build。当前 Qt 6 工具不提供 XP、Vista、Windows 7、8、8.1 兼容包；ARM64 上游可用也不等于本仓已经交付并验收 ARM64 成品。

[**Python 3.11 官方 Windows 要求**](https://docs.python.org/3.11/using/windows.html)为 Windows 8.1 起；它只能说明 `JobsRemoteHost` 所用运行时的边界，不能覆盖新版 Pillow、mss、cloudflared 等组件的要求。当前不提供 XP / Vista / Windows 7 / 8 的兼容构建；Windows 8.1 完整组合仍待验证。使用更高 Python 版本重新打包时，应重新核对系统要求。

构建时须在 Windows 准备兼容的 Python、构建器及依赖；成功分发的成品包含 Python 运行时，接收方无需另装 Python。`.exe` 后缀不表示架构通用，实际架构取决于构建 Python 与原生依赖；x86 / ARM64 尚未形成统一交付与验收矩阵。目录式产物必须完整分发 EXE、`_internal/` 及配套文件，不能只复制单个 EXE。

测试时记录 Windows 版本 / build、CPU 架构及本次 Python、Qt、PyInstaller 和外部工具版本。优先在 Windows 10 / 11 x64 的无 Python 干净虚拟机检查完整成品，再验证各项业务；远程屏幕采集、输入控制、托盘、任务栏和 GPU 能力另做实体机检查。源码检查、打包成功或窗口出现，均不能代替对应系统的完整功能验收。

## <span id="jobs-toc-heading-8" data-jobs-toc="v2">四、输出与忽略规则 <a href="#前言" style="font-size:17px; color:green;"><b>🔼</b></a> <a href="#🔚" style="font-size:17px; color:green;"><b>🔽</b></a></span><!-- jobs-toc:heading-end -->

构建产物默认不入库，根目录 `.gitignore` 已覆盖这些类型：

```text
__pycache__/
.venv/
.venv-*/
build/
dist/
dmg-staging/
output/
*.dmg
*.app/
*.exe
*.egg-info/
```

源码、`README.md`、`requirements.txt`、`pyproject.toml`、`*.spec`、资源文件和打包入口脚本保留入库。

## <span id="jobs-toc-heading-9" data-jobs-toc="v2">五、风险边界 <a href="#前言" style="font-size:17px; color:green;"><b>🔼</b></a> <a href="#🔚" style="font-size:17px; color:green;"><b>🔽</b></a></span><!-- jobs-toc:heading-end -->

- `LANFileServer` 会把选中的文件 / 文件夹暴露给同一局域网设备，不要共享隐私目录、密码文件或浏览器数据。
- `JobsReverseIPA` 只用于用户有权审计的 `.ipa` 文件，不用于未授权分析。
- `JobsMockTool` 默认服务本机 Mock 请求，不要把真实 Token、密码和用户隐私写进 Mock 配置。
- `JobsAppTrafficMonitor` 只读取连接元数据与字节计数，不读取、解析或保存数据包内容。
- 当前构建脚本生成的 macOS / Windows 成品通常没有正式代码签名；公开分发前需要按平台补齐签名和公证。

## <span id="jobs-toc-heading-10" data-jobs-toc="v2">六、维护说明 <a href="#前言" style="font-size:17px; color:green;"><b>🔼</b></a> <a href="#🔚" style="font-size:17px; color:green;"><b>🔽</b></a></span><!-- jobs-toc:heading-end -->

- 新增工具时优先保持同类结构：`ToolName.py/README.md`、`【MacOS】📦生成dmg.command`、`【Windows】📦生成exe.bat`、`ToolName/`。
- 外层 README 负责用户运行前说明；内层 Python 工程负责源码、依赖、测试和构建细节。
- 修改入口脚本名后，同步更新对应工具 README、脚本内置自述和本文件工具总览。
- 提交前先看 `git status --ignored`，确认构建产物仍然被忽略。

打包前会清理该应用工程的旧 `dist` 产物，清理失败则停止；成功后自动打开当前平台产物的磁盘位置并运行本次生成的 APP / EXE，结尾无需回车。失败时不启动软件；运行前的防误触确认保留。

必需依赖缺失时，直接回车联网安装；输入任意字符后回车取消整个流程。安装失败或复检仍不可用时停止，不继续清理旧产物或打包。健康依赖直接复用；可选升级和词库更新仍为回车跳过、任意字符执行。

第一层交付目录与平台打包脚本同层保存 `dist/`，以及最新 APP / DMG 的相对符号链接（Mac）或 EXE / 分发包的 `.lnk`（Windows）。双击快捷方式即可接触成品，真实文件保留在 `dist/`；成功构建自动更新入口，清理旧产物时移除对应旧入口。尚无成品时不生成无效快捷方式。

## <span id="jobs-toc-heading-11" data-jobs-toc="v2">七、上传 README 演示视频 <a href="#前言" style="font-size:17px; color:green;"><b>🔼</b></a> <a href="#🔚" style="font-size:17px; color:green;"><b>🔽</b></a></span><!-- jobs-toc:heading-end -->

上传入口位于相邻的 `JobsCommand@Gits` 仓，需要同时检出该仓后使用下方链接；本工具仓内保留完整使用说明。

双击 [上传 GitHub 视频附件脚本](../JobsCommand@Gits/MacOS/【MacOS】🎬上传GitHub视频附件.command/【MacOS】🎬上传GitHub视频附件.command)，按回车确认，再输入 GitHub 仓库首页地址并拖入本地视频。支持 MP4 / MOV / WEBM；也可通过命令行传入这两个参数。需要安装 [**GitHub CLI**](https://cli.github.com/)，当前账号须有目标仓库写权限；未登录时脚本会引导登录。

上传成功后显示附件 URL 并复制到剪贴板。将 URL 单独放到本地 README 的一段中，前后留空行，再正常提交、推送即可；以后只替换该 URL。脚本不修改 README，不创建提交或推送。每次运行都会创建新附件，失败时不自动重试，防止重复上传。运行日志路径会在终端显示，保存在系统临时目录。

**上传后的附件单独删除比较麻烦，需要联系 [GitHub Support](https://support.github.com/)。** 删除本地项目文件夹、仓库中的视频文件或 README 链接不会删除附件。[GitHub 工作人员曾说明](https://github.com/orgs/community/discussions/54551#discussioncomment-6730698)，删除整个 GitHub **远端仓库**会触发附件延迟清理；这不是即时删除承诺，不建议仅为删除视频而删除整个仓库。

构建产物使用本机本地构建时间，格式为 `YYYY.MM.DD HH-mm-ss`（年月日时分秒），例如 `2020.06.04 12-23-21`。每次构建的 APP、DMG、EXE、ZIP 和配套文件统一保存到交付层 `./dist/YYYY.MM.DD HH-mm-ss/`，同次构建只取一次时间；第一层快捷方式指向本次时间目录，成功后打开该目录并启动其中的软件。旧产物沿用原有清理规则；历史产物缺少可靠构建时间时，不补写推测时间。

[**Homebrew**](https://brew.sh/) 安装路径由用户选择：已有可运行安装时复用；确实需要安装时先强提示，只有精确输入大写 `YES` 才选择系统标准目录，其它输入或直接回车选择当前用户的 `.local/homebrew`。`YES` 只表示选择路径，权限与密码由官方安装器实际处理；有管理员权限也可以选用户目录。选定路径失败立即停止，不自动切换；`Ctrl+C` / 输入结束取消整个任务。

## 八、<span id="single-repository-management">单仓管理与文档目录</span> <a href="#前言" style="font-size:17px; color:green;"><b>🔼</b></a> <a href="#🔚" style="font-size:17px; color:green;"><b>🔽</b></a>

所有工具随本仓一起取得和更新，不再分别初始化、下载或关联子仓。日常在本仓现行分支审阅改动并提交；功能目录保留各自源码、资源、依赖、测试和打包入口。

忽略规则集中在根目录 `./.gitignore`，子功能目录不再放置 `.gitignore`、`.gitmodules` 或 `.git`。通用缓存与构建规则共用，特定工具的规则使用对应目录前缀，保持原有作用范围。工程目录内保留业务文件和必要的构建声明。

<strong id="external-markdown-toc">文档目录工具与 Git 属性存放在工程外</strong>

[**Markdown**](https://markdown.cn) 目录仍按“本地 `[toc]`、整文件暂存生成默认收起的折叠目录、检出还原 `[toc]`”运行。`.jobs-markdown-toc` 工具与精确文档清单保存在用户数据目录，Git 属性存放在本仓实际元数据的 `info/attributes`；工程树不携带 `.gitattributes` 或目录转换工具。原有 BAT 行尾约束按功能路径保留。

在本仓根目录查看本机配置，并检查目录转换：

```shell
git rev-parse --git-path info/attributes
git config --local --get filter.jobs-markdown-toc.clean
node "$(git config --local --get jobs.markdown-toc-tool)" status
node "$(git config --local --get jobs.markdown-toc-tool)" verify
```

外置工具同目录的 `README.md` 说明维护、预览与恢复命令。以上配置只保存在本机；换机或全新克隆时，需另行部署外置工具、精确清单和本地属性，配置不会随源码克隆传播。

## 九、<span id="repository-layout-and-entrypoints">本仓目录与脚本入口</span> <a href="#前言" style="font-size:17px; color:green;"><b>🔼</b></a> <a href="#🔚" style="font-size:17px; color:green;"><b>🔽</b></a>

以下为本仓统一管理的源码与维护入口；依赖环境、Git 元数据、构建缓存和生成产物略去，各工具仅展开主要入口。

```text
.
├── .gitignore
├── icon.png
├── JobsAppTrafficMonitor.py/  # 本仓普通源码目录
├── JobsCodexAccountSwitcher.py/  # 本仓普通源码目录
├── JobsCodexTokenMonitor.py/
│   ├── 【MacOS】📦生成dmg.command/
│   ├── 【Windows】📦生成exe.bat/
│   ├── icon.png
│   ├── JobsCodexTokenMonitor/
│   └── README.md
├── JobsMockTool.py/  # 本仓普通源码目录
├── JobsRemoteHost.py/  # 本仓普通源码目录
├── JobsReverseIPA.py/  # 本仓普通源码目录
├── JobsSystemMonitor.py/  # 本仓普通源码目录
├── LANFileServer.py/  # 本仓普通源码目录
└── README.md
```

- 各工具目录均由本仓统一跟踪，分别在各自 `README.md` 查看源码职责与入口。
  * [JobsAppTrafficMonitor.py](./JobsAppTrafficMonitor.py/README.md)、[JobsCodexAccountSwitcher.py](./JobsCodexAccountSwitcher.py/README.md)、[JobsMockTool.py](./JobsMockTool.py/README.md)、[JobsRemoteHost.py](./JobsRemoteHost.py/README.md)、[JobsReverseIPA.py](./JobsReverseIPA.py/README.md)、[JobsSystemMonitor.py](./JobsSystemMonitor.py/README.md)、[LANFileServer.py](./LANFileServer.py/README.md)。
* `JobsCodexTokenMonitor.py/` 当前是本仓内普通工具目录，保存独立用量监控源码、资源和平台入口；下列流程由本仓统一列出。

### <span id="jobs-toc-heading-14" data-jobs-toc="v2">[【MacOS】📦生成dmg.command](./JobsCodexTokenMonitor.py/【MacOS】📦生成dmg.command/【MacOS】📦生成dmg.command)</span><!-- jobs-toc:heading-end -->

> **目的：** 在本机生成 JobsCodexTokenMonitor 的 APP / DMG，并打开本次成品。

* 阅读自述，确认环境准备；检查 Homebrew 和兼容的 Python，再交给本工程构建器。
  * 必需依赖缺失：回车安装，任意非空输入取消；环境或复检失败时停止。
* 确认构建范围后准备虚拟环境与依赖，仅清理本工具外层 `dist/` 的旧产物。
* 打包并校验 APP，封装 DMG，统一输出到 `dist/YYYY.MM.DD HH-mm-ss/`。
* 更新第一层产物快捷方式，打开产物目录，再启动本次 APP；失败时查看系统临时目录中的构建日志。

### <span id="jobs-toc-heading-15" data-jobs-toc="v2">[【Windows】📦生成exe.bat](./JobsCodexTokenMonitor.py/【Windows】📦生成exe.bat/【Windows】📦生成exe.bat)</span><!-- jobs-toc:heading-end -->

> **目的：** 在 Windows 本机生成 JobsCodexTokenMonitor 的 EXE 分发目录与 ZIP。

* 显示构建说明，依次检查 `py -3` 和 `python`，转交本工程构建器。
  * 没有可用 Python 3.11+：提示安装并停止；`--help` 只显示说明。
* 确认后准备项目虚拟环境；必需依赖缺失时回车安装，任意非空输入取消。
* 清理本工具外层 `dist/`，生成并核验 EXE 目录和 ZIP，保存到同一构建时间目录。
* 更新 EXE / ZIP 快捷方式，打开产物目录并启动新 EXE；失败时停止并保留日志。

<a id="🔚" href="#前言" style="font-size:17px; color:green; font-weight:bold;">我是有底线的➤点我回到首页</a>
