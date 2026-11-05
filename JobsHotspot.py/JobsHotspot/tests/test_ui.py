"""Critical UI state rules, isolated from host networking. Created by Jobs."""
import os
os.environ.setdefault('QT_QPA_PLATFORM','offscreen')
from pathlib import Path
import tempfile
import unittest
from PySide6.QtCore import QSettings
from PySide6.QtWidgets import QApplication
from jobs_hotspot.app import DemoBackend
from jobs_hotspot.models import Interface,Issue,Snapshot
from jobs_hotspot.ui import MainWindow
from jobs_hotspot.i18n import LANGUAGES


class UITests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])
        cls.app.setStyle('Fusion')

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        settings = QSettings(str(Path(self.temp.name)/'settings.ini'),QSettings.Format.IniFormat)
        self.window = MainWindow(DemoBackend(),smoke=True,settings=settings)

    def tearDown(self):
        self.window.tray.hide()
        self.window.deleteLater()
        self.app.processEvents()
        self.temp.cleanup()

    def test_missing_hardware_disabled_but_stopping_survives_link_loss(self):
        self.window.received(Snapshot('MacOS',state='off',issues=[Issue('no_upstream'),Issue('no_wifi')]),None)
        self.assertFalse(self.window.toggle.isEnabled())
        self.assertTrue(self.window.alert.isVisibleTo(self.window))
        self.window.received(Snapshot('MacOS',state='on',can_stop=True,issues=[Issue('no_upstream')]),None)
        self.assertTrue(self.window.toggle.isEnabled())
        self.assertTrue(self.window.stop_action.isEnabled())

    def test_windows_credentials_and_no_stale_enable(self):
        self.window.received(Snapshot('Windows',state='off',can_start=True),None)
        self.assertFalse(self.window.toggle.isEnabled())
        self.window.password.setText('12345678')
        self.assertTrue(self.window.toggle.isEnabled())
        self.window.received(Snapshot('Windows',issues=[Issue('probe_failed')]),None)
        self.assertFalse(self.window.toggle.isEnabled())
        self.assertFalse(self.window.stop_action.isEnabled())
        self.assertEqual(self.window.input_card.speed.text(),'—')

    def test_mac_permissions_discoverable(self):
        self.window.received(Snapshot('MacOS',state='off',issues=[Issue('mac_permission')]),None)
        self.assertFalse(self.window.credentials.isVisibleTo(self.window))
        self.assertTrue(self.window.permissions_button.isVisibleTo(self.window))
        self.assertFalse(self.window.toggle.isEnabled())

    def test_translations_themes_and_saved_settings(self):
        for locale,_ in LANGUAGES:
            self.window.language.setCurrentIndex(self.window.language.findData(locale))
            self.assertEqual(self.window.locale,locale)
            for theme in ('light','dark','system'):
                self.window.appearance.setCurrentIndex(self.window.appearance.findData(theme))
                self.assertEqual(self.window.theme,theme)
        self.window.language.setCurrentIndex(self.window.language.findData('zh_TW'))
        self.window.appearance.setCurrentIndex(self.window.appearance.findData('dark'))
        reloaded = MainWindow(DemoBackend(),smoke=True,settings=self.window.settings)
        self.assertEqual(reloaded.locale,'zh_TW')
        self.assertEqual(reloaded.theme,'dark')
        reloaded.deleteLater()

    def test_source_smoke_exits_without_hiding_forever(self):
        import subprocess, sys
        entry = Path(__file__).resolve().parents[1] / 'scripts/launch.py/launch.py'
        result = subprocess.run([sys.executable,str(entry),'--smoke'],
            env=dict(os.environ,QT_QPA_PLATFORM='offscreen'),capture_output=True,text=True,timeout=15)
        self.assertEqual(result.returncode,0,result.stderr)

    def test_recovered_snapshot_clears_current_error_but_retains_diagnostic(self):
        from jobs_hotspot.models import ActionResult
        self.window.received(Snapshot('MacOS',state='off',can_start=True),ActionResult(False,'mac_ui_changed'))
        self.assertTrue(self.window.failure_visible)
        self.window.received(Snapshot('MacOS',state='off',can_start=True),None)
        self.assertFalse(self.window.failure_visible)
        self.assertIn('mac_ui_changed',self.window.details.toPlainText())
