"""Windows Mobile Hotspot through the inbox Windows PowerShell/WinRT bridge.

Created by Jobs on 2026年11月5日，星期四.
Only explicit start/stop calls change networking. Credentials travel through stdin,
never the command line, a temporary file, or diagnostic output.
"""
from __future__ import annotations

import base64
import ctypes
import json
import os
from pathlib import Path
import subprocess
import sys
import uuid

from ..models import ActionResult, Interface, Issue, Snapshot

# Static code is encoded only to preserve Unicode and avoid shell quoting. The
# request is separate JSON read from stdin; it is never evaluated as source code.
POWERSHELL_BRIDGE = r'''
$ErrorActionPreference = 'Stop'
$ProgressPreference = 'SilentlyContinue'
[Console]::InputEncoding = New-Object System.Text.UTF8Encoding($false)
[Console]::OutputEncoding = New-Object System.Text.UTF8Encoding($false)
$OutputEncoding = [Console]::OutputEncoding
function Emit($Value) { ConvertTo-Json -InputObject $Value -Depth 8 -Compress }
function Await-Result($Operation, [Type]$ResultType) {
    $method = [System.WindowsRuntimeSystemExtensions].GetMethods() | Where-Object {
        $_.Name -eq 'AsTask' -and $_.IsGenericMethodDefinition -and
        $_.GetGenericArguments().Count -eq 1 -and $_.GetParameters().Count -eq 1 -and
        $_.GetParameters()[0].ParameterType.Name -eq 'IAsyncOperation`1'
    } | Select-Object -First 1
    $task = $method.MakeGenericMethod($ResultType).Invoke($null, @($Operation))
    if (-not $task.Wait(12000)) { throw 'native_timeout' }
    return $task.GetAwaiter().GetResult()
}
function Await-Action($Operation) {
    $method = [System.WindowsRuntimeSystemExtensions].GetMethods() | Where-Object {
        $_.Name -eq 'AsTask' -and -not $_.IsGenericMethod -and
        $_.GetParameters().Count -eq 1 -and
        $_.GetParameters()[0].ParameterType.Name -eq 'IAsyncAction'
    } | Select-Object -First 1
    $task = $method.Invoke($null, @($Operation))
    if (-not $task.Wait(12000)) { throw 'native_timeout' }
    $task.GetAwaiter().GetResult() | Out-Null
}
function Native-Error($ErrorRecord) {
    $native = $ErrorRecord.Exception
    while ($native.InnerException) { $native = $native.InnerException }
    return $native
}
function Error-Code($ErrorRecord) {
    $native = Native-Error $ErrorRecord
    if ($native.ToString() -match 'native_timeout') { return 'timeout' }
    if (($native.HResult -band 0xffff) -eq 5) { return 'permission' }
    return 'operation_failed'
}
function Error-Detail($ErrorRecord) {
    # Windows error text can contain user supplied values; emit only the HRESULT.
    return ('HRESULT=0x{0:X8}' -f ((Native-Error $ErrorRecord).HResult -band 0xffffffffL))
}
try {
    $request = [Console]::In.ReadToEnd() | ConvertFrom-Json
    Add-Type -AssemblyName System.Runtime.WindowsRuntime
    [Windows.Networking.Connectivity.NetworkInformation,Windows.Networking.Connectivity,ContentType=WindowsRuntime] | Out-Null
    [Windows.Networking.NetworkOperators.NetworkOperatorTetheringManager,Windows.Networking.NetworkOperators,ContentType=WindowsRuntime] | Out-Null
    [Windows.Networking.NetworkOperators.NetworkOperatorTetheringOperationResult,Windows.Networking.NetworkOperators,ContentType=WindowsRuntime] | Out-Null
    [Windows.Networking.NetworkOperators.NetworkOperatorTetheringAccessPointConfiguration,Windows.Networking.NetworkOperators,ContentType=WindowsRuntime] | Out-Null
    $profiles = @([Windows.Networking.Connectivity.NetworkInformation]::GetConnectionProfiles())
    $adapters = @(Get-NetAdapter -IncludeHidden | Where-Object {
        -not $_.Virtual -and ($_.HardwareInterface -or $_.PnPDeviceID -like 'USB\*')
    })
    $interfaces = @()
    foreach ($adapter in $adapters) {
        $kind = 'other'
        if ([int]$adapter.InterfaceType -eq 71 -or [int]$adapter.NdisPhysicalMedium -in @(1,9)) {
            $kind = 'wifi'
        } elseif ([int]$adapter.InterfaceType -eq 6 -or $adapter.PnPDeviceID -like 'USB\*') {
            $kind = 'ethernet'
            if ($adapter.PnPDeviceID -like 'USB\*') { $kind = 'usb' }
        }
        $stats = $null
        try { $stats = $adapter | Get-NetAdapterStatistics } catch {}
        $ip = @(Get-NetIPAddress -InterfaceIndex $adapter.InterfaceIndex -AddressFamily IPv4 -ErrorAction SilentlyContinue |
            Where-Object { $_.IPAddress -notlike '169.254.*' -and $_.AddressState -eq 'Preferred' })
        $interfaces += @{
            id = ([guid]$adapter.InterfaceGuid).ToString().ToLowerInvariant(); name = [string]$adapter.Name
            kind = $kind; up = ([int]$adapter.InterfaceOperationalStatus -eq 1)
            ipv4 = (($ip | Select-Object -First 1).IPAddress -as [string])
            received = $(if($stats){[long]$stats.ReceivedBytes}else{-1}); sent = $(if($stats){[long]$stats.SentBytes}else{-1})
            admin_enabled = ([int]$adapter.InterfaceAdminStatus -eq 1)
        }
    }
    $wireProfiles = @()
    foreach ($profile in $profiles) {
        if ($null -eq $profile.NetworkAdapter) { continue }
        $id = $profile.NetworkAdapter.NetworkAdapterId.ToString().ToLowerInvariant()
        $physical = @($interfaces | Where-Object { $_.id -eq $id -and $_.kind -in @('ethernet','usb') })
        if ($physical.Count -gt 0) {
            $wireProfiles += @{profile=$profile; id=$id; internet=($profile.GetNetworkConnectivityLevel().ToString() -eq 'InternetAccess')}
        }
    }
    $selected = $null
    if ($request.upstream_id) {
        $selected = $wireProfiles | Where-Object { $_.id -eq $request.upstream_id } | Select-Object -First 1
    } else {
        $selected = $wireProfiles | Sort-Object -Property @{Expression={$_.internet};Descending=$true} | Select-Object -First 1
    }
    $wifi = @($interfaces | Where-Object { $_.kind -eq 'wifi' })
    $issues = @()
    $upstreamId = [string]$request.upstream_id
    if ($selected) { $upstreamId = $selected.id }
    $upstream = $interfaces | Where-Object { $_.id -eq $upstreamId } | Select-Object -First 1
    if (-not $upstream -or $upstream.kind -notin @('ethernet','usb')) {
        $issues += @{code='no_upstream';detail=''}
    } elseif (-not $upstream.up) {
        $issues += @{code='upstream_down';detail=''}
    } elseif (-not $selected -or -not $selected.internet) {
        $issues += @{code='upstream_not_internet';detail=''}
    }
    if ($wifi.Count -eq 0) { $issues += @{code='no_wifi';detail=''} }
    elseif ($wifi.Count -gt 1) { $issues += @{code='capability_blocked';detail='MultipleWiFiAdapters'} }
    elseif (-not @($wifi | Where-Object { $_.admin_enabled }).Count) { $issues += @{code='wifi_off';detail=''} }

    $capability = ''
    $selectedManager = $null
    if ($selected) {
        try {
            $capability = [Windows.Networking.NetworkOperators.NetworkOperatorTetheringManager]::GetTetheringCapabilityFromConnectionProfile($selected.profile).ToString()
            if ($capability -eq 'Enabled') {
                # This overload explicitly uses Wi-Fi as the private interface.
                $selectedManager = [Windows.Networking.NetworkOperators.NetworkOperatorTetheringManager]::CreateFromConnectionProfile($selected.profile)
            } else { $issues += @{code='capability_blocked';detail=$capability} }
        } catch { $issues += @{code=(Error-Code $_);detail=(Error-Detail $_)} }
    }
    # Observe every available profile so loss of the wired input does not prevent
    # stopping a running system hotspot when another profile still provides access.
    $observedManager = $selectedManager
    $state = 'unknown'
    if ($observedManager) { $state = $observedManager.TetheringOperationalState.ToString() }
    if ($state -notin @('On','InTransition')) {
        foreach ($profile in $profiles) {
            try {
                $manager = [Windows.Networking.NetworkOperators.NetworkOperatorTetheringManager]::CreateFromConnectionProfile($profile)
                $candidateState = $manager.TetheringOperationalState.ToString()
                if ($candidateState -in @('On','InTransition')) {
                    $observedManager = $manager; $state = $candidateState; break
                }
                if (-not $observedManager) { $observedManager = $manager; $state = $candidateState }
            } catch {}
        }
    }
    if ($state -eq 'Unknown' -or $state -eq 'unknown') { $issues += @{code='state_unknown';detail=''} }
    $ssid = ''; $clients = $null
    if ($observedManager) {
        try { $ssid = $observedManager.GetCurrentAccessPointConfiguration().Ssid } catch {}
        try { $clients = [int]$observedManager.ClientCount } catch {}
    }
    $stateName = switch ($state) { 'On' {'on'} 'Off' {'off'} 'InTransition' {'transition'} default {'unknown'} }
    if ($stateName -in @('on','transition')) {
        # A manager created for a profile is not proof that it is the active source.
        # Read ICS public-side ownership; do not relabel an external hotspot.
        $upstreamId = ''; $publicIds = @()
        $issues = @($issues | Where-Object { $_.code -notin @('no_upstream','upstream_down','upstream_not_internet') })
        try {
            $sharing = New-Object -ComObject HNetCfg.HNetShare
            foreach ($connection in $sharing.EnumEveryConnection) {
                $sharingConfig = $sharing.INetSharingConfigurationForINetConnection.Invoke($connection)
                if ($sharingConfig.SharingEnabled -and [int]$sharingConfig.SharingConnectionType -eq 0) {
                    $props = $sharing.NetConnectionProps.Invoke($connection)
                    $publicIds += ([guid]$props.Guid).ToString().ToLowerInvariant()
                }
            }
            if ($publicIds.Count -eq 1) { $upstreamId = $publicIds[0] }
        } catch {}
        if (-not $upstreamId) { $issues += @{code='state_unknown';detail='Active source unverified'} }
    }
    if ($request.operation -eq 'snapshot') {
        Emit @{ok=$true;interfaces=$interfaces;upstream_id=$upstreamId;wifi_id=[string]($wifi | Select-Object -First 1).id;
            state=$stateName;issues=$issues;ssid=[string]$ssid;clients=$clients;
            can_start=($issues.Count -eq 0 -and $stateName -eq 'off' -and $null -ne $selectedManager);
            can_stop=($stateName -eq 'on' -and $null -ne $observedManager)}
    } elseif ($request.operation -eq 'start') {
        if ($issues.Count -gt 0 -or $stateName -ne 'off' -or -not $selectedManager) {
            $code = 'state_unknown'; $detail = $stateName
            if ($issues.Count -gt 0) { $code=$issues[0].code; $detail=$issues[0].detail }
            Emit @{ok=$false;code=$code;detail=$detail}
        } else {
            $config = New-Object Windows.Networking.NetworkOperators.NetworkOperatorTetheringAccessPointConfiguration
            $config.Ssid = [string]$request.ssid; $config.Passphrase = [string]$request.password
            Await-Action ($selectedManager.ConfigureAccessPointAsync($config))
            $result = Await-Result ($selectedManager.StartTetheringAsync()) ([Windows.Networking.NetworkOperators.NetworkOperatorTetheringOperationResult])
            $verified = ($result.Status.ToString() -eq 'Success' -and $selectedManager.TetheringOperationalState.ToString() -eq 'On')
            Emit @{ok=$verified;code=$(if($verified){'started'}else{'operation_failed'});detail=$result.Status.ToString()}
        }
    } elseif ($request.operation -eq 'stop') {
        if ($stateName -eq 'off' -and $observedManager) { Emit @{ok=$true;code='stopped';detail=''} }
        elseif ($stateName -eq 'on' -and $observedManager) {
            $result = Await-Result ($observedManager.StopTetheringAsync()) ([Windows.Networking.NetworkOperators.NetworkOperatorTetheringOperationResult])
            $verified = ($result.Status.ToString() -eq 'Success' -and $observedManager.TetheringOperationalState.ToString() -eq 'Off')
            Emit @{ok=$verified;code=$(if($verified){'stopped'}else{'operation_failed'});detail=$result.Status.ToString()}
        } else { Emit @{ok=$false;code='state_unknown';detail=$stateName} }
    } else { Emit @{ok=$false;code='unsupported';detail='operation'} }
} catch { Emit @{ok=$false;code=(Error-Code $_);detail=(Error-Detail $_)} }
'''


