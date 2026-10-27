"""Device registry: JSON file, no secrets inside.

Default scope is the agreed set from 2026-10-27:
pc-windows, laptop, hp-android, tv-android.
Secrets (private keys, tokens) are NEVER stored here — they live in
~/.device-control/keys/ (0600) or in the OS keystore/TPM.
"""
import json
import os
from dataclasses import asdict, dataclass, field

DEFAULT_REGISTRY = os.path.expanduser("~/.device-control/devices.json")

EXAMPLE_DEVICES = [
    {"name": "pc-windows", "kind": "windows", "transport": "powershell",
     "address": "localhost",
     "scopes": ["windows.probe", "windows.debloate", "windows.appearance", "windows.apps", "windows.services"],
     "public_key_fingerprint": ""},
    {"name": "laptop", "kind": "laptop", "transport": "auto",
     "address": "localhost",
     "scopes": ["windows.probe", "windows.debloate", "windows.appearance", "windows.apps", "linux.probe", "linux.debloate", "linux.appearance"],
     "public_key_fingerprint": ""},
    {"name": "hp-android", "kind": "android-phone", "transport": "adb",
     "address": "",
     "scopes": ["adb.probe", "adb.debloat", "adb.screenshot", "adb.appearance", "adb.apps"],
     "public_key_fingerprint": ""},
    {"name": "tv-android", "kind": "android-tv", "transport": "adb",
     "address": "",
     "scopes": ["adb.probe", "adb.debloat", "adb.screenshot", "adb.appearance", "adb.apps"],
     "public_key_fingerprint": ""},
]

# Scope families: a debloat scope is any scope ending in .debloat, etc.
def _scope_family(scope):
    return scope.split(".")[-1]


@dataclass
class Device:
    name: str
    kind: str
    transport: str
    address: str = ""
    scopes: list = field(default_factory=list)
    public_key_fingerprint: str = ""

    def to_dict(self):
        return asdict(self)

    def has(self, family):
        return any(s.endswith("." + family) or s == family for s in self.scopes)


def load_registry(path=DEFAULT_REGISTRY):
    if os.path.exists(path):
        try:
            with open(path) as f:
                data = json.load(f)
            return [Device(**d) for d in data.get("devices", [])]
        except Exception:
            pass
    return [Device(**d) for d in EXAMPLE_DEVICES]


def save_registry(devs, path=DEFAULT_REGISTRY):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        json.dump({"devices": [d.to_dict() for d in devs]}, f, indent=2)
    return path


def get_device(name, path=DEFAULT_REGISTRY):
    for d in load_registry(path):
        if d.name == name:
            return d
    return None


def add_device(dev, path=DEFAULT_REGISTRY):
    devs = load_registry(path)
    devs = [d for d in devs if d.name != dev.name] + [dev]
    save_registry(devs, path)
    return dev


def remove_device(name, path=DEFAULT_REGISTRY):
    devs = [d for d in load_registry(path) if d.name != name]
    save_registry(devs, path)
    return len(devs)
