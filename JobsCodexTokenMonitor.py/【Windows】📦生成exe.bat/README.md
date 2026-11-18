# `【Windows】📦生成exe.bat`

![Jobs出品，必属精品](https://picsum.photos/1500/400)

<!-- jobs-toc:start -->
<!-- jobs-toc:source {"v":2,"token":"[toc]"} -->
<details>
<summary>📚 目录（点击展开 / 收起）</summary>

- [🔥 前言](#%E5%89%8D%E8%A8%80)
- [一、运行与依赖](#jobs-toc-heading-2)
- [二、产物、日志与边界](#jobs-toc-heading-3)

</details>
<!-- jobs-toc:end -->

---

## 🔥 <span id="前言">前言</span>

JobsCodexTokenMonitor 的 Windows 本机打包入口，用于生成本工具的 EXE 与相应分发包。完整功能与系统限制见[工具说明](../README.md)。

## <span id="jobs-toc-heading-2" data-jobs-toc="v2">一、运行与依赖 <a href="#前言" style="font-size:17px; color:green;"><b>🔼</b></a> <a href="#🔚" style="font-size:17px; color:green;"><b>🔽</b></a></span><!-- jobs-toc:heading-end -->

双击同目录脚本，或从本 README 所在目录执行：

```bat
".\【Windows】📦生成exe.bat"
```

Windows 本机；最低交付基线为 Windows 10 64 位（x64），具体 build 未锁定。使用本机 Python / 系统 PowerShell 与脚本声明的打包工具；缺失依赖按实际提示处理。

先显示源码内置自述，再按入口与内层构建器的现有确认流程继续；Ctrl+C 或提示中的取消操作停止。环境检查、清理、构建及结果处理各自保留真实失败状态。

`【Windows】📦生成exe.bat` 支持 `--help` 时仅显示用法；实际构建请使用上面的命令。

## <span id="jobs-toc-heading-3" data-jobs-toc="v2">二、产物、日志与边界 <a href="#前言" style="font-size:17px; color:green;"><b>🔼</b></a> <a href="#🔚" style="font-size:17px; color:green;"><b>🔽</b></a></span><!-- jobs-toc:heading-end -->

- 项目路径从脚本实际位置解析，完整工具目录复制或改名后仍按相对结构定位；不要只拷贝一个包装入口。
- 构建可能联网准备依赖，并清理本工具固定 `dist` 中的旧产物。真实产物、时间目录和最新快捷方式由实际构建器维护，保留原有保护；不会因为新增脚本包装目录而改变交付层位置。
- 日志沿用该工具在系统临时目录中的构建日志及内层命令诊断；路径由运行时自述显示。失败时保留原始错误，不把已有旧包当作本次成功产物。
- MacOS 成品在 MacOS 构建，Windows 成品在 Windows 构建；完成路径与语法检查不代表真实打包、安装或跨机运行已验收。

<a id="🔚" href="#前言" style="font-size:17px; color:green; font-weight:bold;">我是有底线的➤点我回到首页</a>
