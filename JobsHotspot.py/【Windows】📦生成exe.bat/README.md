# 【Windows】📦生成exe.bat · Windows 打包入口

![Jobs出品，必属精品](https://picsum.photos/1500/400)

[toc]

---

## 🔥 <span id="前言">前言</span>

在 [**Windows**](https://www.microsoft.com/windows) 本机生成 Jobs Hotspot EXE 完整目录 / ZIP。外层只检查平台及 Python，唯一构建实现为 [build.py](../JobsHotspot/scripts/build.py/README.md)。

## 一、运行与检查 <a href="#前言" style="font-size:17px; color:green;"><b>🔼</b></a> <a href="#🔚" style="font-size:17px; color:green;"><b>🔽</b></a>

双击同目录 `【Windows】📦生成exe.bat`，或在终端将完整脚本路径加引号运行；`--help` 仅显示内置自述。先阅读自述，实际清理前由内层统一等待回车，Ctrl+C 或任意非空输入取消。先检查系统 Python Launcher `py -3`，再检查 PATH 中 `python`，需要 Python 3.11+。缺少运行时则停止并显示 Python 官方下载入口；不会静默安装或修改系统策略。

入口使用 UTF-8、关闭延迟展开并为工程路径加引号；失败保留控制台错误，成功不暂停。

## 二、输出、日志与影响范围 <a href="#前言" style="font-size:17px; color:green;"><b>🔼</b></a> <a href="#🔚" style="font-size:17px; color:green;"><b>🔽</b></a>

将清理当前工具外层固定 `dist` 的旧成品，再写入 `dist/YYYY.MM.DD HH-mm-ss/`。不清理其它项目、源码和系统热点配置；链接改向、依赖缺失、检查失败或取消时立即停止。构建依赖仅在缺失时经回车确认安装到当前用户构建缓存；未授权不会升级已有健康依赖。

日志为系统临时目录中的 `JobsHotspot-build.log`。成品通过 GUI 冒烟与分发包校验后，建立外层最新产物入口，打开产物目录，再启动当次软件。成品携带运行依赖；Windows 分发完整 ZIP，MacOS 分发完整 APP／DMG，不能跨系统生成或混用。

## 三、常见问题与验证 <a href="#前言" style="font-size:17px; color:green;"><b>🔼</b></a> <a href="#🔚" style="font-size:17px; color:green;"><b>🔽</b></a>

缺资源、当前 Python 不兼容或原生系统命令缺失时，按错误位置准备后重试。Windows 原生构建只能在 Windows 进行；MacOS 生成的包不提供 Windows EXE。构建不会开启真实热点，不要求 sudo，不修改代理、Gatekeeper 或系统网络策略。

当前脚本已做语法／路径／变量静态核对；另一系统的真实双击与硬件共享效果需在对应环境验收。



<!-- JOBS_TERMINAL_STYLE_V1:BEGIN -->

> Windows 终端配色保护：支持完整颜色查询的交互控制台会先保存当前会话默认前景、背景与16色色表，再临时使用黑底白字和统一强调色；正常结束、业务失败及可捕获中断后恢复。用户运行中自行改动的颜色保留并提示，不修改用户主题、共享 Profile、注册表或全局策略。快照不包含进入前任意叠加的临时文字样式。非控制台、重定向、`NO_COLOR`、Sourcetree 及无法可靠保存／恢复颜色的环境保持原状态或降级为纯文本。

> `.cmd`／`.bat` 入口内嵌完整会话守护：黑底白字及强调色保护就绪或明确降级后才开始业务，全部退出路径同步等待恢复回执；同时核对父进程身份。原 PowerShell／Python 启动命令和业务参数不经过再次解析，保护初始化后恢复进入时的延迟扩展模式，原业务自己的 `setlocal` 保留；嵌套 PowerShell 复用同一会话保护。守护脚本只写入本轮系统临时目录，成功恢复后清理控制文件。

> 强制结束进程或终端崩溃无法保证自动恢复。恢复失败时保留并提示本轮 `%TEMP%\JobsTerminalStyle-<PID>-*.ps1` 恢复脚本，需在原控制台核对后运行；不要通过重置用户配置恢复。`-ExecutionPolicy Bypass` 如被入口使用，仅作用于本次子进程，不持久修改策略。

> 验证范围：已完成 PowerShell 语法、参数／退出与隔离生命周期核验；Windows 原生控制台的显示、按键与 `Ctrl+C` 实机验证尚未完成。

<!-- JOBS_TERMINAL_STYLE_V1:END -->

<a id="🔚" href="#前言" style="font-size:17px; color:green; font-weight:bold;">我是有底线的➤点我回到首页</a>
