"""按 ETW 网络事件中的 PID 统计字节，不读取数据包内容。Created by Jobs."""
from __future__ import annotations

import ctypes as ct
from collections import deque
from dataclasses import dataclass
import ntpath
import os
import struct
import sys
import threading
import time
import uuid

from jobs_app_traffic_monitor.app_resolver import AppIdentity
from jobs_app_traffic_monitor.collectors.base import TrafficCollector
from jobs_app_traffic_monitor.models import AppTraffic

TCP_GUID = uuid.UUID("9a280ac0-c8e0-11d1-84e2-00c04fb998a2").bytes_le
UDP_GUID = uuid.UUID("bf3a50c5-a9c9-4988-a005-2df0b7c80f80").bytes_le
SESSION_NAME = "JobsAppTrafficMonitor.Network"
U16, U32, U64 = ct.c_uint16, ct.c_uint32, ct.c_uint64
FILETIME_EPOCH = 116444736000000000


@dataclass(frozen=True, slots=True)
class _ProcessIdentity:
    identity: AppIdentity
    created: int
    observed_until: int


@dataclass(slots=True)
class _Ledger:
    pid: int
    identity: AppIdentity
    bytes_in: int = 0
    bytes_out: int = 0
    updated_at: float = 0.0


def _filetime_now() -> int:
    """与 ProcessTrace 默认转换后的事件时间、GetProcessTimes 使用同一时间基准。"""
    return time.time_ns() // 100 + FILETIME_EPOCH


class _SessionCleanupError(OSError):
    """同时保存启动原错与撤回错误，避免清理失败覆盖诊断。"""
    def __init__(self, primary_error: BaseException, cleanup_error: Exception) -> None:
        self.primary_error = primary_error
        self.cleanup_error = cleanup_error
        super().__init__(f"{primary_error}；撤回本次会话失败，可重试停止：{cleanup_error}")


class _Wnode(ct.Structure):
    _fields_ = [("BufferSize", U32), ("ProviderId", U32), ("HistoricalContext", U64),
                ("TimeStamp", U64), ("Guid", ct.c_ubyte * 16), ("ClientContext", U32),
                ("Flags", U32)]


class _Properties(ct.Structure):
    _fields_ = [("Wnode", _Wnode)] + [(name, U32) for name in (
        "BufferSize", "MinimumBuffers", "MaximumBuffers", "MaximumFileSize", "LogFileMode",
        "FlushTimer", "EnableFlags", "AgeLimit", "NumberOfBuffers", "FreeBuffers", "EventsLost",
        "BuffersWritten", "LogBuffersLost", "RealTimeBuffersLost",
    )] + [("LoggerThreadId", ct.c_void_p), ("LogFileNameOffset", U32), ("LoggerNameOffset", U32)]


class _Descriptor(ct.Structure):
    _fields_ = [("Id", U16), ("Version", ct.c_ubyte), ("Channel", ct.c_ubyte),
                ("Level", ct.c_ubyte), ("Opcode", ct.c_ubyte), ("Task", U16), ("Keyword", U64)]


class _Header(ct.Structure):
    _fields_ = [("Size", U16), ("HeaderType", U16), ("Flags", U16), ("EventProperty", U16),
                ("ThreadId", U32), ("ProcessId", U32), ("TimeStamp", U64),
                ("ProviderId", ct.c_ubyte * 16), ("EventDescriptor", _Descriptor),
                ("ProcessorTime", U64), ("ActivityId", ct.c_ubyte * 16)]


class _Record(ct.Structure):
    _fields_ = [("EventHeader", _Header), ("BufferContext", U32),
                ("ExtendedDataCount", U16), ("UserDataLength", U16),
                ("ExtendedData", ct.c_void_p), ("UserData", ct.c_void_p),
                ("UserContext", ct.c_void_p)]


