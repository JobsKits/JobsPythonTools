"""独立用量监控入口；钩子快返路径只加载标准库。Created by Jobs."""
from __future__ import annotations

import argparse
import os
from pathlib import Path
import sys


def _parser():
    parser = argparse.ArgumentParser(description='Jobs Codex Token 上下行监控')
    parser.add_argument('--codex-home', type=Path, help='要监听的 Codex 数据目录（默认 CODEX_HOME 或 ~/.codex）')
    modes = parser.add_mutually_exclusive_group()
    modes.add_argument('--token-widget', action='store_true', help='兼容旧版的浮窗启动参数')
    modes.add_argument('--hook-launch', action='store_true', help='供 SessionStart 钩子使用的后台启动器')
    modes.add_argument('--hook-report', action='store_true', help='供 Stop 钩子使用的同轮统计')
    modes.add_argument('--install-token-hook', action='store_true', help='合并并备份本工具钩子，之后需在 /hooks 审阅')
    modes.add_argument('--remove-token-hook', action='store_true', help='备份后移除本工具钩子')
    return parser


def _prepare_qt_environment():
    # 源码运行可能继承其它打包 Qt 应用的插件路径，不能混载其 Qt。
    if not getattr(sys, 'frozen', False):
        for key in tuple(os.environ):
            if key in ('QT_PLUGIN_PATH', 'QT_QPA_PLATFORM_PLUGIN_PATH') or key.startswith('_PYI_'):
                os.environ.pop(key, None)


def _icon_path():
    if getattr(sys, 'frozen', False):
        return Path(getattr(sys, '_MEIPASS', Path(sys.executable).parent)) / 'assets' / 'icon.png'
    return Path(__file__).resolve().parents[3] / 'icon.png'


def main(argv=None):
    args = _parser().parse_args(argv)
    from .token_hooks import (HOOK_REVIEW_MESSAGE, TokenHookError, install_token_hook,
                              launch_token_widget, resolve_codex_home, uninstall_token_hook)
    home = resolve_codex_home(args.codex_home)
    if args.hook_report:
        from .hook_report import report_from_stdin
        return report_from_stdin(home, sys.stdin)
    try:
        if args.hook_launch:
            launch_token_widget(home)
            return 0
        if args.install_token_hook or args.remove_token_hook:
            operation = install_token_hook if args.install_token_hook else uninstall_token_hook
            result = operation(home)
            print(('已更新' if result.changed else '无需修改') + '：' + str(result.hooks_path))
            if result.backup_path:
                print('原配置备份：' + str(result.backup_path))
            if result.requires_trust_review:
                print(HOOK_REVIEW_MESSAGE)
            return 0
    except TokenHookError as error:
        print(str(error), file=sys.stderr)
        return 1

    _prepare_qt_environment()
    from PySide6.QtCore import QStandardPaths
    from PySide6.QtGui import QIcon
    from PySide6.QtWidgets import QApplication
    from .token_widget import run_token_widget
    app = QApplication.instance() or QApplication([sys.argv[0]])
    app.setOrganizationName('Jobs')
    app.setApplicationName('CodexTokenWidget')
    app.setApplicationDisplayName('Jobs · Codex Token 监控')
    app.setStyle('Fusion')
    icon = _icon_path()
    if icon.is_file():
        app.setWindowIcon(QIcon(str(icon)))
    data_dir = Path(QStandardPaths.writableLocation(QStandardPaths.StandardLocation.AppLocalDataLocation))
    data_dir.mkdir(parents=True, exist_ok=True)
    return run_token_widget(app, home, data_dir)
