# `artifact_shortcuts.py`

![Jobs出品，必属精品](https://picsum.photos/1500/400)

<!-- jobs-toc:start -->
<!-- jobs-toc:source {"v":2,"token":"[toc]"} -->
<details>
<summary>📚 目录（点击展开 / 收起）</summary>

- [🔥 前言](#%E5%89%8D%E8%A8%80)
- [一、调用与行为](#jobs-toc-heading-2)
- [二、验证与限制](#jobs-toc-heading-3)

</details>
<!-- jobs-toc:end -->

---

## 🔥 <span id="前言">前言</span>

构建器使用的产物快捷方式模块；不直接启动 GUI、不安装依赖。模块使用 [**Python**](https://www.python.org/) 标准库，Windows 创建 `.lnk` 时使用系统 [**PowerShell**](https://learn.microsoft.com/powershell/) 与 `WScript.Shell`。

## <span id="jobs-toc-heading-2" data-jobs-toc="v2">一、调用与行为 <a href="#前言" style="font-size:17px; color:green;"><b>🔼</b></a> <a href="#🔚" style="font-size:17px; color:green;"><b>🔽</b></a></span><!-- jobs-toc:heading-end -->

由[构建器](../build.py/README.md)导入 `clear_shortcuts(root)` 与 `publish_shortcuts(root, artifacts)`。`root` 必须为当前工具真实交付目录，产物必须存在且位于该目录固定 `dist` 内；不提供需要手工输入目录的命令行。

MacOS 使用指向当前 `dist` 的相对符号链接；Windows 使用普通用户可创建的 EXE / ZIP `.lnk`，工作目录为真实产物目录。清理仅移除指向本工具 `dist` 的旧入口；同名真实文件、无关链接和外部目标一律拒绝覆盖。

## <span id="jobs-toc-heading-3" data-jobs-toc="v2">二、验证与限制 <a href="#前言" style="font-size:17px; color:green;"><b>🔼</b></a> <a href="#🔚" style="font-size:17px; color:green;"><b>🔽</b></a></span><!-- jobs-toc:heading-end -->

已在临时目录验证相对链接、同名冲突、外部目标和符号链接改向保护。没有创建用户真实产物快捷方式；Windows COM 创建与桌面打开尚未进行原生实机验证。
<a id="🔚" href="#前言" style="font-size:17px; color:green; font-weight:bold;">我是有底线的➤点我回到首页</a>