class _Logfile(ct.Structure):
    # Win64 EVENT_TRACE (88) / TRACE_LOGFILE_HEADER (280) 只作 OpenTrace 输出区。
    # 保留完整 ABI 空间；本项目从 EVENT_RECORD 读取事件，不能缩短这两个结构。
    _fields_ = [("LogFileName", ct.c_wchar_p), ("LoggerName", ct.c_wchar_p),
                ("CurrentTime", U64), ("BuffersRead", U32), ("ProcessTraceMode", U32),
                ("CurrentEvent", ct.c_ubyte * 88), ("LogfileHeader", ct.c_ubyte * 280),
                ("BufferCallback", ct.c_void_p), ("BufferSize", U32), ("Filled", U32),
                ("EventsLost", U32), ("EventRecordCallback", ct.c_void_p),
                ("IsKernelTrace", U32), ("Context", ct.c_void_p)]


def decode_network_event(provider: bytes, version: int, opcode: int,
                         payload: bytes) -> tuple[int, int, int] | None:
    """只解释 v2 TCP/UDP 收发；重传/连接不重复计数，PID 来自 payload。"""
    if provider not in (TCP_GUID, UDP_GUID) or version != 2 or opcode not in (10, 11, 26, 27):
        return None
    if len(payload) < 8:
        return None
    pid, size = struct.unpack_from("<II", payload)
    if not pid or not size:
        return None
    return (pid, size, 0) if opcode in (11, 27) else (pid, 0, size)


def _etw_error(operation: str, code: int) -> OSError:
    """把常见原生权限/会话错误转换为可操作提示。"""
    if code in (5, 1314):
        message = "网络采集需要管理员权限；请退出后以管理员身份重新运行。"
    elif code == 183:
        message = (f"{SESSION_NAME} 会话已存在；先退出其它流量监控实例。"
                   "若上次异常退出，可在管理员终端运行 logman stop " + SESSION_NAME + " -ets。")
    else:
        message = "Windows ETW 调用失败。"
    return OSError(code, f"{operation}: {message}（错误 {code}）")


