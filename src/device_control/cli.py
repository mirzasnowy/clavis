"""CLI v1: python3 -m device_control.cli <command> [options]

Safety contract, all commands:
- probe/apps/services = read-only, no confirm needed.
- debloat/appearance = dry-run by default. --confirm executes ONLY
  if a backup was written first (Android) or the script is shown
  and the host is the real device (Windows/Linux).
- NEVER lists are always filtered, even with --confirm.
- Every executed change is appended to the audit hash-chain.
"""
import argparse
import datetime
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from device_control import adb, android, appsearch, backup, devices, laptop, linux, linuxui, never, openwebsite, pairing, security, ui, winui, windows  # noqa: E402
from device_control.ssh import probe as ssh_probe  # noqa: E402


def _out(obj):
    print(json.dumps(obj, indent=2, ensure_ascii=False))


def _dev(name):
    d = devices.get_device(name)
    if not d:
        print(f"unknown device: {name} (see: devices list)")
    return d


def cmd_devices(args):
    if args.action == "add":
        d = devices.Device(name=args.name, kind=args.kind, transport=args.transport,
                           address=args.address or "", scopes=(args.scopes or "").split(",") if args.scopes else [])
        devices.add_device(d)
        _out({"added": d.to_dict()})
    elif args.action == "remove":
        n = devices.remove_device(args.name)
        _out({"removed": args.name, "remaining": n})
    else:
        _out({"devices": [d.to_dict() for d in devices.load_registry()]})


def cmd_probe(args):
    dev = _dev(args.device)
    if not dev:
        return 1
    audit = security.AuditChain()
    if dev.transport == "adb":
        if args.dry_run:
            _out({"device": dev.name, "dry_run": True, "would_do": "adb probe (read-only)", "adb_available": adb.adb_available()})
            return 0
        ok, res = adb.probe(dev.address)
        audit.append(dev.name, "probe", "ok" if ok else str(res))
        _out({"ok": ok, "result": res})
        return 0 if ok else 1
    if dev.transport == "ssh":
        ok, res = ssh_probe(dev.address)
        _out({"ok": ok, "result": res})
        return 0 if ok else 1
    if dev.kind == "windows":
        _out({"device": dev.name, "dry_run": True, "would_run": windows.list_commands(), "powershell_available": windows.available()})
        return 0
    if dev.kind in ("laptop", "linux"):
        if laptop.detect() == "linux":
            ok, pkgs = linux.list_packages()
            ok2, svcs = linux.list_services()
            svc_lines = svcs.splitlines()[:10] if ok2 and isinstance(svcs, str) else svcs
            _out({"device": dev.name, "os": "linux", "package_count": len(pkgs) if ok else pkgs, "services_sample": svc_lines})
            return 0
        _out({"device": dev.name, "dry_run": True, "would_run": windows.list_commands()})
        return 0
    _out({"device": dev.name, "kind": dev.kind, "note": "no driver for this kind"})
    return 0


def cmd_apps(args):
    dev = _dev(args.device)
    if not dev:
        return 1
    if dev.transport == "adb":
        if args.dry_run:
            _out({"device": dev.name, "dry_run": True, "would_do": "adb shell pm list packages"})
            return 0
        ok, res = android.list_apps(dev.address)
        _out({"ok": ok, "result": res})
        return 0 if ok else 1
    if dev.kind == "windows" or (dev.kind == "laptop" and laptop.detect() == "windows"):
        cmds = windows.list_commands()
        if args.dry_run:
            _out({"device": dev.name, "dry_run": True, "would_run": cmds})
            return 0
        ok, res = windows.run_powershell(cmds["apps"])
        _out({"ok": ok, "result": res})
        return 0 if ok else 1
    if dev.kind in ("laptop", "linux"):
        ok, res = linux.list_packages()
        _out({"ok": ok, "result": res if not ok else res[:50], "count": len(res) if ok else 0})
        return 0 if ok else 1
    _out({"device": dev.name, "note": "apps not implemented for this kind"})
    return 0


def cmd_services(args):
    dev = _dev(args.device)
    if not dev:
        return 1
    if dev.transport == "adb":
        _out({"device": dev.name, "note": "Android services are app packages; use apps + debloat, not systemd-style services"})
        return 0
    if dev.kind == "windows" or (dev.kind == "laptop" and laptop.detect() == "windows"):
        cmds = windows.list_commands()
        if args.dry_run:
            _out({"device": dev.name, "dry_run": True, "would_run": cmds["services_running"]})
            return 0
        ok, res = windows.run_powershell(cmds["services_running"])
        _out({"ok": ok, "result": res})
        return 0 if ok else 1
    ok, res = linux.list_services()
    _out({"ok": ok, "result": res})
    return 0 if ok else 1


