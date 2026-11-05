"""Windows 原生 ETW 本地收发验收；不访问互联网。Created by Jobs."""
from pathlib import Path
import ctypes as ct
import json
import os
import socket
import sys
import threading
import time

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from jobs_app_traffic_monitor.collectors.windows_etw import WindowsEtwCollector
from jobs_app_traffic_monitor.collectors.windows_etw import SESSION_NAME, _Properties


def main():
    """真实 TCP/UDP 回环收发后检查当前 PID 计数与 ETW 会话撤回。"""
    if sys.platform != "win32":
        raise SystemExit("此验收只能在 64 位 Windows 中运行。")
    collector = WindowsEtwCollector()
    collector.start()
    session = collector._session
    try:
        def wait_for_bytes(minimum_in, minimum_out):
            deadline = time.monotonic() + 10
            observed = None
            while time.monotonic() < deadline:
                observed = next((row for row in collector.snapshot() if os.getpid() in row.pids), None)
                if observed and observed.bytes_in >= minimum_in and observed.bytes_out >= minimum_out:
                    return observed
                time.sleep(0.5)
            raise RuntimeError("ETW 没有观察到当前 PID 的真实收发：" + repr(observed))

        payload = b"J" * 65536
        with socket.socket() as listener:
            listener.bind(("127.0.0.1", 0))
            listener.listen()
            listener.settimeout(5)
            errors = []
            def receive():
                try:
                    connection, _ = listener.accept()
                    with connection:
                        connection.settimeout(5)
                        while chunk := connection.recv(65536):
                            connection.sendall(chunk)
                except Exception as error:
                    errors.append(str(error))
            thread = threading.Thread(target=receive, daemon=True)
            thread.start()
            with socket.create_connection(listener.getsockname(), timeout=5) as client:
                for _ in range(16):
                    client.sendall(payload)
                    remaining = len(payload)
                    while remaining:
                        data = client.recv(remaining)
                        if not data:
                            raise RuntimeError("TCP echo closed early")
                        remaining -= len(data)
            thread.join(6)
            if thread.is_alive() or errors:
                raise RuntimeError("TCP local fixture failed: " + str(errors))
        tcp = wait_for_bytes(2097152, 2097152)
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as receiver:
            receiver.bind(("127.0.0.1", 0))
            receiver.settimeout(5)
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sender:
                for _ in range(32):
                    sender.sendto(payload[:1400], receiver.getsockname())
                    if len(receiver.recv(2048)) != 1400:
                        raise RuntimeError("UDP local fixture length mismatch")
        observed = wait_for_bytes(tcp.bytes_in + 44800, tcp.bytes_out + 44800)
        if not observed.app_path or os.path.normcase(os.path.realpath(observed.app_path)) != os.path.normcase(os.path.realpath(sys.executable)):
            raise RuntimeError("ETW 收发没有绑定到当前进程已验证的 Python EXE 身份：" + repr(observed))
        print(json.dumps({"status": "PASS", "pid": os.getpid(), "exe": observed.app_path,
                          "bytes_in": observed.bytes_in, "bytes_out": observed.bytes_out,
                          "udp_bytes_in": observed.bytes_in - tcp.bytes_in,
                          "udp_bytes_out": observed.bytes_out - tcp.bytes_out,
                          "session": SESSION_NAME}, ensure_ascii=False))
    finally:
        collector.stop()
    # 按命名查询验证会话真的消失，而非只检查 Python 状态。
    props = ct.create_string_buffer(ct.sizeof(_Properties) + 2048)
    ct.cast(props, ct.POINTER(_Properties)).contents.Wnode.BufferSize = ct.sizeof(props)
    ct.cast(props, ct.POINTER(_Properties)).contents.LoggerNameOffset = ct.sizeof(_Properties)
    result = session._dll.ControlTraceW(0, SESSION_NAME, props, 0)
    if result != 4201:
        raise RuntimeError("ETW 会话停止后仍可查询，错误码：" + str(result))
    print("PASS: owned ETW session removed; local TCP/UDP sockets closed")


if __name__ == "__main__":
    main()
