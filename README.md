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
- [八、Git 子模块脚本](#git-submodule-scripts)
  - [【MacOS】⏬下载配置当前Git子模块（可向下同步递归）.command](#jobs-toc-heading-13)
  - [【MacOS】🧾更新gitmodules.command](#jobs-toc-heading-14)
- [九、本仓目录与脚本入口](#repository-layout-and-entrypoints)
  - [【MacOS】📦生成dmg.command](#jobs-toc-heading-16)
  - [【Windows】📦生成exe.bat](#jobs-toc-heading-17)

</details>
<!-- jobs-toc:end -->

---

## <span id="jobs-toc-heading-1" data-jobs-toc="v2">🔥 <font id=前言>前言</font></span><!-- jobs-toc:heading-end -->

**最低支持系统：** [**Windows**](https://www.microsoft.com/windows) **10 64 位（x64）**。这是当前最低支持目标；具体最低 build 尚未锁定，完整实机兼容性仍待验证。

`JobsPythonTools.py` 是 Jobs 本地 [**Python**](https://www.python.org) 桌面工具集合，覆盖文件共享、Mock API、IPA 静态分析、按 App 流量监控、整机监控、浏览器远程协助、Codex 账户切换及 Token 用量监控。各工具的当前能力和详细操作入口见下方总览。

**系统兼容范围：** 当前 EXE 以 [**Windows**](https://www.microsoft.com/windows) 10 / 11 x64 为主要构建与测试目标；Windows 打包入口不代表 XP、Vista、7、8、8.1 或所有 CPU 架构通用。多数工具使用 [**Qt 6**](https://doc.qt.io/qt-6/)，`JobsRemoteHost` 的 [**Tkinter**](https://docs.python.org/3.11/library/tkinter.html) 路线另有依赖边界，详见 [Windows 系统与架构矩阵](#windows-compatibility)。目前尚无覆盖各 Windows 版本与架构的完整实机验收结果。

多数工具采用“外层交付目录 + 内层 Python 工程”结构：外层放总说明、双击入口和 `dist/YYYY.MM.DD HH-mm-ss/` 产物，内层放源码、依赖、资源、测试与构建配置；具体布局以各工具 README 为准。

独立 `.command` 入口先显示内置自述：标题红色加粗，编号正文蓝色且不加粗，非彩色终端显示纯文本；在终端回车确认后执行，`Ctrl+C` 取消，缺少可交互输入时停止。子仓下载与关联操作见 [Git 子模块脚本](#git-submodule-scripts)。

## <span id="jobs-toc-heading-2" data-jobs-toc="v2">一、工具总览 <a href="#前言" style="font-size:17px; color:green;"><b>🔼</b></a> <a href="#🔚" style="font-size:17px; color:green;"><b>🔽</b></a></span><!-- jobs-toc:heading-end -->

| 工具 | 目录 | 核心用途 | 主要入口 |
| --- | --- | --- | --- |
| `LANFileServer` | [功能与操作](./LANFileServer.py/README.md) | 临时 Python / 非临时 Nginx 文件共享、浏览器预览 / 下载、可选上传、二维码、项目聊天室与访问记录。 | [macOS](./LANFileServer.py/【MacOS】📦生成dmg.command) / [Windows](./LANFileServer.py/【Windows】📦生成exe.bat) 打包 |
| `JobsMockTool` | [功能与操作](./JobsMockTool.py/README.md) | 多接口、单端口 / 独立端口、query / body / headers 条件响应、JSON 树形编辑、内置请求测试与配置保存。 | [macOS](./JobsMockTool.py/【MacOS】📦生成dmg.command) / [Windows](./JobsMockTool.py/【Windows】📦生成exe.bat)；[构建脚本](./JobsMockTool.py/build_macos.command/README.md) |
| `JobsReverseIPA` | [功能与操作](./JobsReverseIPA.py/README.md) | 授权 IPA 静态分析、环境体检、资源 / 敏感字符串扫描，输出 HTML / JSON / Markdown 报告。 | [macOS](./JobsReverseIPA.py/【MacOS】📦生成dmg.command) / [Windows](./JobsReverseIPA.py/【Windows】📦生成exe.bat) 打包 |
| `JobsAppTrafficMonitor` | [功能与操作](./JobsAppTrafficMonitor.py/README.md) | macOS 用 nettop、Windows 用 ETW 按 App / 进程统计速率与收发字节；Windows 采集需管理员权限。 | [macOS](./JobsAppTrafficMonitor.py/【MacOS】📦生成dmg.command) / [Windows](./JobsAppTrafficMonitor.py/【Windows】📦生成exe.bat) 打包 |
| `JobsSystemMonitor` | [功能与操作](./JobsSystemMonitor.py/README.md) | CPU / GPU / 内存 / 上下行速率、历史趋势、网卡选择、刷新间隔；macOS 菜单栏与 Windows 监控条 / 托盘。 | 双端打包入口，Windows 桌面行为需目标机验收 |
| `JobsRemoteHost` | [功能与操作](./JobsRemoteHost.py/README.md) | 浏览器发起观看 / 控制申请，本机弹窗授权；局域网地址 / 临时公网链接、菜单栏 / 托盘驻留及停止服务。 | 双端打包、源码运行及协议自检入口见功能说明 |
| `JobsCodexAccountSwitcher` | `./JobsCodexAccountSwitcher.py/` | 保存 Codex 文件登录态（口令保护可选）、退出后切换与重启；桌面兼容需核验。 | [说明](./JobsCodexAccountSwitcher.py/README.md)、双端打包入口 |
| `JobsCodexTokenMonitor` | `./JobsCodexTokenMonitor.py/` | 独立显示 Codex 每轮输入 / 输出 Token；主面板常驻“窗口置顶”复选框，主题及会话联动统一从 `⋯ → 设置…` 进入。 | [说明](./JobsCodexTokenMonitor.py/README.md)、双端打包入口 |

账户切换与 Token 监控是两个独立 Python 工程，各有源码、依赖、测试、APP / EXE 和分发包。Token 工具不依赖账户工具；可以只安装其中一个。`JobsCodexTokenMonitor.py/` 当前由本总仓直接管理，尚未配置独立远端或登记为子模块，`./.gitmodules` 不包含虚构的下载地址。

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
└── JobsCodexTokenMonitor.py/
```

- `./README.md`：当前整库说明和工具索引。
- `./.gitignore`：整库 Git 忽略规则，排除虚拟环境、缓存和构建产物。
- `./icon.png`：仓库级图标资源。
- `./*/README.md`：每个工具自己的完整说明，包含运行方式、输出目录、日志位置和风险边界。

## <span id="jobs-toc-heading-4" data-jobs-toc="v2">三、运行与打包 <a href="#前言" style="font-size:17px; color:green;"><b>🔼</b></a> <a href="#🔚" style="font-size:17px; color:green;"><b>🔽</b></a></span><!-- jobs-toc:heading-end -->

### <span id="jobs-toc-heading-5" data-jobs-toc="v2">3.1、macOS <a href="#前言" style="font-size:17px; color:green;"><b>🔼</b></a> <a href="#🔚" style="font-size:17px; color:green;"><b>🔽</b></a></span><!-- jobs-toc:heading-end -->

macOS 安装包必须在 macOS 本机生成。进入目标工具目录后，双击或执行对应入口：

```shell
./【MacOS】📦生成dmg.command
```

脚本通常会创建或复用 `.venv` / `.venv-universal2`，按需安装依赖，再通过 [**PyInstaller**](https://pyinstaller.org/) 生成 `.app` 和 `.dmg`。涉及清理旧 `build` / `dist` 的脚本，会在内部自述里提示影响范围，部分工具要求输入 `YES` 才继续。

### <span id="jobs-toc-heading-6" data-jobs-toc="v2">3.2、Windows <a href="#前言" style="font-size:17px; color:green;"><b>🔼</b></a> <a href="#🔚" style="font-size:17px; color:green;"><b>🔽</b></a></span><!-- jobs-toc:heading-end -->

Windows 可执行程序必须在 Windows 本机生成或启动。进入目标工具目录后，双击或执行对应入口：

```shell
./【Windows】📦生成exe.bat
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

## 八、<span id="git-submodule-scripts">Git 子模块脚本</span> <a href="#前言" style="font-size:17px; color:green;"><b>🔼</b></a> <a href="#🔚" style="font-size:17px; color:green;"><b>🔽</b></a>

<strong id="markdown-toc-sync">同步后文档目录：本地 `[toc]`，提交后发布折叠目录</strong>

本地编辑保留独占行 `[toc]`；整文件暂存时由 [**Git**](https://git-scm.com/) 过滤器生成按标题层级缩进、默认收起的可折叠目录，正常提交推送后供远端展示。下载入口逐仓检查已生效的 `filter.jobs-markdown-toc` 配置，再决定是否恢复当前工作区；父仓配置不能代替子仓配置。

| 本仓配置与工具 | 同步入口处理 | 结果与依赖 |
| --- | --- | --- |
| 已有有效目录过滤器 | 执行本仓 `.jobs-markdown-toc/MarkdownToc.mjs restore`，再执行 `verify`；已有工作树即使没有新提交，也显式恢复当前正文 | 需要可用的 [**Node.js**](https://nodejs.org) 和完整目录工具；保留正文及原暂存语义 |
| 未配置有效目录过滤器 | 明确跳过目录恢复，不自动安装、注册或改写 Git 配置 | 不额外依赖 Node.js；跳过不代表已有生成目录已恢复为 `[toc]` |
| 已有有效过滤器，但缺少 Node.js / 工具，或还原、验证失败 | 报出具体仓库并停止本轮同步 | 处理该仓配置或工具后重试，不能将本轮视为全部成功 |

默认只拉取的首次克隆先以 `--no-checkout` 复制已预检对象，记录真实远端地址后才首次安全检出，让按真实 URL 匹配的机器过滤器有机会生效；不会为此再次联网获取未经预检的提交。已有生成目录的恢复以当前磁盘正文为来源，不从旧 `HEAD` 或暂存区覆盖正文，也不自动暂存、提交或推送。当前机器尚未注册或换机后没有有效配置时，仍按表中“跳过”处理，不能承诺首次落盘已经是 `[toc]`。

<strong id="readonly-submodule-mode">先选用途：只拉取电脑默认跟随分支最新，子仓保持本地分支</strong>

用途、维护菜单、子仓多选和同步深度统一使用 [**fzf**](https://formulae.brew.sh/formula/fzf)。两种模式启动前都需已有可用 fzf，缺失或损坏时安全停止并提示修复，不自动退回数字菜单。维护菜单按 `←` 返回用途页，子仓与深度页按 `←` 返回维护菜单；返回后保留当前深度并恢复菜单位置。子仓多选用回车勾选 / 取消、空格确认、`Ctrl+A` 全选、`Ctrl+D` 清空；空选不启动同步，`Esc` / `Ctrl+C` 取消本轮。返回只改变后续选择，已经完成的父仓更新不会撤销。

| 启动选择 | 版本依据 | 是否写入父仓提交 |
| --- | --- | --- |
| 只拉取，默认 | 更新当前父仓明确的远程上游，再逐层跟随子仓目标分支最新提交，保持本地跟踪分支 | 不暂存、不提交、不推送 |
| 维护子模块，显式选择 | 按本仓清单及原有菜单，把所选子树更新到各自远端目标分支最新 | 沿用 `AUTO_PARENT_COMMIT` / `AUTO_PARENT_PUSH` 原有开关 |

启动第一屏显示同步策略版本 `2026.10.27-audited`。新电脑须先取得并运行带此版本号的入口；另一台电脑上的本地修改不会自动更新到新电脑。任一仓库拉取、分支切换或递归校验失败时，本轮不能视为全部完成；处理日志中的具体路径后重新运行。

只拉取模式从脚本所在仓库向下递归处理全部已登记子模块；不向上处理，不使用清单新增关联，也不把子仓最新提交自动提交回父仓。各层优先使用直接父仓 `.gitmodules` 的显式 `branch`，`.` 继承该层计划更新后的直接父仓分支；未配置时读取该子仓远端默认分支。首次下载和已有游离 HEAD 都会恢复或创建对应本地跟踪分支，获取最新提交并快进；成功结束时子仓显示实际分支名。每层相对 URL 随当前父仓的下载线路解析。只拉取模式使用系统 Git、zsh、Perl 等现有工具；仅命中有效目录过滤器时另需 Node.js 和该仓完整目录工具，外层用途选择仍需 fzf；只拉取不需要 Homebrew。

子仓源码、未跟踪内容、已暂存 gitlink、未完成操作或本地独有提交会报出具体路径并停止；不会强制覆盖或丢弃独有的游离提交，父仓 `YES` 不扩散到子仓。当前父仓自己的源码改动或本地独有提交，仍须红字列明并精确输入 `YES` 才舍弃。目标分支不存在、远端默认分支无法确定或最新提交获取失败时，停止并报告对应仓库与来源；不会把旧 gitlink SHA 当作最新分支结果。

只拉取模式在入口仓已有本地分支时仍要求明确上游。入口仓自身处于游离 HEAD 时，先使用直接父仓 `.gitmodules` 的显式 `branch`，`.` 继承直接父仓当前分支；无配置时读取 `origin` 或唯一远端的默认分支。已有目标本地分支须明确跟踪所选远端的同名分支；先获取最新提交，预检整棵子树与提交历史，并复查确认期间的状态，再恢复或创建本地跟踪分支。入口源码未提交、需继承分支时直接父仓同样游离、目标不明、目标分支无法快进或存在未受引用保护的独有游离提交时停止；普通父仓的 `YES` 不授权舍弃这些提交。

`REMOTE_NAME` 等原有清单参数只用于维护模式。设置 `DRY_RUN=1` 时，默认只拉取会停止并提示选择维护演练，不能忽略演练标志后执行真实更新。未初始化但存在旧 Git 缓存的空工作树须先恢复，脚本不会覆盖缓存内索引或独有提交。

下文关于清单新增、多选、可切换同步深度、目录清理及自动提交的既有流程，均指显式选择的**维护模式**。只拉取模式默认向下递归到分支最新，不使用这些写入父仓的开关；子仓最新提交与父仓 gitlink 可能不同，父仓会显示待审阅的子模块指针改动。两种模式都保留各仓独立清单和来源显示；两种模式均使用本次私有随机日志，终端会输出实际路径。

<strong id="download-resume-cache">网络不稳定时：保留下载缓存，安全发布工作树</strong>

只拉取与维护模式都会复用已有工作树。首次下载先把目标分支获取到持久裸对象库，再在实际 Git 元数据目录内的本次临时目录以 `--no-checkout` 复制对象、设置真实远端、检出并核验固定提交；全部成功后才移入经过复检的空目标目录。获取或检出失败时只清理本次临时目录，保留持久缓存供重跑使用，不把半成品工作树留在目标位置，不覆盖已有非空目录。已有条件过滤器仍在真实远端配置完成后的首次检出参与转换，不额外联网获取未经预检的提交。

缓存位于实际 Git 目录内的 `jobs-download-cache/v1/<路径与来源哈希>.git`：只拉取统一使用入口仓的 Git 目录，维护模式逐层使用当前父仓的 Git 目录。路径、配置来源与实际展开来源共同区分缓存；成功、失败和正常中断后均保留，不自动清空，所占磁盘空间会持续保留。中断只留下本工具的空缓存目录时可以重新初始化；不明或非空冲突目录保留并停止，不借恢复删除用户内容。

需要同步时正常获取最新分支，已完整下载的对象参与增量协商；后续某仓失败不会清除前面已下载成功的准备对象。**这不是半截 pack 按字节续传**：当前尚未完整接收的 pack 仍可能重新传输。只拉取的首次下载使用 `--depth=1`；维护模式沿用 `SUBMODULE_SHALLOW_CLONE`、`SUBMODULE_DEPTH` 和 `SUBMODULE_FETCH_TAGS`。已有完整仓不改成浅仓，已有工作树更新不重新设置浅克隆深度；浅克隆主要减少历史，当前工作文件中的大包仍须下载。

<strong id="download-complete-marker">每仓完成标记：先查询远端，版本匹配才跳过</strong>

每次运行先用 `ls-remote` 查询目标分支的远端最新提交，再核对该仓实际 Git 目录中的 `jobs-download-complete`。标记记录来源签名（包含配置来源与实际展开 URL 的哈希）、目标分支和已完成提交；本地 `HEAD`、当前分支、远端提交和标记全部匹配，并通过源码风险检查，默认才跳过**当前仓库**的下载与检出。来源哈希避免把带凭据的原始地址写进完成标记。

| 检查结果 | 当前仓库的处理 |
| --- | --- |
| 标记匹配远端最新提交，本地分支 / `HEAD` 和源码状态也符合，且使用默认不取 tags 策略 | 跳过当前仓下载与检出，仍核对或补齐子模块登记、`active` 和 `absorbgitdirs` 元数据归集，再独立检查所选范围内的后代。 |
| 标记不存在、来源 / 分支 / 提交改变，或本地状态与标记不一致 | 进入正常同步及既有风险检查，成功核验后才写入或更新标记。 |
| 已经是最新代码，但此前没有完成标记 | 正常同步一次，核验成功后建立标记，后续运行才可按标记跳过。 |
| 查询远端、下载、检出或核验失败 | 不写本轮成功标记；保留失败状态和下载缓存，处理具体原因后重跑。 |

父仓标记只表示该仓完成，**不表示整棵子树完成**；每个后代仍独立查询与核对。标记不会放宽源码、暂存内容、分叉或独有提交的保护，也不会跳过必要的本地登记修复；发现风险仍按原有门禁停止或确认。维护模式中 `SUBMODULE_FETCH_TAGS=0` 为默认省流量策略；显式设为 `1` 时，每次仍同步 tags，目标分支 `HEAD` 没变也不能被完成标记跳过。完成标记和下载缓存都在 Git 元数据目录内，不生成源码文件或自动提交。

需要强制重新同步某个仓库时，先停止该下载任务，在该仓执行下面的只读命令定位标记，然后只移除这个 `jobs-download-complete` 文件；保留 `modules/`、索引、对象缓存和其它 Git 元数据。移除某个仓的标记只影响该仓，后代仍按各自标记检查：

```shell
git rev-parse --git-path jobs-download-complete
```

| 环境变量 | 默认值 | 允许范围 | 作用 |
| --- | --- | --- | --- |
| `JOBS_DOWNLOAD_TIMEOUT` | `900` | `1–86400` | 单次 Git 网络命令总时限，单位秒；超时终止该命令及其子进程。 |
| `JOBS_DOWNLOAD_ATTEMPTS` | `3` | `1–10` | `clone` / `fetch` / 远端查询遇网络错误时的最多尝试次数，包含首次。 |
| `JOBS_DOWNLOAD_RETRY_DELAY` | `2` | `0–60` | 重试等待基数，默认两次分别等待 2、4 秒；`0` 表示不等待。 |
| `JOBS_DOWNLOAD_LOW_SPEED_LIMIT` | `1024` | `1–1000000000` | HTTP / HTTPS 低速阈值，单位字节 / 秒。 |
| `JOBS_DOWNLOAD_LOW_SPEED_TIME` | `60` | `1–3600` | 持续低于阈值达到此秒数后终止该次传输。 |

参数须为对应范围内的十进制整数，空值、表达式和越界值会停止执行。认证、权限、分支不存在和本地仓库错误保留失败状态，按日志处理后重跑；`pull` 不自动重复合并 / rebase，`push` 不使用下载重试包装。参数只影响本次脚本及其 Git 子进程，不修改全局 HTTP 或代理配置。同一入口通过共用锁阻止并行运行；异常强制结束留下锁时，须先确认旧进程已经退出再处理日志指明的锁目录。

维护模式在父仓工作区可拉取时，只精确 `fetch` 当前目标分支一次，固定本次远端跟踪目标，再在本地 `rebase` 到该目标；不会为了同一次父仓更新再发起 `pull` 的第二次网络获取。远端获取失败或 rebase 冲突会停止本轮，不继续处理子仓。父仓存在未提交内容时继续按原有策略跳过父仓拉取，具体风险与后续所选子仓分别检查。

脚本是可单独复制的完整入口：共享函数在本文件内只维护一份，只拉取流程按明确白名单导出所需函数到独立 zsh 子进程，不依赖外置支持库。两种模式的外层用途选择均要求已有健康的 fzf；只拉取不需要 Homebrew，维护模式仅在 fzf 修复确需且确认后使用 Homebrew，不为拉代码批量升级全部已安装软件。

两种模式的日志都在系统临时目录中使用本次唯一的随机文件名，权限为 `600`；以终端打印的“本次日志”或“日志”完整路径为准，不根据固定名称猜测。来源和诊断按既有规则脱敏。缓存、临时检出目录与完成标记放在 Git 元数据目录内，不进入源码或提交。

在本 README 所在目录运行，下面把单次时限放宽到 30 分钟，其余参数使用默认值；普通使用仍可直接双击脚本。网络慢但持续有数据时可适当提高总时限，避免完整大包尚未传完就达到时限：

```shell
JOBS_DOWNLOAD_TIMEOUT=1800 \
  /bin/zsh './【MacOS】⏬下载配置当前Git子模块（可向下同步递归）.command'
```

终端来源块后会显示 `下载缓存（重跑复用已完成对象）` 及其实际路径。这里的下载对象缓存与 `modules/` 中已有子模块的索引、配置和历史不同；后者仍按原有归属及索引保护规则处理，不能为重试删除它们。

维护模式补齐或新增登记时，不自动写入 `branch = main`；已有 `branch` 与缺省状态均保留。显式 `branch` 严格指定目标分支，`.` 继承直接父仓分支；未配置时跟随子仓远端默认分支。目标不存在、直接父仓分支无法确定或远端默认分支无法确定时停止。

<strong id="submodule-quick-look">父子仓多平台地址速览</strong>

当前 `./.gitmodules` 使用相对地址，例如：

```ini
[submodule "LANFileServer.py"]
    path = LANFileServer.py
    url = ../LANFileServer.git
    branch = main
```

下表展示原生 Git 从父仓地址解析相对 URL 的结果，前提是全新克隆且没有本地 URL 覆盖。前两行来自本地已配置的 [**GitHub**](https://github.com) / [**Gitee**](https://gitee.com) 远端；自建平台仅为结构示例，未部署。

| 平台 | 父仓克隆地址 | 子仓解析地址 |
| --- | --- | --- |
| GitHub | `git@github.com:JobsKits/JobsPythonTools.git` | `git@github.com:JobsKits/LANFileServer.git` |
| Gitee | `git@gitee.com:JobsGo/JobsPythonTools.git` | `git@gitee.com:JobsGo/LANFileServer.git` |
| 自建平台，仅结构示例 | `ssh://git@git.example.com:2222/team/JobsPythonTools.git` | `ssh://git@git.example.com:2222/team/LANFileServer.git` |

`path` 是本地目录，`url` 是远端仓库位置；相对 URL 跟随父仓默认远端的平台、组织、协议与端口，前提是该平台已有对应子仓及父仓锁定的提交。已有克隆须核对默认远端和本地子模块配置，仅新增 remote 不会切换线路。

**下载脚本的 Gitee 传输规则：** `【MacOS】⏬下载配置当前Git子模块（可向下同步递归）.command` 在本次运行中，将 `git@gitee.com:`、`ssh://git@gitee.com/`、`ssh://git@gitee.com:22/` 开头的标准地址统一通过 `https://gitee.com/` 访问，保留账号、真实仓名和分支；即使设置 `GIT_URL_STYLE=ssh`，这类 Gitee 地址仍使用 HTTPS。各层首次克隆和后续拉取都继承该规则，历史子模块中的 SSH 地址无需新电脑先配置 SSH 密钥。

规则通过追加进程级 `GIT_CONFIG_COUNT` / `url.https://gitee.com/.insteadOf` 配置传给子进程，不写入全局 Git 配置，也不依赖其它工程路径。GitHub、其它主机及非 `22` 的自定义 SSH 端口保持原规则。克隆或递归更新失败会返回非零状态，停止本轮同步并保留错误；不会再输出该项同步成功。各仓清单与浅克隆参数保留；全量同步默认逐仓复用已有工作区，空或缺失目录才首次克隆，不批量删除旧仓名目录、多层子树或缓存。未提交内容须逐仓处理，精确 `YES` 仅放弃当前仓自己的内容。

### <span id="jobs-toc-heading-13" data-jobs-toc="v2">[【MacOS】⏬下载配置当前Git子模块（可向下同步递归）.command](./【MacOS】⏬下载配置当前Git子模块（可向下同步递归）.command)</span><!-- jobs-toc:heading-end -->

> **目的：** 把选定子仓及可选的后代子模块同步到各自远端目标分支最新提交，并让入口父仓记录对应版本。

- 启动时回车默认进入[只拉取模式](#readonly-submodule-mode)，先预检本地状态，再查询当前父仓及子仓目标分支最新提交，按完成标记判断跳过或同步；恢复已有游离 HEAD，不提交、不推送。
- 显式选择维护模式后，按以下原有清单和菜单流程处理。

* 阅读自述并回车，检查环境、载入脚本子仓清单，先精确获取父仓目标分支一次，再本地 rebase 到已固定的目标；获取失败或冲突即停止本轮。

  * 父仓有未提交改动时跳过拉取，继续进入子仓菜单。

* 在主菜单选择同步范围；“切换同步深度”可在默认“向下递归”和“仅直属子模块”之间切换，当前深度适用于各同步动作。

  * 全量：逐项同步清单内全部目标，按目录状态复用或首次克隆。
  * 指定：勾选需要的子仓；已有：只更新清单中本地已有的子仓，没有任何已有子仓时转全量。
  * 新地址：输入地址，添加并同步一个子仓。

* 补齐 `.gitmodules` 缺项，默认保留已有 URL、分支和旧登记；子仓有未提交、已暂存或未跟踪内容：红字加粗显示该仓绝对路径并循环等待；精确输入 `YES` 只放弃当前仓自己的未提交内容，或在外部处理后回车复检。其它输入继续复检；无交互或输入结束则停止。

  * 全量模式逐仓复用已有工作区；空或缺失目录首次克隆，既有缓存核验后恢复；非 Git 非空目录保护并停止。

* 拉取并快进到远端目标分支最新提交：优先使用该层 `.gitmodules` 显式 `branch`，`.` 继承直接父仓分支；未设置时读取该子仓远端默认分支；显式目标分支不存在时立即停止，不回退其它分支。

  * 目录为空或缺失：首次克隆；已有有效 Git 工作区：默认不取 tags 时，远端最新提交、完成标记与本地状态匹配可跳过当前仓，否则 `fetch` 后切换或创建目标本地跟踪分支，仅快进更新；本地领先远端或分叉时停止并保留提交。

* 按当前深度同步：默认逐层读取所选子仓下的 `.gitmodules`，将已登记后代同步到各自远端目标分支最新提交；仅直属模式不下载或更新下层代码。
  * 只处理本层所选子树，不向上扫描，也不接管未登记的嵌套仓库。
  * 递归更新本层前先检查当前已有后代；各仓单独确认，子模块 HEAD 与父仓 gitlink 的普通差异不作为源码未提交反复提示。
  * `YES` 清理仅作用于当前仓：`reset --hard HEAD` 与 `clean -fd`；保留忽略文件和独立嵌套 Git 仓，残留冲突须外部处理后复检。
  * `PRUNE_STALE_GITMODULES` 默认 `0`，保留清单外旧登记；主动设为 `1` 时，每个旧登记另用红字加粗列明目录和后代删除范围，逐项精确输入 `YES` 才删除，其它输入、输入结束或非交互则停止；演练只展示，删除前仍逐仓检查已有后代。
  * 深层只下载更新，不自动暂存或提交其父仓的 gitlink；递归后这些父仓可能显示子模块指针改动，保留待审阅。

* 整理入口父仓关联与 Git 元数据。

* 默认自动提交入口父仓的 `.gitmodules` / 子模块指针变化，不自动推送（`AUTO_PARENT_COMMIT=1`、`AUTO_PARENT_PUSH=0`），最后显示日志位置。

### <span id="jobs-toc-heading-14" data-jobs-toc="v2">[【MacOS】🧾更新gitmodules.command](./【MacOS】🧾更新gitmodules.command)</span><!-- jobs-toc:heading-end -->

> **目的：** 把已在本地的直属子仓增量登记为完整子模块，保留已有版本选择。

* 阅读自述并回车，只扫描父仓第一层真实子仓，预检路径、远端与关联冲突。

* 展示增量关联计划：补齐缺失登记，保留已有 URL、分支、扩展字段、子模块指针和暂未下载目录的登记。

* 确认计划后执行。

  * 直接回车：跳过；输入任意字符后回车：继续；`--dry-run`：只预检与预览。

* 先备份关联配置与索引，再暂存 `.gitmodules` 和缺失的子模块指针，执行 `submodule init` 与必要的 `absorbgitdirs`。

  * 新指针取子仓当前提交；已有指针保留。备份位于父仓实际 Git 目录的 `jobs-submodule-backups/`，终端显示具体位置。

* 核验登记、元数据位置与父子关系，确认子仓提交未变，显示状态与日志位置；不联网、不提交、不推送。

## 九、<span id="repository-layout-and-entrypoints">本仓目录与脚本入口</span> <a href="#前言" style="font-size:17px; color:green;"><b>🔼</b></a> <a href="#🔚" style="font-size:17px; color:green;"><b>🔽</b></a>

以下为当前检出的源码与维护入口；依赖环境、Git 元数据、构建缓存和生成产物略去，独立子仓仅列目录。

```text
.
├── .gitignore
├── .gitmodules
├── 【MacOS】⏬下载配置当前Git子模块（可向下同步递归）.command
├── 【MacOS】🧾更新gitmodules.command
├── icon.png
├── JobsAppTrafficMonitor.py/  # 独立 Git 子仓
├── JobsCodexAccountSwitcher.py/  # 独立 Git 子仓
├── JobsCodexTokenMonitor.py/
│   ├── 【MacOS】📦生成dmg.command
│   ├── 【Windows】📦生成exe.bat
│   ├── icon.png
│   ├── JobsCodexTokenMonitor/
│   └── README.md
├── JobsMockTool.py/  # 独立 Git 子仓
├── JobsRemoteHost.py/  # 独立 Git 子仓
├── JobsReverseIPA.py/  # 独立 Git 子仓
├── JobsSystemMonitor.py/  # 独立 Git 子仓
├── LANFileServer.py/  # 独立 Git 子仓
└── README.md
```

* 各已登记工具目录是独立 Git 子仓，分别在各自根 `README.md` 查看源码职责与入口；本仓的两个 Git 脚本见上一章。
  * [JobsAppTrafficMonitor.py](./JobsAppTrafficMonitor.py/README.md)、[JobsCodexAccountSwitcher.py](./JobsCodexAccountSwitcher.py/README.md)、[JobsMockTool.py](./JobsMockTool.py/README.md)、[JobsRemoteHost.py](./JobsRemoteHost.py/README.md)、[JobsReverseIPA.py](./JobsReverseIPA.py/README.md)、[JobsSystemMonitor.py](./JobsSystemMonitor.py/README.md)、[LANFileServer.py](./LANFileServer.py/README.md)。
* `JobsCodexTokenMonitor.py/` 当前是本仓内普通工具目录，保存独立用量监控源码、资源和平台入口；下列流程由本仓统一列出。

### <span id="jobs-toc-heading-16" data-jobs-toc="v2">[【MacOS】📦生成dmg.command](./JobsCodexTokenMonitor.py/【MacOS】📦生成dmg.command)</span><!-- jobs-toc:heading-end -->

> **目的：** 在本机生成 JobsCodexTokenMonitor 的 APP / DMG，并打开本次成品。

* 阅读自述，确认环境准备；检查 Homebrew 和兼容的 Python，再交给本工程构建器。
  * 必需依赖缺失：回车安装，任意非空输入取消；环境或复检失败时停止。
* 确认构建范围后准备虚拟环境与依赖，仅清理本工具外层 `dist/` 的旧产物。
* 打包并校验 APP，封装 DMG，统一输出到 `dist/YYYY.MM.DD HH-mm-ss/`。
* 更新第一层产物快捷方式，打开产物目录，再启动本次 APP；失败时查看系统临时目录中的构建日志。

### <span id="jobs-toc-heading-17" data-jobs-toc="v2">[【Windows】📦生成exe.bat](./JobsCodexTokenMonitor.py/【Windows】📦生成exe.bat)</span><!-- jobs-toc:heading-end -->

> **目的：** 在 Windows 本机生成 JobsCodexTokenMonitor 的 EXE 分发目录与 ZIP。

* 显示构建说明，依次检查 `py -3` 和 `python`，转交本工程构建器。
  * 没有可用 Python 3.11+：提示安装并停止；`--help` 只显示说明。
* 确认后准备项目虚拟环境；必需依赖缺失时回车安装，任意非空输入取消。
* 清理本工具外层 `dist/`，生成并核验 EXE 目录和 ZIP，保存到同一构建时间目录。
* 更新 EXE / ZIP 快捷方式，打开产物目录并启动新 EXE；失败时停止并保留日志。

<a id="🔚" href="#前言" style="font-size:17px; color:green; font-weight:bold;">我是有底线的➤点我回到首页</a>
