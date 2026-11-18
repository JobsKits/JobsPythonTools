# `windows_etw_smoke.py`

![Jobs出品，必属精品](https://picsum.photos/1500/400)

<!-- jobs-toc:start -->
<!-- jobs-toc:source {"v":2,"token":"[toc]"} -->
<details>
<summary>📚 目录（点击展开 / 收起）</summary>

- [🔥 前言](#%E5%89%8D%E8%A8%80)
- [一、运行与调用](#jobs-toc-heading-2)
- [二、路径与验证](#jobs-toc-heading-3)

</details>
<!-- jobs-toc:end -->

---

## 🔥 <span id="前言">前言</span>

Windows ETW 原生烟雾测试；会实际使用本机采集能力，应在已授权的 Windows 管理员会话执行。

## <span id="jobs-toc-heading-2" data-jobs-toc="v2">一、运行与调用 <a href="#前言" style="font-size:17px; color:green;"><b>🔼</b></a> <a href="#🔚" style="font-size:17px; color:green;"><b>🔽</b></a></span><!-- jobs-toc:heading-end -->

从本 README 所在目录执行：

```shell
python "./windows_etw_smoke.py"
```

不是纯语法检查，不应在未知权限或未授权环境自动运行；原有平台和权限检查保持。

## <span id="jobs-toc-heading-3" data-jobs-toc="v2">二、路径与验证 <a href="#前言" style="font-size:17px; color:green;"><b>🔼</b></a> <a href="#🔚" style="font-size:17px; color:green;"><b>🔽</b></a></span><!-- jobs-toc:heading-end -->

脚本采用同名目录包装，项目位置从源码实际位置定位；完整项目复制、改名后仍需保留相对结构。配套源码、测试或构建资源不能只复制本脚本后假定齐全。Python 版本、依赖与平台限制见上级工具说明；本文件不添加新的分发运行时。

语法与发现检查只证明对应调用范围；真实构建、外部依赖安装、权限、设备和图形界面由各工具的实际验证另行记录。失败应保留原错误及日志，不从旧产物或零用例推断成功。

<a id="🔚" href="#前言" style="font-size:17px; color:green; font-weight:bold;">我是有底线的➤点我回到首页</a>
