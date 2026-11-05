"""Read MacOS links; control only the native Internet Sharing switch.

Created by Jobs on 2026年11月5日，星期四.
The sharing preference format is private, read-only evidence, never a write API.
Unknown formats and unmatched accessibility controls fail closed.
"""
from __future__ import annotations

import ctypes
import ipaddress
import os
from pathlib import Path
import plistlib
import re
import subprocess
import time

from ..models import ActionResult, Interface, Issue, Snapshot


NAT_PATH = Path('/Library/Preferences/SystemConfiguration/com.apple.nat.plist')
SHARING_URL = 'x-apple.systempreferences:com.apple.Sharing-Settings.extension?Internet'
ACCESS_URL = 'x-apple.systempreferences:com.apple.preference.security?Privacy_Accessibility'
DEVICE_RE = re.compile(r'^(?:en\d+|bridge\d+|ap\d+)$')


def run_command(args, *, timeout=4, input_text=None):
    """A bounded child process with stable command output; no shell interpolation."""
    environment = os.environ.copy()
    environment.update({'LC_ALL': 'C', 'LANG': 'C'})
    return subprocess.run(args, input=input_text, text=True, capture_output=True,
                          timeout=timeout, check=False, env=environment)


def parse_hardware(text):
    ports = {}
    for block in re.split(r'\n\s*\n', text):
        name = re.search(r'^Hardware Port:\s*(.+)$', block, re.M)
        device = re.search(r'^Device:\s*(\S+)', block, re.M)
        if name and device and DEVICE_RE.fullmatch(device[1]):
            ports[device[1]] = name[1].strip()
    return ports


def parse_services(text):
    """Service order also exposes disconnected iPhone/USB network interfaces."""
    ports = {}
    for match in re.finditer(r'\(\*?\d+\)\s*(.+)\n\(Hardware Port:.*?Device:\s*(\w+)\)', text):
        if DEVICE_RE.fullmatch(match[2]):
            ports[match[2]] = match[1].strip()
    return ports


def interface_kind(name, device):
    folded = name.casefold()
    if any(token in folded for token in ('wi-fi', 'wifi', 'airport', '802.11')):
        return 'wifi'
    if device.startswith('bridge') or re.fullmatch(r'thunderbolt\s+\d+', folded):
        return 'other'
    if any(token in folded for token in ('usb', 'iphone', 'rndis', 'ncm')):
        return 'usb'
    if any(token in folded for token in ('ethernet', 'lan', '以太网', '乙太網')):
        return 'ethernet'
    return 'other'


def parse_ifconfig(text):
    result = {}
    for match in re.finditer(r'^(\w+): flags=([^\n]+)\n((?:[ \t].*\n?)*)', text, re.M):
        device, flags, block = match.groups()
        address = re.search(r'^\s*inet (\S+)', block, re.M)
        ipv4 = address[1] if address else ''
        try:
            usable = bool(ipv4) and not (ipaddress.ip_address(ipv4).is_link_local
                                         or ipaddress.ip_address(ipv4).is_loopback)
        except ValueError:
            usable = False
        active = bool(re.search(r'^\s*status: active\s*$', block, re.M))
        result[device] = (active and '<UP,' in flags and usable, ipv4)
    return result


def parse_counters(text):
    """Use one link-layer row per interface, never sum duplicate address rows."""
    result = {}
    for line in text.splitlines():
        fields = line.split()
        if len(fields) < 10 or not fields[2].startswith('<Link#'):
            continue
        try:
            # The MAC column is omitted for a number of tunnel/link interfaces.
            tail = fields[-8:]
            if len(tail) == 8:
                result[fields[0].rstrip('*')] = (int(tail[2]), int(tail[5]))
        except (ValueError, IndexError):
            continue
    return result