class _EtwSession:
    """只创建/停止本应用命名会话；不接管 NT Kernel Logger，不写 ETL。"""
    def __init__(self, consume) -> None:
        if sys.platform != "win32" or ct.sizeof(ct.c_void_p) != 8:
            raise OSError("Windows ETW 采集需要 64 位 Windows Python。")
        self._dll = ct.WinDLL("advapi32", use_last_error=True)
        for name, arguments, result in (
            ("StartTraceW", [ct.POINTER(U64), ct.c_wchar_p, ct.c_void_p], U32),
            ("ControlTraceW", [U64, ct.c_wchar_p, ct.c_void_p, U32], U32),
            ("OpenTraceW", [ct.POINTER(_Logfile)], U64),
            ("ProcessTrace", [ct.POINTER(U64), U32, ct.c_void_p, ct.c_void_p], U32),
            ("CloseTrace", [U64], U32),
        ):
            function = getattr(self._dll, name)
            function.argtypes, function.restype = arguments, result
        self._consume = consume
        self._controller = U64()
        self._consumer: int | None = None
        self._buffer = ct.create_string_buffer(ct.sizeof(_Properties) + 2048)
        self._properties = _Properties.from_buffer(self._buffer)
        self._properties.Wnode.BufferSize = ct.sizeof(self._buffer)
        self._properties.Wnode.Flags = 0x00020000  # WNODE_FLAG_TRACED_GUID
        self._properties.Wnode.ClientContext = 1  # QPC
        self._properties.LogFileMode = 0x02000100  # SYSTEM_LOGGER | REAL_TIME
        self._properties.EnableFlags = 0x10010000  # NETWORK_TCPIP | NO_SYSCONFIG
        self._properties.BufferSize = 64
        self._properties.MinimumBuffers = 4
        self._properties.MaximumBuffers = 64
        self._properties.FlushTimer = 1
        self._properties.LoggerNameOffset = ct.sizeof(_Properties)
        callback_type = ct.WINFUNCTYPE(None, ct.POINTER(_Record))
        self._callback = callback_type(self._on_event)
        self._logfile = _Logfile()
        self._logfile.LoggerName = SESSION_NAME
        self._logfile.ProcessTraceMode = 0x10000100  # EVENT_RECORD | REAL_TIME
        self._logfile.EventRecordCallback = ct.cast(self._callback, ct.c_void_p)

    def _on_event(self, pointer) -> None:
        """回调只复制 PID/计数，进程查询放在快照线程，避免阻塞 ETW。"""
        event = pointer.contents
        header = event.EventHeader
        provider = bytes(header.ProviderId)
        if provider not in (TCP_GUID, UDP_GUID) or not event.UserData or event.UserDataLength < 8:
            return
        parsed = decode_network_event(provider, header.EventDescriptor.Version,
                                      header.EventDescriptor.Opcode, ct.string_at(event.UserData, 8))
        if parsed is not None:
            self._consume(*parsed, header.TimeStamp)

    @property
    def owns_resources(self) -> bool:
        """只有本对象成功取得的句柄才需要撤回；失败后保留所有权。"""
        return bool(self._controller.value or self._consumer is not None)

    def open(self) -> None:
        """同步报告权限失败；OpenTrace 失败时撤回刚创建的会话。"""
        code = self._dll.StartTraceW(ct.byref(self._controller), SESSION_NAME, self._buffer)
        if code:
            self._controller.value = 0
            raise _etw_error("StartTraceW", code)
        try:
            handle = self._dll.OpenTraceW(ct.byref(self._logfile))
            if handle == 0xFFFFFFFFFFFFFFFF:
                raise _etw_error("OpenTraceW", ct.get_last_error())
            self._consumer = handle
        except BaseException as error:
            try:
                self.close()
            except Exception as cleanup_error:
                raise _SessionCleanupError(error, cleanup_error) from error
            raise

    def process(self) -> None:
        """后台消费，非正常退出反馈给 GUI/终端。"""
        handle = U64(self._consumer)
        code = self._dll.ProcessTrace(ct.byref(handle), 1, None, None)
        if code not in (0, 1223):
            raise _etw_error("ProcessTrace", code)

    def check(self) -> None:
        """丢事件代表计数不完整，不能静默展示为精确流量。"""
        code = self._dll.ControlTraceW(self._controller, None, self._buffer, 0)
        if code:
            raise _etw_error("ControlTraceW(query)", code)
        if self._properties.EventsLost or self._properties.RealTimeBuffersLost:
            raise OSError("ETW 缓冲区丢失事件，当前计数不完整；请重新加载采集。")

    def close(self) -> None:
        """只停止自身 controller；失败保留句柄以便再次清理。"""
        error = None
        if self._controller.value:
            code = self._dll.ControlTraceW(self._controller, None, self._buffer, 1)
            if code not in (0, 4201):
                error = _etw_error("ControlTraceW(stop)", code)
            else:
                self._controller.value = 0
        if self._consumer is not None:
            code = self._dll.CloseTrace(self._consumer)
            if code not in (0, 7007):
                error = error or _etw_error("CloseTrace", code)
            else:
                self._consumer = None
        if error:
            raise error


