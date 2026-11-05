"""只读发现已保存的个人 SSH 公钥。Created by Jobs on 2026年11月5日，星期四."""
from __future__ import annotations

import hashlib
import os
from pathlib import Path
import re
import stat

from .core import BEGIN, END, PUBLIC_KEY, SetupResult


# 同时识别 GUI 的摘要后缀、MacOS CLI 的 cksum 后缀与 Windows CLI 的摘要后缀。
_PERSONAL_NAME = re.compile(
    r'id_(?:ed25519|rsa)_personal(?:_(?:[0-9a-f]{10}_(?:[1-9][0-9]?|100)'
    r'|[0-9]{1,10}_(?:[1-9][0-9]?|100)|[0-9a-f]{12}(?:_[1-9][0-9]*)?))?')
_IDENTITY = re.compile(r'''\s*IdentityFile(?:\s+|\s*=\s*)(?:"([^"\r\n]+)"|'([^'\r\n]+)'|([^\s#]+))\s*(?:#.*)?''', re.IGNORECASE)
_REPARSE_POINT = getattr(stat, 'FILE_ATTRIBUTE_REPARSE_POINT', 0x400)


def _metadata(path, directory=False):
    try:
        info = path.lstat()
    except OSError:
        return None
    if (stat.S_ISLNK(info.st_mode)
            or getattr(info, 'st_file_attributes', 0) & _REPARSE_POINT
            or not (stat.S_ISDIR(info.st_mode) if directory else stat.S_ISREG(info.st_mode))):
        return None
    return info


def _read_text(path, limit):
    info = _metadata(path)
    if info is None or info.st_size > limit:
        return None
    try:
        flags = os.O_RDONLY | getattr(os, 'O_BINARY', 0) | getattr(os, 'O_NOFOLLOW', 0)
        descriptor = os.open(path, flags)
        with os.fdopen(descriptor, 'rb') as stream:
            opened = os.fstat(stream.fileno())
            if ((opened.st_dev, opened.st_ino) != (info.st_dev, info.st_ino)
                    or not stat.S_ISREG(opened.st_mode)
                    or getattr(opened, 'st_file_attributes', 0) & _REPARSE_POINT
                    or opened.st_size > limit):
                return None
            data = stream.read(limit + 1)
        current = _metadata(path)
        if (current is None or (current.st_dev, current.st_ino) != (info.st_dev, info.st_ino)
                or len(data) > limit):
            return None
        return data.decode('utf-8')
    except (OSError, UnicodeError):
        return None


def _configured_names(folder):
    text = _read_text(folder / 'config', 131072)
    if text is None:
        return []
    lines = text.splitlines()
    begin = [index for index, line in enumerate(lines) if line.strip() == BEGIN]
    end = [index for index, line in enumerate(lines) if line.strip() == END]
    if len(begin) != 1 or len(end) != 1 or begin[0] >= end[0]:
        return []
    names = []
    for line in lines[begin[0] + 1:end[0]]:
        match = _IDENTITY.fullmatch(line)
        if match is None:
            continue
        value = next(part for part in match.groups() if part is not None).replace('\\', '/')
        name = value.rsplit('/', 1)[-1]
        if not _PERSONAL_NAME.fullmatch(name):
            continue
        allowed = ('~/.ssh/' + name, (folder / name).as_posix())
        if os.path.normcase(value) in {os.path.normcase(path) for path in allowed}:
            names.append(name)
    return names


def find_existing_public_key(*, home=None, preferred_name='', algorithm='ed25519', email='') -> SetupResult | None:
    """按配置、上次选择和工具文件名寻找公钥；不读取私钥正文或执行外部命令。"""
    folder = Path(os.path.abspath(os.fspath(Path.home() if home is None else home))) / '.ssh'
    original = _metadata(folder, directory=True)
    if original is None:
        return None
    names = _configured_names(folder)
    if isinstance(preferred_name, str) and _PERSONAL_NAME.fullmatch(preferred_name):
        names.append(preferred_name)
    selected = 'rsa' if algorithm == 'rsa' else 'ed25519'
    other = 'ed25519' if selected == 'rsa' else 'rsa'
    names.extend((f'id_{selected}_personal', f'id_{other}_personal'))
    try:
        suffixes = [path.name[:-4] for path in folder.iterdir()
                    if path.name.endswith('.pub') and _PERSONAL_NAME.fullmatch(path.name[:-4])
                    and path.name[:-4] not in names]
    except OSError:
        suffixes = []
    digest = hashlib.sha256(email.casefold().encode()).hexdigest()[:10] if email else ''
    suffixes.sort(key=lambda name: (not name.startswith(f'id_{selected}_personal_'),
                                   not bool(digest and f'_{digest}_' in name), name))
    for name in dict.fromkeys([*names, *suffixes]):
        key = folder / name
        if _metadata(key) is None:
            continue
        content = _read_text(folder / (name + '.pub'), 32768)
        current = _metadata(folder, directory=True)
        if (current is None
                or (current.st_dev, current.st_ino) != (original.st_dev, original.st_ino)):
            return None
        if content is not None and PUBLIC_KEY.fullmatch(content):
            return SetupResult(key, content.strip(), False)
    return None