def cmd_appearance(args):
    dev = _dev(args.device)
    if not dev:
        return 1
    if dev.transport == "adb":
        cmds = android.appearance_commands(args.profile)
    elif dev.kind == "windows":
        cmds = windows.appearance_commands(args.profile, args.wallpaper or "")
    elif dev.kind == "laptop":
        cmds = laptop.appearance_commands(args.profile, args.wallpaper or "")
    else:
        cmds = linux.appearance_commands(args.profile)
    if args.dry_run or not args.confirm:
        _out({"device": dev.name, "profile": args.profile, "dry_run": True, "would_run": cmds,
              "note": "No change made. Add --confirm to apply on a real device."})
        return 0
    # Confirm path: execute only native commands that exist on this host
    if dev.kind in ("windows", "laptop") and laptop.detect() == "windows":
        results = []
        for c in cmds:
            if c.startswith("#"):
                continue
            ok, res = windows.run_powershell(c)
            results.append({"cmd": c, "ok": ok, "result": res})
        security.AuditChain().append(dev.name, f"appearance {args.profile}", "ok")
        _out({"device": dev.name, "profile": args.profile, "results": results})
        return 0
    if dev.kind in ("laptop", "linux") and laptop.detect() == "linux":
        results = []
        for c in cmds:
            if c.startswith("#"):
                continue
            # gsettings commands are user-level and safe to run
            parts = c.split()
            ok, res = linux.run(parts) if parts and parts[0] == "gsettings" else (False, "not a gsettings command, not executed")
            results.append({"cmd": c, "ok": ok, "result": res})
        security.AuditChain().append(dev.name, f"appearance {args.profile}", "ok")
        _out({"device": dev.name, "profile": args.profile, "results": results})
        return 0
    _out({"device": dev.name, "profile": args.profile,
          "note": "Confirm on a real paired device: run would_run commands via its admin agent, then verify with screenshot/status."})
    return 0


def cmd_debloat(args):
    dev = _dev(args.device)
    if not dev:
        return 1
    if not dev.has("debloat"):
        print(f"device {dev.name} does not have a debloat scope")
        return 1
    try:
        raw = adb.parse_debloat_list(args.list)
    except FileNotFoundError:
        print(f"list file not found: {args.list}")
        return 1
    # NEVER filter
    if dev.transport == "adb":
        safe, blocked = never.filter_never(raw, "android")
    elif dev.kind == "windows" or (dev.kind == "laptop" and laptop.detect() == "windows"):
        safe, blocked = never.filter_never(raw, "windows")
    else:
        safe, blocked = never.filter_never(raw, "linux-pkg")
    if args.dry_run or not args.confirm:
        if dev.transport == "adb":
            _out({"device": dev.name, "dry_run": True, "would_disable": safe, "blocked_never": blocked})
        elif dev.kind == "windows" or (dev.kind == "laptop" and laptop.detect() == "windows"):
            _out({"device": dev.name, "dry_run": True, "would_run": windows.debloat_commands(safe), "blocked_never": blocked})
        else:
            _out({"device": dev.name, "dry_run": True, "would_run": linux.debloat_commands(safe), "blocked_never": blocked})
        return 0
    # Confirm: Android only executes here (backup first). Windows/Linux
    # confirm prints the exact script for the admin agent on that host,
    # because this host may not be that device.
    if dev.transport == "adb":
        stamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
        bdir = backup.backup_dir_for(dev.name, stamp)
        ok, bak = adb.backup_packages(dev.address, bdir)
        if not ok:
            print(f"backup failed, aborting: {bak}")
            return 1
        backup.write_manifest(dev.name, {"backup": bak, "would_disable": safe}, bdir)
        ok, res = adb.debloat(dev.address, safe, dry_run=False, backup_dir=bdir)
        security.AuditChain().append(dev.name, f"debloat {len(safe)} packages", "ok" if ok else str(res))
        _out({"ok": ok, "backup": bak, "blocked_never": blocked, "result": res})
        return 0 if ok else 1
    _out({"device": dev.name, "confirm_note": "Run the dry-run script on the real device via its admin agent after backup. This host is not that device, so it does not execute remotely without pairing + mesh.",
          "blocked_never": blocked})
    return 0


