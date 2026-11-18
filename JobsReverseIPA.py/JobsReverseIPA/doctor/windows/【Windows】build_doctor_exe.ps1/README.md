# `【Windows】build_doctor_exe.ps1`

![Jobs出品，必属精品](https://picsum.photos/1500/400)

<!-- jobs-toc:start -->
<!-- jobs-toc:source {"v":2,"token":"[toc]"} -->
<details>
<summary>📚 目录（点击展开 / 收起）</summary>

- [🔥 前言](#%E5%89%8D%E8%A8%80)
- [一、运行与参数](#jobs-toc-heading-2)
- [二、依赖与产物边界](#jobs-toc-heading-3)

</details>
<!-- jobs-toc:end -->

---

## 🔥 <span id="前言">前言</span>

Windows 原生 PowerShell 5.1 构建辅助入口，生成 IPA 环境体检控制台 EXE；与完整 GUI 打包入口分别承担各自职责。

## <span id="jobs-toc-heading-2" data-jobs-toc="v2">一、运行与参数 <a href="#前言" style="font-size:17px; color:green;"><b>🔼</b></a> <a href="#🔚" style="font-size:17px; color:green;"><b>🔽</b></a></span><!-- jobs-toc:heading-end -->

从本 README 所在目录执行：

```powershell
powershell.exe -NoProfile -File ".\【Windows】build_doctor_exe.ps1"
```

先展示内置自述，再等待回车；非空输入、EOF 或 Ctrl+C 取消。父流程完成确认后可显式传入 `-Confirmed`，但缺失 PyInstaller 仍要求交互确认安装。`-ProjectRoot` 默认为完整工程中本脚本推导出的内层目录。

## <span id="jobs-toc-heading-3" data-jobs-toc="v2">二、依赖与产物边界 <a href="#前言" style="font-size:17px; color:green;"><b>🔼</b></a> <a href="#🔚" style="font-size:17px; color:green;"><b>🔽</b></a></span><!-- jobs-toc:heading-end -->

检查实际 Python 可执行性与 PyInstaller 健康状态，健康环境不安装、不升级 pip；缺失时确认安装并复检。只写本工具 dist 的独立时间目录，不清理其它产物；本轮日志在系统临时目录，实际路径由运行时显示。

Windows 入口仅在 Windows 执行业务；本轮没有运行真实依赖安装或生成 EXE。MacOS 入口完成对应语法检查；路径／隔离夹具与真实 GUI、系统权限、跨机打包分别验收。

<a id="🔚" href="#前言" style="font-size:17px; color:green; font-weight:bold;">我是有底线的➤点我回到首页</a>
