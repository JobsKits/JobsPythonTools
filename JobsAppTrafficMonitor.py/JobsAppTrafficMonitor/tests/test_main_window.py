import os
import unittest
from unittest.mock import MagicMock, patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

from jobs_app_traffic_monitor.models import AppTraffic
from jobs_app_traffic_monitor.ui.main_window import MainWindow
from jobs_app_traffic_monitor.ui import main_window


class _CollectorStub:
    def __init__(self) -> None:
        self.items: list[AppTraffic] = []

    def start(self) -> None:
        pass

    def stop(self) -> None:
        pass

    def snapshot(self) -> list[AppTraffic]:
        return self.items


class MainWindowTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self) -> None:
        self.collector = _CollectorStub()
        self.window = MainWindow(self.collector)

    def tearDown(self) -> None:
        self.window.close()

    def test_shows_sampling_hint_until_data_arrives(self) -> None:
        self.window._refresh()
        self.assertFalse(self.window._empty_state.isHidden())

        self.collector.items = [
            AppTraffic("Example", None, None, False, (1,), 10, 5, 10, 5, 10, 5, 1)
        ]
        self.window._refresh()

        self.assertTrue(self.window._empty_state.isHidden())
        self.assertEqual(self.window._table.rowCount(), 1)

    def test_switches_between_dark_and_light_themes(self) -> None:
        self.window._toggle_theme()
        self.assertTrue(self.window._dark_mode)
        self.assertEqual(self.window._theme_button.text(), "☀️ 浅色")

        self.window._toggle_theme()
        self.assertFalse(self.window._dark_mode)
        self.assertEqual(self.window._theme_button.text(), "🌙 深色")

    def test_sampling_failure_keeps_retry_available_and_does_not_show_zero_traffic(self):
        with patch.object(self.collector, "snapshot", side_effect=PermissionError("需要管理员权限")):
            self.window._refresh()
        self.assertIn("需要管理员权限", self.window._empty_state.text())
        self.assertFalse(self.window._empty_state.isHidden())
        self.assertFalse(self.window._timer.isActive())
        self.window._empty_state.click()
        self.assertTrue(self.window._timer.isActive())
        self.assertIn("正在采集", self.window._empty_state.text())

    def test_startup_failure_is_shown_in_window(self):
        with patch.object(self.collector, "start", side_effect=PermissionError("denied")):
            self.window._restart_collector()
        self.assertIn("denied", self.window._empty_state.text())
        self.assertFalse(self.window._timer.isActive())

    def test_windows_reveal_uses_explorer_with_separate_path_argument(self):
        with patch.object(main_window.sys, "platform", "win32"), patch.object(main_window.QProcess, "startDetached") as start:
            self.window._reveal_in_finder("C:\\Apps with 空格\\example.exe")
        start.assert_called_once_with("explorer.exe", ["/select,", "C:\\Apps with 空格\\example.exe"])

    def test_close_cleanup_failure_keeps_window_available_for_retry(self):
        event = MagicMock()
        with patch.object(self.collector, "stop", side_effect=OSError("stop failed")):
            self.window.closeEvent(event)
        event.ignore.assert_called_once()
        event.accept.assert_not_called()
        self.assertFalse(self.window._quitting)
        self.assertIn("stop failed", self.window._empty_state.text())

    def test_tray_quit_cleanup_failure_does_not_discard_collector_owner(self):
        with patch.object(self.collector, "stop", side_effect=OSError("stop failed")), patch.object(QApplication, "quit") as quit_app:
            self.window._quit_application()
        quit_app.assert_not_called()
        self.assertFalse(self.window._quitting)
        self.assertIs(self.window._collector, self.collector)


if __name__ == "__main__":
    unittest.main()
