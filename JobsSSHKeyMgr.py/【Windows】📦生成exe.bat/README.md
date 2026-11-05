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
<a id="🔚" href="#前言" style="font-size:17px; color:green; font-weight:bold;">我是有底线的➤点我回到首页</a>
