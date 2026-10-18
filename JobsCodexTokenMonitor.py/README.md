# `JobsCodexTokenMonitor`

![Jobs出品，必属精品](https://picsum.photos/1500/400)

[toc]

---

## 🔥 <font id=前言>前言</font>

使用 [**Python**](https://www.python.org/) 和 [**PySide6**](https://doc.qt.io/qtforpython-6/) 编写的独立 [**Codex**](https://openai.com/codex) Token 上下行监控工具。只读本地会话日志，显示每轮输入 / 输出、对话标题、提问摘要和完成状态；主面板常驻“窗口置顶”复选框，一键置顶或取消。

本工具有自己的源码包、依赖、测试、启动器和 [**macOS**](https://www.apple.com/macos/) / [**Windows**](https://www.microsoft.com/windows) 打包入口，可以单独安装运行。账户管理由同级 [JobsCodexAccountSwitcher](../JobsCodexAccountSwitcher.py/README.md) 提供，监控工具不导入账户包、不打开账户库，也不读取登录凭据。

入口导航：[使用与设置](#settings) · [统计口径](#counting) · [会话联动](#hooks) · [打包](#build) · [验证](#verification)。

## 一、<span id="layout">工程与入口速览</span> <a href="#前言" style="font-size:17px; color:green;"><b>🔼</b></a> <a href="#🔚" style="font-size:17px; color:green;"><b>🔽</b></a>

| 工具 | 功能 | 依赖关系 |
| --- | --- | --- |
| `../JobsCodexAccountSwitcher.py/` | 保存 / 切换账户 | 独立运行，不包含监控 |
| `./` | 每轮 Token 上下行监控 | 独立运行，不需要账户 APP / EXE |

```text
JobsCodexTokenMonitor.py/
├── README.md
├── icon.png
├── 【MacOS】📦生成dmg.command
├── 【Windows】📦生成exe.bat
├── dist/YYYY.MM.DD HH-mm-ss/
│   ├── JobsCodexTokenMonitor.app            # macOS
│   ├── JobsCodexTokenMonitor/               # Windows 完整运行目录
│   │   ├── JobsCodexTokenMonitor.exe
│   │   └── _internal/
│   └── JobsCodexTokenMonitor.dmg / .zip
└── JobsCodexTokenMonitor/
    ├── pyproject.toml
    ├── src/jobs_codex_token_monitor/
    │   ├── app.py / token_widget.py / appearance.py
    │   ├── usage.py / labels.py
    │   └── token_hooks.py / hook_report.py
    ├── scripts/
    └── tests/
```

工程当前由直接父仓 `JobsPythonTools.py` 作为普通目录管理，父仓真实 `../.gitmodules` 尚无本工具条目。没有独立远端地址或 gitlink，不提供假设的克隆命令或平台解析表；将来登记子模块时需先确认真实仓库与提交。现有其它子模块的配置保持原样。

## 二、<span id="settings">打开监控与设置面板</span> <a href="#前言" style="font-size:17px; color:green;"><b>🔼</b></a> <a href="#🔚" style="font-size:17px; color:green;"><b>🔽</b></a>

1、双击第一层 `JobsCodexTokenMonitor.app` 或 Windows EXE 快捷方式。成品内置 Python 和依赖，无需启动账户工具；已运行的 Codex 可以直接接入，不重启或中断任务。

2、直接点击主面板常驻的“窗口置顶”复选框：勾选后浮窗始终置顶，取消后恢复普通窗口，立即生效，无需打开设置面板。

置顶与主题保存在本机，重启后恢复；首次默认置顶，沿用原 `always_on_top` 设置键与已有选择。切换置顶保留位置、当前选中轮次和后台监听。保留旧 `Jobs/CodexTokenWidget` 外观和位置设置，避免拆分时丢失既有选择。

3、使用浮窗顶部的 `⋯ → 设置…` 打开设置面板，这是唯一设置入口。设置面板只保留主题与会话联动，关闭面板不关闭浮窗。

| 设置 | 行为 |
| --- | --- |
| 白天 / 黑夜 / 跟随系统 | 统一作用于浮窗、设置、记录和弹出菜单；跟随系统会监听外观变化 |
| 会话联动 | 由监控工具自行安装或移除本工具的 Codex 钩子 |

4、拖动浮窗标题移动位置，数字支持选择和复制。`⋯ → 查看对话用量记录…` 可按标题或本轮提问搜索、滚动，并选择在浮窗显示的轮次。

5、无记录时显示完整等待状态与重新加载入口；读取异常时可在菜单重新加载。每个 Codex 数据目录只保留一个浮窗，重复启动只唤起并刷新已有窗口。

标题优先读取 `session_index.jsonl`；必要时只读查询非活跃 WAL 标题库，无法读取则回退短编号。提问摘要在内存中截取用户实际请求，跳过系统指导与附件路径包装，不保存聊天副本。

## 三、<span id="counting">Token 统计口径</span> <a href="#前言" style="font-size:17px; color:green;"><b>🔼</b></a> <a href="#🔚" style="font-size:17px; color:green;"><b>🔽</b></a>

| 显示 | 含义 |
| --- | --- |
| ↑ 上行 / 输入 | 模型实际输入 Token，包含历史上下文、工具内容与缓存输入 |
| ↓ 下行 / 输出 | 模型实际输出 Token，可包含推理输出，不限于可见回复 |
| 部分 / 未知用量 | 该轮无法完整归属、事件缺失或尚未补写完整统计 |
| `—` | 尚无已结束的主对话记录，不表示用量为零 |

一轮从用户输入开始，到完成、失败或中断结束，可能含多次模型 / 工具调用。优先读取精确 `turn_token_usage`；旧记录使用相邻累计 `total_token_usage` 的差值，不能把最后一次调用冒充整轮用量。缓存输入和推理输出已经包含在对应总数里，不重复相加。子代理记录单独识别，不混入主对话数字。

默认读取所选 Codex 目录 `sessions` 下近期最多 64 份 JSONL，每份首读末尾最多 16 MiB，保留最多 200 个近期轮次；约每秒读取新增内容，每 10 秒发现新文件。归档、云端、远程机器和未落盘记录不保证覆盖。工具不计算费用、不查询订阅剩余额度，不提供账户级账单。

## 四、<span id="hooks">可选会话联动与旧配置迁移</span> <a href="#前言" style="font-size:17px; color:green;"><b>🔼</b></a> <a href="#🔚" style="font-size:17px; color:green;"><b>🔽</b></a>

先把成品放在固定位置，再从监控的设置面板启用会话联动。程序只合并所选 Codex 目录的 `hooks.json`：`SessionStart` 在新建 / 恢复会话时启动浮窗，`Stop` 提供匹配轮次的用量提示。安装会识别原账号工具中带本工具专属标识的旧动作，将其替换为独立监控程序的命令；不保留对旧账户 APP 的依赖。

**首次安装或启动路径变化后，需要在 Codex CLI 的 `/hooks` 中审阅并信任两个动作。** 工具不写信任哈希、不自动批准、不修改 `config.toml`。只打开空会话不保证触发启动事件，已经运行的会话可手动打开监控接入。

修改磁盘配置不代表已加载的旧会话立即更新。本机桌面客户端实测会继续执行拆分前的账号 APP 命令；账户启动器对此只返回退役提示，不统计用量或打开窗口。独立浮窗仍可直接使用；客户端空闲时重启并完成新钩子审阅后，再核对自动启动及同轮提示。不要用恢复账号侧监控功能的方式处理旧会话缓存。

`Stop` 的 `systemMessage` 由客户端渲染，不改写原回复；只有最终答复后落盘且匹配该轮的精确累计才显示完整统计，其它情况提示待统计 / 未知，浮窗继续补齐。客户端内提示的实际显示位置依赖其实现。

配置改变前保留原文备份 `hooks.json.jobs-token-widget.*.bak`；其它钩子、事件和元数据保留。重复安装不叠加动作，移除只处理本工具标记。格式异常、符号链接或并发写入时拒绝覆盖。备份可能包含其它钩子命令，不公开上传。移动程序、删虚拟环境或重建清理旧 `dist` 后应重新安装并审阅；固定联动不宜长期绑定会清理的时间目录。

## 五、<span id="build">源码运行与双端打包</span> <a href="#前言" style="font-size:17px; color:green;"><b>🔼</b></a> <a href="#🔚" style="font-size:17px; color:green;"><b>🔽</b></a>

| 入口 | 用途 |
| --- | --- |
| `./【MacOS】📦生成dmg.command` | macOS 本机生成独立 APP / DMG |
| `./【Windows】📦生成exe.bat` | Windows 本机生成独立 EXE / ZIP |
| `./JobsCodexTokenMonitor/scripts/build.py` | 内层构建入口，保留同样的确认与安全边界 |

需要 Python 3.11+，运行依赖只有 PySide6，构建另需 [**PyInstaller**](https://pyinstaller.org/)。Token 解析、标题索引与钩子配置使用标准库；不依赖账户工具、cryptography 或 psutil。macOS 额外使用系统 `hdiutil`，Windows 由系统 [**PowerShell**](https://learn.microsoft.com/powershell/) 创建快捷方式；不使用 VBS 代理启动。Windows ZIP 包含 EXE 和 `_internal/` 的完整运行目录，分发时不能只复制 EXE。

Mac 外层脚本在自身具名函数中封装完整 [**Homebrew**](https://brew.sh/) / Python 自检，不依赖外置环境库。Brew 已有则更新自身与配方索引，无则安装；安装位置精确输入 `YES` 选系统目录，其它输入或回车选用户目录。Python 满足版本和标准库要求则复用，否则通过 Brew 修复并复检；不兼容旧虚拟环境改名备份再重建。健康依赖不重复安装；必需依赖缺失时直接回车安装，任意非空输入、EOF 或非交互取消，失败立即停止。

开始构建前阅读自述并确认：只清理本工具固定 `./dist/` 的旧产物及对应快捷方式，拒绝符号链接和外部目录。输出使用 `dist/YYYY.MM.DD HH-mm-ss/`；成功验证后发布第一层 APP / DMG 相对链接或 EXE / ZIP 快捷方式，打开产物位置并启动监控。构建不安装钩子、不操作登录数据，成功结尾不等待回车；失败不启动旧包。macOS / Windows 分别本机打包，包未正式签名 / 公证。

macOS 源码运行：

```shell
python3 -m venv ./JobsCodexTokenMonitor/.venv
./JobsCodexTokenMonitor/.venv/bin/python -m pip install \
    -e ./JobsCodexTokenMonitor
./JobsCodexTokenMonitor/.venv/bin/python \
    ./JobsCodexTokenMonitor/scripts/launch.py
```

Windows PowerShell：

```powershell
& .\JobsCodexTokenMonitor\.venv\Scripts\python.exe `
    .\JobsCodexTokenMonitor\scripts\launch.py
```

| 参数 | 行为 |
| --- | --- |
| 无参数 | 默认直接打开 Token 监控 |
| `--codex-home PATH` | 指定日志目录；未传时读取 `CODEX_HOME`，再回退当前用户的 `.codex` |
| `--token-widget` | 兼容监控模式名称，与默认启动效果相同 |
| `--install-token-hook` | 备份并合并联动动作，不打开 GUI |
| `--remove-token-hook` | 只移除本工具联动，不打开 GUI |
| `--hook-launch` | 钩子内部使用，派生独立监控后立即返回，不初始化 Qt |
| `--hook-report` | 钩子内部使用，读取标准输入事件并输出用量提示 JSON |

模式参数互斥，含空格路径整体加引号。独立监控入口和打包成品共用这些参数。

## 六、<span id="verification">数据、日志与验证</span> <a href="#前言" style="font-size:17px; color:green;"><b>🔼</b></a> <a href="#🔚" style="font-size:17px; color:green;"><b>🔽</b></a>

- 外观、置顶与位置：沿用 [**Qt**](https://www.qt.io/) 的 `Jobs/CodexTokenWidget` 设置，不保存凭据。
- 单实例锁：位于监控工具的系统应用数据目录，按 Codex 数据目录区分，不写会话日志。
- 会话数据：只读原有日志，在内存中重建近期记录；不写聊天副本、不上传。
- 构建日志：系统临时目录中的 `JobsCodexTokenMonitor-build.log`。
- 测试：临时数据覆盖输入 / 输出统计、跨轮与子代理归属、标题摘要、日志损坏与补写、钩子备份与迁移、单实例、三态主题和置顶切换 / 重启恢复。真实双账户授权不属于监控验证；Windows GUI / 打包需 Windows 本机验收。

2026-10-18 验证基线：169 项回归通过；独立 Mac ARM64 APP / DMG 已生成并校验。成品实测主面板“窗口置顶”复选框双向切换、取消后重启恢复，以及设置面板不再提供置顶控制；保留单实例唤起和 Stop 标准输入 / JSON 输出验证。两套工具另通过 176 项隔离的 Shell 环境自检回归；未执行真实包管理器安装或升级。账号包、cryptography 与 psutil 未进入监控成品的模块归档。

```shell
cd ./JobsCodexTokenMonitor
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src .venv/bin/python \
    -m unittest discover \
    -s tests \
    -v
```

**窗口怎么取消置顶？** 直接取消主面板常驻“窗口置顶”复选框即可；重启仍保持选择。

**为什么看不到完整数字？** 该轮可能尚未结束或客户端没有完整写入用量；保持监听或重新加载，不把未知当成零。

**为什么联动后没有自动出现？** 检查 `/hooks` 中两个动作是否已审阅、客户端是否支持并触发对应事件；手动启动可以接入现有会话。

<a id="🔚" href="#前言" style="font-size:17px; color:green; font-weight:bold;">我是有底线的➤点我回到首页</a>
