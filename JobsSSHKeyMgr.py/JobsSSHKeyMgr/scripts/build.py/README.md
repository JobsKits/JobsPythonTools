# `build.py`

![Jobs出品，必属精品](https://picsum.photos/1500/400)

<!-- jobs-toc:start -->
<!-- jobs-toc:source {"v":2,"token":"[toc]"} -->
<details>
<summary>📚 目录（点击展开 / 收起）</summary>

- [🔥 前言](#%E5%89%8D%E8%A8%80)
- [一、运行与依赖](#jobs-toc-heading-2)
- [二、清理与输出](#jobs-toc-heading-3)
- [三、成功行为与验证](#jobs-toc-heading-4)

</details>
<!-- jobs-toc:end -->

---

## 🔥 <span id="前言">前言</span>

使用 [**PyInstaller**](https://pyinstaller.org/) 在本机生成个人 SSH 密钥管理器。[**MacOS**](https://www.apple.com/macos/) 生成 APP / DMG；[**Windows**](https://www.microsoft.com/windows) 生成 EXE 完整依赖目录及 ZIP，不交叉构建。

## <span id="jobs-toc-heading-2" data-jobs-toc="v2">一、运行与依赖 <a href="#前言" style="font-size:17px; color:green;"><b>🔼</b></a> <a href="#🔚" style="font-size:17px; color:green;"><b>🔽</b></a></span><!-- jobs-toc:heading-end -->

需要 [**Python**](https://www.python.org/) 3.11+、[**PySide6**](https://doc.qt.io/qtforpython-6/) 6.8 至 7 之前、PyInstaller 6.10 至 7 之前。MacOS 还使用系统 `hdiutil` / `open`；Windows 使用系统 PowerShell / Explorer。

```shell
python ./build.py --help
python ./build.py
python ./build.py --prepared
```

`--help` 无副作用。`--prepared` 只复检当前解释器的构建依赖，不允许安装；它仍保留构建确认与实际构建行为。正常模式先复用健康解释器或本工具 `.venv`，只有缺失或损坏时确认安装。依赖安装采用直接回车同意，任意非空输入（含空格）或 EOF 取消。已有坏 `.venv` 在确认后完整改名备份，不删除。

## <span id="jobs-toc-heading-3" data-jobs-toc="v2">二、清理与输出 <a href="#前言" style="font-size:17px; color:green;"><b>🔼</b></a> <a href="#🔚" style="font-size:17px; color:green;"><b>🔽</b></a></span><!-- jobs-toc:heading-end -->

实际构建前显示影响范围并等待回车。仅清理本工具外层固定 `dist` 中的旧产物，不清理源码、用户 SSH 或其它工具目录；拒绝链接改向、工程根、外部路径和非目录目标。缺失依赖、取消、前置检查或清理失败都停止，不启动旧包。

产物保存至工具外层 `dist/YYYY.MM.DD HH-mm-ss/`，同次 APP / DMG 或 EXE / ZIP 共用时间目录。构建中间文件位于工具外层 `work/`，日志为系统临时目录中的 `JobsSSHKeyMgr-build.log`。无需额外图标资源；运行产物仍需目标系统可用的 OpenSSH，GitHub CLI 仅用于可选自动登记。

## <span id="jobs-toc-heading-4" data-jobs-toc="v2">三、成功行为与验证 <a href="#前言" style="font-size:17px; color:green;"><b>🔼</b></a> <a href="#🔚" style="font-size:17px; color:green;"><b>🔽</b></a></span><!-- jobs-toc:heading-end -->

验证可执行文件与分发包后，第一层发布 MacOS 相对链接或 Windows `.lnk`，只替换属于本工具 `dist` 的旧入口；随后打开本次磁盘位置，再启动本次应用。快捷方式失败不会覆盖同名真实文件或无关入口。

已完成帮助入口、语法与临时目录中删除边界、取消和快捷方式保护验证。未安装依赖、未生成真实 APP / DMG / EXE / ZIP，目标平台成品及跨机运行仍需实际验证。

<!-- jobs-language-terminal-style-v1 -->

**终端配色保护：** `build.py` 直接运行时，在可可靠保存与恢复配色的交互终端中临时使用黑底白字和统一强调色；正常退出、失败及可捕获中断后恢复进入前的配色，保留原业务清理和退出状态。导入本文件不接管终端；无法可靠保护、纯文本模式或无交互终端时按纯文本约定降级。运行中另行修改的颜色会保留并报告冲突，强制终止后可按运行提示使用独立恢复入口。 模块启动等无法安全重复初始化的场景不重启原程序。

<a id="🔚" href="#前言" style="font-size:17px; color:green; font-weight:bold;">我是有底线的➤点我回到首页</a>
