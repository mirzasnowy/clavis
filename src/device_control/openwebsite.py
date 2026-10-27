"""Open a website via the OS native opener — not via UI clicks.

Why a separate tool, not `ui tap` on a browser icon + address bar:
clicking is a multi-step, screen-dependent guess (find icon, wait
for the browser, find the address bar, type, press Enter, survive
autocomplete/focus loss). Opening is one deterministic intent:
the OS is told "open this URL in the default browser" and does it.

Native commands, per device:
- Windows: Start-Process '<url>'
- Linux:   xdg-open '<url>'
- Android: adb shell am start -a android.intent.action.VIEW -d '<url>'

Validation is part of the tool, not an afterthought: only http/https,
no spaces, no shell metacharacters or quotes. A javascript:, file:,
or shell-injected string is rejected before any command is built.
"""
from device_control import android, laptop, linux, windows

_BAD = (" ", "'", '"', ";", "|", "&", "`", "$", "(", ")", "<", ">", "\n", "\r", "\t")


def validate_url(url):
    """Return (True, url) or (False, reason)."""
    if not url or not isinstance(url, str):
        return False, "url is empty"
    url = url.strip()
    if not (url.startswith("http://") or url.startswith("https://")):
        return False, "only http:// or https:// URLs are allowed"
    if any(c in url for c in _BAD):
        return False, "url contains a character that is not allowed"
    rest = url.split("://", 1)[1]
    if not rest or "." not in rest.split("/")[0]:
        return False, "url has no host"
    return True, url


def command_for(dev, url):
    """Native would-run command for this device, or (None, reason)."""
    ok, url_or_reason = validate_url(url)
    if not ok:
        return None, url_or_reason
    url = url_or_reason
    if dev.transport == "adb":
        return android.launch_command("", "", url), None
    if dev.kind == "windows":
        return windows.launch_command("", url), None
    if dev.kind == "laptop":
        if laptop.detect() == "windows":
            return windows.launch_command("", url), None
        return linux.launch_command("", url), None
    return linux.launch_command("", url), None
