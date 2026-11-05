"""ETW 二进制解码、统计与会话生命周期隔离回归。Created by Jobs."""
import ctypes as ct
import struct
import threading
import unittest
from unittest.mock import MagicMock, patch

from jobs_app_traffic_monitor.app_resolver import AppIdentity
from jobs_app_traffic_monitor.collectors import windows_etw as etw


def process_identity(name="example.exe", created=1, observed_until=10**18):
    """夹具显式给出已验证生命周期，不靠当前 PID 名称猜历史归属。"""
    path = "C:\\Apps\\" + name
    return etw._ProcessIdentity(AppIdentity(name, path, path, False), created, observed_until)


class WindowsEtwTests(unittest.TestCase):
    def test_win64_abi_sizes_and_callback_offset(self):
        if ct.sizeof(ct.c_void_p) != 8:
            self.skipTest("Win64 ABI only")
        self.assertEqual(ct.sizeof(etw._Wnode), 48)
        self.assertEqual(ct.sizeof(etw._Properties), 120)
        self.assertEqual(ct.sizeof(etw._Header), 80)
        self.assertEqual(ct.sizeof(etw._Record), 112)
        self.assertEqual(ct.sizeof(etw._Logfile), 448)
        self.assertEqual(etw._Logfile.EventRecordCallback.offset, 424)

    def test_tcp_udp_ipv4_ipv6_directions(self):
        for provider in (etw.TCP_GUID, etw.UDP_GUID):
            for opcode in (10, 26):
                self.assertEqual(etw.decode_network_event(provider, 2, opcode, struct.pack("<II", 123, 456)), (123, 0, 456))
            for opcode in (11, 27):
                self.assertEqual(etw.decode_network_event(provider, 2, opcode, struct.pack("<II", 123, 456)), (123, 456, 0))

    def test_unknown_versions_retransmissions_and_malformed_events_are_not_counted(self):
        payload = struct.pack("<II", 123, 456)
        for provider, version, opcode, data in (
            (bytes(16), 2, 10, payload), (etw.TCP_GUID, 0, 10, payload),
            (etw.UDP_GUID, 1, 10, payload), (etw.TCP_GUID, 2, 14, payload),
            (etw.TCP_GUID, 2, 12, payload), (etw.TCP_GUID, 2, 10, b"bad"),
            (etw.UDP_GUID, 2, 10, struct.pack("<II", 0, 5)),
        ):
            self.assertIsNone(etw.decode_network_event(provider, version, opcode, data))

    def test_callback_uses_payload_pid_instead_of_system_header_pid(self):
        session = object.__new__(etw._EtwSession)
        session._consume = MagicMock()
        event = etw._Record()
        event.EventHeader.ProviderId[:] = etw.TCP_GUID
        event.EventHeader.ProcessId = 4
        event.EventHeader.EventDescriptor.Version = 2
        event.EventHeader.EventDescriptor.Opcode = 11
        payload = ct.create_string_buffer(struct.pack("<II", 4242, 1000))
        event.UserDataLength = 8
        event.UserData = ct.cast(payload, ct.c_void_p)
        session._on_event(ct.pointer(event))
        session._consume.assert_called_once_with(4242, 1000, 0, 0)

    def test_aggregation_delta_and_idle_rate(self):
        with patch.object(etw.time, "monotonic", return_value=10):
            collector = etw.WindowsEtwCollector()
            collector._consume(100, 1024, 512, 100)
            collector._consume(101, 2048, 128, 100)
        with patch.object(etw, "resolve_windows_process", return_value=process_identity()):
            with patch.object(etw.time, "monotonic", return_value=12):
                rows = collector.snapshot()
            self.assertEqual(len(rows), 1)
            self.assertEqual(rows[0].pids, (100, 101))
            self.assertEqual((rows[0].bytes_in, rows[0].bytes_out), (3072, 640))
            self.assertEqual((rows[0].download_rate, rows[0].upload_rate), (1536, 320))
            with patch.object(etw.time, "monotonic", return_value=13):
                idle = collector.snapshot()[0]
            self.assertEqual((idle.sample_bytes_in, idle.upload_rate), (0, 0))
            with patch.object(etw.time, "monotonic", return_value=25):
                self.assertEqual(collector.snapshot(), [])

    def test_unknown_processes_are_not_combined(self):
        collector = etw.WindowsEtwCollector()
        collector._consume(100, 10, 0, 100)
        collector._consume(101, 20, 0, 100)
        with patch.object(etw, "resolve_windows_process", return_value=None):
            self.assertEqual(len(collector.snapshot()), 2)

    def test_permission_failure_never_starts_consumer(self):
        with patch.object(etw, "_EtwSession") as session:
            session.return_value.open.side_effect = PermissionError("denied")
            session.return_value.owns_resources = False
            collector = etw.WindowsEtwCollector()
            with self.assertRaises(PermissionError):
                collector.start()
            self.assertIsNone(collector._session)
            self.assertIsNone(collector._thread)

    def test_session_lifecycle_is_idempotent_and_background_failure_is_visible(self):
        finished = threading.Event()
        with patch.object(etw, "_EtwSession") as factory:
            session = factory.return_value
            session.process.side_effect = lambda: finished.wait(2)
            session.close.side_effect = finished.set
            collector = etw.WindowsEtwCollector()
            collector.start()
            collector.start()
            self.assertEqual(factory.call_count, 1)
            collector.stop()
            collector.stop()
            self.assertIsNone(collector._session)
            session.close.assert_called_once()
        collector._error = OSError("consumer failed")
        with self.assertRaisesRegex(OSError, "consumer failed"):
            collector.snapshot()

    def test_native_api_open_failure_stops_only_owned_handle(self):
        dll = MagicMock()
        dll.StartTraceW.side_effect = lambda pointer, name, props: setattr(pointer._obj, "value", 123) or 0
        dll.OpenTraceW.return_value = 0xFFFFFFFFFFFFFFFF
        stopped = []
        dll.ControlTraceW.side_effect = lambda handle, name, props, code: stopped.append((handle.value, name, code)) or 0
        with patch.object(etw.sys, "platform", "win32"), patch.object(ct, "WinDLL", return_value=dll, create=True):
            with patch.object(ct, "WINFUNCTYPE", ct.CFUNCTYPE, create=True), patch.object(ct, "get_last_error", return_value=5, create=True):
                session = etw._EtwSession(lambda *args: None)
                with self.assertRaisesRegex(OSError, "管理员"):
                    session.open()
        self.assertEqual(stopped, [(123, None, 1)])
        dll.CloseTrace.assert_not_called()

    def test_existing_or_denied_session_is_never_stopped(self):
        for error in (5, 183):
            dll = MagicMock()
            dll.StartTraceW.return_value = error
            with patch.object(etw.sys, "platform", "win32"), patch.object(ct, "WinDLL", return_value=dll, create=True):
                with patch.object(ct, "WINFUNCTYPE", ct.CFUNCTYPE, create=True):
                    session = etw._EtwSession(lambda *args: None)
                    with self.assertRaises(OSError):
                        session.open()
                    session.close()
            dll.ControlTraceW.assert_not_called()
            dll.OpenTraceW.assert_not_called()

    def test_dropped_events_are_reported_instead_of_returning_zero_traffic(self):
        collector = etw.WindowsEtwCollector()
        collector._session = MagicMock()
        collector._session.check.side_effect = OSError("events lost")
        with self.assertRaisesRegex(OSError, "events lost"):
            collector.snapshot()

    def test_idle_row_hides_without_resetting_session_ledger(self):
        with patch.object(etw, "resolve_windows_process", return_value=process_identity()):
            with patch.object(etw.time, "monotonic", return_value=10):
                collector = etw.WindowsEtwCollector()
                collector._consume(100, 1000, 0, 100)
                self.assertEqual(collector.snapshot()[0].bytes_in, 1000)
            with patch.object(etw.time, "monotonic", return_value=25):
                self.assertEqual(collector.snapshot(), [])
            with patch.object(etw.time, "monotonic", return_value=30):
                collector._consume(100, 5, 0, 300)
                row = collector.snapshot()[0]
            self.assertEqual(row.bytes_in, 1005)
            self.assertEqual(row.sample_bytes_in, 5)

    def test_pid_reuse_preserves_old_exe_and_uses_event_lifetime(self):
        collector = etw.WindowsEtwCollector()
        with patch.object(etw, "resolve_windows_process", return_value=process_identity("old.exe", 100, 200)):
            collector._consume(100, 1000, 0, 150)
            self.assertEqual(collector.snapshot()[0].app_name, "old.exe")
        with patch.object(etw, "resolve_windows_process", return_value=process_identity("new.exe", 300, 400)):
            collector._consume(100, 10, 0, 180)  # 延迟交付，仍在已验证旧生命周期内。
            collector._consume(100, 5, 0, 350)
            collector._consume(100, 7, 0, 250)  # 没有证据证明属于哪个进程。
            rows = {row.app_name: row for row in collector.snapshot()}
        self.assertEqual(rows["old.exe"].bytes_in, 1010)
        self.assertEqual(rows["new.exe"].bytes_in, 5)
        unknown = next(row for row in rows.values() if row.app_path is None)
        self.assertEqual(unknown.bytes_in, 7)
        self.assertIn("身份未验证", unknown.app_name)

    def test_first_buffered_event_before_current_birth_is_not_given_to_new_exe(self):
        collector = etw.WindowsEtwCollector()
        collector._consume(100, 1000, 0, 150)
        with patch.object(etw, "resolve_windows_process", return_value=process_identity("new.exe", 300, 400)):
            row = collector.snapshot()[0]
        self.assertIsNone(row.app_path)
        self.assertEqual(row.bytes_in, 1000)

    def test_overlapping_lifetime_clock_intervals_are_not_guessed(self):
        collector = etw.WindowsEtwCollector()
        with patch.object(etw, "resolve_windows_process", return_value=process_identity("old.exe", 100, 200)):
            collector._consume(100, 1000, 0, 150)
            collector.snapshot()
        with patch.object(etw, "resolve_windows_process", return_value=process_identity("new.exe", 50, 250)):
            collector._consume(100, 7, 0, 150)
            rows = collector.snapshot()
        unknown = next(row for row in rows if row.app_path is None)
        self.assertEqual(unknown.bytes_in, 7)
        self.assertEqual(next(row for row in rows if row.app_name == "old.exe").bytes_in, 1000)

    def test_exe_total_survives_old_process_inactivity_and_new_process_start(self):
        with patch.object(etw, "resolve_windows_process", return_value=process_identity()):
            with patch.object(etw.time, "monotonic", return_value=10):
                collector = etw.WindowsEtwCollector()
                collector._consume(100, 1000, 0, 100)
                collector.snapshot()
            with patch.object(etw.time, "monotonic", return_value=25):
                self.assertEqual(collector.snapshot(), [])
        with patch.object(etw, "resolve_windows_process", return_value=process_identity(created=200)):
            with patch.object(etw.time, "monotonic", return_value=30):
                collector._consume(101, 5, 0, 300)
                row = collector.snapshot()[0]
        self.assertEqual(row.bytes_in, 1005)
        self.assertEqual(row.sample_bytes_in, 5)
        self.assertEqual(row.pids, (100, 101))

    def test_open_and_cleanup_failure_keep_both_errors_and_retryable_owner(self):
        dll = MagicMock()
        dll.StartTraceW.side_effect = lambda pointer, name, props: setattr(pointer._obj, "value", 123) or 0
        dll.OpenTraceW.return_value = 0xFFFFFFFFFFFFFFFF
        dll.ControlTraceW.return_value = 31
        with patch.object(etw.sys, "platform", "win32"), patch.object(ct, "WinDLL", return_value=dll, create=True):
            with patch.object(ct, "WINFUNCTYPE", ct.CFUNCTYPE, create=True), patch.object(ct, "get_last_error", return_value=5, create=True):
                collector = etw.WindowsEtwCollector()
                with self.assertRaises(etw._SessionCleanupError) as raised:
                    collector.start()
                self.assertEqual(raised.exception.primary_error.errno, 5)
                self.assertEqual(raised.exception.cleanup_error.errno, 31)
                self.assertIn("OpenTraceW", str(raised.exception))
                self.assertIn("ControlTraceW(stop)", str(raised.exception))
                self.assertIsNotNone(collector._session)
                self.assertTrue(collector._session.owns_resources)
                dll.ControlTraceW.return_value = 0
                collector.stop()
                self.assertIsNone(collector._session)
                self.assertEqual(dll.ControlTraceW.call_count, 2)

    def test_queue_overflow_is_visible_instead_of_silently_dropping_traffic(self):
        collector = etw.WindowsEtwCollector()
        collector._pending_limit = 1
        collector._consume(100, 1, 0, 100)
        collector._consume(100, 2, 0, 100)
        with self.assertRaisesRegex(OSError, "队列已满"):
            collector.snapshot()

    def test_identity_binds_creation_and_exe_to_one_handle_ignoring_undefined_live_exit_time(self):
        kernel = MagicMock()
        kernel.OpenProcess.return_value = 55
        def times(handle, created, exited, kernel_time, user_time):
            self.assertEqual(handle, 55)
            created._obj.value = 100
            exited._obj.value = 99999  # Windows 文档：进程运行时该字段未定义。
            return 1
        def exit_code(handle, code):
            self.assertEqual(handle, 55)
            code._obj.value = 259
            return 1
        def image(handle, flags, buffer, length):
            self.assertEqual(handle, 55)
            buffer.value = "C:\\Apps\\example.exe"
            return 1
        kernel.GetProcessTimes.side_effect = times
        kernel.GetExitCodeProcess.side_effect = exit_code
        kernel.QueryFullProcessImageNameW.side_effect = image
        with patch.object(ct, "WinDLL", return_value=kernel, create=True), patch.object(etw, "_filetime_now", return_value=500):
            process = etw.resolve_windows_process(123)
        self.assertEqual(process.created, 100)
        self.assertEqual(process.observed_until, 500)
        self.assertEqual(process.identity.app_path, "C:\\Apps\\example.exe")
        kernel.OpenProcess.assert_called_once_with(0x1000, False, 123)
        kernel.CloseHandle.assert_called_once_with(55)

    def test_unverifiable_creation_never_exposes_current_exe_as_verified_identity(self):
        kernel = MagicMock()
        kernel.OpenProcess.return_value = 55
        kernel.GetProcessTimes.return_value = 0
        with patch.object(ct, "WinDLL", return_value=kernel, create=True):
            self.assertIsNone(etw.resolve_windows_process(123))
        kernel.QueryFullProcessImageNameW.assert_not_called()
        kernel.CloseHandle.assert_called_once_with(55)


if __name__ == "__main__":
    unittest.main()