def parse_nat(data):
    """Return explicit evidence only; missing/changed keys mean unconfigured."""
    nat = data.get('NAT') if isinstance(data, dict) else None
    if not isinstance(nat, dict):
        return None
    enabled = nat.get('Enabled')
    primary = nat.get('PrimaryInterface')
    if not isinstance(primary, dict):
        return None
    source = primary.get('Device')
    targets = nat.get('SharingDevices')
    if (type(enabled) not in (int, bool) or enabled not in (0, 1)
            or not isinstance(source, str)
            or not DEVICE_RE.fullmatch(source) or not isinstance(targets, list)
            or not targets or not all(isinstance(item, str) and DEVICE_RE.fullmatch(item)
                                      for item in targets)):
        return None
    return bool(enabled), source, targets


def accessibility_trusted():
    """The non-prompting public check; passive polling never opens a dialog."""
    try:
        library = ctypes.CDLL('/System/Library/Frameworks/ApplicationServices.framework/ApplicationServices')
        library.AXIsProcessTrusted.restype = ctypes.c_bool
        return bool(library.AXIsProcessTrusted())
    except (OSError, AttributeError):
        return False


def request_accessibility():
    """Register the requesting app only after an explicit permission action."""
    try:
        ax = ctypes.CDLL('/System/Library/Frameworks/ApplicationServices.framework/ApplicationServices')
        cf = ctypes.CDLL('/System/Library/Frameworks/CoreFoundation.framework/CoreFoundation')
        key = ctypes.c_void_p.in_dll(ax, 'kAXTrustedCheckOptionPrompt')
        true = ctypes.c_void_p.in_dll(cf, 'kCFBooleanTrue')
        keys = (ctypes.c_void_p * 1)(key.value)
        values = (ctypes.c_void_p * 1)(true.value)
        cf.CFDictionaryCreate.argtypes = [ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p,
                                          ctypes.c_long, ctypes.c_void_p, ctypes.c_void_p]
        cf.CFDictionaryCreate.restype = ctypes.c_void_p
        options = cf.CFDictionaryCreate(None, keys, values, 1, None, None)
        if options:
            try:
                ax.AXIsProcessTrustedWithOptions.argtypes = [ctypes.c_void_p]
                ax.AXIsProcessTrustedWithOptions.restype = ctypes.c_bool
                ax.AXIsProcessTrustedWithOptions(options)
            finally:
                cf.CFRelease.argtypes = [ctypes.c_void_p]
                cf.CFRelease(options)
    except (OSError, AttributeError, ValueError):
        pass


def sharing_state(config, daemon):
    """A preference alone or a process alone cannot establish a live hotspot."""
    running = daemon.returncode == 0 and bool(re.search(r'^\s*pid = \d+\s*$', daemon.stdout, re.M))
    absent = daemon.returncode != 0 and 'Could not find service' in daemon.stderr
    if config is not None:
        if config[0] and running:
            return 'on'
        if not config[0] and not running and (absent or daemon.returncode == 0):
            return 'off'
        if config[0] != running:
            return 'transition'
    # A never-configured host can be proven inactive only when launchd says absent.
    if config is None and absent:
        return 'off'
    return 'unknown'


# Match the control itself by exact accessible label. Never click a coordinate,
# a row number, a generic "sharing" control, or a confirmation/password dialog.
TOGGLE_SCRIPT = r'''
on run argv
    set desired to item 1 of argv as integer
    tell application "System Events"
        if not (exists process "System Settings") then return "layout"
        tell process "System Settings"
            set frontmost to true
            repeat 16 times
                if exists window 1 then exit repeat
                delay 0.2
            end repeat
            if not (exists window 1) then return "layout"
            set labels to {"Internet Sharing", "互联网共享", "網際網路共享", "互聯網共享", "インターネット共有", "인터넷 공유", "Partage Internet", "Internetfreigabe", "Compartir Internet", "Общий интернет"}
            set matches to {}
            set nodes to entire contents of window 1
            repeat with candidate in nodes
                try
                    set controlRole to value of attribute "AXRole" of candidate
                    if controlRole is "AXCheckBox" or controlRole is "AXSwitch" then
                        set exactLabel to false
                        try
                            if (name of candidate as text) is in labels then set exactLabel to true
                        end try
                        try
                            if (description of candidate as text) is in labels then set exactLabel to true
                        end try
                        try
                            if (value of attribute "AXTitle" of candidate as text) is in labels then set exactLabel to true
                        end try
                        if exactLabel then set end of matches to contents of candidate
                    end if
                end try
            end repeat
            if (count matches) is not 1 then return "layout"
            set toggle to item 1 of matches
            if not (enabled of toggle) then return "disabled"
            set actual to value of attribute "AXValue" of toggle as integer
            if actual is desired then return "unchanged"
            if actual is not 0 and actual is not 1 then return "layout"
            click toggle
            return "clicked"
        end tell
    end tell
end run
'''


