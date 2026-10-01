# `JobsPythonTools.py`

![Jobs出品，必属精品](https://picsum.photos/1500/400)

[toc]

---

## 🔥 <font id=前言>前言</font>

`JobsPythonTools.py` 是 Jobs 本地 [**Python**](https://www.python.org) 桌面工具集合仓库，当前收口了局域网文件共享、Mock API、IPA 静态分析、App 流量监控四类工具。

每个工具都采用“外层交付目录 + 内层 Python 工程”的结构：外层放 `README.md` 和双击入口脚本，内层放源码、依赖、资源、测试和构建配置，外层 `dist/YYYY.MM.DD HH-mm-ss/` 保存交付产物。

## 一、工具总览 <a href="#前言" style="font-size:17px; color:green;"><b>🔼</b></a> <a href="#🔚" style="font-size:17px; color:green;"><b>🔽</b></a>

| 工具 | 目录 | 核心用途 | 主要入口 |
| --- | --- | --- | --- |
| `LANFileServer` | `./LANFileServer.py/` | 把本机文件 / 文件夹临时共享给同一局域网设备。 | `./LANFileServer.py/【MacOS】📦生成dmg.command`、`./LANFileServer.py/【Windows】📦生成exe.bat` |
| `JobsMockTool` | `./JobsMockTool.py/` | 图形化配置本地 Mock API，用于前端、客户端和脚本联调。 | `./JobsMockTool.py/【MacOS】📦生成dmg.command`、`./JobsMockTool.py/【Windows】📦生成exe.bat` |
| `JobsReverseIPA` | `./JobsReverseIPA.py/` | 对授权 `.ipa` 做静态分析、环境体检、资源和敏感字符串扫描。 | `./JobsReverseIPA.py/【MacOS】📦生成dmg.command`、`./JobsReverseIPA.py/【Windows】📦生成exe.bat` |
| `JobsAppTrafficMonitor` | `./JobsAppTrafficMonitor.py/` | 按 App 实时统计 macOS / Windows 上下行流量。 | `./JobsAppTrafficMonitor.py/【MacOS】📦生成dmg.command`、`./JobsAppTrafficMonitor.py/【Windows】📦生成exe.bat` |

## 二、目录结构 <a href="#前言" style="font-size:17px; color:green;"><b>🔼</b></a> <a href="#🔚" style="font-size:17px; color:green;"><b>🔽</b></a>

```text
.
├── README.md
├── .gitignore
├── icon.png
├── LANFileServer.py/
├── JobsMockTool.py/
├── JobsReverseIPA.py/
└── JobsAppTrafficMonitor.py/
```

- `./README.md`：当前整库说明和工具索引。
- `./.gitignore`：整库 Git 忽略规则，排除虚拟环境、缓存和构建产物。
- `./icon.png`：仓库级图标资源。
- `./*/README.md`：每个工具自己的完整说明，包含运行方式、输出目录、日志位置和风险边界。

## 三、运行与打包 <a href="#前言" style="font-size:17px; color:green;"><b>🔼</b></a> <a href="#🔚" style="font-size:17px; color:green;"><b>🔽</b></a>

### 3.1、macOS

macOS 安装包必须在 macOS 本机生成。进入目标工具目录后，双击或执行对应入口：

```shell
./【MacOS】📦生成dmg.command
```

脚本通常会创建或复用 `.venv` / `.venv-universal2`，按需安装依赖，再通过 [**PyInstaller**](https://pyinstaller.org/) 生成 `.app` 和 `.dmg`。涉及清理旧 `build` / `dist` 的脚本，会在内部自述里提示影响范围，部分工具要求输入 `YES` 才继续。

### 3.2、Windows

Windows 可执行程序必须在 Windows 本机生成或启动。进入目标工具目录后，双击或执行对应入口：

```shell
./【Windows】📦生成exe.bat
```

不同工具的 Windows 入口行为略有差异：`JobsMockTool`、`JobsReverseIPA`、`JobsAppTrafficMonitor` 以打包 `.exe` 为主；`LANFileServer` 默认启动图形界面，内部保留 `build-exe` 打包模式。

## 四、输出与忽略规则 <a href="#前言" style="font-size:17px; color:green;"><b>🔼</b></a> <a href="#🔚" style="font-size:17px; color:green;"><b>🔽</b></a>

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

## 五、风险边界 <a href="#前言" style="font-size:17px; color:green;"><b>🔼</b></a> <a href="#🔚" style="font-size:17px; color:green;"><b>🔽</b></a>

- `LANFileServer` 会把选中的文件 / 文件夹暴露给同一局域网设备，不要共享隐私目录、密码文件或浏览器数据。
- `JobsReverseIPA` 只用于用户有权审计的 `.ipa` 文件，不用于未授权分析。
- `JobsMockTool` 默认服务本机 Mock 请求，不要把真实 Token、密码和用户隐私写进 Mock 配置。
- `JobsAppTrafficMonitor` 只读取连接元数据与字节计数，不读取、解析或保存数据包内容。
- 当前构建脚本生成的 macOS / Windows 成品通常没有正式代码签名；公开分发前需要按平台补齐签名和公证。

## 六、维护说明 <a href="#前言" style="font-size:17px; color:green;"><b>🔼</b></a> <a href="#🔚" style="font-size:17px; color:green;"><b>🔽</b></a>

- 新增工具时优先保持同类结构：`ToolName.py/README.md`、`【MacOS】📦生成dmg.command`、`【Windows】📦生成exe.bat`、`ToolName/`。
- 外层 README 负责用户运行前说明；内层 Python 工程负责源码、依赖、测试和构建细节。
- 修改入口脚本名后，同步更新对应工具 README、脚本内置自述和本文件工具总览。
- 提交前先看 `git status --ignored`，确认构建产物仍然被忽略。

打包前会清理该应用工程的旧 `dist` 产物，清理失败则停止；成功后自动打开当前平台产物的磁盘位置并运行本次生成的 APP / EXE，结尾无需回车。失败时不启动软件；运行前的防误触确认保留。

必需依赖缺失时，直接回车联网安装；输入任意字符后回车取消整个流程。安装失败或复检仍不可用时停止，不继续清理旧产物或打包。健康依赖直接复用；可选升级和词库更新仍为回车跳过、任意字符执行。

第一层交付目录与平台打包脚本同层保存 `dist/`，以及最新 APP / DMG 的相对符号链接（Mac）或 EXE / 分发包的 `.lnk`（Windows）。双击快捷方式即可接触成品，真实文件保留在 `dist/`；成功构建自动更新入口，清理旧产物时移除对应旧入口。尚无成品时不生成无效快捷方式。

## 七、上传 README 演示视频

双击 [上传 GitHub 视频附件脚本](./【MacOS】🎬上传GitHub视频附件.command)，按回车确认，再输入 GitHub 仓库首页地址并拖入本地视频。支持 MP4 / MOV / WEBM；也可通过命令行传入这两个参数。需要安装 [**GitHub CLI**](https://cli.github.com/)，当前账号须有目标仓库写权限；未登录时脚本会引导登录。

上传成功后显示附件 URL 并复制到剪贴板。将 URL 单独放到本地 README 的一段中，前后留空行，再正常提交、推送即可；以后只替换该 URL。脚本不修改 README，不创建提交或推送。每次运行都会创建新附件，失败时不自动重试，防止重复上传。运行日志路径会在终端显示，保存在系统临时目录。

**上传后的附件单独删除比较麻烦，需要联系 [GitHub Support](https://support.github.com/)。** 删除本地项目文件夹、仓库中的视频文件或 README 链接不会删除附件。[GitHub 工作人员曾说明](https://github.com/orgs/community/discussions/54551#discussioncomment-6730698)，删除整个 GitHub **远端仓库**会触发附件延迟清理；这不是即时删除承诺，不建议仅为删除视频而删除整个仓库。

构建产物使用本机本地构建时间，格式为 `YYYY.MM.DD HH-mm-ss`（年月日时分秒），例如 `2020.06.04 12-23-21`。每次构建的 APP、DMG、EXE、ZIP 和配套文件统一保存到交付层 `./dist/YYYY.MM.DD HH-mm-ss/`，同次构建只取一次时间；第一层快捷方式指向本次时间目录，成功后打开该目录并启动其中的软件。旧产物沿用原有清理规则；历史产物缺少可靠构建时间时，不补写推测时间。

<a id="🔚" href="#前言" style="font-size:17px; color:green; font-weight:bold;">我是有底线的➤点我回到首页</a>
