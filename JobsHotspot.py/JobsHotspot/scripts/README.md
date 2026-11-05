# JobsHotspot 构建与运行入口

![Jobs出品，必属精品](https://picsum.photos/1500/400)

[toc]

---

## 🔥 <span id="前言">前言</span>

仅保存当前工程的运行、构建及产物入口辅助代码，业务逻辑位于 Python 包。

## 一、入口与职责 <a href="#前言" style="font-size:17px; color:green;"><b>🔼</b></a> <a href="#🔚" style="font-size:17px; color:green;"><b>🔽</b></a>

| 脚本包 | 用途与说明 |
| --- | --- |
| [launch.py](./launch.py/README.md) | 按自身位置加载源码或直接进入冻结应用 |
| [build.py](./build.py/README.md) | 依赖检查、受限清理、原生打包、成品校验及启动 |
| [artifact_shortcuts.py](./artifact_shortcuts.py/README.md) | 仅操作本工具固定 dist 内已验证成品的快捷入口 |

直接执行构建器与外层包装入口遵从同一套防误触确认；单独导入辅助模块不执行打包或修改系统热点。

<a id="🔚" href="#前言" style="font-size:17px; color:green; font-weight:bold;">我是有底线的➤点我回到首页</a>
