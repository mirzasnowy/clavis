"""See the screen + click buttons — Android via ADB, no root.

How it works (all native Android tools, nothing rebuilt):
1. See what app is open: `dumpsys window` -> mCurrentFocus / mFocusedApp.
2. See the screen as a picture: `adb exec-out screencap -p` (PNG).
3. See buttons as data (not just pixels): `uiautomator dump`
   -> /sdcard/window_dump.xml -> parse nodes: text, content-desc,
   resource-id, class, clickable, bounds [x1,y1][x2,y2].
4. Click a button by its label: find node whose text/content-desc
   contains the label (clickable preferred) -> tap its centre:
   `adb shell input tap <x> <y>`.
5. Other input: `input keyevent <KEY>`, `input swipe x1 y1 x2 y2`,
   `input text <text with spaces as %s>`.

On Windows, the equivalent is: screenshot via PowerShell/.NET +
UI Automation (inspect.exe / FlaUI pattern) — not implemented in
v1 here because this host is not Windows; the Android path below
is the complete one, Windows UI Automation is documented as TODO
in docs/ui-automation.md.
On Linux, equivalent is: screenshot (gnome-screenshot / grim) +
AT-SPI (pyatspi) — also TODO, same reason.
"""
import re
import xml.etree.ElementTree as ET

from device_control import adb


def parse_bounds(bounds):
    """'[100,200][300,400]' -> (100,200,300,400)."""
    m = re.match(r"\[(\d+),(\d+)\]\[(\d+),(\d+)\]", bounds or "")
    if not m:
        return None
    return tuple(int(x) for x in m.groups())


def parse_dump(xml_text):
    """Parse uiautomator XML into a list of nodes."""
    nodes = []
    try:
        root = ET.fromstring(xml_text)
    except Exception as e:
        return {"error": f"invalid ui xml: {e}", "nodes": []}
    for el in root.iter("node"):
        b = parse_bounds(el.get("bounds", ""))
        if not b:
            continue
        x1, y1, x2, y2 = b
        nodes.append({
            "text": el.get("text", ""),
            "content_desc": el.get("content-desc", ""),
            "resource_id": el.get("resource-id", ""),
            "class": el.get("class", ""),
            "clickable": el.get("clickable") == "true",
            "bounds": [x1, y1, x2, y2],
            "center": [(x1 + x2) // 2, (y1 + y2) // 2],
        })
    return {"nodes": nodes, "count": len(nodes)}


def find_by_text(nodes, query):
    """Find clickable node whose text/content-desc contains query (case-insensitive)."""
    q = query.lower()
    candidates = [n for n in nodes
                  if q in (n["text"] or "").lower() or q in (n["content_desc"] or "").lower()]
    if not candidates:
        return None
    # Prefer clickable, then exact text match, then shortest label
    candidates.sort(key=lambda n: (not n["clickable"],
                                   n["text"].lower() != q,
                                   len(n["text"] or n["content_desc"] or "")))
    return candidates[0]


def dump_ui(device_address=""):
    """Return parsed UI nodes for the current screen (needs adb + device)."""
    ok, out = adb.run_adb(["shell", "uiautomator", "dump", "/sdcard/window_dump.xml"], device_address)
    if not ok:
        return False, out
    # Pull via exec-out cat (binary-safe text for XML)
    ok2, xml = adb.run_adb(["shell", "cat", "/sdcard/window_dump.xml"], device_address)
    if not ok2:
        return False, xml
    parsed = parse_dump(xml)
    if "error" in parsed:
        return False, parsed["error"]
    return True, parsed


def current_app(device_address=""):
    ok, out = adb.run_adb(["shell", "dumpsys", "window", "windows"], device_address)
    if not ok:
        return False, out
    m = re.search(r"mCurrentFocus=.*?(\S+?)/", out)
    if m:
        return True, {"current_app": m.group(1), "raw_focus": m.group(0)}
    m2 = re.search(r"mFocusedApp=.*?(\S+?)/", out)
    if m2:
        return True, {"current_app": m2.group(1), "raw_focus": m2.group(0)}
    return False, "could not parse current app from dumpsys window"


def tap_xy(device_address="", x=0, y=0):
    return adb.run_adb(["shell", "input", "tap", str(x), str(y)], device_address)


def tap_by_text(device_address="", text=""):
    ok, parsed = dump_ui(device_address)
    if not ok:
        return False, parsed
    node = find_by_text(parsed["nodes"], text)
    if not node:
        return False, f"button '{text}' not found on screen ({parsed['count']} nodes dumped)"
    x, y = node["center"]
    ok2, out = tap_xy(device_address, x, y)
    return ok2, {"tapped": node, "tap": [x, y], "adb": out}


def key(device_address="", keycode="KEYCODE_BACK"):
    return adb.run_adb(["shell", "input", "keyevent", keycode], device_address)


def swipe(device_address="", x1=0, y1=0, x2=0, y2=0, duration_ms=300):
    return adb.run_adb(["shell", "input", "swipe", str(x1), str(y1), str(x2), str(y2), str(duration_ms)], device_address)


def type_text(device_address="", text=""):
    safe = text.replace(" ", "%s")
    return adb.run_adb(["shell", "input", "text", safe], device_address)
