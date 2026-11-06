# 🔑Jobs GitHub SSH 配置辅助工具

![Jobs出品，必属精品](https://picsum.photos/1500/400)

<!-- jobs-toc:start -->
<!-- jobs-toc:source {"v":2,"token":"[toc]"} -->
<details>
<summary>📚 目录（点击展开 / 收起）</summary>

- [🔥 前言](#%E5%89%8D%E8%A8%80)
- [一、功能与交互](#features)
- [二、源码运行](#run)
- [三、密钥与配置行为](#security)
- [四、目录与打包](#layout)
- [五、日志、验证与限制](#validation)

</details>
<!-- jobs-toc:end -->

---

## 🔥 <span id="前言">前言</span>

> 使用 [**Python**](https://www.python.org/) 与 [**PySide6**](https://doc.qt.io/qtforpython-6/) 编写的双端图形工具。输入绑定邮箱，选择算法后自动生成或复用个人密钥、配置 SSH、加载 agent，并尝试登记与验证 GitHub 公钥。

本目录放图形工具；`JobsCommand@Gits` 中的 MacOS / WindowsOS 入口继续用于终端命令行。图形工具自包含业务实现，可单独复制，不依赖另一个仓库的位置。

- Windows 最低目标为 Windows 10 64 位、Python 3.11+；系统最低 build 尚未锁定，Windows 桌面与成品打包待实机验证。
- MacOS 使用 Python 3.11+；实际系统与架构要求取决于所安装 PySide6 6.8+ 的官方运行库。MacOS 源码界面和隔离回归已验，已在本机构建并启动 arm64 APP，DMG 校验通过；Windows 成品与原生桌面仍待验证。

## 一、<span id="features">功能与交互</span> <a href="#前言" style="font-size:17px; color:green;"><b>🔼</b></a> <a href="#🔚" style="font-size:17px; color:green;"><b>🔽</b></a>

| 入口 | 行为 |
| --- | --- |
| 绑定邮箱 | 可编辑；默认 `295060456@qq.com`，有上次显式保存的邮箱时优先恢复该值，不读取 Git 全局配置；当前值等于默认邮箱时用较淡文字显示，输入其它邮箱恢复正常文字色，真实值始终可编辑。 |
| 密钥算法 | ED25519（推荐）/ RSA 4096；默认 ED25519，保存上次选择。算法说明紧跟下拉框，按字段实际可用宽度自动换行，切换算法或语言立即刷新；放大窗口时由执行结果区承接剩余空间。 |
| 生成并配置 / 重新生成配置 | 按钮独占一行；尚无密钥时显示蓝底白字的“生成并配置”，恢复或生成过密钥后显示红底白字的“重新生成配置”。重新执行前弹窗确认，显示当前邮箱、算法及已有密钥复用规则，默认取消；取消、Esc 或关闭弹窗不修改偏好、不清空公钥、不启动任务。确认后后台完成密钥、目录 README、SSH 配置、agent、公钥登记及连接测试，更新内嵌公钥面板。 |
| 复制公钥 | 位于底部四个辅助按钮的左上角；有有效公钥内容时可用，否则置灰。可反复复制，面板不再重复放置复制按钮。 |
| 测试 SSH 连接 | 位于执行结果标题旁，左侧网络检测图标、右侧完整文字，按当前字体和主题自然撑开高度；取得可用密钥后启用。网页登记公钥后可重测，认证成功会按返回的真实用户名自动补齐 Sourcetree 识别入口；不重新生成密钥、不重写 SSH 连接配置、不上传公钥、不改写 known_hosts。 |
| 打开当前系统密钥文件夹 | 打开当前用户 `.ssh`，不存在时创建此目录。 |
| 打开 GitHub 公钥网页 | 打开 [GitHub 官方添加公钥页面](https://github.com/settings/ssh/new)。 |
| 内嵌公钥面板 | 常驻于执行结果下方；启动时自动读取当前已有个人公钥，恢复路径、完整内容及复制 / 测试入口，不必重新生成。没有可用公钥时显示空态；生成或复用后更新面板。 |
| 打开 GitHub Token 配置网页 | 打开 [GitHub Personal Access Token 设置页](https://github.com/settings/tokens)，与公钥登记页面分别提供按钮。 |
| 语言 | 标题同一行右上角的紧凑图文按钮，图标在左、文字在右；点击打开选项菜单，不显示下拉箭头；简体中文、繁体中文、藏文、英文、日文、法文、西班牙文、德文、俄罗斯文、韩文、跟随系统。 |
| 主题 | 与语言按钮并排放在右上角，以弱化的图文按钮显示；图标随模式变化，点击选择；白天、黑夜、跟随系统，默认跟随系统，保存选择，系统外观改变时刷新。 |

ED25519 是现代算法，密钥更小、签名快，优先推荐使用。RSA 4096 主要兼容不支持 ED25519 的旧系统；4096 位不代表必然比 ED25519 更安全。

主标题以“🔑Jobs GitHub SSH 配置辅助工具”明确服务范围。“生成并配置”单独占满一行；其下四个图文按钮两行两列，第一行“复制公钥 / 打开当前系统密钥文件夹”，第二行“打开 GitHub 公钥网页 / 打开 GitHub Token 配置网页”。所有辅助按钮均左图标、右文字。主界面通过系统窗口关闭控件退出，不提供独立弹窗或额外退出按钮。执行中暂时禁止关闭主窗口及重复生成，结束后恢复。

窗口字段、按钮、验证、过程状态和结果均使用同一语言表，切换语言后已有结果及内嵌公钥面板同步重译。执行日志与公钥内容均为可上下滚动的只读文本区，中间分隔条可调整两块高度；黑夜模式采用纯黑背景 `#000000`、绿色文字 `#00ff00`，白天模式保持浅色主题。日志更新仅在用户已位于底部时跟随新输出，向上翻阅时保留近似滚动位置。外部工具与操作系统原始诊断保留原文。藏文使用系统字体后备：MacOS 的 `Kailasa`、Windows 的 `Microsoft Himalaya` 或已安装的 `Noto Serif Tibetan` / `Noto Sans Tibetan`；缺失时语言控件提供字体提示，不下载来源不明字体。

## 二、<span id="run">源码运行</span> <a href="#前言" style="font-size:17px; color:green;"><b>🔼</b></a> <a href="#🔚" style="font-size:17px; color:green;"><b>🔽</b></a>

> 从本 README 所在目录执行，依赖为 Python 3.11+、PySide6 6.8+，以及系统可用的 OpenSSH。

```shell
python3 './JobsSSHKeyMgr/scripts/launch.py/launch.py'
```

Windows 可用 `py -3` 代替 `python3`。源码启动入口不自行安装依赖；开发环境缺依赖时，可在自己的虚拟环境中安装 `./JobsSSHKeyMgr`。打包入口负责检查构建依赖，缺少必需依赖才按提示确认安装。

邮箱默认值不依赖 Git；可在窗口中直接修改并保存。[**GitHub CLI**](https://cli.github.com/) 为可选依赖，仅用于已授权账户的自动登记；缺少、未登录、令牌失效、邮箱无法验证或公钥权限不足时，本机配置仍可完成，并明确提示远端步骤未完成。

GitHub CLI 登录检测分别显示“未检测到 gh”“gh 已安装但未登录”“登录凭据被拒绝（HTTP 401）”“请求被拒绝（HTTP 403）”“网络连接失败”“检测超时”或“无法确定登录状态”，并给出重新授权或网页添加公钥的下一步。只有找不到可执行文件才提示缺少工具；网络错误或无法解析的输出不视为令牌失效。按[官方登录状态接口](https://cli.github.com/manual/gh_auth_status)读取当前活跃账户的结构化状态，JSON 模式的退出码为零也须检查账户状态；其它已保存账户的错误不会阻止当前有效账户登记。检测失败时停止自动登记，保留本地密钥；状态诊断不回显授权 JSON 或令牌。

## 三、<span id="security">密钥与配置行为</span> <a href="#前言" style="font-size:17px; color:green;"><b>🔼</b></a> <a href="#🔚" style="font-size:17px; color:green;"><b>🔽</b></a>

- 新密钥使用空口令。只复用邮箱、算法及公私钥配对均能验证的个人密钥；不覆盖现有私钥、公钥或其它账户密钥。
- 生成或复用密钥后，在当前用户 `.ssh` 中首次创建中文 `README.md`，说明 `config`、`id_ed25519_personal`、`id_ed25519_personal.pub`、`known_hosts` 及 RSA / 带后缀文件名的用途、公私钥区别和后续登记测试步骤；只写文件名与说明，不写私钥正文。已有 README（包括同名链接或目录）直接跳过，不读取、覆盖、追加或修改；并发创建只保留先完成的一份。README 创建失败会提示并继续密钥配置，独立连接测试不会生成说明。
- 重新打开 GUI 时，优先恢复本工具 SSH 托管配置指向的个人公钥，其次使用上次成功显示的文件名，再查找当前算法的默认个人密钥及其它受支持的个人密钥文件。启动恢复只读取配置与经过格式检查的 `.pub`，私钥仅检查文件属性，不读取正文，不执行 SSH / gh，也不生成 README 或重写 SSH 配置。恢复的公钥可立即复制；认证状态不会从上次沿用，点击“测试 SSH 连接”后再确认。只在偏好设置中保存相对文件名，不缓存公钥正文。
- 新建默认文件名为 `id_ed25519_personal` / `id_rsa_personal`。旧 `id_rsa_personal` 只在匹配当前请求时复用；重名冲突使用邮箱摘要及序号另建文件。
- 备份当前 `.ssh/config` 后，只替换本工具托管块，配置 `github.com` 与 `github-personal` 指向实际私钥；原 Host、全局指令及其它账户 IdentityFile 保留。重复运行不累积托管块或额外空行。原有 `github.com` 身份可作为后续候选，当前个人密钥优先。
- MacOS 优先使用系统 OpenSSH，并复用现有 agent；Windows 尝试复用或启动系统 `ssh-agent` 服务。服务权限不足时不提权、不改变启动类型，结果明确显示未加载，SSH 仍可通过 IdentityFile 使用私钥。
- 自动登记前核验 GitHub CLI 活跃账户的已验证邮箱，匹配才上传公钥；操作固定到 `github.com`，不读取令牌或上传私钥。
- 首次主机信任只从 [GitHub 官方 HTTPS 元数据](https://api.github.com/meta) 获取 `ssh_keys`。已有主机记录保持不变，主机密钥冲突不会自动覆盖。
- 认证测试仅用本次私钥，禁用 agent 的其它身份，设超时、批处理及严格主机检查。[GitHub SSH 成功约定退出码为 1](https://docs.github.com/en/authentication/connecting-to-github-with-ssh/testing-your-ssh-connection)，同时识别认证成功消息及账号。
- “生成并配置”自动测试成功，或网页登记公钥后点击“测试 SSH 连接”认证成功，都会按服务端返回的实际 GitHub 用户名建立 `<用户名>-GitHub` 与 `<用户名>-GitHub.pub` 兼容别名，供 Sourcetree 按账户用户名探测。MacOS 使用同目录相对符号链接，Windows 使用同目录硬链接，不复制私钥正文；不会根据邮箱猜用户名，也不修改 Sourcetree 账户或读取其令牌。Sourcetree 中填写的账户用户名须与认证结果一致，配置后重新打开账户编辑窗口刷新探测。已有正确链接重复运行直接复用；已有不同文件或 Windows 重解析点保留并提示，别名创建失败不会改变 SSH 已认证成功的结果。
- 内嵌公钥面板只显示经过格式检查的 `.pub` 内容，绝不显示私钥正文；文本可选择，长公钥可滚动查看，复制按钮始终复制完整内容。只有点击底部“复制公钥”才改写剪贴板，复制不弹出对话框或抢焦点。开始下一轮生成时清除面板中的旧公钥并禁用复制，防止使用过期数据；本轮密钥已生成或复用但后续配置失败时，仍在面板中保留该公钥供复制。结果显示私钥文件路径、公钥路径和日志位置。打开网页、复制公钥或本机配置成功都不代表 GitHub 登记成功；须看认证结果。[**Sourcetree**](https://www.sourcetreeapp.com/) 的账户图标不能替代实际 SSH 认证检查。本工具不改仓库远端地址，也不覆盖默认密钥或已有账户密钥来消除图标。

## 四、<span id="layout">目录与打包</span> <a href="#前言" style="font-size:17px; color:green;"><b>🔼</b></a> <a href="#🔚" style="font-size:17px; color:green;"><b>🔽</b></a>

```text
JobsSSHKeyMgr.py/
├── README.md
├── 【MacOS】📦生成dmg.command/
├── 【Windows】📦生成exe.bat/
└── JobsSSHKeyMgr/
    ├── pyproject.toml
    ├── src/jobs_ssh_key_mgr/
    ├── tests/
    └── scripts/
```

- [MacOS APP / DMG 打包入口](<./【MacOS】📦生成dmg.command/README.md>)。
- [Windows EXE / ZIP 打包入口](<./【Windows】📦生成exe.bat/README.md>)。
- [源码启动、构建及快捷方式脚本说明](./JobsSSHKeyMgr/scripts/README.md)。
- [本地图标来源与 Apache 2.0 授权](./JobsSSHKeyMgr/src/jobs_ssh_key_mgr/assets/preferences/README.md)：设置按钮、四个辅助按钮与连接测试按钮使用随包 SVG；运行时不下载图标。

构建清理只限本应用固定 `dist`，输出 `dist/YYYY.MM.DD HH-mm-ss/`；成功后更新第一层快捷入口，打开产物目录并启动本次程序。MacOS / Windows 分别在本机打包，不交叉编译。成品携带 Python / Qt 运行库；OpenSSH 为目标系统原生依赖，Git 与 GitHub CLI 按上述可选边界使用。

## 五、<span id="validation">日志、验证与限制</span> <a href="#前言" style="font-size:17px; color:green;"><b>🔼</b></a> <a href="#🔚" style="font-size:17px; color:green;"><b>🔽</b></a>

日志为系统临时目录中的 `JobsSSHKeyMgr.log`，保存消息标识、时间和诊断，窗口结果另显示实际位置；不保存私钥、密码、Cookie 或令牌。用户语言、主题、邮箱和算法使用系统 QSettings 位置保存，不写回源码；为兼容已有偏好，继续沿用 `Jobs / SSHKeyManager` 设置域，不删除用户数据。

```shell
PYTHONPATH='./JobsSSHKeyMgr/src' QT_QPA_PLATFORM=offscreen python3 -m unittest discover -s './JobsSSHKeyMgr/tests' -v
```

已覆盖密钥冲突保护、复用、配置备份及幂等、GitHub 邮箱与上传主机检查、仅本次密钥认证、十语言结果切换、底部四按钮两列布局、默认邮箱弱色与编辑恢复、主题跟随及偏好恢复；常驻公钥面板的空态、反复显式复制、语言 / 主题联动、黑底绿字及滚动位置、配置失败回传公钥，以及私钥格式拒显均有隔离回归；推荐标记与算法说明切换、Token 网页实际地址、无箭头图文菜单和公钥路径栏字体高度也通过验证；SSH 验证内核覆盖只读约束、成功账号、超时和配置失败后的结果保留；测试按钮另覆盖认证成功后自动补齐 Sourcetree 识别别名，以及从空目录首次生成、网页登记后重测、幂等和冲突保留；Sourcetree 别名覆盖 MacOS 相对链接、Windows 硬链接原语、正确指向幂等、冲突 / 重解析点保留及认证失败不关联。隔离回归与成品烟测未改动用户现有私钥、SSH 配置或远端公钥；已从成品内核在临时空目录真实生成 ED25519，使用隔离 GitHub 响应验证首次未登记、登记后重测及 Sourcetree 识别补齐，只生成一次且保留原配置 / 密钥 / README。已构建并启动本机 MacOS arm64 APP，验证 DMG 校验和、APP 签名与 Python 运行库 ZIP 完整性；隔离回归仍不能替代 Windows GUI、原生服务、Windows EXE 及其它机器兼容性验收。

<a id="🔚" href="#前言" style="font-size:17px; color:green; font-weight:bold;">我是有底线的➤点我回到首页</a>
