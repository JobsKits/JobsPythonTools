# build.py · 双端原生打包

![Jobs出品，必属精品](https://picsum.photos/1500/400)

[toc]

---

## 🔥 <span id="前言">前言</span>

使用 [**PyInstaller**](https://pyinstaller.org/) 在当前操作系统生成独立 APP／DMG 或 EXE 完整目录／ZIP。只读帮助不检查环境、不联网、不清理产物。

## 一、运行与依赖 <a href="#前言" style="font-size:17px; color:green;"><b>🔼</b></a> <a href="#🔚" style="font-size:17px; color:green;"><b>🔽</b></a>

```shell
python ./build.py --help
python ./build.py
python ./build.py --prepared
```

Python 3.11+、PySide6 6.8 至 7 之前、PyInstaller 6.22 至 7 之前。MacOS 使用系统 `hdiutil`／`open`，Windows 使用系统 PowerShell／Explorer。`--prepared` 只复检当前解释器全部依赖并禁止安装，仍然保留打包前确认。

健康当前解释器优先复用；否则使用工程外的当前用户构建缓存，按 Python 次版本和 CPU 架构分开，目录结构为 `JobsPythonTools/BuildEnvironments/JobsHotspot-py版本-架构`。MacOS 位于当前用户 Library/Caches，Windows 位于当前用户 LocalAppData。源码目录不夹带公共环境。必要依赖缺失时，打印软件源及目标位置，再“直接回车安装；输入任意字符后回车取消”；空格也取消，EOF／非交互输入停止。安装失败或复检仍不健康立即停止。坏环境完整改名保留，未登记为虚拟环境的既有目录不会被覆盖。

## 二、自述、清理与输出 <a href="#前言" style="font-size:17px; color:green;"><b>🔼</b></a> <a href="#🔚" style="font-size:17px; color:green;"><b>🔽</b></a>

首次实际构建先显示范围并等待回车。依赖、资源和原生系统工具检查完成后，只清理本工具外层固定 `dist`；拒绝符号链接改向、工程根目录、外部目录及非目录目标。清理失败停止；旧快捷入口仅在明确属于本工具 dist 时移除。不会清理源码、用户网络配置、其它工具或真实数据。

产物保存至外层 `dist/YYYY.MM.DD HH-mm-ss/`；同次构建只取一次时间，APP／DMG 或 EXE／ZIP 共用目录。构建工作文件位于外层 `work/`，日志为系统临时目录中的 `JobsHotspot-build.log`。所有入口、spec 和资源以脚本位置解析，支持从其它当前目录运行。

## 三、成品校验、资源与成功行为 <a href="#前言" style="font-size:17px; color:green;"><b>🔼</b></a> <a href="#🔚" style="font-size:17px; color:green;"><b>🔽</b></a>

打包清单包含 Python、PySide6、两端后端及 `src/jobs_hotspot/assets` 的全部本地图片、图标与许可说明。平台图标分别为 `app.icns`、`app.ico`；缺失时在清理旧产物前停止。冻结入口为 `../launch.py/launch.py`，成品不依赖构建机源码，也不会自动移除系统隔离属性。

成品执行 `--smoke`，在离屏 GUI 中验证启动和资源，失败／45 秒超时不发布快捷入口。随后检查 DMG／ZIP 完整性，写入 `build-info.json` 的系统、架构、Python／Qt／PyInstaller 实际版本、分发包 SHA-256 和签名边界。MacOS 为本地／临时签名，未做 Developer ID 公证；Windows 未做 Authenticode 签名。此步骤不会测试或修改真实热点。

成功后在外层建立 MacOS 相对 APP／DMG 链接或 Windows EXE／ZIP `.lnk`；拒绝覆盖同名真实文件或无关快捷方式。最后打开本次产物目录，再启动本次 APP／EXE；成功结尾不等待回车。失败不启动旧包。

## 四、验证范围 <a href="#前言" style="font-size:17px; color:green;"><b>🔼</b></a> <a href="#🔚" style="font-size:17px; color:green;"><b>🔽</b></a>

当前任务执行语法、取消、固定删除边界、符号链接保护、产物快捷方式及 spec 输入解析的隔离用例。原生打包与 GUI 冒烟结果由实际构建记录提供；Windows、其它 CPU 架构、跨机分发及真实热点客户端传输分别验收，不以源码单元检查代替。

<a id="🔚" href="#前言" style="font-size:17px; color:green; font-weight:bold;">我是有底线的➤点我回到首页</a>
