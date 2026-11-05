"""Select native platform operations without importing the other platform."""
import sys

def create_backend():
    if sys.platform == "darwin":
        from .macos import MacOSBackend
        return MacOSBackend()
    if sys.platform == "win32":
        from .windows import WindowsBackend
        return WindowsBackend()
    raise RuntimeError("JobsHotspot supports MacOS and Windows only")
