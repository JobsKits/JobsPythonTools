# `JobsPythonTools.py`

![Jobs出品，必属精品](https://picsum.photos/1500/400)

[toc]

---

## 🔥 <font id=前言>前言</font>

`JobsPythonTools.py` 是 Jobs 本地 [**Python**](https://www.python.org) 桌面工具集合仓库，当前收口了局域网文件共享、Mock API、IPA 静态分析、App 流量监控四类工具。

每个工具都采用“外层交付目录 + 内层 Python 工程”的结构：外层放 `README.md` 和双击入口脚本，内层放源码、依赖、资源、测试、构建配置和产物目录。

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

<a id="🔚" href="#前言" style="font-size:17px; color:green; font-weight:bold;">我是有底线的➤点我回到首页</a>