class BridgeError(RuntimeError):
    def __init__(self, code: str, detail: str = ""):
        super().__init__(code)
        self.code, self.detail = code, detail


def _radio_states() -> dict[str, bool | None]:
    """Query native WLAN software AND hardware radio without localized netsh text."""
    if sys.platform != "win32":
        return {}
    from ctypes import wintypes

    class Guid(ctypes.Structure):
        _fields_ = [("data", ctypes.c_ubyte * 16)]

    class WlanInterface(ctypes.Structure):
        _fields_ = [("guid", Guid), ("description", wintypes.WCHAR * 256),
                    ("state", wintypes.DWORD)]

    class PhyRadio(ctypes.Structure):
        _fields_ = [("index", wintypes.DWORD), ("software", wintypes.DWORD),
                    ("hardware", wintypes.DWORD)]

    wlan = ctypes.WinDLL("wlanapi.dll")
    wlan.WlanOpenHandle.argtypes = [wintypes.DWORD, ctypes.c_void_p,
                                    ctypes.POINTER(wintypes.DWORD), ctypes.POINTER(wintypes.HANDLE)]
    wlan.WlanOpenHandle.restype = wintypes.DWORD
    wlan.WlanEnumInterfaces.argtypes = [wintypes.HANDLE, ctypes.c_void_p,
                                       ctypes.POINTER(ctypes.c_void_p)]
    wlan.WlanEnumInterfaces.restype = wintypes.DWORD
    wlan.WlanQueryInterface.argtypes = [wintypes.HANDLE, ctypes.POINTER(Guid), wintypes.DWORD,
                                       ctypes.c_void_p, ctypes.POINTER(wintypes.DWORD),
                                       ctypes.POINTER(ctypes.c_void_p), ctypes.POINTER(wintypes.DWORD)]
    wlan.WlanQueryInterface.restype = wintypes.DWORD
    wlan.WlanFreeMemory.argtypes = [ctypes.c_void_p]
    wlan.WlanFreeMemory.restype = None
    wlan.WlanCloseHandle.argtypes = [wintypes.HANDLE, ctypes.c_void_p]
    wlan.WlanCloseHandle.restype = wintypes.DWORD
    handle, version = wintypes.HANDLE(), wintypes.DWORD()
    if wlan.WlanOpenHandle(2, None, ctypes.byref(version), ctypes.byref(handle)):
        return {}
    listing = ctypes.c_void_p()
    states: dict[str, bool | None] = {}
    try:
        if wlan.WlanEnumInterfaces(handle, None, ctypes.byref(listing)):
            return states
        count = ctypes.cast(listing, ctypes.POINTER(wintypes.DWORD))[0]
        if count > 128:
            return states
        array = ctypes.cast(listing.value + 8, ctypes.POINTER(WlanInterface))
        for index in range(count):
            entry = array[index]
            key = str(uuid.UUID(bytes_le=bytes(entry.guid.data)))
            size, opcode = wintypes.DWORD(), wintypes.DWORD()
            data = ctypes.c_void_p()
            if wlan.WlanQueryInterface(handle, ctypes.byref(entry.guid), 4, None,
                                       ctypes.byref(size), ctypes.byref(data), ctypes.byref(opcode)):
                states[key] = None
                continue
            try:
                phy_count = ctypes.cast(data, ctypes.POINTER(wintypes.DWORD))[0]
                required = 4 + phy_count * ctypes.sizeof(PhyRadio)
                if not 0 < phy_count <= 64 or size.value < required:
                    states[key] = None
                    continue
                phys = ctypes.cast(data.value + 4, ctypes.POINTER(PhyRadio))
                # A single powered PHY suffices; unknown values never count as on.
                states[key] = any(phys[n].software == 1 and phys[n].hardware == 1
                                  for n in range(phy_count))
            finally:
                wlan.WlanFreeMemory(data)
    except (OSError, ValueError):
        return {}
    finally:
        if listing.value:
            wlan.WlanFreeMemory(listing)
        wlan.WlanCloseHandle(handle, None)
    return states


