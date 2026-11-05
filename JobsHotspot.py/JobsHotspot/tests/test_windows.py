"""Windows bridge contracts; no networking changes. Created by Jobs."""
import base64
import copy
import json
from pathlib import Path
import subprocess
import sys
import unittest
from unittest.mock import Mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from jobs_hotspot.backends.windows import (BridgeError, POWERSHELL_BRIDGE, WindowsBackend,
                                          _validate_credentials)

WIRED = "01234567-1234-1234-1234-123456789abc"
WIFI = "89abcdef-1234-1234-1234-123456789abc"


def ready(**changes):
    data = dict(ok=True, interfaces=[
        dict(id=WIRED, name="USB 以太网", kind="usb", up=True,
             ipv4="10.0.0.2", received=10000, sent=2500),
        dict(id=WIFI, name="Wi-Fi", kind="wifi", up=False,
             ipv4="", received=500, sent=1500),
    ], upstream_id=WIRED, wifi_id=WIFI, state="off", issues=[], ssid="Jobs Hotspot",
        clients=0, can_start=True, can_stop=False)
    data.update(changes)
    return data


def result(data):
    return subprocess.CompletedProcess([], 0, json.dumps(data, ensure_ascii=False), "")


class WindowsBackendTests(unittest.TestCase):
    def backend(self, *responses, radios=None):
        runner = Mock(side_effect=[result(item) for item in responses])
        backend = WindowsBackend(runner=runner, radio_reader=lambda: radios if radios is not None else {WIFI: True})
        return backend, runner

    def test_disconnected_station_is_valid_hotspot_output(self):
        backend, _ = self.backend(ready())
        snapshot = backend.snapshot()
        self.assertTrue(snapshot.can_start)
        self.assertFalse(snapshot.interface(WIFI).up)
        self.assertEqual(snapshot.interface(WIRED).kind, "usb")
        self.assertEqual(snapshot.interface(WIRED).received, 10000)

    def test_wifi_radio_off_disables_start(self):
        backend, _ = self.backend(ready(), radios={WIFI: False})
        snapshot = backend.snapshot()
        self.assertFalse(snapshot.can_start)
        self.assertIn("wifi_off", [issue.code for issue in snapshot.issues])

    def test_unknown_radio_fails_closed(self):
        backend, _ = self.backend(ready(), radios={})
        snapshot = backend.snapshot()
        self.assertFalse(snapshot.can_start)
        self.assertIn("state_unknown", [issue.code for issue in snapshot.issues])

    def test_no_wired_input_does_not_use_wifi(self):
        data = ready(upstream_id=WIFI)
        backend, _ = self.backend(data)
        snapshot = backend.snapshot()
        self.assertFalse(snapshot.can_start)
        self.assertIn("no_upstream", [issue.code for issue in snapshot.issues])

    def test_input_link_loss_keeps_shutdown_available(self):
        data = ready(state="on", can_start=False, can_stop=True)
        data["interfaces"][0]["up"] = False
        backend, _ = self.backend(data)
        snapshot = backend.snapshot()
        self.assertFalse(snapshot.can_start)
        self.assertTrue(snapshot.can_stop)
        self.assertIn("upstream_down", [issue.code for issue in snapshot.issues])

    def test_running_external_wifi_source_is_not_relabelled_as_wired(self):
        backend, _ = self.backend(ready(upstream_id=WIFI, state="on", can_start=False, can_stop=True))
        snapshot = backend.snapshot(WIRED)
        self.assertEqual(snapshot.upstream_id, WIFI)
        self.assertTrue(snapshot.can_stop)
        self.assertIn("no_upstream", [issue.code for issue in snapshot.issues])

    def test_unverified_active_source_remains_unknown_but_stoppable(self):
        backend, _ = self.backend(ready(upstream_id="", state="on", can_start=False, can_stop=True,
            issues=[dict(code="state_unknown", detail="Active source unverified")]))
        snapshot = backend.snapshot(WIRED)
        self.assertEqual(snapshot.upstream_id, "")
        self.assertTrue(snapshot.can_stop)
        self.assertFalse(snapshot.can_start)

    def test_missing_counters_are_unknown(self):
        data = ready()
        data["interfaces"][0].pop("received")
        data["interfaces"][0]["sent"] = -1
        backend, _ = self.backend(data)
        snapshot = backend.snapshot()
        self.assertEqual(snapshot.interface(WIRED).received, -1)
        self.assertEqual(snapshot.interface(WIRED).sent, -1)

    def test_policy_blocks_start_but_not_stop(self):
        data = ready(state="on", can_start=False, can_stop=True,
                     issues=[dict(code="capability_blocked", detail="DisabledByGroupPolicy")])
        backend, _ = self.backend(data)
        snapshot = backend.snapshot()
        self.assertFalse(snapshot.can_start)
        self.assertTrue(snapshot.can_stop)
        self.assertEqual(snapshot.issues[0].detail, "DisabledByGroupPolicy")

    def test_snapshot_timeout_discards_previous_start_permission(self):
        backend, runner = self.backend(ready())
        self.assertTrue(backend.snapshot().can_start)
        runner.side_effect = subprocess.TimeoutExpired("powershell", 32)
        snapshot = backend.snapshot()
        self.assertFalse(snapshot.can_start)
        self.assertEqual(snapshot.state, "unknown")
        self.assertEqual(snapshot.issues[0].code, "timeout")

    def test_malformed_or_incomplete_json_fails_closed(self):
        for output in ("garbage", "null", "[]", '{"ok":true}', '{"ok":"true"}'):
            with self.subTest(output=output):
                runner = Mock(return_value=subprocess.CompletedProcess([], 0, output, ""))
                snapshot = WindowsBackend(runner=runner).snapshot()
                self.assertFalse(snapshot.can_start)
                self.assertFalse(snapshot.can_stop)
                self.assertEqual(snapshot.state, "unknown")

    def test_native_permission_failure(self):
        backend, _ = self.backend(dict(ok=False, code="permission", detail="HRESULT=0x80070005"))
        snapshot = backend.snapshot()
        self.assertEqual(snapshot.issues[0].code, "permission")
        self.assertFalse(snapshot.can_start)

    def test_start_rechecks_and_keeps_password_out_of_commandline(self):
        password = 'abc";$(secret)123'
        ssid = 'Jobs "USB" 热点'
        backend, runner = self.backend(ready(), dict(ok=True, code="started"))
        action = backend.start(WIRED, ssid, password)
        self.assertTrue(action.ok)
        self.assertEqual(runner.call_count, 2)
        args, kwargs = runner.call_args
        command = args[0]
        self.assertNotIn(password, " ".join(command))
        self.assertNotIn(ssid, " ".join(command))
        payload = json.loads(kwargs["input"])
        self.assertEqual(payload["password"], password)
        self.assertEqual(payload["ssid"], ssid)
        self.assertEqual(payload["upstream_id"], WIRED)
        self.assertEqual(base64.b64decode(command[-1]).decode("utf-16-le"), POWERSHELL_BRIDGE)
        self.assertFalse(kwargs.get("shell", False))

    def test_start_refuses_stale_ready_state(self):
        data = ready(issues=[dict(code="upstream_not_internet", detail="")], can_start=False)
        backend, runner = self.backend(data)
        action = backend.start(WIRED, "Jobs", "abcdefgh")
        self.assertFalse(action.ok)
        self.assertEqual(action.code, "upstream_not_internet")
        self.assertEqual(runner.call_count, 1)

    def test_stop_ignores_missing_ingress_and_credentials(self):
        backend, runner = self.backend(dict(ok=True, code="stopped"))
        backend._upstream_id = WIRED
        action = backend.stop()
        self.assertTrue(action.ok)
        self.assertEqual(runner.call_count, 1)
        self.assertEqual(json.loads(runner.call_args.kwargs["input"])["operation"], "stop")

    def test_invalid_credentials_never_start_bridge(self):
        for ssid, password in (("", "abcdefgh"), ("a" * 33, "abcdefgh"),
                               ("Jobs", "short"), ("Jobs", "密碼abcdefgh"),
                               ("Jobs\n", "abcdefgh")):
            backend, runner = self.backend()
            with self.subTest(ssid=ssid):
                self.assertEqual(backend.start(WIRED, ssid, password).code, "invalid_credentials")
                runner.assert_not_called()
        self.assertTrue(_validate_credentials("热点", "A strong password 123"))

    def test_nonzero_exit_does_not_leak_stderr_or_stdout(self):
        secret = "arbitrary sensitive stdout"
        runner = Mock(return_value=subprocess.CompletedProcess([], 1, secret, secret))
        snapshot = WindowsBackend(runner=runner).snapshot()
        self.assertEqual(snapshot.issues[0].detail, "PowerShell exit=1")
        self.assertNotIn(secret, str(snapshot))

    def test_compiled_bridge_fits_windows_commandline_budget(self):
        # CreateProcessW maximum command line is 32767 characters.
        encoded = base64.b64encode(POWERSHELL_BRIDGE.encode("utf-16-le"))
        self.assertLess(len(encoded) + 512, 32767)
        self.assertNotIn("netsh", POWERSHELL_BRIDGE)
        self.assertNotIn("ExecutionPolicy", POWERSHELL_BRIDGE)

    def test_unknown_native_state_never_offers_start_or_stop(self):
        backend, _ = self.backend(ready(state="unknown", can_start=True, can_stop=True))
        snapshot = backend.snapshot()
        self.assertFalse(snapshot.can_start)
        self.assertFalse(snapshot.can_stop)

    def test_unavailable_powershell_fails_closed(self):
        backend = WindowsBackend(runner=Mock(side_effect=FileNotFoundError()))
        self.assertEqual(backend.snapshot().issues[0].code, "unsupported")


if __name__ == "__main__":
    unittest.main()