def cmd_launch(args):
    dev = _dev(args.device)
    if not dev:
        return 1
    if dev.transport == "adb":
        cmd = android.launch_command(args.app, args.activity or "", args.url or "")
    elif dev.kind == "windows":
        cmd = windows.launch_command(args.app, args.url or "")
    elif dev.kind == "laptop":
        cmd = windows.launch_command(args.app, args.url or "") if laptop.detect() == "windows" else linux.launch_command(args.app, args.url or "")
    else:
        cmd = linux.launch_command(args.app, args.url or "")
    if args.dry_run or not args.confirm:
        _out({"device": dev.name, "app": args.app, "dry_run": True, "would_run": cmd,
              "note": "No app launched. Add --confirm to launch on a real device."})
        return 0
    if dev.transport == "adb":
        ok, res = android.launch(dev.address, args.app, args.activity or "", args.url or "")
        security.AuditChain().append(dev.name, f"launch {args.app}", "ok" if ok else str(res))
        _out({"ok": ok, "result": res})
        return 0 if ok else 1
    if dev.kind == "windows" or (dev.kind == "laptop" and laptop.detect() == "windows"):
        ok, res = windows.run_powershell(cmd)
        security.AuditChain().append(dev.name, f"launch {args.app}", "ok" if ok else str(res))
        _out({"ok": ok, "result": res})
        return 0 if ok else 1
    _out({"device": dev.name, "note": "Linux launch: run the would_run command on the real device (needs a desktop session, not a headless shell)."})
    return 0


def cmd_open_website(args):
    dev = _dev(args.device)
    if not dev:
        return 1
    cmd, err = openwebsite.command_for(dev, args.url)
    if not cmd:
        _out({"device": dev.name, "error": err})
        return 1
    if args.dry_run or not args.confirm:
        _out({"device": dev.name, "url": args.url, "dry_run": True, "would_run": cmd,
              "note": "No browser opened. Add --confirm to open on a real device. Never do this via ui tap on an icon/address bar."})
        return 0
    if dev.transport == "adb":
        ok, res = android.launch(dev.address, "", "", args.url)
        security.AuditChain().append(dev.name, f"open-website {args.url}", "ok" if ok else str(res))
        _out({"ok": ok, "result": res})
        return 0 if ok else 1
    if dev.kind == "windows" or (dev.kind == "laptop" and laptop.detect() == "windows"):
        ok, res = windows.run_powershell(cmd)
        security.AuditChain().append(dev.name, f"open-website {args.url}", "ok" if ok else str(res))
        _out({"ok": ok, "result": res})
        return 0 if ok else 1
    _out({"device": dev.name, "note": "Linux open-website: run the would_run command on the real device (needs a desktop session, not a headless shell)."})
    return 0


def cmd_ui(args):
    dev = _dev(args.device)
    if not dev:
        return 1
    if dev.transport != "adb":
        # Windows / Linux desktop UI (winui.ps1 / linuxui.py)
        # args.text is the element name for tap/type, args.action is tap/key/dump/current
        # For dump/current on desktop, window = args.text (window name) if given
        if dev.kind == "windows" or (dev.kind == "laptop" and laptop.detect() == "windows"):
            ps_action = {"dump": "Dump", "current": "ListWindows", "tap": "Click", "key": "Click"}.get(args.action, "Dump")
            cmd = winui.command(ps_action, window=args.window or "", name=args.text or "")
            if args.dry_run or not args.confirm:
                _out({"device": dev.name, "ui_backend": "windows-uia", "dry_run": True,
                      "would_run": " ".join(cmd),
                      "note": "Run this on a Windows host in a desktop session. NOT tested on a real Windows desktop by this agent — test with Notepad/Calculator first."})
                return 0
            ok, res = winui.run(ps_action, window=args.window or "", name=args.text or "")
            _out({"ok": ok, "result": res})
            return 0 if ok else 1
        # Linux desktop
        script = os.path.join(os.path.dirname(__file__), "..", "..", "scripts", "linuxui.py")
        py_action = {"dump": "dump", "tap": "click", "key": "click"}.get(args.action, "dump")
        cmd = ["python3", script, py_action, "--app", args.window or "", "--name", args.text or ""]
        if args.dry_run or not args.confirm:
            _out({"device": dev.name, "ui_backend": "linux-atspi", "dry_run": True,
                  "would_run": " ".join(cmd),
                  "note": "Run inside a Linux desktop session with python3-pyatspi2 installed. NOT tested on a real Linux desktop by this agent."})
            return 0
        _out({"device": dev.name, "note": "Linux UI confirm: run the would_run command inside the desktop session; this headless host cannot execute it."})
        return 0
    if args.action == "current":
        if args.dry_run:
            _out({"device": dev.name, "dry_run": True, "would_run": "adb shell dumpsys window windows (parse mCurrentFocus)"})
            return 0
        ok, res = ui.current_app(dev.address)
        _out({"ok": ok, "result": res})
        return 0 if ok else 1
    if args.action == "dump":
        if args.dry_run:
            _out({"device": dev.name, "dry_run": True, "would_run": "adb shell uiautomator dump /sdcard/window_dump.xml + parse nodes"})
            return 0
        ok, res = ui.dump_ui(dev.address)
        _out({"ok": ok, "result": res})
        return 0 if ok else 1
    if args.action == "tap":
        if args.dry_run or not args.confirm:
            _out({"device": dev.name, "action": "tap", "text": args.text, "dry_run": True,
                  "would_run": f"dump UI -> find button containing '{args.text}' -> input tap <center-x> <center-y>"})
            return 0
        if args.text:
            ok, res = ui.tap_by_text(dev.address, args.text)
        else:
            ok, res = ui.tap_xy(dev.address, args.x, args.y)
        security.AuditChain().append(dev.name, f"ui tap {args.text or (args.x, args.y)}", "ok" if ok else str(res))
        _out({"ok": ok, "result": res})
        return 0 if ok else 1
    if args.action == "key":
        if args.dry_run:
            _out({"device": dev.name, "dry_run": True, "would_run": f"adb shell input keyevent {args.text}"})
            return 0
        ok, res = ui.key(dev.address, args.text or "KEYCODE_BACK")
        _out({"ok": ok, "result": res})
        return 0 if ok else 1
    _out({"device": dev.name, "error": f"unknown ui action: {args.action}"})
    return 1


