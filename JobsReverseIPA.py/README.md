# `JobsReverseIPA`

![Jobs出品，必属精品](https://picsum.photos/1500/400)

<!-- jobs-toc:start -->
<!-- jobs-toc:source {"v":2,"token":"[toc]"} -->
<details>
<summary>📚 目录（点击展开 / 收起）</summary>

- [🔥 前言](#jobs-toc-heading-1)
- [一、目录结构](#jobs-toc-heading-2)
- [二、打包方式](#jobs-toc-heading-3)
  - [【MacOS】📦生成dmg.command](#jobs-toc-heading-4)
  - [【Windows】📦生成exe.bat](#jobs-toc-heading-5)
- [三、成品运行](#jobs-toc-heading-6)
- [四、当前能力](#jobs-toc-heading-7)
- [五、风险说明](#jobs-toc-heading-8)
- [六、Mac Python 环境自检](#jobs-toc-heading-9)
- [七、本仓目录与脚本入口](#repository-layout-and-entrypoints)
  - [IPA环境体检.command](#jobs-toc-heading-11)
  - [build\_doctor\_exe.ps1](#jobs-toc-heading-12)

</details>
<!-- jobs-toc:end -->

---

## <span id="jobs-toc-heading-1" data-jobs-toc="v2">🔥 <font id=前言>前言</font></span><!-- jobs-toc:heading-end -->

**最低支持系统：[Windows](https://www.microsoft.com/windows) 10 64 位（x64）。** 这是当前最低支持目标；具体最低 build 尚未锁定，完整实机兼容性仍待验证。

`JobsReverseIPA` 是面向授权 `.ipa` 的桌面静态分析工具：支持 GUI 拖入 IPA、环境体检、资源与敏感字符串扫描，并输出 `HTML` / `JSON` / `Markdown` 报告。

[**Windows**](https://www.microsoft.com/windows) **兼容范围：当前构建与成品测试目标为 Windows 10 / 11 x64；Windows XP、Vista、7、8、8.1 不支持当前图形依赖。** [**Qt 6.8 官方 Windows 平台表**](https://doc.qt.io/qt-6.8/windows.html)列出的 x64 基线为 Windows 10 1809+ / Windows 11；本项目未锁定具体运行库版本，不能据此承诺每次构建都兼容同一最低系统版本。

成品已包含 [**Python**](https://www.python.org) 与图形依赖，运行成品无需另外安装 Python；源码运行和打包才需要开发依赖。EXE 架构随构建所用 Python 和依赖 wheel 决定，x86 / ARM64 尚无统一交付验收；Windows 原生界面与分发仍须在对应目标机验证。

[项目配置](./JobsReverseIPA/pyproject.toml)声明 `Python>=3.10`、`PySide6>=6.6.0`，打包另需 `PyInstaller>=6.0`；Windows 入口使用 PATH 中的 Python，没有固定解释器版本。GUI 主程序按 `onedir` 分发，须保留完整程序目录，不能只拷 EXE。

外层目录只保留总说明和平台打包入口；Python 源码、配置、资源、工具链、doctor 和构建产物都收在内层 `./JobsReverseIPA/`。

## <span id="jobs-toc-heading-2" data-jobs-toc="v2">一、目录结构 <a href="#前言" style="font-size:17px; color:green;"><b>🔼</b></a> <a href="#🔚" style="font-size:17px; color:green;"><b>🔽</b></a></span><!-- jobs-toc:heading-end -->

```text
.
├── README.md
├── 【MacOS】📦生成dmg.command
├── 【Windows】📦生成exe.bat
└── JobsReverseIPA/
    ├── pyproject.toml
    ├── requirements.txt
    ├── IPAReverseAnalysisTool.spec
    ├── icon.png
    ├── ipa_reverse_tool/
    ├── doctor/
    ├── rules/
    ├── scripts/
    ├── templates/
    ├── tools/
    └── assets/
```

- `./README.md`：外层总说明，统一解释 macOS / Windows 打包入口和内层 Python 工程。
- `./【MacOS】📦生成dmg.command`：macOS 打包入口，双击后构建 `.app` 和 `.dmg`。
- `./【Windows】📦生成exe.bat`：Windows 打包入口，在 Windows 本机生成 GUI 主程序和环境体检 `.exe`。
- `./JobsReverseIPA/`：内层 Python 工程目录，保存源码、依赖、doctor、规则、模板、工具链和构建产物。

外层 `.bat` / `.command` 不使用同名文件夹包裹，也不分别放独立 `README.md`；两端打包说明统一收口在本文件。

## <span id="jobs-toc-heading-3" data-jobs-toc="v2">二、打包方式 <a href="#前言" style="font-size:17px; color:green;"><b>🔼</b></a> <a href="#🔚" style="font-size:17px; color:green;"><b>🔽</b></a></span><!-- jobs-toc:heading-end -->

### <span id="jobs-toc-heading-4" data-jobs-toc="v2">[【MacOS】📦生成dmg.command](./【MacOS】📦生成dmg.command)</span><!-- jobs-toc:heading-end -->

> **目的：** 生成 IPA 静态分析工具的 macOS APP / DMG，并附带环境体检入口。

* 阅读自述并回车，检查 Homebrew、兼容的 Python、macOS 工具与项目输入。
* 创建或复用内层 `.venv/`，检查构建依赖。
  * 必需依赖缺失：回车安装，任意非空输入取消；失败停止。
* 输入 `YES` 后清理旧 `build/` 与外层 `dist/`，其它输入取消构建。
* 构建并校验 APP、执行本地临时签名，封装含 `IPA环境体检.command` 的 DMG。
* 在构建时间目录输出成品、更新快捷方式，打开目录并启动 APP；日志位于系统临时目录。

在 Finder 中双击：

```text
./【MacOS】📦生成dmg.command
```

脚本会进入内层 `./JobsReverseIPA/`，创建或复用 `.venv`，安装构建依赖，经 `YES` 确认后清理旧 `build` / `dist`，再通过 [**PyInstaller**](https://pyinstaller.org/) 构建 App 和 DMG。

构建产物：

```text
./dist/YYYY.MM.DD HH-mm-ss/IPA Reverse Analysis Tool.app
./dist/YYYY.MM.DD HH-mm-ss/IPA-Reverse-Analysis-Tool-macOS.dmg
```

### <span id="jobs-toc-heading-5" data-jobs-toc="v2">[【Windows】📦生成exe.bat](./【Windows】📦生成exe.bat)</span><!-- jobs-toc:heading-end -->

> **目的：** 在 Windows 本机生成 IPA 分析 GUI 与环境体检 EXE。

* 阅读说明并继续，检查 Python 和内层工程，创建或复用 `.venv/`。
  * 依赖缺失：回车安装，任意非空输入取消；失败停止。
* 确认输入 `YES` 后清理旧构建产物与外层 `dist/`；其它输入取消。
* 构建主程序及 `IPA环境体检.exe`，将体检工具复制到主程序分发目录。
* 更新成品快捷方式，打开构建时间目录并启动新 EXE；分发时保留整个程序目录。

在 Windows 中双击：

```text
./【Windows】📦生成exe.bat
```

脚本会进入内层 `./JobsReverseIPA/`，创建或复用 `.venv`，安装依赖，经 `YES` 确认后清理旧 `build` / `dist`，再构建 GUI 主程序和 `IPA环境体检.exe`。Windows `.exe` 必须在 Windows 本机生成，macOS 不负责交叉构建。

内层 [PowerShell 体检构建辅助脚本](./JobsReverseIPA/doctor/windows/build_doctor_exe.ps1) 会检查每次 Python 命令的退出码，任一步失败立即停止；仅在 `IPA环境体检.exe` 存在且非空时显示成功。该辅助入口使用当前 PATH 中的 Python，单独调用时也会安装 / 更新构建依赖。

构建产物：

```text
.\dist\YYYY.MM.DD HH-mm-ss\IPA Reverse Analysis Tool\IPA Reverse Analysis Tool.exe
.\dist\YYYY.MM.DD HH-mm-ss\IPA Reverse Analysis Tool\IPA环境体检.exe
```

## <span id="jobs-toc-heading-6" data-jobs-toc="v2">三、成品运行 <a href="#前言" style="font-size:17px; color:green;"><b>🔼</b></a> <a href="#🔚" style="font-size:17px; color:green;"><b>🔽</b></a></span><!-- jobs-toc:heading-end -->

- macOS 用户通过生成的 `.dmg` 安装或直接运行其中的 `IPA Reverse Analysis Tool.app`。
- Windows 用户运行 `.\dist\YYYY.MM.DD HH-mm-ss\IPA Reverse Analysis Tool\IPA Reverse Analysis Tool.exe`。
- 环境体检工具随构建产物一起分发；macOS 体检脚本位于 DMG 内，Windows 体检程序位于主程序目录内。

源码调试仅面向开发维护，可进入内层 Python 工程后运行：

```shell
cd ./JobsReverseIPA
python3 -m ipa_reverse_tool.main doctor --output output/diagnostics
python3 -m ipa_reverse_tool.main analyze <path-to>/App.ipa --output output/latest
python3 -m ipa_reverse_tool.main gui
```

## <span id="jobs-toc-heading-7" data-jobs-toc="v2">四、当前能力 <a href="#前言" style="font-size:17px; color:green;"><b>🔼</b></a> <a href="#🔚" style="font-size:17px; color:green;"><b>🔽</b></a></span><!-- jobs-toc:heading-end -->

- GUI：拖入 IPA、文件选择、输出目录、进度、日志、打开报告；macOS 最小化后驻留系统顶部菜单栏，可从图标恢复或退出。
- 环境体检：Python 包、Apple CLT、radare2、Ghidra、Java、jtool2。
- IPA 解包：定位 `Payload/*.app`。
- `Info.plist`：基础字段、权限、URL Scheme、ATS、后台模式。
- 资源分类：图片、plist、json、sqlite、framework、dylib、证书、web、多语言。
- 字符串扫描：URL、IP、JWT、token/secret/api key 关键词。
- 报告输出：`reverse_report.html` / `reverse_report.json` / `reverse_report.md`。

## <span id="jobs-toc-heading-8" data-jobs-toc="v2">五、风险说明 <a href="#前言" style="font-size:17px; color:green;"><b>🔼</b></a> <a href="#🔚" style="font-size:17px; color:green;"><b>🔽</b></a></span><!-- jobs-toc:heading-end -->

- 只分析用户有权审计的 `.ipa` 文件。
- macOS 构建脚本只做本机 ad-hoc 签名，正式公开分发仍需 Developer ID 签名和 notarization。
- Windows 构建未做代码签名，SmartScreen 可能提示未知发布者。
- 构建脚本会在内层 `./JobsReverseIPA/` 里创建 `.venv`，并在用户输入 `YES` 后删除旧 `build` / `dist`。

打包前会清理该应用工程的旧 `dist` 产物，清理失败则停止；成功后自动打开当前平台产物的磁盘位置并运行本次生成的 APP / EXE，结尾无需回车。失败时不启动软件；运行前的防误触确认保留。

必需依赖缺失时，直接回车联网安装；输入任意字符后回车取消整个流程。安装失败或复检仍不可用时停止，不继续清理旧产物或打包。健康依赖直接复用；可选升级和词库更新仍为回车跳过、任意字符执行。

第一层交付目录与平台打包脚本同层保存 `dist/`，以及最新 APP / DMG 的相对符号链接（Mac）或 EXE / 分发包的 `.lnk`（Windows）。双击快捷方式即可接触成品，真实文件保留在 `dist/`；成功构建自动更新入口，清理旧产物时移除对应旧入口。尚无成品时不生成无效快捷方式。

构建产物使用本机本地构建时间，格式为 `YYYY.MM.DD HH-mm-ss`（年月日时分秒），例如 `2020.06.04 12-23-21`。每次构建的 APP、DMG、EXE、ZIP 和配套文件统一保存到交付层 `./dist/YYYY.MM.DD HH-mm-ss/`，同次构建只取一次时间；第一层快捷方式指向本次时间目录，成功后打开该目录并启动其中的软件。旧产物沿用原有清理规则；历史产物缺少可靠构建时间时，不补写推测时间。

## <span id="jobs-toc-heading-9" data-jobs-toc="v2">六、Mac Python 环境自检 <a href="#前言" style="font-size:17px; color:green;"><b>🔼</b></a> <a href="#🔚" style="font-size:17px; color:green;"><b>🔽</b></a></span><!-- jobs-toc:heading-end -->

实际使用 Python 的 Mac 入口通过脚本内部的具名函数执行环境自检，完整自检实现随该脚本携带。先阅读自述并确认，再自检 [**Homebrew**](https://brew.sh/)：已有安装执行 `brew update`，只更新自身和配方索引，不全量升级其它软件；缺少时安装并复检。安装路径精确输入 `YES` 选择系统标准目录，其它输入或回车选择用户目录；失败停止，不自动改换路线。新系统缺少 Command Line Tools 时按系统提示完成安装后重试。

[**Python**](https://www.python.org) 使用 Homebrew 配方；实际版本和标准库满足工具要求时复用，不兼容时才安装 / 升级并复检。必需修复直接回车执行，任意非空输入（含空格）、EOF 或非交互缺失环境均停止。旧虚拟环境不兼容时完整改名备份后重建，保留备份。Homebrew 安装路径选择、更新、Python 版本与健康检查均封装在实际执行脚本内部，不依赖外部环境支持库、同步脚本或父仓文件。Windows 入口保持原有平台环境流程；运行已打包成品无需准备构建环境。

## 七、<span id="repository-layout-and-entrypoints">本仓目录与脚本入口</span> <a href="#前言" style="font-size:17px; color:green;"><b>🔼</b></a> <a href="#🔚" style="font-size:17px; color:green;"><b>🔽</b></a>

以下为本工具的源码与维护入口，由父仓 `JobsPythonTools.py` 统一跟踪；依赖环境、Git 元数据、构建缓存和生成产物略去。

```text
.
├── .gitignore
├── 【MacOS】📦生成dmg.command
├── 【Windows】📦生成exe.bat
├── JobsReverseIPA/
│   ├── assets/
│   ├── doctor/
│   ├── icon.png
│   ├── ipa_reverse_tool/
│   ├── IPAReverseAnalysisTool.spec
│   ├── output/
│   ├── pyproject.toml
│   ├── requirements.txt
│   ├── rules/
│   ├── scripts/
│   ├── templates/
│   └── tools/
└── README.md
```

* `JobsReverseIPA/ipa_reverse_tool/` 保存 GUI、命令行与分析逻辑；`rules/`、`templates/` 为规则和报告模板，`doctor/` 为独立环境工具。

### <span id="jobs-toc-heading-11" data-jobs-toc="v2">[IPA环境体检.command](./JobsReverseIPA/doctor/macos/IPA环境体检.command)</span><!-- jobs-toc:heading-end -->

> **目的：** 检查并修复 IPA 分析所需环境，直接在终端显示体检结果。

* 阅读自述并回车，选择整轮自动修复或逐项确认。
  * 直接回车默认安装缺失项并升级已有项；输入 `n` 进入逐项模式，每项回车执行、`n` 跳过。
* 准备 Homebrew 与兼容的 Python，核验项目虚拟环境及 Python 包。
  * 缺失的必需依赖仍需确认安装；取消或失败会停止流程。
* 检查 Apple CLT、Homebrew 公式、radare2 命令及 Ghidra / jtool2 等工具，按当前选择安装、升级或提示人工处理。
* 在终端汇总结果并保留日志，不默认生成 `doctor_report` 文件。

### <span id="jobs-toc-heading-12" data-jobs-toc="v2">[build_doctor_exe.ps1](./JobsReverseIPA/doctor/windows/build_doctor_exe.ps1)</span><!-- jobs-toc:heading-end -->

> **目的：** 单独构建可分发的 Windows IPA 环境体检 EXE。

* 根据脚本位置确定内层项目目录；可用 `ProjectRoot` 参数指定项目。
* 检查 `python`，直接联网升级 pip 并安装 PyInstaller。
  * 找不到 Python 时抛错停止；此入口没有额外回车确认。
* 将 `doctor_entry.py` 打包为单文件控制台 EXE，写入外层 `dist/构建时间/`。
* 打印成品路径；此入口不清理旧时间目录，也不自动启动体检程序。

<a id="🔚" href="#前言" style="font-size:17px; color:green; font-weight:bold;">我是有底线的➤点我回到首页</a>
