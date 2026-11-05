"""Credential and counter rules independent of the GUI. Created by Jobs."""
from time import monotonic


def valid_credentials(ssid: str, password: str) -> bool:
    return (bool(ssid.strip()) and 1 <= len(ssid.encode('utf-8')) <= 32
            and not any(ord(c) < 32 or ord(c) == 127 for c in ssid)
            and 8 <= len(password) <= 63 and all(32 <= ord(c) <= 126 for c in password))


class RateTracker:
    """Ignore initial samples, counter resets and adapter changes."""
    def __init__(self):
        self.previous = {}

    def update(self, snapshot, now=None):
        now = monotonic() if now is None else now
        rates = {}
        for interface in snapshot.interfaces:
            old = self.previous.get(interface.id)
            if old and now > old[0]:
                elapsed = now - old[0]
                rates[interface.id] = tuple((value - previous) / elapsed
                    if value >= previous >= 0 else None
                    for value, previous in zip((interface.received, interface.sent), old[1:]))
            else:
                rates[interface.id] = (None, None)
        self.previous = {item.id: (now, item.received, item.sent) for item in snapshot.interfaces}
        return rates


def format_bytes(value, rate=False):
    if value is None or value < 0:
        return '—'
    units = ['B', 'KiB', 'MiB', 'GiB', 'TiB']
    index = 0
    while value >= 1024 and index < len(units) - 1:
        value /= 1024
        index += 1
    return f'{value:.1f} {units[index]}' + ('/s' if rate else '')
