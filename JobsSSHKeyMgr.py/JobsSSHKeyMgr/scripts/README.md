# `JobsSSHKeyMgr 构建与源码入口`

![Jobs出品，必属精品](https://picsum.photos/1500/400)

<!-- jobs-toc:start -->
<!-- jobs-toc:source {"v":2,"token":"[toc]"} -->
<details>
<summary>📚 目录（点击展开 / 收起）</summary>

- [🔥 前言](#%E5%89%8D%E8%A8%80)
- [一、入口与职责](#jobs-toc-heading-2)
- [二、使用与边界](#jobs-toc-heading-3)

</details>
<!-- jobs-toc:end -->

---

## 🔥 <span id="前言">前言</span>

本目录保存 [**Python**](https://www.python.org/) 辅助入口。每个脚本采用同名目录包装，构建业务不依赖启动工作目录。

## <span id="jobs-toc-heading-2" data-jobs-toc="v2">一、入口与职责 <a href="#前言" style="font-size:17px; color:green;"><b>🔼</b></a> <a href="#🔚" style="font-size:17px; color:green;"><b>🔽</b></a></span><!-- jobs-toc:heading-end -->

| 入口 | 职责 |
| --- | --- |
| [源码运行](./launch.py/README.md) | 启动个人 SSH 密钥 GUI；不自动安装依赖。 |
| [本机打包](./build.py/README.md) | [**PyInstaller**](https://pyinstaller.org/) 生成本机 APP / DMG 或 EXE / ZIP；构建前确认。 |
| [产物快捷方式](./artifact_shortcuts.py/README.md) | 只发布或移除本工具 `dist` 内产物的第一层入口，供构建器导入。 |

## <span id="jobs-toc-heading-3" data-jobs-toc="v2">二、使用与边界 <a href="#前言" style="font-size:17px; color:green;"><b>🔼</b></a> <a href="#🔚" style="font-size:17px; color:green;"><b>🔽</b></a></span><!-- jobs-toc:heading-end -->

从本 README 所在目录执行：

```shell
python ./launch.py/launch.py --help
python ./launch.py/launch.py
python ./build.py/build.py --help
```

源码运行需要已安装 [**PySide6**](https://doc.qt.io/qtforpython-6/) 的环境；打包器会验证依赖并仅在确认后安装缺失项。`--help` 不写日志、不清理产物、不启动 GUI。构建日志保存在系统临时目录中的 `JobsSSHKeyMgr-build.log`。

本目录已验证语法、帮助入口和临时目录中的构建保护；已复用现有环境完成 MacOS arm64 APP / DMG 构建并启动；未安装依赖、未生成 Windows EXE。
<a id="🔚" href="#前言" style="font-size:17px; color:green; font-weight:bold;">我是有底线的➤点我回到首页</a>
