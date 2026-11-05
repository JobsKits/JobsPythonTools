# launch.py | JobsHotspot
# Created by Jobs on 2026年11月5日，星期四.
"""源码与冻结程序共用入口；包内资源不回退到构建机路径。"""
from pathlib import Path
import sys


def main(argv=None):
    if not getattr(sys, "frozen", False):
        sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))
    from jobs_hotspot.app import main as application_main
    return application_main(argv)


if __name__ == "__main__":
    raise SystemExit(main())
