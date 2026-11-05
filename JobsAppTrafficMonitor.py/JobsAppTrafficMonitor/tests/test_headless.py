"""终端模式启动失败也须撤回采集会话。Created by Jobs."""
import unittest
from unittest.mock import MagicMock, patch

from jobs_app_traffic_monitor import main


class HeadlessCleanupTests(unittest.TestCase):
    def test_start_failure_still_retries_owned_session_cleanup(self):
        collector = MagicMock()
        collector.start.side_effect = OSError("open failed; initial cleanup failed")
        with patch.object(main, "create_collector", return_value=collector):
            with self.assertRaisesRegex(OSError, "open failed"):
                main.run_headless(10)
        collector.stop.assert_called_once()

    def test_keyboard_interrupt_stops_collector(self):
        collector = MagicMock()
        with patch.object(main, "create_collector", return_value=collector), patch.object(main.time, "sleep", side_effect=KeyboardInterrupt):
            self.assertEqual(main.run_headless(10), 0)
        collector.stop.assert_called_once()

    def test_final_cleanup_failure_retains_start_error_as_context(self):
        collector = MagicMock()
        collector.start.side_effect = OSError("open failed")
        collector.stop.side_effect = OSError("cleanup still failed")
        with patch.object(main, "create_collector", return_value=collector):
            with self.assertRaisesRegex(OSError, "cleanup still failed") as raised:
                main.run_headless(10)
        self.assertIn("open failed", str(raised.exception.__context__))


if __name__ == "__main__":
    unittest.main()
