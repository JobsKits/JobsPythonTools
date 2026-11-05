# artifact_shortcuts.py · 成品快捷入口

![Jobs出品，必属精品](https://picsum.photos/1500/400)

[toc]

---

## 🔥 <span id="前言">前言</span>

由构建器导入调用，不作为用户独立执行脚本。只为本工具外层固定 `dist` 内已校验产物建立第一层入口。

## 一、行为与保护 <a href="#前言" style="font-size:17px; color:green;"><b>🔼</b></a> <a href="#🔚" style="font-size:17px; color:green;"><b>🔽</b></a>

MacOS 建立相对符号链接；Windows 使用系统 PowerShell 与普通用户 COM 建立 `.lnk`，同时记录真实目标和工作目录。清理只移除指向本工具 `dist` 的旧入口，保留真实文件和其它链接；目标缺失、输出改向、路径包含链接或同名无关文件时拒绝发布。

无额外 Python 包依赖，不安装软件；结果写入构建日志并复核目标存在。模块直接运行没有执行入口，不产生修改。

<a id="🔚" href="#前言" style="font-size:17px; color:green; font-weight:bold;">我是有底线的➤点我回到首页</a>
