# JobsHotspot 隔离测试与实机检查

![Jobs出品，必属精品](https://picsum.photos/1500/400)

<!-- jobs-toc:start -->
<!-- jobs-toc:source {"v":2,"token":"[toc]"} -->
<details>
<summary>📚 目录（点击展开 / 收起）</summary>

- [🔥 前言](#%E5%89%8D%E8%A8%80)
- [一、运行方式](#jobs-toc-heading-2)
- [二、证据范围](#jobs-toc-heading-3)

</details>
<!-- jobs-toc:end -->

---

## 🔥 <span id="前言">前言</span>

本目录保存跨端后端解析、操作失败、GUI 和构建保护的可运行检查。隔离用例使用假的系统输出及临时目录，不启动或停止本机真实热点。

## <span id="jobs-toc-heading-2" data-jobs-toc="v2">一、运行方式 <a href="#前言" style="font-size:17px; color:green;"><b>🔼</b></a> <a href="#🔚" style="font-size:17px; color:green;"><b>🔽</b></a></span><!-- jobs-toc:heading-end -->

从 Python 工程目录，在具备 PySide6 的 Python 3.11+ 环境中执行：

```shell
python -m unittest discover -s ./tests -t . -v
python ./scripts/launch.py/launch.py --smoke
python ./scripts/launch.py/launch.py --diagnose
```

无显示器环境使用 `QT_QPA_PLATFORM=offscreen` 运行 GUI 冒烟。具体用例错误直接输出到当前终端，失败退出码为非零；复制命令及首个失败堆栈后按被测模块排查。测试不会安装依赖或修改系统策略。

## <span id="jobs-toc-heading-3" data-jobs-toc="v2">二、证据范围 <a href="#前言" style="font-size:17px; color:green;"><b>🔼</b></a> <a href="#🔚" style="font-size:17px; color:green;"><b>🔽</b></a></span><!-- jobs-toc:heading-end -->

构建保护在临时工程中验证固定清理范围、链接改向、取消、缺资源、成品冒烟失败及快捷入口冲突。平台用例只证明给定输出的状态处理，不能替代真实驱动和系统授权。离线演示不会改变系统热点。

真实热点启停、手机／其它客户端连接上网、拔线恢复、休眠唤醒、系统托盘、跨机分发和另一 CPU 架构按 [验收用例](../../需求/项目需求与开发评审/README.md#acceptance)分别在目标机器执行。未连接相应硬件、没有执行或被系统权限阻塞时，记录未执行／阻塞，不计为通过。

<a id="🔚" href="#前言" style="font-size:17px; color:green; font-weight:bold;">我是有底线的➤点我回到首页</a>