def _validate_credentials(ssid: str, password: str) -> bool:
    """WPA2 interoperable subset: SSID 1–32 UTF-8 bytes, passphrase 8–63 ASCII."""
    return (bool(ssid.strip()) and 0 < len(ssid.encode("utf-8")) <= 32
            and not any(ord(c) < 32 or ord(c) == 127 for c in ssid)
            and 8 <= len(password) <= 63 and all(32 <= ord(c) <= 126 for c in password))


class WindowsBackend:
    def __init__(self, *, runner=None, radio_reader=None, timeout: float = 32):
        self._runner = runner or subprocess.run
        self._radio_reader = radio_reader or _radio_states
        self.timeout = timeout
        self._upstream_id = ""

    def _request(self, operation: str, **values) -> dict:
        system_root = Path(os.environ.get("SystemRoot", r"C:\Windows"))
        executable = system_root / "System32" / "WindowsPowerShell" / "v1.0" / "powershell.exe"
        encoded = base64.b64encode(POWERSHELL_BRIDGE.encode("utf-16-le")).decode("ascii")
        request = json.dumps({"operation": operation, **values}, ensure_ascii=False)
        try:
            result = self._runner(
                [str(executable), "-NoLogo", "-NoProfile", "-NonInteractive", "-EncodedCommand", encoded],
                input=request, capture_output=True, text=True, encoding="utf-8", errors="replace",
                timeout=self.timeout, creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
                check=False,
            )
        except subprocess.TimeoutExpired as error:
            raise BridgeError("timeout") from error
        except (OSError, ValueError) as error:
            raise BridgeError("unsupported", type(error).__name__) from error
        # Never forward stdout/stderr on error: neither is trusted to omit secrets.
        if result.returncode:
            raise BridgeError("operation_failed", f"PowerShell exit={result.returncode}")
        try:
            data = json.loads(result.stdout.lstrip("\ufeff").strip())
        except (ValueError, TypeError) as error:
            raise BridgeError("state_unknown", "Invalid PowerShell JSON") from error
        if not isinstance(data, dict) or type(data.get("ok")) is not bool:
            raise BridgeError("state_unknown", "Invalid PowerShell response")
        if not data["ok"]:
            code = data.get("code")
            if code not in {"timeout", "permission", "operation_failed", "unsupported", "state_unknown",
                            "no_upstream", "upstream_down", "upstream_not_internet", "no_wifi",
                            "wifi_off", "capability_blocked"}:
                code = "operation_failed"
            detail = data.get("detail", "")
            # Native detail is an enum, HRESULT, or state, never arbitrary error text.
            if not isinstance(detail, str) or len(detail) > 160 or any(c in detail for c in "\n\r"):
                detail = ""
            raise BridgeError(code, detail)
        return data

    def snapshot(self, upstream_id: str = "") -> Snapshot:
        try:
            data = self._request("snapshot", upstream_id=upstream_id or self._upstream_id)
            snapshot = self._snapshot_from_response(data)
            if snapshot.upstream_id:
                self._upstream_id = snapshot.upstream_id
            return snapshot
        except BridgeError as error:
            return Snapshot("Windows", issues=[Issue(error.code, error.detail)])
        except (TypeError, ValueError, KeyError, AttributeError):
            return Snapshot("Windows", issues=[Issue("state_unknown", "Invalid adapter data")])

    def _snapshot_from_response(self, data: dict) -> Snapshot:
        if (not isinstance(data.get("interfaces"), list)
                or data.get("state") not in {"on", "off", "transition", "unknown"}
                or type(data.get("can_start")) is not bool or type(data.get("can_stop")) is not bool
                or not isinstance(data.get("issues"), list)):
            raise BridgeError("state_unknown", "Incomplete adapter data")
        interfaces = []
        for item in data["interfaces"]:
            if (not isinstance(item, dict) or not isinstance(item.get("id"), str)
                    or not isinstance(item.get("name"), str) or type(item.get("up")) is not bool
                    or item.get("kind") not in {"ethernet", "usb", "wifi", "other"}):
                raise BridgeError("state_unknown", "Invalid adapter data")
            interfaces.append(Interface(
                item["id"].strip("{}").lower(), item["name"], item["kind"], item["up"],
                str(item.get("ipv4") or ""), max(-1, int(item.get("received", -1))),
                max(-1, int(item.get("sent", -1))),
            ))
        issues = [Issue(str(item["code"]), str(item.get("detail", ""))) for item in data["issues"]]
        upstream_id = str(data.get("upstream_id") or "").strip("{}").lower()
        wifi_id = str(data.get("wifi_id") or "").strip("{}").lower()
        upstream = next((item for item in interfaces if item.id == upstream_id), None)
        wifi = next((item for item in interfaces if item.id == wifi_id and item.kind == "wifi"), None)
        if upstream is None or upstream.kind not in {"ethernet", "usb"}:
            if not any(item.code == "no_upstream" for item in issues):
                issues.append(Issue("no_upstream"))
        elif not upstream.up and not any(item.code == "upstream_down" for item in issues):
            issues.append(Issue("upstream_down"))
        if wifi is None and not any(item.code == "no_wifi" for item in issues):
            issues.append(Issue("no_wifi"))
        if wifi:
            try:
                radios = self._radio_reader()
            except (OSError, ValueError, AttributeError):
                radios = {}
            enabled = radios.get(wifi_id)
            if enabled is not True and not any(item.code == "wifi_off" for item in issues):
                issues.append(Issue("wifi_off" if enabled is False else "state_unknown", "WLAN radio"))
        state = data["state"]
        if state == "unknown" and not any(item.code == "state_unknown" for item in issues):
            issues.append(Issue("state_unknown"))
        clients = data.get("clients")
        if clients is not None:
            clients = max(0, int(clients))
        return Snapshot("Windows", interfaces=interfaces, upstream_id=upstream_id, wifi_id=wifi_id,
                        state=state, issues=issues, ssid=str(data.get("ssid") or ""), clients=clients,
                        can_start=data["can_start"] and state == "off" and not issues,
                        can_stop=data["can_stop"] and state == "on")

    def start(self, upstream_id: str, ssid: str, password: str) -> ActionResult:
        if not _validate_credentials(ssid, password):
            return ActionResult(False, "invalid_credentials")
        # Re-observe immediately before mutation; stale UI state never authorizes it.
        current = self.snapshot(upstream_id)
        if not current.can_start:
            issue = current.issues[0] if current.issues else Issue("state_unknown")
            return ActionResult(False, issue.code, issue.detail)
        try:
            data = self._request("start", upstream_id=current.upstream_id, ssid=ssid, password=password)
            if data.get("code") != "started":
                return ActionResult(False, "operation_failed")
            self._upstream_id = current.upstream_id
            return ActionResult(True, "started")
        except BridgeError as error:
            return ActionResult(False, error.code, error.detail)

    def stop(self) -> ActionResult:
        # Do not validate ingress, radio, or credentials here: shutdown must remain
        # possible after a cable is removed or its Internet access disappears.
        try:
            data = self._request("stop", upstream_id=self._upstream_id)
            return ActionResult(data.get("code") == "stopped",
                                "stopped" if data.get("code") == "stopped" else "operation_failed")
        except BridgeError as error:
            return ActionResult(False, error.code, error.detail)

    def open_settings(self) -> None:
        if sys.platform != "win32":
            raise RuntimeError("Windows settings can only be opened on Windows")
        os.startfile("ms-settings:network-mobilehotspot")
