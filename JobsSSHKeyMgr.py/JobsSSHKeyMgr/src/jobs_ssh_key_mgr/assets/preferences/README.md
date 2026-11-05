# 界面按钮图标

![Jobs出品，必属精品](https://picsum.photos/1500/400)

[toc]

---

## 🔥 <span id="前言">前言</span>

> 本目录保存语言、主题、连接测试与底部操作按钮使用的本地图标。八枚图标均来自 [**Google Material Icons**](https://github.com/google/material-design-icons) 的 Outlined 系列，保留官方原始 SVG 字节，运行时无需联网。

## 一、<span id="files">文件与来源</span> <a href="#前言" style="font-size:17px; color:green;"><b>🔼</b></a> <a href="#🔚" style="font-size:17px; color:green;"><b>🔽</b></a>

> 统一画布为 `24 × 24`，固定上游提交 `10ecc14790612ca8fd164e3f4ffe9c16fc50d5b7`，避免分支更新改变同一来源地址的内容。

| 本地文件 | 界面用途 | 官方原文件 |
| --- | --- | --- |
| [translate.svg](./translate.svg) | 语言切换 | [action/translate/materialiconsoutlined/24px.svg](https://github.com/google/material-design-icons/blob/10ecc14790612ca8fd164e3f4ffe9c16fc50d5b7/src/action/translate/materialiconsoutlined/24px.svg) |
| [light_mode.svg](./light_mode.svg) | 白天主题 | [device/light_mode/materialiconsoutlined/24px.svg](https://github.com/google/material-design-icons/blob/10ecc14790612ca8fd164e3f4ffe9c16fc50d5b7/src/device/light_mode/materialiconsoutlined/24px.svg) |
| [dark_mode.svg](./dark_mode.svg) | 黑夜主题 | [device/dark_mode/materialiconsoutlined/24px.svg](https://github.com/google/material-design-icons/blob/10ecc14790612ca8fd164e3f4ffe9c16fc50d5b7/src/device/dark_mode/materialiconsoutlined/24px.svg) |
| [computer.svg](./computer.svg) | 跟随系统主题 | [hardware/computer/materialiconsoutlined/24px.svg](https://github.com/google/material-design-icons/blob/10ecc14790612ca8fd164e3f4ffe9c16fc50d5b7/src/hardware/computer/materialiconsoutlined/24px.svg) |
| [content_copy.svg](./content_copy.svg) | 复制公钥 | [content/content_copy/materialiconsoutlined/24px.svg](https://github.com/google/material-design-icons/blob/10ecc14790612ca8fd164e3f4ffe9c16fc50d5b7/src/content/content_copy/materialiconsoutlined/24px.svg) |
| [folder_open.svg](./folder_open.svg) | 打开当前 SSH 密钥文件夹 | [file/folder_open/materialiconsoutlined/24px.svg](https://github.com/google/material-design-icons/blob/10ecc14790612ca8fd164e3f4ffe9c16fc50d5b7/src/file/folder_open/materialiconsoutlined/24px.svg) |
| [open_in_new.svg](./open_in_new.svg) | 打开 GitHub 公钥网页与令牌设置网页 | [action/open_in_new/materialiconsoutlined/24px.svg](https://github.com/google/material-design-icons/blob/10ecc14790612ca8fd164e3f4ffe9c16fc50d5b7/src/action/open_in_new/materialiconsoutlined/24px.svg) |
| [network_check.svg](./network_check.svg) | 测试 SSH 连接，网络信号与检测指针造型 | [notification/network_check/materialiconsoutlined/24px.svg](https://github.com/google/material-design-icons/blob/10ecc14790612ca8fd164e3f4ffe9c16fc50d5b7/src/notification/network_check/materialiconsoutlined/24px.svg) |

下载地址与上述固定提交一一对应，主机为 `raw.githubusercontent.com`，路径为 `google/material-design-icons/<提交号>/<官方原文件路径>`。授权原文取自[同一提交的 LICENSE](https://github.com/google/material-design-icons/blob/10ecc14790612ca8fd164e3f4ffe9c16fc50d5b7/LICENSE)，本地副本为 [LICENSE](./LICENSE)。

## 二、<span id="selection">来源选择</span> <a href="#前言" style="font-size:17px; color:green;"><b>🔼</b></a> <a href="#🔚" style="font-size:17px; color:green;"><b>🔽</b></a>

- 已于 2026-11-05 优先查询 [**iconfont**](https://www.iconfont.cn/) 的翻译、主题与电脑图标，并检查[候选图标库页面](https://www.iconfont.cn/collections/detail?cid=51731)。当前可读取的页面未能提供这四枚同风格素材可逐项核验的作者与授权条件，因此本目录没有采用该站素材；这不代表对该站所有素材授权状况作统一判断。
- iconfont [官方用户服务协议](https://terms.alicdn.com/legal-agreement/terms/platform_service/20220704165734807/20220704165734807.html)要求使用素材时遵守具体授权条件。本目录按已确认的素材来源顺序，转用上述 Google 官方仓库中授权明确的一套图标。
- 复制、打开文件夹与打开网页图标沿用同一官方仓库、固定提交与许可证，保证按钮之间的视觉风格与来源一致。
- 连接测试图标同样先查询 iconfont 的“网络检测”素材；可读取的[搜索入口](https://www.iconfont.cn/search/index?searchType=icon&q=%E7%BD%91%E7%BB%9C%E6%A3%80%E6%B5%8B)未提供可逐项核验的素材与授权信息，因此沿用上述官方图标体系的 `network_check`，保持相同画布和轮廓风格。

## 三、<span id="rendering">主题着色与使用</span> <a href="#前言" style="font-size:17px; color:green;"><b>🔼</b></a> <a href="#🔚" style="font-size:17px; color:green;"><b>🔽</b></a>

- 八枚文件都是轮廓造型的单色路径，根 `svg` 未指定 `fill`，可见路径继承默认黑色；透明画布的 `path` 或 `rect` 单独保留 `fill="none"`，没有外链、位图、脚本或字体依赖。
- 按钮以左侧图标、右侧文字排列。按当前主题为渲染结果统一着色，或只在内存中给根 `svg` 设置主题 `fill`；保留子节点的 `fill="none"`，避免把透明画布填成实心方块。不要改写本目录的上游素材文件。
- 从应用包内读取资源并按实际屏幕像素比例渲染；图标尺寸保持正方形，文字仍使用完整的国际化字符串。

## 四、<span id="license-validation">授权与校验</span> <a href="#前言" style="font-size:17px; color:green;"><b>🔼</b></a> <a href="#🔚" style="font-size:17px; color:green;"><b>🔽</b></a>

- 图标采用 [**Apache License 2.0**](https://www.apache.org/licenses/LICENSE-2.0)。分发时保留本目录 [LICENSE](./LICENSE) 及来源说明；若后续修改素材，应按许可证保留所需声明并标明修改。
- 已检查八枚 SVG 的 XML、`viewBox`、可见路径与透明节点结构；资源为官方原文件的逐字节副本。来源校验摘要如下：

  | 文件 | SHA-256 |
  | --- | --- |
  | `translate.svg` | `372d577b72d294609093a420e9bab9d183cc58c63f1c3a3ca98c205f9a0a0700` |
  | `light_mode.svg` | `14663a04fa08793052c5a43cbf5ed0d0f9ca5ca54a780327337aa400d444fea8` |
  | `dark_mode.svg` | `39467d90533e60eedb473848dda3a25b5f17341d0cae19463d09cef9b4f4cd8e` |
  | `computer.svg` | `f7621c691b145c5e2303f9483e2c1e5e4bdf628fea7517ccf2fec724302d4146` |
  | `content_copy.svg` | `a978f7983cb6c8abffb09a1c71081ef2a038003114bccc7a06c1026198b17888` |
  | `folder_open.svg` | `d8f67d1736489be02387aed93d6952bf4f40312899d526ed8d70d91a20ee6b53` |
  | `open_in_new.svg` | `c8117992219bb914a560094f460e0a49c75f4a2ddae5e872b7934e15025c4e5b` |
  | `network_check.svg` | `5aa175bcdd53c46742c9c409c4797b223cd8f0d5b302a7aafaf582e48841b46e` |
  | `LICENSE` | `58d1e17ffe5109a7ae296caafcadfdbe6a7d176f0bc4ab01e12a689b0499d8bd` |

<a id="🔚" href="#前言" style="font-size:17px; color:green; font-weight:bold;">我是有底线的➤点我回到首页</a>
