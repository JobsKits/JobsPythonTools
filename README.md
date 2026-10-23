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
- [四、输出与忽略规则](#jobs-toc-heading-7)
- [五、风险边界](#jobs-toc-heading-8)
- [六、维护说明](#jobs-toc-heading-9)
- [七、上传 README 演示视频](#jobs-toc-heading-10)
- [八、Git 子模块脚本](#git-submodule-scripts)
  - [【MacOS】⏬下载配置当前Git子模块（可向下同步递归）.command](#jobs-toc-heading-12)
  - [【MacOS】🧾更新gitmodules.command](#jobs-toc-heading-13)
- [九、本仓目录与脚本入口](#repository-layout-and-entrypoints)
  - [【MacOS】📦生成dmg.command](#jobs-toc-heading-15)
  - [【Windows】📦生成exe.bat](#jobs-toc-heading-16)

</details>
<!-- jobs-toc:end -->

---

## <span id="jobs-toc-heading-1" data-jobs-toc="v2">🔥 <font id=前言>前言</font></span><!-- jobs-toc:heading-end -->

`JobsPythonTools.py` 是 Jobs 本地 [**Python**](https://www.python.org) 桌面工具集合，覆盖文件共享、Mock API、IPA 静态分析、按 App 流量监控、整机监控、浏览器远程协助、Codex 账户切换及 Token 用量监控。各工具的当前能力和详细操作入口见下方总览。

多数工具采用“外层交付目录 + 内层 Python 工程”结构：外层放总说明、双击入口和 `dist/YYYY.MM.DD HH-mm-ss/` 产物，内层放源码、依赖、资源、测试与构建配置；具体布局以各工具 README 为准。

独立 `.command` 入口先显示内置自述：标题红色加粗，编号正文蓝色且不加粗，非彩色终端显示纯文本；在终端回车确认后执行，`Ctrl+C` 取消，缺少可交互输入时停止。子仓下载与关联操作见 [Git 子模块脚本](#git-submodule-scripts)。

## <span id="jobs-toc-heading-2" data-jobs-toc="v2">一、工具总览 <a href="#前言" style="font-size:17px; color:green;"><b>🔼</b></a> <a href="#🔚" style="font-size:17px; color:green;"><b>🔽</b></a></span><!-- jobs-toc:heading-end -->

| 工具 | 目录 | 核心用途 | 主要入口 |
| --- | --- | --- | --- |
| `LANFileServer` | [功能与操作](./LANFileServer.py/README.md) | 临时 Python / 非临时 Nginx 文件共享、浏览器预览 / 下载、可选上传、二维码、项目聊天室与访问记录。 | [macOS](./LANFileServer.py/【MacOS】📦生成dmg.command) / [Windows](./LANFileServer.py/【Windows】📦生成exe.bat) 打包 |
| `JobsMockTool` | [功能与操作](./JobsMockTool.py/README.md) | 多接口、单端口 / 独立端口、query / body / headers 条件响应、JSON 树形编辑、内置请求测试与配置保存。 | [macOS](./JobsMockTool.py/【MacOS】📦生成dmg.command) / [Windows](./JobsMockTool.py/【Windows】📦生成exe.bat)；[构建脚本](./JobsMockTool.py/build_macos.command/README.md) |
| `JobsReverseIPA` | [功能与操作](./JobsReverseIPA.py/README.md) | 授权 IPA 静态分析、环境体检、资源 / 敏感字符串扫描，输出 HTML / JSON / Markdown 报告。 | [macOS](./JobsReverseIPA.py/【MacOS】📦生成dmg.command) / [Windows](./JobsReverseIPA.py/【Windows】📦生成exe.bat) 打包 |
| `JobsAppTrafficMonitor` | [功能与操作](./JobsAppTrafficMonitor.py/README.md) | macOS 按 App / 进程统计实时速率与累计流量，归并 Helper / XPC；Windows ETW 采集接口尚为预留。 | [macOS](./JobsAppTrafficMonitor.py/【MacOS】📦生成dmg.command) / [Windows](./JobsAppTrafficMonitor.py/【Windows】📦生成exe.bat) 打包 |
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

不同工具的 Windows 入口行为略有差异：`JobsMockTool`、`JobsReverseIPA`、`JobsAppTrafficMonitor` 以打包 `.exe` 为主；`LANFileServer` 默认启动图形界面，内部保留 `build-exe` 打包模式。

## <span id="jobs-toc-heading-7" data-jobs-toc="v2">四、输出与忽略规则 <a href="#前言" style="font-size:17px; color:green;"><b>🔼</b></a> <a href="#🔚" style="font-size:17px; color:green;"><b>🔽</b></a></span><!-- jobs-toc:heading-end -->

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

## <span id="jobs-toc-heading-8" data-jobs-toc="v2">五、风险边界 <a href="#前言" style="font-size:17px; color:green;"><b>🔼</b></a> <a href="#🔚" style="font-size:17px; color:green;"><b>🔽</b></a></span><!-- jobs-toc:heading-end -->

- `LANFileServer` 会把选中的文件 / 文件夹暴露给同一局域网设备，不要共享隐私目录、密码文件或浏览器数据。
- `JobsReverseIPA` 只用于用户有权审计的 `.ipa` 文件，不用于未授权分析。
- `JobsMockTool` 默认服务本机 Mock 请求，不要把真实 Token、密码和用户隐私写进 Mock 配置。
- `JobsAppTrafficMonitor` 只读取连接元数据与字节计数，不读取、解析或保存数据包内容。
- 当前构建脚本生成的 macOS / Windows 成品通常没有正式代码签名；公开分发前需要按平台补齐签名和公证。

## <span id="jobs-toc-heading-9" data-jobs-toc="v2">六、维护说明 <a href="#前言" style="font-size:17px; color:green;"><b>🔼</b></a> <a href="#🔚" style="font-size:17px; color:green;"><b>🔽</b></a></span><!-- jobs-toc:heading-end -->

- 新增工具时优先保持同类结构：`ToolName.py/README.md`、`【MacOS】📦生成dmg.command`、`【Windows】📦生成exe.bat`、`ToolName/`。
- 外层 README 负责用户运行前说明；内层 Python 工程负责源码、依赖、测试和构建细节。
- 修改入口脚本名后，同步更新对应工具 README、脚本内置自述和本文件工具总览。
- 提交前先看 `git status --ignored`，确认构建产物仍然被忽略。

打包前会清理该应用工程的旧 `dist` 产物，清理失败则停止；成功后自动打开当前平台产物的磁盘位置并运行本次生成的 APP / EXE，结尾无需回车。失败时不启动软件；运行前的防误触确认保留。

必需依赖缺失时，直接回车联网安装；输入任意字符后回车取消整个流程。安装失败或复检仍不可用时停止，不继续清理旧产物或打包。健康依赖直接复用；可选升级和词库更新仍为回车跳过、任意字符执行。

第一层交付目录与平台打包脚本同层保存 `dist/`，以及最新 APP / DMG 的相对符号链接（Mac）或 EXE / 分发包的 `.lnk`（Windows）。双击快捷方式即可接触成品，真实文件保留在 `dist/`；成功构建自动更新入口，清理旧产物时移除对应旧入口。尚无成品时不生成无效快捷方式。

## <span id="jobs-toc-heading-10" data-jobs-toc="v2">七、上传 README 演示视频 <a href="#前言" style="font-size:17px; color:green;"><b>🔼</b></a> <a href="#🔚" style="font-size:17px; color:green;"><b>🔽</b></a></span><!-- jobs-toc:heading-end -->

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

| 启动选择 | 版本依据 | 是否写入父仓提交 |
| --- | --- | --- |
| 只拉取，默认 | 更新当前父仓明确的远程上游，再逐层跟随子仓目标分支最新提交，保持本地跟踪分支 | 不暂存、不提交、不推送 |
| 维护子模块，显式选择 | 按本仓清单及原有菜单，把所选子树更新到各自远端目标分支最新 | 沿用 `AUTO_PARENT_COMMIT` / `AUTO_PARENT_PUSH` 原有开关 |

启动第一屏显示同步策略版本 `2026.10.21-toc`。新电脑须先取得并运行带此版本号的入口；另一台电脑上的本地修改不会自动更新到新电脑。任一仓库拉取、分支切换或递归校验失败时，本轮不能视为全部完成；处理日志中的具体路径后重新运行。

只拉取模式从脚本所在仓库向下递归处理全部已登记子模块；不向上处理，不使用清单新增关联，也不把子仓最新提交自动提交回父仓。各层优先使用直接父仓 `.gitmodules` 的显式 `branch`，`.` 继承该层计划更新后的直接父仓分支；未配置时读取该子仓远端默认分支。首次下载和已有游离 HEAD 都会恢复或创建对应本地跟踪分支，获取最新提交并快进；成功结束时子仓显示实际分支名。每层相对 URL 随当前父仓的下载线路解析。只拉取模式使用系统 Git、zsh、Perl 等现有工具；仅命中有效目录过滤器时另需 Node.js 和该仓完整目录工具，不进入维护模式的 Homebrew / fzf 安装流程。

子仓源码、未跟踪内容、已暂存 gitlink、未完成操作或本地独有提交会报出具体路径并停止；不会强制覆盖或丢弃独有的游离提交，父仓 `YES` 不扩散到子仓。当前父仓自己的源码改动或本地独有提交，仍须红字列明并精确输入 `YES` 才舍弃。目标分支不存在、远端默认分支无法确定或最新提交获取失败时，停止并报告对应仓库与来源；不会把旧 gitlink SHA 当作最新分支结果。

只拉取模式在入口仓已有本地分支时仍要求明确上游。入口仓自身处于游离 HEAD 时，先使用直接父仓 `.gitmodules` 的显式 `branch`，`.` 继承直接父仓当前分支；无配置时读取 `origin` 或唯一远端的默认分支。已有目标本地分支须明确跟踪所选远端的同名分支；先获取最新提交，预检整棵子树与提交历史，并复查确认期间的状态，再恢复或创建本地跟踪分支。入口源码未提交、需继承分支时直接父仓同样游离、目标不明、目标分支无法快进或存在未受引用保护的独有游离提交时停止；普通父仓的 `YES` 不授权舍弃这些提交。

`REMOTE_NAME` 等原有清单参数只用于维护模式。设置 `DRY_RUN=1` 时，默认只拉取会停止并提示选择维护演练，不能忽略演练标志后执行真实更新。未初始化但存在旧 Git 缓存的空工作树须先恢复，脚本不会覆盖缓存内索引或独有提交。

下文关于清单新增、多选、可切换同步深度、目录清理及自动提交的既有流程，均指显式选择的**维护模式**。只拉取模式默认向下递归到分支最新，不使用这些写入父仓的开关；子仓最新提交与父仓 gitlink 可能不同，父仓会显示待审阅的子模块指针改动。两种模式都保留各仓独立清单和来源显示；只拉取日志带运行时间与进程号，终端会输出实际路径。

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

### <span id="jobs-toc-heading-12" data-jobs-toc="v2">[【MacOS】⏬下载配置当前Git子模块（可向下同步递归）.command](./【MacOS】⏬下载配置当前Git子模块（可向下同步递归）.command)</span><!-- jobs-toc:heading-end -->

> **目的：** 把选定子仓及可选的后代子模块同步到各自远端目标分支最新提交，并让入口父仓记录对应版本。

- 启动时回车默认进入[只拉取模式](#readonly-submodule-mode)，先预检本地状态，再更新当前父仓并逐层快进到子仓目标分支最新提交；恢复已有游离 HEAD，不提交、不推送。
- 显式选择维护模式后，按以下原有清单和菜单流程处理。

* 阅读自述并回车，检查环境、载入脚本子仓清单，先拉取父仓并执行 `pull --rebase`。

  * 父仓有未提交改动时跳过拉取，继续进入子仓菜单。

* 在主菜单选择同步范围；“切换同步深度”可在默认“向下递归”和“仅直属子模块”之间切换，当前深度适用于各同步动作。

  * 全量：逐项同步清单内全部目标，按目录状态复用或首次克隆。
  * 指定：勾选需要的子仓；已有：只更新清单中本地已有的子仓，没有任何已有子仓时转全量。
  * 新地址：输入地址，添加并同步一个子仓。

* 补齐 `.gitmodules` 缺项，默认保留已有 URL、分支和旧登记；子仓有未提交、已暂存或未跟踪内容：红字加粗显示该仓绝对路径并循环等待；精确输入 `YES` 只放弃当前仓自己的未提交内容，或在外部处理后回车复检。其它输入继续复检；无交互或输入结束则停止。

  * 全量模式逐仓复用已有工作区；空或缺失目录首次克隆，既有缓存核验后恢复；非 Git 非空目录保护并停止。

* 拉取并快进到远端目标分支最新提交：优先使用该层 `.gitmodules` 显式 `branch`，`.` 继承直接父仓分支；未设置时读取该子仓远端默认分支；显式目标分支不存在时立即停止，不回退其它分支。

  * 目录为空或缺失：首次克隆；已有有效 Git 工作区：`fetch` 后切换或创建目标本地跟踪分支，仅快进更新；本地领先远端或分叉时停止并保留提交。

* 按当前深度同步：默认逐层读取所选子仓下的 `.gitmodules`，将已登记后代同步到各自远端目标分支最新提交；仅直属模式不下载或更新下层代码。
  * 只处理本层所选子树，不向上扫描，也不接管未登记的嵌套仓库。
  * 递归更新本层前先检查当前已有后代；各仓单独确认，子模块 HEAD 与父仓 gitlink 的普通差异不作为源码未提交反复提示。
  * `YES` 清理仅作用于当前仓：`reset --hard HEAD` 与 `clean -fd`；保留忽略文件和独立嵌套 Git 仓，残留冲突须外部处理后复检。
  * `PRUNE_STALE_GITMODULES` 默认 `0`，保留清单外旧登记；主动设为 `1` 时，每个旧登记另用红字加粗列明目录和后代删除范围，逐项精确输入 `YES` 才删除，其它输入、输入结束或非交互则停止；演练只展示，删除前仍逐仓检查已有后代。
  * 深层只下载更新，不自动暂存或提交其父仓的 gitlink；递归后这些父仓可能显示子模块指针改动，保留待审阅。

* 整理入口父仓关联与 Git 元数据。

* 默认自动提交入口父仓的 `.gitmodules` / 子模块指针变化，不自动推送（`AUTO_PARENT_COMMIT=1`、`AUTO_PARENT_PUSH=0`），最后显示日志位置。

### <span id="jobs-toc-heading-13" data-jobs-toc="v2">[【MacOS】🧾更新gitmodules.command](./【MacOS】🧾更新gitmodules.command)</span><!-- jobs-toc:heading-end -->

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

### <span id="jobs-toc-heading-15" data-jobs-toc="v2">[【MacOS】📦生成dmg.command](./JobsCodexTokenMonitor.py/【MacOS】📦生成dmg.command)</span><!-- jobs-toc:heading-end -->

> **目的：** 在本机生成 JobsCodexTokenMonitor 的 APP / DMG，并打开本次成品。

* 阅读自述，确认环境准备；检查 Homebrew 和兼容的 Python，再交给本工程构建器。
  * 必需依赖缺失：回车安装，任意非空输入取消；环境或复检失败时停止。
* 确认构建范围后准备虚拟环境与依赖，仅清理本工具外层 `dist/` 的旧产物。
* 打包并校验 APP，封装 DMG，统一输出到 `dist/YYYY.MM.DD HH-mm-ss/`。
* 更新第一层产物快捷方式，打开产物目录，再启动本次 APP；失败时查看系统临时目录中的构建日志。

### <span id="jobs-toc-heading-16" data-jobs-toc="v2">[【Windows】📦生成exe.bat](./JobsCodexTokenMonitor.py/【Windows】📦生成exe.bat)</span><!-- jobs-toc:heading-end -->

> **目的：** 在 Windows 本机生成 JobsCodexTokenMonitor 的 EXE 分发目录与 ZIP。

* 显示构建说明，依次检查 `py -3` 和 `python`，转交本工程构建器。
  * 没有可用 Python 3.11+：提示安装并停止；`--help` 只显示说明。
* 确认后准备项目虚拟环境；必需依赖缺失时回车安装，任意非空输入取消。
* 清理本工具外层 `dist/`，生成并核验 EXE 目录和 ZIP，保存到同一构建时间目录。
* 更新 EXE / ZIP 快捷方式，打开产物目录并启动新 EXE；失败时停止并保留日志。

<a id="🔚" href="#前言" style="font-size:17px; color:green; font-weight:bold;">我是有底线的➤点我回到首页</a>
