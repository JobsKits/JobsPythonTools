# launch.py · 源码与冻结入口

![Jobs出品，必属精品](https://picsum.photos/1500/400)

[toc]

---

## 🔥 <span id="前言">前言</span>

本入口由开发命令或打包程序调用，转交 `jobs_hotspot.app.main`，本身不安装依赖、不清理产物、不保存网络凭据。

## 一、运行与依赖 <a href="#前言" style="font-size:17px; color:green;"><b>🔼</b></a> <a href="#🔚" style="font-size:17px; color:green;"><b>🔽</b></a>

```shell
python ./launch.py --help
python ./launch.py --diagnose
python ./launch.py --smoke
python ./launch.py --demo
python ./launch.py
```

源码运行依赖 Python 3.11+ 与 PySide6；正常 GUI 只读取状态，用户点击分享开关才请求系统写操作。`--demo` 永不执行真实共享写操作。冻结时按包内路径导入，不回退到开发机源码。诊断信息输出至当前终端；系统控制失败在界面显示。

<a id="🔚" href="#前言" style="font-size:17px; color:green; font-weight:bold;">我是有底线的➤点我回到首页</a>
