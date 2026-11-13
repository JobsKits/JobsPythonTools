# `【Windows】📦生成exe.bat`

![Jobs出品，必属精品](https://picsum.photos/1500/400)

<!-- jobs-toc:start -->
<!-- jobs-toc:source {"v":2,"token":"[toc]"} -->
<details>
<summary>📚 目录（点击展开 / 收起）</summary>

- [🔥 前言](#%E5%89%8D%E8%A8%80)
- [一、执行与环境](#jobs-toc-heading-2)
- [二、清理、产物与验证](#jobs-toc-heading-3)

</details>
<!-- jobs-toc:end -->

---

## 🔥 <span id="前言">前言</span>

本入口在 [**Windows**](https://www.microsoft.com/windows) 本机生成个人 SSH 密钥 GUI 的 EXE 完整依赖目录及 ZIP。使用 [**Python**](https://www.python.org/) 3.11+、[**PyInstaller**](https://pyinstaller.org/) 和 [**PySide6**](https://doc.qt.io/qtforpython-6/)，不从其它系统交叉构建。

## <span id="jobs-toc-heading-2" data-jobs-toc="v2">一、执行与环境 <a href="#前言" style="font-size:17px; color:green;"><b>🔼</b></a> <a href="#🔚" style="font-size:17px; color:green;"><b>🔽</b></a></span><!-- jobs-toc:heading-end -->

最低计划系统为 Windows 10 64 位；具体 build 与打包运行兼容性尚待原生验证。先安装带 PATH 或 Python Launcher 的 Python 3.11+。双击同目录脚本，或从本 README 所在目录运行：

```bat
"【Windows】📦生成exe.bat" --help
"【Windows】📦生成exe.bat"
```

优先检测 `py -3`，其次检测 `python`；不能运行符合版本的解释器时停止并提供官方安装入口。健康构建依赖直接复用，缺失时构建器询问直接回车安装；任意非空输入（含空格）、EOF 或安装失败都取消，不继续清理或打包。

## <span id="jobs-toc-heading-3" data-jobs-toc="v2">二、清理、产物与验证 <a href="#前言" style="font-size:17px; color:green;"><b>🔼</b></a> <a href="#🔚" style="font-size:17px; color:green;"><b>🔽</b></a></span><!-- jobs-toc:heading-end -->

实际构建前显示自述并确认，只清理本工具外层固定 `dist`。当次 EXE、`_internal` 运行库和 ZIP 位于外层 `dist/YYYY.MM.DD HH-mm-ss/`；分发 ZIP 包含完整 EXE 目录，不能只复制 EXE。生成成功后发布第一层 EXE / ZIP `.lnk`、打开当次磁盘位置再启动当次程序，不在成功结尾暂停。失败保留错误窗口和日志。

日志为系统临时目录中的 `JobsSSHKeyMgr-build.log`。更多参数和边界见[构建器说明](../JobsSSHKeyMgr/scripts/build.py/README.md)。已检查参数、路径与 CRLF；未在 Windows 实机执行此入口、依赖安装或 EXE 打包。


<!-- JOBS_TERMINAL_STYLE_V1:BEGIN -->

> Windows 终端配色保护：支持完整颜色查询的交互控制台会先保存当前会话默认前景、背景与16色色表，再临时使用黑底白字和统一强调色；正常结束、业务失败及可捕获中断后恢复。用户运行中自行改动的颜色保留并提示，不修改用户主题、共享 Profile、注册表或全局策略。快照不包含进入前任意叠加的临时文字样式。非控制台、重定向、`NO_COLOR`、Sourcetree 及无法可靠保存／恢复颜色的环境保持原状态或降级为纯文本。

> `.cmd`／`.bat` 入口内嵌完整会话守护：黑底白字及强调色保护就绪或明确降级后才开始业务，全部退出路径同步等待恢复回执；同时核对父进程身份。原 PowerShell／Python 启动命令和业务参数不经过再次解析，保护初始化后恢复进入时的延迟扩展模式，原业务自己的 `setlocal` 保留；嵌套 PowerShell 复用同一会话保护。守护脚本只写入本轮系统临时目录，成功恢复后清理控制文件。

> 强制结束进程或终端崩溃无法保证自动恢复。恢复失败时保留并提示本轮 `%TEMP%\JobsTerminalStyle-<PID>-*.ps1` 恢复脚本，需在原控制台核对后运行；不要通过重置用户配置恢复。`-ExecutionPolicy Bypass` 如被入口使用，仅作用于本次子进程，不持久修改策略。

> 验证范围：已完成 PowerShell 语法、参数／退出与隔离生命周期核验；Windows 原生控制台的显示、按键与 `Ctrl+C` 实机验证尚未完成。

<!-- JOBS_TERMINAL_STYLE_V1:END -->

<a id="🔚" href="#前言" style="font-size:17px; color:green; font-weight:bold;">我是有底线的➤点我回到首页</a>
