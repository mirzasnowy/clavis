#!/usr/bin/env python3
"""Linux UI Automation — AT-SPI via pyatspi (GNOME official stack).

AT-SPI model (GNOME/Accerciser docs):
- Desktop = registry.getDesktop(0), each app = an Accessible.
- Every Accessible has: name, role, childCount, getChildAt(i).
- If it implements Action: queryAction().doAction(i) where the
  action name is usually "click" or "press".
- If it implements EditableText: queryEditableText().setText(...).
- If it implements Text: queryText() to read text.

Install on Ubuntu/Debian (desktop session, not headless):
    sudo apt install python3-pyatspi2 at-spi2-core
    # then run inside the desktop session (same $DISPLAY / Wayland session as the app)

Usage:
    python3 linuxui.py dump --app Firefox
    python3 linuxui.py find --app Firefox --name "Settings"
    python3 linuxui.py click --app Firefox --name "Settings"
    python3 linuxui.py type --app "Text Editor" --name "Text" --text "Hello"

Safety: click/type fail closed on 0 or >1 matches.
STATUS: written from AT-SPI docs, NOT tested on a real Linux desktop
by this agent (host here is headless). Test on your Linux laptop
in a desktop session first.
"""
import argparse
import json
import sys

try:
    import pyatspi
    HAS_ATSPI = True
except Exception as e:
    HAS_ATSPI = False
    ATSPI_ERROR = str(e)


def walk(acc, depth=0, max_depth=12):
    if depth > max_depth:
        return None
    node = {"name": acc.name or "", "role": str(acc.getRoleName()),
            "children": []}
    try:
        for i in range(acc.childCount):
            child = walk(acc.getChildAt(i), depth + 1, max_depth)
            if child:
                node["children"].append(child)
    except Exception:
        pass
    return node


def find_all(acc, query, out, depth=0, max_depth=12):
    if depth > max_depth:
        return
    name = (acc.name or "").lower()
    if query.lower() in name:
        out.append(acc)
    try:
        for i in range(acc.childCount):
            find_all(acc.getChildAt(i), query, out, depth + 1, max_depth)
    except Exception:
        pass


def find_app(app_name):
    desktop = pyatspi.Registry.getDesktop(0)
    for i in range(desktop.childCount):
        app = desktop.getChildAt(i)
        if app_name.lower() in (app.name or "").lower():
            return app
    return None


def do_click(acc):
    try:
        action = acc.queryAction()
        for i in range(action.nActions):
            if action.getName(i) in ("click", "press", "activate"):
                action.doAction(i)
                return True, action.getName(i)
        # Fallback: first action
        if action.nActions > 0:
            action.doAction(0)
            return True, action.getName(0)
    except Exception as e:
        return False, str(e)
    return False, "no Action interface"


def do_type(acc, text):
    try:
        editable = acc.queryEditableText()
        editable.setText(text, len(text))
        return True, "EditableText.setText"
    except Exception:
        pass
    try:
        # Fallback via Action? No — typing needs focus + keyboard.
        # Caller should use xdotool type after focusing, documented in docs.
        return False, "element is not editable via EditableText; focus it then use keyboard input"
    except Exception as e:
        return False, str(e)


def main():
    if not HAS_ATSPI:
        print(json.dumps({"error": f"pyatspi not available: {ATSPI_ERROR}",
                          "install": "sudo apt install python3-pyatspi2 at-spi2-core, run inside a desktop session"}))
        return 1
    p = argparse.ArgumentParser()
    p.add_argument("action", choices=["dump", "find", "click", "type"])
    p.add_argument("--app", required=True)
    p.add_argument("--name", default="")
    p.add_argument("--text", default="")
    args = p.parse_args()
    app = find_app(args.app)
    if not app:
        print(json.dumps({"error": f"app not found: {args.app}"}))
        return 1
    if args.action == "dump":
        print(json.dumps({"app": app.name, "tree": walk(app)}))
        return 0
    matches = []
    find_all(app, args.name, matches)
    if args.action == "find":
        print(json.dumps({"app": app.name, "matches": len(matches),
                          "names": [m.name for m in matches]}))
        return 0
    if len(matches) == 0:
        print(json.dumps({"error": f"element not found: {args.name}"}))
        return 1
    if len(matches) > 1:
        print(json.dumps({"error": f"ambiguous: {len(matches)} match '{args.name}', refusing first"}))
        return 1
    if args.action == "click":
        ok, how = do_click(matches[0])
        print(json.dumps({"ok": ok, "via": how, "name": matches[0].name}))
        return 0 if ok else 1
    if args.action == "type":
        ok, how = do_type(matches[0], args.text)
        print(json.dumps({"ok": ok, "via": how, "name": matches[0].name}))
        return 0 if ok else 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