def resolve_windows_process(pid: int) -> _ProcessIdentity | None:
    """从同一进程句柄读取创建时间/EXE，避免 PID 复用时把旧流量归新程序。"""
    kernel = ct.WinDLL("kernel32", use_last_error=True)
    kernel.OpenProcess.argtypes, kernel.OpenProcess.restype = [U32, ct.c_int, U32], ct.c_void_p
    kernel.QueryFullProcessImageNameW.argtypes = [ct.c_void_p, U32, ct.c_wchar_p, ct.POINTER(U32)]
    kernel.QueryFullProcessImageNameW.restype = ct.c_int
    kernel.GetProcessTimes.argtypes = [ct.c_void_p] + [ct.POINTER(U64)] * 4
    kernel.GetProcessTimes.restype = ct.c_int
    kernel.GetExitCodeProcess.argtypes = [ct.c_void_p, ct.POINTER(U32)]
    kernel.GetExitCodeProcess.restype = ct.c_int
    kernel.CloseHandle.argtypes, kernel.CloseHandle.restype = [ct.c_void_p], ct.c_int
    handle = kernel.OpenProcess(0x1000, False, pid)
    if not handle:
        return None
    path = None
    try:
        created, exited, kernel_time, user_time = U64(), U64(), U64(), U64()
        if not kernel.GetProcessTimes(handle, ct.byref(created), ct.byref(exited),
                                      ct.byref(kernel_time), ct.byref(user_time)) or not created.value:
            return None
        exit_code = U32()
        if not kernel.GetExitCodeProcess(handle, ct.byref(exit_code)):
            return None
        if exit_code.value != 259:  # STILL_ACTIVE；运行中 GetProcessTimes 的退出时间未定义。
            if not kernel.GetProcessTimes(handle, ct.byref(created), ct.byref(exited),
                                          ct.byref(kernel_time), ct.byref(user_time)) or not exited.value:
                return None
            observed_until = exited.value
        else:
            observed_until = _filetime_now()
        buffer, length = ct.create_unicode_buffer(32768), U32(32768)
        if kernel.QueryFullProcessImageNameW(handle, 0, buffer, ct.byref(length)):
            path = buffer.value
    finally:
        kernel.CloseHandle(handle)
    name = ntpath.basename(path) if path else f"PID {pid}"
    system_root = os.environ.get("SystemRoot", "")
    system = bool(pid == 4 or (path and system_root and
                              path.casefold().startswith(system_root.rstrip("\\").casefold() + "\\")))
    return _ProcessIdentity(AppIdentity(name, path, path, system), created.value, observed_until)


