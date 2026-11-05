# launch.py | JobsSSHKeyMgr
# Created by Jobs on 2026年11月4日，星期三.
"""源码和打包应用共用入口；帮助页不初始化 GUI 或操作 SSH。"""
from __future__ import annotations

import argparse
from pathlib import Path
import sys


def main(argv=None):
    """通过脚本自身位置加载包，冻结运行时不回退到开发机路径。"""
    parser = argparse.ArgumentParser(description='Jobs SSH Key Mgr · personal SSH key GUI')
    parser.parse_args(argv)
    if not getattr(sys, 'frozen', False):
        sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'src'))
    from jobs_ssh_key_mgr.app import main as application_main
    return application_main()


if __name__ == '__main__':
    raise SystemExit(main())
