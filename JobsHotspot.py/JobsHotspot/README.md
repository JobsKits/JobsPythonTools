# JobsHotspot Python 工程

![Jobs出品，必属精品](https://picsum.photos/1500/400)

<!-- jobs-toc:start -->
<!-- jobs-toc:source {"v":2,"token":"[toc]"} -->
<details>
<summary>📚 目录（点击展开 / 收起）</summary>

- [🔥 前言](#%E5%89%8D%E8%A8%80)
- [一、代码地图](#jobs-toc-heading-2)
- [二、源码运行与可运行测试](#jobs-toc-heading-3)
- [三、依赖与许可](#jobs-toc-heading-4)

</details>
<!-- jobs-toc:end -->

---

## 🔥 <span id="前言">前言</span>

共享 GUI 使用 [**PySide6**](https://doc.qt.io/qtforpython-6/)，平台后端分别调用系统网络能力。本层是唯一 Python 工程，打包入口从外层脚本进入。

## <span id="jobs-toc-heading-2" data-jobs-toc="v2">一、代码地图 <a href="#前言" style="font-size:17px; color:green;"><b>🔼</b></a> <a href="#🔚" style="font-size:17px; color:green;"><b>🔽</b></a></span><!-- jobs-toc:heading-end -->

| 模块 | 职责 |
| --- | --- |
| `src/jobs_hotspot/app.py` | 应用启动、显式演示、资源冒烟及命令行诊断 |
| `src/jobs_hotspot/ui.py` | 主界面、工作线程、主题、托盘与退出流程 |
| `src/jobs_hotspot/i18n.py` | 十种完整界面语言 |
| `src/jobs_hotspot/core.py` | 凭据边界及接口速率计算 |
| `src/jobs_hotspot/controls.py` | 右上角语言／主题图文菜单与本地图标渲染 |
| `src/jobs_hotspot/models.py` | 网络接口、故障、共享状态与操作结果 |
| `src/jobs_hotspot/backends/macos.py` | MacOS 网卡、路由、流量、系统共享状态与受限开关 |
| `src/jobs_hotspot/backends/windows.py` | Windows 原生移动热点、适配器状态与流量 |
| `src/jobs_hotspot/assets/` | 随包视觉素材、图标及来源说明 |
| `tests/` | 平台原生输出的隔离用例和 GUI／构建安全检查 |
| [scripts](./scripts/README.md) | 源码入口、构建器与快捷方式辅助模块 |

## <span id="jobs-toc-heading-3" data-jobs-toc="v2">二、源码运行与可运行测试 <a href="#前言" style="font-size:17px; color:green;"><b>🔼</b></a> <a href="#🔚" style="font-size:17px; color:green;"><b>🔽</b></a></span><!-- jobs-toc:heading-end -->

在已准备好 PySide6 的 Python 3.11+ 环境中，从本工程目录执行：

```shell
python ./scripts/launch.py/launch.py --help
python ./scripts/launch.py/launch.py --diagnose
python ./scripts/launch.py/launch.py --smoke
python ./scripts/launch.py/launch.py --demo
python ./scripts/launch.py/launch.py
python -m unittest discover -s ./tests -t . -v
```

`--diagnose` 只读取本机网络并输出 JSON，不执行热点开关；`--smoke` 验证 GUI 及本地资源后退出；`--demo` 为可交互离线演示，禁止真实网络写操作。源码运行不要求安装本包；入口按自身位置导入源码，当前目录不会成为运行依赖。安装本包后也可通过 `jobs-hotspot` 或 `python -m jobs_hotspot` 启动。

无显示器的自动化环境可用 `QT_QPA_PLATFORM=offscreen` 运行 smoke；测试原生热点仍需真实硬件和交互授权，不能以离屏渲染替代。

## <span id="jobs-toc-heading-4" data-jobs-toc="v2">三、依赖与许可 <a href="#前言" style="font-size:17px; color:green;"><b>🔼</b></a> <a href="#🔚" style="font-size:17px; color:green;"><b>🔽</b></a></span><!-- jobs-toc:heading-end -->

[打包器说明](./scripts/build.py/README.md)列明依赖检查、安装确认、清理范围和输出。常规运行需要 PySide6 6.8 至 7 之前；构建另需 PyInstaller 6.22 至 7 之前，当前版本按实际构建记录核对。

Qt/PySide6 使用其 [开源／商业许可](https://doc.qt.io/qtforpython-6/licenses.html)，分发须保留包内许可并按所选许可履行义务；PyInstaller 具有[分发例外](https://pyinstaller.org/en/stable/license.html)。图像、图标与藏文字体已随包提供，[来源与许可](./src/jobs_hotspot/assets/README.md)由资源目录统一维护。

<a id="🔚" href="#前言" style="font-size:17px; color:green; font-weight:bold;">我是有底线的➤点我回到首页</a>