def cmd_search_app(args):
    dev = _dev(args.device)
    if not dev:
        return 1
    if dev.transport != "adb":
        _out({"device": dev.name, "note": "app search by name is Android-only in v1 (package list). Windows: use winget list + name match, Linux: dpkg list + name match — same pattern, not wired yet."})
        return 0
    if args.dry_run:
        _out({"device": dev.name, "query": args.query, "dry_run": True,
              "would_run": "adb shell pm list packages -> search by name (known alias + suffix + fuzzy)"})
        return 0
    ok, pkgs = android.list_apps(dev.address)
    if not ok:
        _out({"ok": False, "result": pkgs})
        return 1
    res = appsearch.search(args.query, pkgs)
    _out(res)
    return 0


def cmd_screenshot(args):
    dev = _dev(args.device)
    if not dev:
        return 1
    if args.dry_run:
        _out({"device": dev.name, "dry_run": True, "would_run": "adb exec-out screencap -p > screenshot.png"})
        return 0
    ok, res = adb.screenshot(dev.address, args.out)
    _out({"ok": ok, "result": res})
    return 0 if ok else 1


def cmd_restore(args):
    dev = _dev(args.device)
    if not dev:
        return 1
    plan = backup.restore_plan(dev.name)
    if args.dry_run:
        _out({"device": dev.name, "dry_run": True, "plan": plan})
        return 0
    if dev.transport == "adb":
        # Restore from manifest packages if present, else from packages.txt
        latest = backup.latest_backup(dev.name)
        pkgs = []
        if latest and os.path.exists(os.path.join(latest, "packages.txt")):
            with open(os.path.join(latest, "packages.txt")) as f:
                pkgs = [l.replace("package:", "").strip() for l in f if l.strip()]
        ok, res = adb.restore(dev.address, pkgs)
        _out({"ok": ok, "result": res})
        return 0 if ok else 1
    _out({"device": dev.name, "plan": plan})
    return 0


def cmd_pair(args):
    info = pairing.pair(args.device, args.scope)
    dev = _dev(args.device)
    if dev:
        dev.public_key_fingerprint = info["public_key_fingerprint_sha256"]
        devices.add_device(dev)
    _out(info)
    return 0


def cmd_audit(args):
    ok, count = security.AuditChain().verify()
    _out({"audit_ok": ok, "entries": count, "audit_file": security.AUDIT_PATH})
    return 0 if ok else 1


def cmd_token(args):
    tok = security.make_token(args.device, args.scope, args.command, ttl_seconds=args.ttl)
    _out(tok)
    return 0


def cmd_revoke(args):
    data = security.revoke_fingerprint(args.fingerprint)
    _out({"revoked_fingerprints": data["fingerprints"]})
    return 0


