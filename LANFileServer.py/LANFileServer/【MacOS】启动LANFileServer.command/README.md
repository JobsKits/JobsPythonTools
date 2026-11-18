# `【MacOS】启动LANFileServer.command`

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

LANFileServer 的项目内启动入口，保留日常 GUI 启动及本平台打包模式。

## <span id="jobs-toc-heading-2" data-jobs-toc="v2">一、运行与参数 <a href="#前言" style="font-size:17px; color:green;"><b>🔼</b></a> <a href="#🔚" style="font-size:17px; color:green;"><b>🔽</b></a></span><!-- jobs-toc:heading-end -->

从本 README 所在目录执行：

```shell
./【MacOS】启动LANFileServer.command
```

保留既有一键协议：显示源码内置说明后继续，GUI 启动和打包模式由原参数选择；不是新增一层重复确认。需要准备依赖时使用原有提示与取消方式。

## <span id="jobs-toc-heading-3" data-jobs-toc="v2">二、依赖与产物边界 <a href="#前言" style="font-size:17px; color:green;"><b>🔼</b></a> <a href="#🔚" style="font-size:17px; color:green;"><b>🔽</b></a></span><!-- jobs-toc:heading-end -->

完整工程复制或改名后由脚本实际位置定位项目、requirements、虚拟环境与构建辅助模块。输出层不因增加同名包装目录而改变；环境或构建失败保留日志并停止下游。

Windows 入口仅在 Windows 执行业务；本轮没有运行真实依赖安装或生成 EXE。MacOS 入口完成对应语法检查；路径／隔离夹具与真实 GUI、系统权限、跨机打包分别验收。

必需 Homebrew 的获取沿用本入口已有授权和安装路径选择：系统安装器按已声明官方 URL 轮询；用户目录只获取固定官方 release tag，在本轮私有暂存仓复用已收 Git 对象。临时网络错误持续退避（上限 30 秒），按 Ctrl+C 取消；本地、权限、认证、证书、版本及日志写入确定错误停止。获取成功后安装或业务只执行一次，不重放整个入口；终端显示真实进度，日志保持纯文本。

<a id="🔚" href="#前言" style="font-size:17px; color:green; font-weight:bold;">我是有底线的➤点我回到首页</a>