class WindowsEtwCollector(TrafficCollector):
    """累计启动后的 TCP/UDP IPv4/IPv6 收发，按真实 EXE 聚合。"""
    def __init__(self, stale_after: float = 12.0) -> None:
        self._stale_after = stale_after
        self._lock = threading.Lock()
        self._pending = deque()
        self._pending_limit = 100000
        self._lifetimes: dict[int, dict[int, _ProcessIdentity]] = {}
        self._totals: dict[tuple[int, int | None], _Ledger] = {}
        self._previous: dict[tuple[int, int | None], tuple[int, int]] = {}
        self._last_sample = time.monotonic()
        self._session = None
        self._thread = None
        self._stopping = threading.Event()
        self._error: Exception | None = None

    def _consume(self, pid: int, bytes_in: int, bytes_out: int, event_time: int) -> None:
        """回调只入有界队列；保留事件时间才能验证对应的进程生命周期。"""
        with self._lock:
            if len(self._pending) >= self._pending_limit:
                self._error = OSError("网络事件处理队列已满，当前计数不完整；请重新加载。")
                return
            self._pending.append((pid, bytes_in, bytes_out, event_time, time.monotonic()))

    def _apply_events(self, events, resolved: dict[int, _ProcessIdentity | None]) -> None:
        """在已验证的出生/存活区间内归属事件；无法证明身份时保留未知 PID。"""
        for pid, process in resolved.items():
            if process is None:
                continue
            lifetimes = self._lifetimes.setdefault(pid, {})
            previous = lifetimes.get(process.created)
            if previous and not process.identity.app_path and previous.identity.app_path:
                process = _ProcessIdentity(previous.identity, process.created, process.observed_until)
            lifetimes[process.created] = process
            ledger = self._totals.get((pid, process.created))
            if ledger is not None:
                ledger.identity = process.identity
        for pid, received, sent, event_time, seen_at in events:
            # 不能用“最新 PID”推断已经缓冲的事件属于最新 EXE。
            candidates = [process for process in self._lifetimes.get(pid, {}).values()
                          if process.created <= event_time <= process.observed_until]
            # 时钟变化等原因造成区间重叠时也不能猜测归属。
            process = candidates[0] if len(candidates) == 1 else None
            key = (pid, process.created if process else None)
            if key not in self._totals:
                identity = process.identity if process else AppIdentity(
                    f"PID {pid}（身份未验证）", None, None, pid == 4,
                )
                self._totals[key] = _Ledger(pid, identity)
            ledger = self._totals[key]
            ledger.bytes_in += received
            ledger.bytes_out += sent
            ledger.updated_at = max(ledger.updated_at, seen_at)

    def start(self) -> None:
        """先取得会话再开消费线程；权限错误由调用方直接显示。"""
        if self._thread and self._thread.is_alive() and not self._stopping.is_set():
            return
        if self._session is not None:
            self.stop()
        self._error = None
        self._stopping.clear()
        with self._lock:
            self._totals.clear()
            self._previous.clear()
            self._pending.clear()
            self._lifetimes.clear()
            self._last_sample = time.monotonic()
        session = _EtwSession(self._consume)
        # open 本身也可能在“已建会话但消费失败”后撤回失败，必须先持有 owner。
        self._session = session
        try:
            session.open()
        except BaseException:
            if not session.owns_resources:
                self._session = None
            raise
        self._thread = threading.Thread(target=self._run, name="windows-etw-collector", daemon=True)
        try:
            self._thread.start()
        except BaseException as error:
            try:
                session.close()
            except Exception as cleanup_error:
                raise _SessionCleanupError(error, cleanup_error) from error
            self._session = None
            raise

    def _run(self) -> None:
        """后台失败保留原因，快照不得伪装成正常空列表。"""
        try:
            self._session.process()
            if not self._stopping.is_set():
                self._error = OSError("ETW 采集会话已结束，请重新加载。")
        except Exception as error:
            if not self._stopping.is_set():
                self._error = error

    def stop(self) -> None:
        """停止本次会话并有界等待，不触碰其它跟踪会话。"""
        self._stopping.set()
        if self._session is not None:
            self._session.close()
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=3)
            if self._thread.is_alive():
                raise OSError("ETW 消费线程尚未退出，请稍后重试退出。")
        self._session = None
        self._thread = None

    def snapshot(self) -> list[AppTraffic]:
        """活动行可隐藏，累计账本保留；同 EXE 统计整个采集会话的流量。"""
        if self._error:
            raise self._error
        if self._session is not None:
            self._session.check()
        with self._lock:
            events = list(self._pending)
            self._pending.clear()
        resolved = {pid: resolve_windows_process(pid) for pid in {event[0] for event in events}}
        now = time.monotonic()
        with self._lock:
            self._apply_events(events, resolved)
            if self._error:
                raise self._error
            elapsed = max(now - self._last_sample, 0.001)
            self._last_sample = now
            rows = []
            for key, ledger in self._totals.items():
                before_in, before_out = self._previous.get(key, (0, 0))
                self._previous[key] = (ledger.bytes_in, ledger.bytes_out)
                rows.append((key, ledger.pid, ledger.identity, ledger.bytes_in, ledger.bytes_out,
                             ledger.bytes_in - before_in, ledger.bytes_out - before_out, ledger.updated_at))
        groups: dict[str, list[AppTraffic]] = {}
        for key, pid, identity, received, sent, sample_in, sample_out, updated in rows:
            row = AppTraffic(identity.name, identity.app_path, identity.reveal_path, identity.is_system,
                             (pid,), received, sent, sample_in, sample_out,
                             sample_in / elapsed, sample_out / elapsed, updated)
            group = identity.app_path.casefold() if identity.app_path else repr(key)
            groups.setdefault(group, []).append(row)
        return sorted((AppTraffic(
            app_name=members[0].app_name, app_path=members[0].app_path,
            reveal_path=members[0].reveal_path, is_system=all(row.is_system for row in members),
            pids=tuple(sorted({pid for row in members for pid in row.pids})),
            bytes_in=sum(row.bytes_in for row in members), bytes_out=sum(row.bytes_out for row in members),
            sample_bytes_in=sum(row.sample_bytes_in for row in members),
            sample_bytes_out=sum(row.sample_bytes_out for row in members),
            download_rate=sum(row.download_rate for row in members),
            upload_rate=sum(row.upload_rate for row in members),
            updated_at=max(row.updated_at for row in members),
        ) for members in groups.values() if any(now - row.updated_at <= self._stale_after for row in members)),
                      key=lambda row: row.total_bytes, reverse=True)
