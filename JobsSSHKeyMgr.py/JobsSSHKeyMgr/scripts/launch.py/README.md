# `launch.py`

![Jobs出品，必属精品](https://picsum.photos/1500/400)

<!-- jobs-toc:start -->
<!-- jobs-toc:source {"v":2,"token":"[toc]"} -->
<details>
<summary>📚 目录（点击展开 / 收起）</summary>

- [🔥 前言](#%E5%89%8D%E8%A8%80)
- [一、运行方式](#jobs-toc-heading-2)
- [二、副作用与验证](#jobs-toc-heading-3)

</details>
<!-- jobs-toc:end -->

---

## 🔥 <span id="前言">前言</span>

个人 SSH 密钥 GUI 的源码与冻结应用共用入口。项目内代码按脚本自身位置加载；冻结应用使用包内模块，不回退到开发机源码。

## <span id="jobs-toc-heading-2" data-jobs-toc="v2">一、运行方式 <a href="#前言" style="font-size:17px; color:green;"><b>🔼</b></a> <a href="#🔚" style="font-size:17px; color:green;"><b>🔽</b></a></span><!-- jobs-toc:heading-end -->

使用已具备 [**Python**](https://www.python.org/) 3.11+ 与 [**PySide6**](https://doc.qt.io/qtforpython-6/) 的环境：

```shell
python ./launch.py --help
python ./launch.py
```

`--help` 仅展示说明；正常运行进入 GUI。此入口不安装或升级依赖，GUI 生成按钮才启动密钥配置业务。其它参数会报错退出。

## <span id="jobs-toc-heading-3" data-jobs-toc="v2">二、副作用与验证 <a href="#前言" style="font-size:17px; color:green;"><b>🔼</b></a> <a href="#🔚" style="font-size:17px; color:green;"><b>🔽</b></a></span><!-- jobs-toc:heading-end -->

启动后可编辑邮箱、算法、语言与主题；生成按钮的 SSH、agent、剪贴板及远端公钥行为见[工具总说明](../../../README.md)。日志与用户配置按目标系统的运行环境定位。

已检查语法和帮助页；启动与业务测试由 GUI 工程验收记录说明。

<!-- jobs-language-terminal-style-v1 -->

**终端配色保护：** `launch.py` 直接运行时，在可可靠保存与恢复配色的交互终端中临时使用黑底白字和统一强调色；正常退出、失败及可捕获中断后恢复进入前的配色，保留原业务清理和退出状态。导入本文件不接管终端；无法可靠保护、纯文本模式或无交互终端时按纯文本约定降级。运行中另行修改的颜色会保留并报告冲突，强制终止后可按运行提示使用独立恢复入口。 模块启动等无法安全重复初始化的场景不重启原程序。

<a id="🔚" href="#前言" style="font-size:17px; color:green; font-weight:bold;">我是有底线的➤点我回到首页</a>
