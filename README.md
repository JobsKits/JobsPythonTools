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

子仓下载与关联操作见 [Git 子模块脚本](#git-submodule-scripts)。

本目录中可独立运行的 `.command` 入口先显示内置自述：标题红色加粗，编号正文蓝色且不加粗；在终端按回车确认后才进入原有流程，按 `Ctrl+C` 取消。非彩色终端显示纯文本；没有可交互输入时停止，避免确认缺失后继续执行。

`JobsPythonTools.py` 是 Jobs 本地 [**Python**](https://www.python.org) 桌面工具集合仓库，包含局域网文件共享、Mock API、IPA 静态分析、App 流量监控、Codex 账户切换和独立 Token 用量监控等工具。

每个工具都采用“外层交付目录 + 内层 Python 工程”的结构：外层放 `README.md` 和双击入口脚本，内层放源码、依赖、资源、测试和构建配置，外层 `dist/YYYY.MM.DD HH-mm-ss/` 保存交付产物。

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

规则通过追加进程级 `GIT_CONFIG_COUNT` / `url.https://gitee.com/.insteadOf` 配置传给子进程，不写入全局 Git 配置，也不依赖其它工程路径。GitHub、其它主机及非 `22` 的自定义 SSH 端口保持原规则。克隆或递归更新失败会返回非零状态，停止本轮同步并保留错误；不会再输出该项同步成功。各仓清单与浅克隆参数保留；全量删除重建须输入 `YES` 确认，范围限定为清单目标及对应旧仓名目录。

## <span id="jobs-toc-heading-2" data-jobs-toc="v2">一、工具总览 <a href="#前言" style="font-size:17px; color:green;"><b>🔼</b></a> <a href="#🔚" style="font-size:17px; color:green;"><b>🔽</b></a></span><!-- jobs-toc:heading-end -->

| 工具 | 目录 | 核心用途 | 主要入口 |
| --- | --- | --- | --- |
| `LANFileServer` | `./LANFileServer.py/` | 把本机文件 / 文件夹临时共享给同一局域网设备。 | `./LANFileServer.py/【MacOS】📦生成dmg.command`、`./LANFileServer.py/【Windows】📦生成exe.bat` |
| `JobsMockTool` | `./JobsMockTool.py/` | 图形化配置本地 Mock API，用于前端、客户端和脚本联调。 | `./JobsMockTool.py/【MacOS】📦生成dmg.command`、`./JobsMockTool.py/【Windows】📦生成exe.bat` |
| `JobsReverseIPA` | `./JobsReverseIPA.py/` | 对授权 `.ipa` 做静态分析、环境体检、资源和敏感字符串扫描。 | `./JobsReverseIPA.py/【MacOS】📦生成dmg.command`、`./JobsReverseIPA.py/【Windows】📦生成exe.bat` |
| `JobsAppTrafficMonitor` | `./JobsAppTrafficMonitor.py/` | 按 App 实时统计 macOS / Windows 上下行流量。 | `./JobsAppTrafficMonitor.py/【MacOS】📦生成dmg.command`、`./JobsAppTrafficMonitor.py/【Windows】📦生成exe.bat` |
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

双击 [上传 GitHub 视频附件脚本](../JobsCommand@Gits/【MacOS】🎬上传GitHub视频附件.command/【MacOS】🎬上传GitHub视频附件.command)，按回车确认，再输入 GitHub 仓库首页地址并拖入本地视频。支持 MP4 / MOV / WEBM；也可通过命令行传入这两个参数。需要安装 [**GitHub CLI**](https://cli.github.com/)，当前账号须有目标仓库写权限；未登录时脚本会引导登录。

上传成功后显示附件 URL 并复制到剪贴板。将 URL 单独放到本地 README 的一段中，前后留空行，再正常提交、推送即可；以后只替换该 URL。脚本不修改 README，不创建提交或推送。每次运行都会创建新附件，失败时不自动重试，防止重复上传。运行日志路径会在终端显示，保存在系统临时目录。

**上传后的附件单独删除比较麻烦，需要联系 [GitHub Support](https://support.github.com/)。** 删除本地项目文件夹、仓库中的视频文件或 README 链接不会删除附件。[GitHub 工作人员曾说明](https://github.com/orgs/community/discussions/54551#discussioncomment-6730698)，删除整个 GitHub **远端仓库**会触发附件延迟清理；这不是即时删除承诺，不建议仅为删除视频而删除整个仓库。

构建产物使用本机本地构建时间，格式为 `YYYY.MM.DD HH-mm-ss`（年月日时分秒），例如 `2020.06.04 12-23-21`。每次构建的 APP、DMG、EXE、ZIP 和配套文件统一保存到交付层 `./dist/YYYY.MM.DD HH-mm-ss/`，同次构建只取一次时间；第一层快捷方式指向本次时间目录，成功后打开该目录并启动其中的软件。旧产物沿用原有清理规则；历史产物缺少可靠构建时间时，不补写推测时间。

[**Homebrew**](https://brew.sh/) 安装路径由用户选择：已有可运行安装时复用；确实需要安装时先强提示，只有精确输入大写 `YES` 才选择系统标准目录，其它输入或直接回车选择当前用户的 `.local/homebrew`。`YES` 只表示选择路径，权限与密码由官方安装器实际处理；有管理员权限也可以选用户目录。选定路径失败立即停止，不自动切换；`Ctrl+C` / 输入结束取消整个任务。

## 八、<span id="git-submodule-scripts">Git 子模块脚本</span> <a href="#前言" style="font-size:17px; color:green;"><b>🔼</b></a> <a href="#🔚" style="font-size:17px; color:green;"><b>🔽</b></a>

### <span id="jobs-toc-heading-12" data-jobs-toc="v2">[【MacOS】⏬下载配置当前Git子模块（可向下同步递归）.command](./【MacOS】⏬下载配置当前Git子模块（可向下同步递归）.command)</span><!-- jobs-toc:heading-end -->

> **目的：** 把选定子仓及可选的后代子模块同步到各自远端目标分支最新提交，并让入口父仓记录对应版本。

* 阅读自述并回车，检查环境、载入脚本子仓清单，先拉取父仓并执行 `pull --rebase`。

  * 父仓有未提交改动时跳过拉取，继续进入子仓菜单。

* 在主菜单选择同步范围；“切换同步深度”可在默认“向下递归”和“仅直属子模块”之间切换，当前深度适用于各同步动作。

  * 全量：同步清单内全部目标；须输入 `YES` 执行删除重建，其它输入取消。
  * 指定：勾选需要的子仓；已有：只更新清单中本地已有的子仓，没有任何已有子仓时转全量。
  * 新地址：输入地址，添加并同步一个子仓。

* 补齐 `.gitmodules` 缺项，默认保留已有 URL、分支和旧登记；目标子仓有未提交改动时停止更新或删除。

  * 全量模式会在补齐登记后删除目标目录及旧缓存，再重新下载；**本地独有提交可能丢失**。

* 拉取并强制对齐远端目标分支最新提交：优先使用该层 `.gitmodules` 显式 `branch`，`.` 继承直接父仓分支；未设置时优先 `main`，不存在则使用远端默认分支。

  * 目录缺失：首次克隆；目录已有：`fetch` 后以 `checkout -B`、`reset --hard` 对齐远端，**本地目标分支未推送的独有提交可能被覆盖**。

* 按当前深度同步：默认逐层读取所选子仓下的 `.gitmodules`，将已登记后代同步到各自远端目标分支最新提交；仅直属模式不下载或更新下层代码。
  * 只处理本层所选子树，不向上扫描，也不接管未登记的嵌套仓库。
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
