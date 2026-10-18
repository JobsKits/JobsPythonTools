"""源码与打包应用共用的独立监控入口。Created by Jobs."""
import sys
from pathlib import Path


def main():
    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
    from jobs_codex_token_monitor.app import main as application_main
    return application_main()


if __name__ == '__main__':
    raise SystemExit(main())
