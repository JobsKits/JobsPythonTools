"""Platform-neutral hotspot observations. Created by Jobs."""
from dataclasses import dataclass, field

@dataclass(frozen=True)
class Interface:
    id: str
    name: str
    kind: str  # ethernet / usb / wifi / other
    up: bool = False
    ipv4: str = ""
    received: int = -1
    sent: int = -1

@dataclass(frozen=True)
class Issue:
    code: str
    detail: str = ""

@dataclass
class Snapshot:
    platform: str
    interfaces: list[Interface] = field(default_factory=list)
    upstream_id: str = ""
    wifi_id: str = ""
    state: str = "unknown"  # on / off / unknown / transition
    issues: list[Issue] = field(default_factory=list)
    ssid: str = ""
    clients: int | None = None
    # macOS can require one-time setup and permission; controls fail closed.
    can_start: bool = False
    can_stop: bool = False
    detail: str = ""

    def interface(self, identifier):
        return next((item for item in self.interfaces if item.id == identifier), None)

@dataclass(frozen=True)
class ActionResult:
    ok: bool
    code: str
    detail: str = ""
