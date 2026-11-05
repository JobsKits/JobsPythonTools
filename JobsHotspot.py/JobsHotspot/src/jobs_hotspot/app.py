"""Jobs Hotspot entry points. Created by Jobs."""
from __future__ import annotations

import argparse
from dataclasses import asdict
import json
from pathlib import Path
import sys
import tempfile


class DemoBackend:
    """Explicit UI-only fixture; never selected by a native failure."""
    def __init__(self):
        self.active = False
        self.counter = 0

    def snapshot(self, upstream_id=''):
        from .models import Interface, Snapshot
        self.counter += 262144
        return Snapshot('darwin', [Interface('wired','USB Ethernet','ethernet',True,'192.0.2.2',self.counter,0),
            Interface('wifi','Wi-Fi','wifi',True,'198.51.100.1',0,self.counter)],
            'wired','wifi','on' if self.active else 'off', can_start=True,can_stop=True)

    def start(self, upstream_id, ssid, password):
        from .models import ActionResult
        self.active = True
        return ActionResult(True,'demo')

    def stop(self):
        from .models import ActionResult
        self.active = False
        return ActionResult(True,'demo')

    def open_settings(self):
        pass


def main(argv=None):
    parser = argparse.ArgumentParser(description='Jobs Hotspot · wired / USB network → Wi-Fi')
    group = parser.add_mutually_exclusive_group()
    group.add_argument('--diagnose', action='store_true', help='Read native device state as JSON; never change sharing')
    group.add_argument('--smoke', action='store_true', help='Verify GUI resources without network operations; exit automatically')
    group.add_argument('--demo', action='store_true', help='Explicit UI demo; does not change system networking')
    args = parser.parse_args(argv)
    if args.diagnose:
        from .backends import create_backend
        try:
            print(json.dumps(asdict(create_backend().snapshot()), ensure_ascii=False, indent=2))
            return 0
        except Exception as error:
            print(json.dumps({'error': str(error)},ensure_ascii=False),file=sys.stderr)
            return 1
    from PySide6.QtCore import QSettings, QTimer
    from PySide6.QtGui import QFont, QFontDatabase
    from PySide6.QtWidgets import QApplication, QMessageBox
    from .ui import ASSETS, MainWindow
    app = QApplication.instance() or QApplication(sys.argv[:1])
    app.setApplicationName('JobsHotspot')
    app.setOrganizationName('Jobs')
    app.setStyle('Fusion')
    app.setQuitOnLastWindowClosed(False)
    try:
        for name in ('icon.png','wifi.svg','power_settings_new.svg','portable_wifi_off.svg',
                     'translate.svg','settings_ethernet.svg','error_outline.svg','NotoSerifTibetan.ttf'):
            if not (ASSETS / name).is_file():
                raise RuntimeError('Missing packaged resource: ' + name)
        font_id = QFontDatabase.addApplicationFont(str(ASSETS / 'NotoSerifTibetan.ttf'))
        if font_id < 0:
            raise RuntimeError('Cannot load packaged Tibetan font')
        font = QFont('PingFang SC' if sys.platform == 'darwin' else 'Segoe UI')
        font.setFamilies([font.family(), *QFontDatabase.applicationFontFamilies(font_id)])
        app.setFont(font)
        if args.smoke or args.demo:
            backend = DemoBackend()
        else:
            from .backends import create_backend
            backend = create_backend()
        with tempfile.TemporaryDirectory(prefix='JobsHotspot-smoke-') as temp:
            settings = QSettings(str(Path(temp) / 'settings.ini'),QSettings.Format.IniFormat) if args.smoke else None
            window = MainWindow(backend, demo=args.demo, smoke=args.smoke, settings=settings)
            if args.smoke:
                from .i18n import LANGUAGES
                from .controls import preference_icon
                for language, _ in LANGUAGES:
                    window.language.setCurrentIndex(window.language.findData(language))
                    for mode in ('light','dark','system'):
                        window.appearance.setCurrentIndex(window.appearance.findData(mode))
                for name in ('translate','light_mode','dark_mode','computer','wifi','power_settings_new',
                             'portable_wifi_off','error_outline','settings_ethernet','refresh'):
                    if preference_icon(name,'#ffffff').isNull():
                        raise RuntimeError('Invalid icon: ' + name)
                window.show()
                QTimer.singleShot(120, window.finish_quit)
            else:
                window.show()
            return app.exec()
    except Exception as error:
        if args.smoke:
            print(str(error),file=sys.stderr)
        else:
            QMessageBox.critical(None,'Jobs Hotspot',str(error))
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
