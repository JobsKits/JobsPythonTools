# `build_macos.command`

![Jobs出品，必属精品](https://picsum.photos/1500/400)

<!-- jobs-toc:start -->
<!-- jobs-toc:source {"v":2,"token":"[toc]"} -->
<details>
<summary>📚 目录（点击展开 / 收起）</summary>

- [🔥 前言](#jobs-toc-heading-1)
- [一、适用场景](#jobs-toc-heading-2)
- [二、目录结构](#jobs-toc-heading-3)
- [三、执行前检查](#jobs-toc-heading-4)
- [四、运行方式](#jobs-toc-heading-5)
  - [4.1、双击运行](#jobs-toc-heading-6)
  - [4.2、终端运行](#jobs-toc-heading-7)
- [五、操作流程](#jobs-toc-heading-8)
- [六、风险说明](#jobs-toc-heading-9)
- [七、日志文件](#jobs-toc-heading-10)
- [八、常见问题](#jobs-toc-heading-11)
  - [8.1、提示命令不存在](#jobs-toc-heading-12)
  - [8.2、提示权限不足](#jobs-toc-heading-13)
  - [8.3、双击后没有继续执行](#jobs-toc-heading-14)
- [九、未执行声明](#jobs-toc-heading-15)
- [十、Mac Python 环境自检](#jobs-toc-heading-16)

</details>
<!-- jobs-toc:end -->

---

## <span id="jobs-toc-heading-1" data-jobs-toc="v2">🔥 <font id=前言>前言</font></span><!-- jobs-toc:heading-end -->

`build_macos.command` 将上级 `JobsMockTool` 源码打包为本机 [**macOS**](https://www.apple.com/macos/) APP 和拖拽安装 DMG。入口固定使用上级 `app.py`、`requirements.txt`、`icon.png` 和 `scripts/artifact_shortcuts.py`，适合在修改源码后生成可分发桌面程序。完整应用功能见 [JobsMockTool 总说明](../README.md)。

所有工程输入按脚本位置定位，生成的临时 PyInstaller 配置放在上级 `build/pyinstaller-spec/`，不会改写可随工程搬迁的源码配置 [JobsMockTool.spec](../JobsMockTool.spec)。App 图标随包携带，不依赖开发机源码目录。

| 功能 | 输入、输出与默认行为 |
| --- | --- |
| 环境准备 | 内置自检 [**Homebrew**](https://brew.sh/) 和 [**Python**](https://www.python.org/) 3.11+，默认使用 `python@3.13`；复用上级 `../.venv/`。 |
| 依赖检查 | 检查 PySide6 Widgets、QtWebEngine 和 PyInstaller；缺失时经确认从 `../requirements.txt` 安装。 |
| 清理 | 精确输入 `YES` 后删除上级 `../build/`、`../dist/` 及对应旧快捷方式；其它输入取消打包。 |
| APP | 使用 [**PyInstaller**](https://pyinstaller.org/) 的窗口程序 / onedir 模式，收集 PySide6、WebEngine 与图标，生成 `JobsMockTool.app`。 |
| DMG | 用系统 `hdiutil` 生成 `JobsMockTool-Installer.dmg`，内含 APP 和 Applications 拖拽入口。 |
| 完成动作 | 产物集中到 `../dist/YYYY.MM.DD HH-mm-ss/`，更新上级快捷方式，打开产物目录并启动新 APP。 |

该脚本没有子命令或独立的只读参数，直接运行即进入同一套交互构建流程；需要先阅读自述并回车确认。

## <span id="jobs-toc-heading-2" data-jobs-toc="v2">一、适用场景 <a href="#前言" style="font-size:17px; color:green;"><b>🔼</b></a> <a href="#🔚" style="font-size:17px; color:green;"><b>🔽</b></a></span><!-- jobs-toc:heading-end -->

- 从当前 `JobsMockTool` 源码生成本机 APP / DMG，用于本机使用或拷贝安装。
- 需要将 QtWebEngine 和 Python 运行时一并打入产物，使成品无需另外安装 Python 包。
- Windows EXE 使用上级 [Windows 打包入口](../【Windows】📦生成exe.bat)，不由本脚本生成。

## <span id="jobs-toc-heading-3" data-jobs-toc="v2">二、目录结构 <a href="#前言" style="font-size:17px; color:green;"><b>🔼</b></a> <a href="#🔚" style="font-size:17px; color:green;"><b>🔽</b></a></span><!-- jobs-toc:heading-end -->

```text
build_macos.command/
├── build_macos.command
└── README.md
```

## <span id="jobs-toc-heading-4" data-jobs-toc="v2">三、执行前检查 <a href="#前言" style="font-size:17px; color:green;"><b>🔼</b></a> <a href="#🔚" style="font-size:17px; color:green;"><b>🔽</b></a></span><!-- jobs-toc:heading-end -->

- 确认当前系统为 macOS，并保留脚本相对上级工程的位置；缺少 `app.py` 或 `requirements.txt` 时停止。
- 缺少必需环境或依赖时，直接回车安装，任意非空输入或 EOF 取消整个流程；安装失败或复检失败停止。
- 虚拟环境中的 pip 升级属于可选动作，直接回车跳过，输入任意字符后执行。
- 提前将需要保留的成品移出 `../dist/`，后续 `YES` 确认会删除整个旧构建 / 产物目录。

## <span id="jobs-toc-heading-5" data-jobs-toc="v2">四、运行方式 <a href="#前言" style="font-size:17px; color:green;"><b>🔼</b></a> <a href="#🔚" style="font-size:17px; color:green;"><b>🔽</b></a></span><!-- jobs-toc:heading-end -->

### <span id="jobs-toc-heading-6" data-jobs-toc="v2">4.1、双击运行 <a href="#前言" style="font-size:17px; color:green;"><b>🔼</b></a> <a href="#🔚" style="font-size:17px; color:green;"><b>🔽</b></a></span><!-- jobs-toc:heading-end -->

在 Finder 中打开当前目录并双击 `build_macos.command`。阅读终端自述后按回车继续，按 `Ctrl+C` 取消。

### <span id="jobs-toc-heading-7" data-jobs-toc="v2">4.2、终端运行 <a href="#前言" style="font-size:17px; color:green;"><b>🔼</b></a> <a href="#🔚" style="font-size:17px; color:green;"><b>🔽</b></a></span><!-- jobs-toc:heading-end -->

```shell
./build_macos.command
```

在本 README 所在目录执行上述命令；也可从上级目录执行 `./build_macos.command/build_macos.command`。路径根据脚本位置计算，不依赖启动时的工作目录。

## <span id="jobs-toc-heading-8" data-jobs-toc="v2">五、操作流程 <a href="#前言" style="font-size:17px; color:green;"><b>🔼</b></a> <a href="#🔚" style="font-size:17px; color:green;"><b>🔽</b></a></span><!-- jobs-toc:heading-end -->

1、显示脚本内置自述，按回车继续，`Ctrl+C` 取消。

2、自检 Homebrew / Python，定位上级工程，创建或复用 `.venv/` 并补齐所需依赖。

3、询问可选 pip 升级；清理旧 `build/`、`dist/` 另须精确输入 `YES`。

4、构建 APP，检查 App Bundle 存在，再封装 DMG；命令失败立即停止。

5、发布上级最新 APP / DMG 入口，打开产物目录并启动 APP，成功后不等待回车。

## <span id="jobs-toc-heading-9" data-jobs-toc="v2">六、风险说明 <a href="#前言" style="font-size:17px; color:green;"><b>🔼</b></a> <a href="#🔚" style="font-size:17px; color:green;"><b>🔽</b></a></span><!-- jobs-toc:heading-end -->

- 清理范围是上级工程的 `build/`、`dist/`；两端构建若共用该目录，已有另一平台产物也会被删除。
- 环境准备可能安装或更新 Homebrew / Python，以及写入工程 `.venv/`；健康项目依赖直接复用，可选 pip 升级单独确认。
- QtWebEngine 收集体积较大，构建需要相应磁盘空间。脚本生成 DMG，但没有正式发布签名和公证步骤。

## <span id="jobs-toc-heading-10" data-jobs-toc="v2">七、日志文件 <a href="#前言" style="font-size:17px; color:green;"><b>🔼</b></a> <a href="#🔚" style="font-size:17px; color:green;"><b>🔽</b></a></span><!-- jobs-toc:heading-end -->

终端和系统临时目录中的 `build_macos.log` 同步记录依赖准备、构建输出、产物路径及失败原因。日志在每次确认后进入构建时重新初始化；需要保留排查依据时先复制日志。

## <span id="jobs-toc-heading-11" data-jobs-toc="v2">八、常见问题 <a href="#前言" style="font-size:17px; color:green;"><b>🔼</b></a> <a href="#🔚" style="font-size:17px; color:green;"><b>🔽</b></a></span><!-- jobs-toc:heading-end -->

### <span id="jobs-toc-heading-12" data-jobs-toc="v2">8.1、提示命令不存在 <a href="#前言" style="font-size:17px; color:green;"><b>🔼</b></a> <a href="#🔚" style="font-size:17px; color:green;"><b>🔽</b></a></span><!-- jobs-toc:heading-end -->

脚本会自检 Python 和依赖。若系统 `hdiutil`、工程输入或依赖复检失败，按终端显示的具体命令 / 文件处理后重试，不会继续打包。

### <span id="jobs-toc-heading-13" data-jobs-toc="v2">8.2、提示权限不足 <a href="#前言" style="font-size:17px; color:green;"><b>🔼</b></a> <a href="#🔚" style="font-size:17px; color:green;"><b>🔽</b></a></span><!-- jobs-toc:heading-end -->

确认上级工程、虚拟环境、`build/` 和 `dist/` 可写。Homebrew 安装路径选择与权限由第十章的环境准备流程处理，失败时停止，不自动改换安装路径。

### <span id="jobs-toc-heading-14" data-jobs-toc="v2">8.3、双击后没有继续执行 <a href="#前言" style="font-size:17px; color:green;"><b>🔼</b></a> <a href="#🔚" style="font-size:17px; color:green;"><b>🔽</b></a></span><!-- jobs-toc:heading-end -->

查看终端是否正在等待阅读确认或业务输入；不确定时按 `Ctrl+C` 退出后重新检查脚本。

## <span id="jobs-toc-heading-15" data-jobs-toc="v2">九、未执行声明 <a href="#前言" style="font-size:17px; color:green;"><b>🔼</b></a> <a href="#🔚" style="font-size:17px; color:green;"><b>🔽</b></a></span><!-- jobs-toc:heading-end -->

本页按当前脚本的实际输入、确认分支和构建命令说明能力；静态核对不代表 APP / DMG 已在目标机器运行验收，产物仍须在对应 macOS 环境实际打开核验。

构建产物使用本机本地构建时间，格式为 `YYYY.MM.DD HH-mm-ss`（年月日时分秒），例如 `2020.06.04 12-23-21`。每次构建的 APP、DMG、EXE、ZIP 和配套文件统一保存到交付层 `../dist/YYYY.MM.DD HH-mm-ss/`，同次构建只取一次时间；第一层快捷方式指向本次时间目录，成功后打开该目录并启动其中的软件。旧产物沿用原有清理规则；历史产物缺少可靠构建时间时，不补写推测时间。

## <span id="jobs-toc-heading-16" data-jobs-toc="v2">十、Mac Python 环境自检 <a href="#前言" style="font-size:17px; color:green;"><b>🔼</b></a> <a href="#🔚" style="font-size:17px; color:green;"><b>🔽</b></a></span><!-- jobs-toc:heading-end -->

实际使用 Python 的 Mac 入口通过脚本内部的具名函数执行环境自检，完整自检实现随该脚本携带。先阅读自述并确认，再自检 [**Homebrew**](https://brew.sh/)：已有安装执行 `brew update`，只更新自身和配方索引，不全量升级其它软件；缺少时安装并复检。安装路径精确输入 `YES` 选择系统标准目录，其它输入或回车选择用户目录；失败停止，不自动改换路线。新系统缺少 Command Line Tools 时按系统提示完成安装后重试。

[**Python**](https://www.python.org) 使用 Homebrew 配方；实际版本和标准库满足工具要求时复用，不兼容时才安装 / 升级并复检。必需修复直接回车执行，任意非空输入（含空格）、EOF 或非交互缺失环境均停止。旧虚拟环境不兼容时完整改名备份后重建，保留备份。Homebrew 安装路径选择、更新、Python 版本与健康检查均封装在实际执行脚本内部，不依赖外部环境支持库、同步脚本或父仓文件。Windows 入口保持原有平台环境流程；运行已打包成品无需准备构建环境。

<a id="🔚" href="#前言" style="font-size:17px; color:green; font-weight:bold;">我是有底线的➤点我回到首页</a>