class MacOSBackend:
    def __init__(self, runner=run_command, nat_path=NAT_PATH, trusted=accessibility_trusted):
        self._run = runner
        self._nat_path = nat_path
        self._trusted = trusted

    def _read_config(self):
        try:
            with self._nat_path.open('rb') as stream:
                return parse_nat(plistlib.load(stream)), ''
        except FileNotFoundError:
            return None, ''
        except PermissionError:
            return None, 'mac_permission'
        except (OSError, ValueError, plistlib.InvalidFileException):
            return None, 'mac_setup'

    def snapshot(self, upstream_id=''):
        snapshot = Snapshot(platform='MacOS')
        try:
            configured, config_error = self._read_config()
            daemon = self._run(['/bin/launchctl', 'print', 'system/com.apple.InternetSharing'])
            snapshot.state = sharing_state(configured, daemon)
            snapshot.can_stop = snapshot.state == 'on' and self._trusted()
            hardware = self._run(['/usr/sbin/networksetup', '-listallhardwareports'])
            service_order = self._run(['/usr/sbin/networksetup', '-listnetworkserviceorder'])
            links = self._run(['/sbin/ifconfig', '-a'])
            counters = self._run(['/usr/sbin/netstat', '-ibdn'])
            route = self._run(['/sbin/route', '-n', 'get', 'default'])
            if hardware.returncode or links.returncode or counters.returncode:
                raise RuntimeError('networksetup/ifconfig/netstat failed')
            ports = parse_hardware(hardware.stdout)
            # A service can name a USB adapter missing from the hardware list.
            if service_order.returncode == 0:
                for device, name in parse_services(service_order.stdout).items():
                    if device not in ports or interface_kind(name, device) == 'usb':
                        ports[device] = name
            link_info = parse_ifconfig(links.stdout)
            traffic = parse_counters(counters.stdout)
            for device, name in ports.items():
                up, address = link_info.get(device, (False, ''))
                received, sent = traffic.get(device, (-1, -1))
                snapshot.interfaces.append(Interface(device, name, interface_kind(name, device),
                                                     up, address, received, sent))
            route_match = re.search(r'^\s*interface:\s*(\w+)\s*$', route.stdout, re.M)
            default = route_match[1] if route.returncode == 0 and route_match else ''
            wired = [item for item in snapshot.interfaces if item.kind in ('ethernet', 'usb')]
            configured_id = configured[1] if configured else ''
            snapshot.upstream_id = upstream_id or configured_id or next(
                (item.id for item in wired if item.id == default), '') or next(
                (item.id for item in wired if item.up), '')
            upstream = snapshot.interface(snapshot.upstream_id)
            radios = [item for item in snapshot.interfaces if item.kind == 'wifi']
            snapshot.wifi_id = radios[0].id if radios else ''
            if configured:
                snapshot.wifi_id = next((item.id for item in radios if item.id in configured[2]),
                                        snapshot.wifi_id)
            if not upstream or upstream.kind not in ('ethernet', 'usb') or not upstream.up:
                snapshot.issues.append(Issue('no_upstream'))
            if default and any(item.id == default for item in radios):
                snapshot.issues.append(Issue('wifi_input'))
            if not default:
                snapshot.issues.append(Issue('no_route'))
            elif upstream and upstream.id != default:
                snapshot.issues.append(Issue('route_mismatch', upstream.name))
            if not radios:
                snapshot.issues.append(Issue('no_wifi'))
            else:
                power = self._run(['/usr/sbin/networksetup', '-getairportpower', snapshot.wifi_id])
                if power.returncode or not re.search(r':\s*On\s*$', power.stdout):
                    snapshot.issues.append(Issue('wifi_off'))
            if config_error:
                snapshot.issues.append(Issue(config_error))
            if (configured is None or configured[1] != snapshot.upstream_id
                    or configured[2] != [snapshot.wifi_id]):
                snapshot.issues.append(Issue('mac_setup'))
            if not self._trusted():
                snapshot.issues.append(Issue('mac_permission'))
            if snapshot.state in ('unknown', 'transition'):
                snapshot.issues.append(Issue('state_unknown'))
            snapshot.issues = list({issue.code: issue for issue in snapshot.issues}.values())
            snapshot.can_start = snapshot.state == 'off' and not snapshot.issues
            # Stop remains available after unplugging the source or disabling Wi-Fi.
            snapshot.can_stop = snapshot.state == 'on' and self._trusted()
        except (OSError, RuntimeError, subprocess.TimeoutExpired, ValueError) as error:
            # Fresh sharing evidence can still permit stop if link probing fails.
            snapshot.can_start = False
            snapshot.issues.append(Issue('probe_failed', type(error).__name__))
        return snapshot

    def open_settings(self):
        # Navigation alone never enables sharing or changes source/credentials.
        self._run(['/usr/bin/open', SHARING_URL])

    def open_permissions(self):
        request_accessibility()
        self._run(['/usr/bin/open', ACCESS_URL])

    def _toggle(self, enabled, expected_source='', expected_wifi=''):
        try:
            opened = self._run(['/usr/bin/open', SHARING_URL])
            if opened.returncode:
                return ActionResult(False, 'mac_ui_changed')
            # Settings extensions load asynchronously; permit a short bounded delay.
            time.sleep(0.8)
            if enabled:
                # Recheck after opening Settings: do not enable a source/output the
                # user changed while the window was loading.
                config, _error = self._read_config()
                if config is None or config[1:] != (expected_source, [expected_wifi]):
                    return ActionResult(False, 'mac_setup')
            response = self._run(['/usr/bin/osascript', '-e', TOGGLE_SCRIPT, '--',
                                  '1' if enabled else '0'], timeout=12)
            if response.returncode:
                if any(code in response.stderr for code in ('-1743', '-1719', '-25211')):
                    return ActionResult(False, 'mac_permission')
                return ActionResult(False, 'mac_ui_changed')
            if response.stdout.strip() not in ('clicked', 'unchanged'):
                return ActionResult(False, 'mac_ui_changed')
            desired = 'on' if enabled else 'off'
            for _ in range(8):
                config, _error = self._read_config()
                daemon = self._run(['/bin/launchctl', 'print', 'system/com.apple.InternetSharing'])
                if sharing_state(config, daemon) == desired:
                    return ActionResult(True, 'started' if enabled else 'stopped')
                time.sleep(0.5)
            return ActionResult(False, 'operation_failed')
        except (OSError, subprocess.TimeoutExpired):
            return ActionResult(False, 'operation_failed')

    def start(self, upstream_id, ssid='', password=''):
        # The native system owns credentials; input fields must be read-only on Mac.
        snapshot = self.snapshot(upstream_id)
        if not snapshot.can_start:
            return ActionResult(False, snapshot.issues[0].code if snapshot.issues else 'state_unknown')
        return self._toggle(True, snapshot.upstream_id, snapshot.wifi_id)

    def stop(self):
        snapshot = self.snapshot()
        if snapshot.state == 'off':
            return ActionResult(True, 'stopped')
        if not snapshot.can_stop:
            return ActionResult(False, 'mac_permission' if not self._trusted() else 'state_unknown')
        return self._toggle(False)