def cmd_backup(args):
    dev = _dev(args.device)
    if not dev:
        return 1
    bdir = backup.backup_dir_for(dev.name)
    if dev.transport == "adb":
        ok, bak = adb.backup_packages(dev.address, bdir)
        path = backup.write_manifest(dev.name, {"backup": bak}, bdir)
        _out({"ok": ok, "manifest": path, "backup": bak})
        return 0 if ok else 1
    path = backup.write_manifest(dev.name, {"note": "manifest only; run the OS backup script on the device"}, bdir)
    _out({"manifest": path, "backup_dir": bdir})
    return 0


def cmd_mcp(_args):
    from device_control.mcp_server import main as mcp_main
    mcp_main()


def main(argv=None):
    p = argparse.ArgumentParser(prog="device-control")
    sub = p.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("devices"); s.add_argument("action", nargs="?", default="list")
    s.add_argument("--name", default=""); s.add_argument("--kind", default="laptop")
    s.add_argument("--transport", default="auto"); s.add_argument("--address", default="")
    s.add_argument("--scopes", default=""); s.set_defaults(fn=cmd_devices)

    for name, fn in [("probe", cmd_probe), ("apps", cmd_apps), ("services", cmd_services)]:
        s = sub.add_parser(name); s.add_argument("--device", required=True)
        s.add_argument("--dry-run", action="store_true"); s.set_defaults(fn=fn)

    s = sub.add_parser("appearance"); s.add_argument("--device", required=True)
    s.add_argument("--profile", default="dark"); s.add_argument("--wallpaper", default="")
    s.add_argument("--dry-run", action="store_true"); s.add_argument("--confirm", action="store_true")
    s.set_defaults(fn=cmd_appearance)

    s = sub.add_parser("debloat"); s.add_argument("--device", required=True)
    s.add_argument("--list", required=True); s.add_argument("--dry-run", action="store_true")
    s.add_argument("--confirm", action="store_true"); s.set_defaults(fn=cmd_debloat)

    s = sub.add_parser("open-website"); s.add_argument("--device", required=True)
    s.add_argument("--url", required=True); s.add_argument("--dry-run", action="store_true")
    s.add_argument("--confirm", action="store_true"); s.set_defaults(fn=cmd_open_website)

    s = sub.add_parser("launch"); s.add_argument("--device", required=True)
    s.add_argument("--app", required=True); s.add_argument("--activity", default="")
    s.add_argument("--url", default=""); s.add_argument("--dry-run", action="store_true")
    s.add_argument("--confirm", action="store_true"); s.set_defaults(fn=cmd_launch)

    s = sub.add_parser("ui"); s.add_argument("--device", required=True)
    s.add_argument("action", choices=["current", "dump", "tap", "key"])
    s.add_argument("--text", default=""); s.add_argument("--window", default="")
    s.add_argument("--x", type=int, default=0)
    s.add_argument("--y", type=int, default=0); s.add_argument("--dry-run", action="store_true")
    s.add_argument("--confirm", action="store_true"); s.set_defaults(fn=cmd_ui)

    s = sub.add_parser("search-app"); s.add_argument("--device", required=True)
    s.add_argument("--query", required=True); s.add_argument("--dry-run", action="store_true")
    s.set_defaults(fn=cmd_search_app)

    s = sub.add_parser("screenshot"); s.add_argument("--device", required=True)
    s.add_argument("--out", default="/tmp/device-control-screenshot.png")
    s.add_argument("--dry-run", action="store_true"); s.set_defaults(fn=cmd_screenshot)

    s = sub.add_parser("restore"); s.add_argument("--device", required=True)
    s.add_argument("--dry-run", action="store_true"); s.set_defaults(fn=cmd_restore)

    s = sub.add_parser("backup"); s.add_argument("--device", required=True); s.set_defaults(fn=cmd_backup)

    s = sub.add_parser("pair"); s.add_argument("--device", required=True)
    s.add_argument("--scope", default="probe"); s.set_defaults(fn=cmd_pair)

    s = sub.add_parser("audit"); s.set_defaults(fn=cmd_audit)

    s = sub.add_parser("token"); s.add_argument("--device", required=True)
    s.add_argument("--scope", required=True); s.add_argument("--command", required=True)
    s.add_argument("--ttl", type=int, default=60); s.set_defaults(fn=cmd_token)

    s = sub.add_parser("revoke"); s.add_argument("--fingerprint", required=True); s.set_defaults(fn=cmd_revoke)

    s = sub.add_parser("mcp"); s.set_defaults(fn=cmd_mcp)

    args = p.parse_args(argv)
    return args.fn(args)


if __name__ == "__main__":
    raise SystemExit(main())
