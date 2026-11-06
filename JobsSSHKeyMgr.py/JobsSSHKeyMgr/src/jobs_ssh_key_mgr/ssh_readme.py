"""SSH 目录的首次使用说明。Created by Jobs on 2026年11月5日，星期四."""
from pathlib import Path


def directory_readme(key: Path) -> str:
    """只描述文件用途和文件名，不读取密钥正文。"""
    return f'''# 🔑SSH 密钥目录说明

![Jobs出品，必属精品](https://picsum.photos/1500/400)

[toc]

---

## 🔥 <span id="前言">前言</span>

> 本目录供 [**OpenSSH**](https://www.openssh.com/) 保存当前用户的连接配置、个人密钥和远端主机身份记录。Jobs GitHub SSH 配置辅助工具仅在 `README.md` 不存在时生成本说明；已有说明不会覆盖、追加或更新。

首次生成本说明时使用的私钥文件为 `{key.name}`，对应公钥为 `{key.name}.pub`。后续切换算法或账号时，请以工具执行结果和 `config` 中的 `IdentityFile` 为准。

## 一、<span id="files">各个文件的作用</span> <a href="#前言" style="font-size:17px; color:green;"><b>🔼</b></a> <a href="#🔚" style="font-size:17px; color:green;"><b>🔽</b></a>

| 文件 | 用途 | 使用方式 |
| --- | --- | --- |
| `config` | 当前用户的 SSH 客户端配置，按 `Host` 指定服务器、登录用户及 `IdentityFile` 私钥路径。 | 连接 GitHub 时由 SSH 读取；它不是密钥，不需要上传到 GitHub。 |
| `id_ed25519_personal` | ED25519 个人私钥，用于向服务器证明本机持有对应身份。 | 只保存在本人可信设备上，不上传 GitHub、不粘贴到网页或聊天，也不提交到仓库。 |
| `id_ed25519_personal.pub` | 上述私钥对应的公钥，`.pub` 表示公钥文件。 | 将完整公钥添加到正确 GitHub 账号的 SSH 公钥设置页；复制时保留整行内容。 |
| `known_hosts` | 保存远端服务器的主机公钥，供 SSH 校验服务器身份，防止连接到冒充的主机。 | 它用于确认服务器身份，与个人账户公钥用途不同；不需要上传到 GitHub 公钥设置页。 |

选择 RSA 4096 时，个人密钥文件通常为 `id_rsa_personal` 与 `id_rsa_personal.pub`；已有同名文件时，工具会保留原文件并按实际情况使用带后缀的新文件名。上表介绍的是常见文件，是否存在以当前目录为准。

## 二、<span id="usage">配置后的操作</span> <a href="#前言" style="font-size:17px; color:green;"><b>🔼</b></a> <a href="#🔚" style="font-size:17px; color:green;"><b>🔽</b></a>

- 在工具中复制当前公钥，并打开 [GitHub 添加 SSH 公钥页面](https://github.com/settings/ssh/new)，确认登录账号后添加；已有正确授权时工具会尝试自动登记。
- 登记完成后点击“测试 SSH 连接”，核对认证是否成功，以及返回的 GitHub 用户名是否正确；成功后工具会自动补齐 `<用户名>-GitHub` 与 `<用户名>-GitHub.pub` 识别入口，供 Sourcetree 使用同一把密钥。重新打开 Sourcetree 的账户编辑窗口，用户名填写该认证账号。本地生成密钥并不代表 GitHub 已接受该公钥。
- 私钥与公钥必须配对；仅有 `.pub` 不能替代私钥完成认证。不要为了排查提示而随意删除私钥或已有的主机身份记录。

文件格式与用途参见 [OpenSSH 文件说明](https://man.openbsd.org/ssh#FILES)及 [SSH 客户端配置说明](https://man.openbsd.org/ssh_config)。

<a id="🔚" href="#前言" style="font-size:17px; color:green; font-weight:bold;">我是有底线的➤点我回到首页</a>
'''
