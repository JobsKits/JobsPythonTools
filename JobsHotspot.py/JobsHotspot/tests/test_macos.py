"""MacOS observations and fail-closed native controls. Created by Jobs."""
from pathlib import Path
import plistlib
import subprocess
import tempfile
import unittest
from unittest.mock import patch

from jobs_hotspot.backends.macos import (
    MacOSBackend, TOGGLE_SCRIPT, interface_kind, parse_counters, parse_hardware,
    parse_ifconfig, parse_nat, parse_services, sharing_state,
)


HARDWARE = '''Hardware Port: Wi-Fi
Device: en0
Ethernet Address: aa:bb:cc:dd:ee:ff

Hardware Port: USB 10/100/1000 LAN
Device: en7
Ethernet Address: aa:bb:cc:dd:ee:00
'''
LINKS = '''en0: flags=8863<UP,BROADCAST,RUNNING> mtu 1500
\tinet 192.168.1.7 netmask 0xffffff00
\tstatus: active
en7: flags=8863<UP,BROADCAST,RUNNING> mtu 1500
\tinet 10.0.0.2 netmask 0xffffff00
\tstatus: active
'''
COUNTERS = '''Name Mtu Network Address Ipkts Ierrs Ibytes Opkts Oerrs Obytes Coll Drop
en0 1500 <Link#1> aa:bb:cc:dd:ee:ff 20 0 1500 10 0 800 0 0
en0 1500 192.168.1 192.168.1.7 20 - 1500 10 - 800 - -
en7 1500 <Link#2> aa:bb:cc:dd:ee:00 90 0 9000 40 0 4000 0 0
'''


def nat(enabled=0, source='en7', targets=None):
    return {'NAT': {'Enabled': enabled, 'PrimaryInterface': {'Device': source},
                    'SharingDevices': ['en0'] if targets is None else targets}}


def completed(out='', code=0, err=''):
    return subprocess.CompletedProcess([], code, out, err)


class Runner:
    def __init__(self, *, state='off', default='en7', power='On', hardware=HARDWARE,
                 links=LINKS, failure=None):
        self.calls = []
        self.state, self.default, self.power = state, default, power
        self.hardware, self.links, self.failure = hardware, links, failure

    def __call__(self, command, **kwargs):
        self.calls.append((command, kwargs))
        if self.failure and self.failure in command:
            raise subprocess.TimeoutExpired(command, 4)
        if '-listallhardwareports' in command:
            return completed(self.hardware)
        if '-listnetworkserviceorder' in command:
            return completed('(1) iPhone USB\n(Hardware Port: iPhone USB, Device: en9)\n')
        if command[0].endswith('ifconfig'):
            return completed(self.links)
        if command[0].endswith('netstat'):
            return completed(COUNTERS)
        if command[0].endswith('route'):
            return completed(f'interface: {self.default}\n') if self.default else completed(code=1)
        if command[0].endswith('launchctl'):
            if self.state == 'on':
                return completed('system/com.apple.InternetSharing = {\n  state = running\n  pid = 123\n}\n')
            if self.state == 'unknown':
                return completed(code=1, err='Operation not permitted')
            return completed(code=113, err='Could not find service "com.apple.InternetSharing" in domain for system')
        if '-getairportpower' in command:
            return completed(f'Wi-Fi Power (en0): {self.power}\n')
        if command[0].endswith('osascript'):
            return completed('layout\n')
        return completed()


class ParsersTests(unittest.TestCase):
    def test_ports_and_disconnected_usb_services(self):
        self.assertEqual(parse_hardware(HARDWARE), {'en0': 'Wi-Fi', 'en7': 'USB 10/100/1000 LAN'})
        self.assertEqual(parse_services('(1) iPhone USB\n(Hardware Port: iPhone USB, Device: en9)\n'),
                         {'en9': 'iPhone USB'})
        self.assertEqual(interface_kind('Thunderbolt Bridge', 'bridge0'), 'other')
        self.assertEqual(interface_kind('Thunderbolt Ethernet', 'en5'), 'ethernet')
        self.assertEqual(interface_kind('iPhone USB', 'en5'), 'usb')

    def test_link_local_and_no_carrier_are_unusable(self):
        parsed = parse_ifconfig(LINKS)
        self.assertEqual(parsed['en7'], (True, '10.0.0.2'))
        self.assertFalse(parse_ifconfig(LINKS.replace('10.0.0.2', '169.254.2.3'))['en7'][0])
        self.assertFalse(parse_ifconfig(LINKS.replace('status: active', 'status: inactive'))['en7'][0])

    def test_counters_are_not_summed_across_address_rows(self):
        self.assertEqual(parse_counters(COUNTERS), {'en0': (1500, 800), 'en7': (9000, 4000)})
        self.assertEqual(parse_counters('en0 malformed\n'), {})

    def test_nat_unknown_schema_is_not_a_valid_setup(self):
        self.assertEqual(parse_nat(nat()), (False, 'en7', ['en0']))
        for invalid in ({}, {'NAT': {}}, nat(source='utun0'), nat(enabled='1'),
                        nat(enabled=0.5), nat(targets=['en0', '../etc/passwd'])):
            self.assertIsNone(parse_nat(invalid))

    def test_state_needs_both_enabled_configuration_and_running_pid(self):
        on = parse_nat(nat(1))
        off = parse_nat(nat())
        running = completed(' state = running\n pid = 12\n')
        loaded = completed(' state = not running\n')
        absent = completed(code=113, err='Could not find service "com.apple.InternetSharing"')
        self.assertEqual(sharing_state(on, running), 'on')
        self.assertEqual(sharing_state(on, loaded), 'transition')
        self.assertEqual(sharing_state(off, running), 'transition')
        self.assertEqual(sharing_state(off, absent), 'off')
        self.assertEqual(sharing_state(None, completed(code=1, err='not authorized')), 'unknown')


class BackendTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.path = Path(self.directory.name) / 'nat.plist'
        self.write_nat()

    def write_nat(self, **kwargs):
        with self.path.open('wb') as stream:
            plistlib.dump(nat(**kwargs), stream)

    def backend(self, runner=None, trusted=True):
        return MacOSBackend(runner or Runner(), self.path, lambda: trusted)

    def test_wired_ready_does_not_automate_or_modify_network_on_poll(self):
        runner = Runner()
        snapshot = self.backend(runner).snapshot()
        self.assertEqual(snapshot.state, 'off')
        self.assertTrue(snapshot.can_start)
        self.assertEqual(snapshot.upstream_id, 'en7')
        self.assertEqual(snapshot.interface('en9').received, -1)
        self.assertFalse(any(call[0][0].endswith(('osascript', 'open')) for call in runner.calls))

    def test_wifi_ingress_blocked_even_if_ethernet_has_an_address(self):
        snapshot = self.backend(Runner(default='en0')).snapshot()
        self.assertFalse(snapshot.can_start)
        self.assertIn('wifi_input', [issue.code for issue in snapshot.issues])
        self.assertIn('route_mismatch', [issue.code for issue in snapshot.issues])

    def test_disconnected_and_missing_wifi_block_start(self):
        snapshot = self.backend(Runner(links=LINKS.replace('10.0.0.2', '169.254.2.3'))).snapshot()
        self.assertFalse(snapshot.can_start)
        snapshot = self.backend(Runner(hardware='')).snapshot()
        self.assertIn('no_wifi', [issue.code for issue in snapshot.issues])

    def test_radio_off_and_permission_denied_disable_start(self):
        self.assertIn('wifi_off', [issue.code for issue in self.backend(Runner(power='Off')).snapshot().issues])
        snapshot = self.backend(trusted=False).snapshot()
        self.assertFalse(snapshot.can_start)
        self.assertIn('mac_permission', [issue.code for issue in snapshot.issues])

    def test_changed_or_multiple_outputs_rejected(self):
        self.write_nat(targets=['en0', 'en9'])
        snapshot = self.backend().snapshot()
        self.assertFalse(snapshot.can_start)
        self.assertIn('mac_setup', [issue.code for issue in snapshot.issues])

    def test_stop_survives_source_failure_and_interface_probe_timeout(self):
        self.write_nat(enabled=1)
        snapshot = self.backend(Runner(state='on', links='', default='')).snapshot()
        self.assertTrue(snapshot.can_stop)
        self.assertFalse(snapshot.can_start)
        snapshot = self.backend(Runner(state='on', failure='-a')).snapshot()
        self.assertTrue(snapshot.can_stop)
        self.assertEqual(snapshot.state, 'on')
        self.assertIn('probe_failed', [issue.code for issue in snapshot.issues])

    def test_unknown_sharing_state_cannot_enable(self):
        snapshot = self.backend(Runner(state='unknown')).snapshot()
        self.assertEqual(snapshot.state, 'unknown')
        self.assertFalse(snapshot.can_start)

    def test_unconfigured_host_never_attempts_toggle(self):
        self.path.unlink()
        runner = Runner()
        result = self.backend(runner).start('en7', 'ignored', 'ignored')
        self.assertFalse(result.ok)
        self.assertEqual(result.code, 'mac_setup')
        self.assertFalse(any(call[0][0].endswith('osascript') for call in runner.calls))

    def test_layout_mismatch_does_not_report_success(self):
        with patch('jobs_hotspot.backends.macos.time.sleep'):
            result = self.backend().start('en7')
        self.assertFalse(result.ok)
        self.assertEqual(result.code, 'mac_ui_changed')
        self.assertNotIn('click button', TOGGLE_SCRIPT)
        self.assertNotIn('keystroke', TOGGLE_SCRIPT)

    def test_action_permission_error_sanitized(self):
        runner = Runner()
        def deny(command, **kwargs):
            if command[0].endswith('osascript'):
                return completed(code=1, err='Not authorized -1743')
            return runner(command, **kwargs)
        with patch('jobs_hotspot.backends.macos.time.sleep'):
            result = self.backend(deny).start('en7')
        self.assertEqual(result.code, 'mac_permission')
        self.assertEqual(result.detail, '')

    def test_reconfigured_source_during_settings_load_is_not_enabled(self):
        runner = Runner()
        backend = self.backend(runner)
        original_read = backend._read_config
        reads = 0

        def reconfigured():
            nonlocal reads
            reads += 1
            if reads > 1:
                return parse_nat(nat(source='en9')), ''
            return original_read()

        backend._read_config = reconfigured
        with patch('jobs_hotspot.backends.macos.time.sleep'):
            result = backend.start('en7')
        self.assertEqual(result.code, 'mac_setup')
        self.assertFalse(any(call[0][0].endswith('osascript') for call in runner.calls))


if __name__ == '__main__':
    unittest.main()
