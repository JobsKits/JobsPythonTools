# 本地视觉资源

本目录随应用离线打包。先查询 [iconfont](https://www.iconfont.cn/collections/detail?cid=54209)，可读取的候选未提供足够的逐项授权信息，采用 [Google Material Icons 官方仓库](https://github.com/google/material-design-icons/tree/10ecc14790612ca8fd164e3f4ffe9c16fc50d5b7)的 Outlined 图标，许可为 [Apache 2.0](./LICENSE)。语言与主题图标复用相邻 JobsSSHKeyMgr 工程已核验的官方原文件。

| 文件 | 固定提交下的上游路径 |
| --- | --- |
| `translate.svg` | `src/action/translate/materialiconsoutlined/24px.svg` |
| `light_mode.svg`, `dark_mode.svg` | `src/device/<名称>/materialiconsoutlined/24px.svg` |
| `computer.svg` | `src/hardware/computer/materialiconsoutlined/24px.svg` |
| `wifi.svg` | `src/notification/wifi/materialiconsoutlined/24px.svg` |
| `power_settings_new.svg`, `settings_ethernet.svg` | `src/action/<名称>/materialiconsoutlined/24px.svg` |
| `portable_wifi_off.svg` | `src/communication/portable_wifi_off/materialiconsoutlined/24px.svg` |
| `error_outline.svg` | `src/alert/error_outline/materialiconsoutlined/24px.svg` |
| `refresh.svg` | `src/navigation/refresh/materialiconsoutlined/24px.svg` |

SVG 保留上游字节，运行时在内存着色。圆形开关由 Qt 绘制背景并叠加上述不同状态图标；无文字图层，保留键盘焦点、辅助名称和提示。`icon.png`、`app.icns`、`app.ico` 是上述 Wi-Fi 图标与 Jobs 绘制圆形背景的组合衍生图，原路径授权不变。

藏文字体 [Noto Serif Tibetan](https://github.com/google/fonts/tree/main/ofl/notoseriftibetan) 来源 Google Fonts 官方仓库，按 [SIL Open Font License](./OFL-Tibetan.txt)随包分发，解决目标机未安装藏文字体时的显示问题。运行时不联网下载视觉资源。
