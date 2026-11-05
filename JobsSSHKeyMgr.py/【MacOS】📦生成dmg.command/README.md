# `【MacOS】📦生成dmg.command`

![Jobs出品，必属精品](https://picsum.photos/1500/400)

<!-- jobs-toc:start -->
<!-- jobs-toc:source {"v":2,"token":"[toc]"} -->
<details>
<summary>📚 目录（点击展开 / 收起）</summary>

- [🔥 前言](#%E5%89%8D%E8%A8%80)
- [一、执行与环境](#jobs-toc-heading-2)
- [二、清理、产物与限制](#jobs-toc-heading-3)

</details>
<!-- jobs-toc:end -->

---

## 🔥 <span id="前言">前言</span>

本入口在 [**MacOS**](https://www.apple.com/macos/) 本机生成个人 SSH 密钥 GUI 的 APP / DMG，使用系统 zsh 和 [**Python**](https://www.python.org/) 构建器。双击前请先阅读清理范围。

## <span id="jobs-toc-heading-2" data-jobs-toc="v2">一、执行与环境 <a href="#前言" style="font-size:17px; color:green;"><b>🔼</b></a> <a href="#🔚" style="font-size:17px; color:green;"><b>🔽</b></a></span><!-- jobs-toc:heading-end -->

双击同目录脚本，或在本 README 所在目录执行：

```shell
'./【MacOS】📦生成dmg.command' --help
'./【MacOS】📦生成dmg.command'
```

先展示内置自述。已存在的健康 Python 3.11+ 优先复用，不升级；缺失时才进入内嵌 [**Homebrew**](https://brew.sh/) / Python 准备，准备和必需依赖安装均保留确认，失败即停止。Homebrew 安装路径沿现有规则选择；不会为了打包升级其它公式。源码可移动到包含空格、中文的新目录。

## <span id="jobs-toc-heading-3" data-jobs-toc="v2">二、清理、产物与限制 <a href="#前言" style="font-size:17px; color:green;"><b>🔼</b></a> <a href="#🔚" style="font-size:17px; color:green;"><b>🔽</b></a></span><!-- jobs-toc:heading-end -->

实际构建确认后只清理本工具外层固定 `dist`，输出 APP / DMG 到外层 `dist/YYYY.MM.DD HH-mm-ss/`。验证后更新第一层相对链接、打开当次磁盘位置并启动当次 APP，不在成功结尾等待。日志为系统临时目录中的 `JobsSSHKeyMgr-build.log`。取消、EOF、安装或清理失败会停止，不回退启动旧包。

[构建器详细说明](../JobsSSHKeyMgr/scripts/build.py/README.md)列出依赖、`--prepared` 参数与保护边界。已完成脚本语法、帮助页、隔离保护检查及本机 arm64 APP / DMG 构建；APP 已启动，签名、DMG 和 Python 运行库 ZIP 校验通过。未安装依赖，未公证或跨机分发。
<a id="🔚" href="#前言" style="font-size:17px; color:green; font-weight:bold;">我是有底线的➤点我回到首页</a>
