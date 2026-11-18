# 【MacOS】📦生成dmg.command · MacOS 打包入口

![Jobs出品，必属精品](https://picsum.photos/1500/400)

<!-- jobs-toc:start -->
<!-- jobs-toc:source {"v":2,"token":"[toc]"} -->
<details>
<summary>📚 目录（点击展开 / 收起）</summary>

- [🔥 前言](#%E5%89%8D%E8%A8%80)
- [一、运行与检查](#jobs-toc-heading-2)
- [二、输出、日志与影响范围](#jobs-toc-heading-3)
- [三、常见问题与验证](#jobs-toc-heading-4)

</details>
<!-- jobs-toc:end -->

---

## 🔥 <span id="前言">前言</span>

在 [**MacOS**](https://www.apple.com/macos/) 本机生成 Jobs Hotspot APP / DMG。外层只检查平台及 Python，唯一构建实现为 [build.py](../JobsHotspot/scripts/build.py/README.md)。

## <span id="jobs-toc-heading-2" data-jobs-toc="v2">一、运行与检查 <a href="#前言" style="font-size:17px; color:green;"><b>🔼</b></a> <a href="#🔚" style="font-size:17px; color:green;"><b>🔽</b></a></span><!-- jobs-toc:heading-end -->

双击同目录 `【MacOS】📦生成dmg.command`，或在终端将完整脚本路径加引号运行；`--help` 仅显示内置自述。先阅读自述，实际清理前由内层统一等待回车，Ctrl+C 或任意非空输入取消。先复用显式 `JOBS_HOTSPOT_BUILD_PYTHON` 或 PATH 中健康 Python 3.11+；缺失时才进入脚本内置的 Homebrew／Python 准备，独立显示自述和确认。环境变量激活仅影响当前进程及子进程，实际安装的依赖会保留；已有健康解释器不升级。

按脚本确认准备 Homebrew 时，精确大写 YES 选择系统标准目录，其它输入／回车选择用户目录；权限由官方安装器验证，失败不自动换路径。

## <span id="jobs-toc-heading-3" data-jobs-toc="v2">二、输出、日志与影响范围 <a href="#前言" style="font-size:17px; color:green;"><b>🔼</b></a> <a href="#🔚" style="font-size:17px; color:green;"><b>🔽</b></a></span><!-- jobs-toc:heading-end -->

将清理当前工具外层固定 `dist` 的旧成品，再写入 `dist/YYYY.MM.DD HH-mm-ss/`。不清理其它项目、源码和系统热点配置；链接改向、依赖缺失、检查失败或取消时立即停止。构建依赖仅在缺失时经回车确认安装到当前用户构建缓存；未授权不会升级已有健康依赖。

日志为系统临时目录中的 `JobsHotspot-build.log`。成品通过 GUI 冒烟与分发包校验后，建立外层最新产物入口，打开产物目录，再启动当次软件。成品携带运行依赖；Windows 分发完整 ZIP，MacOS 分发完整 APP／DMG，不能跨系统生成或混用。

## <span id="jobs-toc-heading-4" data-jobs-toc="v2">三、常见问题与验证 <a href="#前言" style="font-size:17px; color:green;"><b>🔼</b></a> <a href="#🔚" style="font-size:17px; color:green;"><b>🔽</b></a></span><!-- jobs-toc:heading-end -->

缺资源、当前 Python 不兼容或原生系统命令缺失时，按错误位置准备后重试。Windows 原生构建只能在 Windows 进行；MacOS 生成的包不提供 Windows EXE。构建不会开启真实热点，不要求 sudo，不修改代理、Gatekeeper 或系统网络策略。

当前脚本已做语法／路径／变量静态核对；另一系统的真实双击与硬件共享效果需在对应环境验收。

**终端配色保护：** 独立运行时，在支持完整保存与恢复配色的交互终端中临时使用黑底白字及统一强调色；正常结束、失败或可捕获中断后恢复进入前的配色，不修改终端全局偏好或 Shell 启动配置。不支持完整保护、无交互终端、`NO_COLOR`、既有纯文本模式和 Sourcetree 场景不切换配色，并沿用纯文本输出约定。强制终止（如 `kill -9`）无法由脚本自身保证恢复，请使用运行时显示的独立恢复入口。

<a id="🔚" href="#前言" style="font-size:17px; color:green; font-weight:bold;">我是有底线的➤点我回到首页</a>
