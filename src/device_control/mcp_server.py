"""MCP stdio server v1 — JSON-RPC 2.0, 9 tools, no external deps.

Methods: initialize, ping, notifications/initialized (no-op),
tools/list, tools/call. MCP destructive tools are dry-run only:
device_debloat and device_appearance in MCP never execute, they
return the exact plan. Real execution is via CLI --confirm on the
paired device. This is deliberate: a prompt-injected host must not
be able to debloat a device through MCP alone.
"""
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from device_control import adb, android, appsearch, backup, devices, laptop, linux, never, openwebsite, security, ui, windows  # noqa: E402

TOOLS = [
    {"name": "device_list", "description": "List registered devices, kind, transport, scopes."},
    {"name": "device_probe", "description": "Read-only probe of a device."},
    {"name": "device_apps", "description": "List installed apps/packages (read-only)."},
    {"name": "device_services", "description": "List running services (Windows/Linux; Android returns a note)."},
    {"name": "device_debloat", "description": "DRY-RUN ONLY in MCP: returns would_disable + blocked_never. Use CLI --confirm on the device for real execution."},
    {"name": "device_restore", "description": "Return restore plan from latest backup (dry-run)."},
    {"name": "device_appearance", "description": "DRY-RUN ONLY in MCP: returns native commands for a profile."},
    {"name": "device_backup", "description": "Write a backup manifest (Android: also backup packages if adb present)."},
    {"name": "device_launch", "description": "DRY-RUN ONLY in MCP: returns the native launch command for an app/URL. Use CLI --confirm on the device for real launch."},
    {"name": "device_open_website", "description": "DRY-RUN ONLY in MCP: returns the native OS command to open an http/https URL in the default browser. Never open a site via ui tap. Use CLI open-website --confirm on the device for real opening."},
    {"name": "device_ui", "description": "Android UI: current app + UI dump (read-only). Tap is DRY-RUN ONLY in MCP."},
    {"name": "device_search_app", "description": "Search Android app by NAME (no package needed): known alias + suffix + fuzzy, ranked, with ambiguity flag."},
    {"name": "device_screenshot", "description": "Android screenshot via adb screencap (read-only)."},
    {"name": "audit_verify", "description": "Verify the audit hash-chain."},
]


def call_tool(name, args):
    args = args or {}
    if name == "device_list":
        return {"devices": [d.to_dict() for d in devices.load_registry()]}
    if name == "device_probe":
        dev = devices.get_device(args.get("device", ""))
        if not dev:
            return {"error": "unknown device"}
        if dev.transport == "adb":
            ok, res = adb.probe(dev.address)
            return {"ok": ok, "result": res}
        if dev.kind == "windows":
            return {"dry_run": True, "would_run": windows.list_commands()}
        if dev.kind in ("laptop", "linux") and laptop.detect() == "linux":
            ok, pkgs = linux.list_packages()
            return {"ok": ok, "package_count": len(pkgs) if ok else pkgs}
        return {"device": dev.name, "note": "probe via CLI on the real device"}
    if name == "device_apps":
        dev = devices.get_device(args.get("device", ""))
        if not dev:
            return {"error": "unknown device"}
        if dev.transport == "adb":
            ok, res = android.list_apps(dev.address)
            return {"ok": ok, "result": res}
        return {"dry_run": True, "note": "use CLI apps on the real device"}
    if name == "device_services":
        dev = devices.get_device(args.get("device", ""))
        if not dev:
            return {"error": "unknown device"}
        if dev.kind in ("laptop", "linux") and laptop.detect() == "linux":
            ok, res = linux.list_services()
            return {"ok": ok, "result": res}
        return {"note": "Android: use device_apps. Windows: use CLI services on the real host."}
    if name == "device_debloat":
        dev = devices.get_device(args.get("device", ""))
        if not dev:
            return {"error": "unknown device"}
        pkgs = []
        if args.get("list_file"):
            try:
                pkgs = adb.parse_debloat_list(args["list_file"])
            except FileNotFoundError:
                return {"error": f"list file not found: {args['list_file']}"}
        kind = "android" if dev.transport == "adb" else ("windows" if dev.kind in ("windows", "laptop") else "linux-pkg")
        safe, blocked = never.filter_never(pkgs, kind)
        return {"dry_run": True, "would_disable": safe, "blocked_never": blocked,
                "note": "MCP never executes debloat. Use CLI --confirm on the paired device."}
    if name == "device_restore":
        return backup.restore_plan(args.get("device", ""))
    if name == "device_appearance":
        dev = devices.get_device(args.get("device", ""))
        if not dev:
            return {"error": "unknown device"}
        profile = args.get("profile", "dark")
        if dev.transport == "adb":
            cmds = android.appearance_commands(profile)
        elif dev.kind == "windows":
            cmds = windows.appearance_commands(profile, args.get("wallpaper", ""))
        else:
            cmds = laptop.appearance_commands(profile, args.get("wallpaper", ""))
        return {"dry_run": True, "profile": profile, "would_run": cmds}
    if name == "device_backup":
        dev = devices.get_device(args.get("device", ""))
        if not dev:
            return {"error": "unknown device"}
        bdir = backup.backup_dir_for(dev.name)
        path = backup.write_manifest(dev.name, {"via": "mcp"}, bdir)
        return {"manifest": path, "backup_dir": bdir}
    if name == "device_launch":
        dev = devices.get_device(args.get("device", ""))
        if not dev:
            return {"error": "unknown device"}
        app = args.get("app", "")
        if dev.transport == "adb":
            cmd = android.launch_command(app, args.get("activity", ""), args.get("url", ""))
        elif dev.kind == "windows":
            cmd = windows.launch_command(app, args.get("url", ""))
        else:
            cmd = windows.launch_command(app, args.get("url", "")) if laptop.detect() == "windows" else linux.launch_command(app, args.get("url", ""))
        return {"dry_run": True, "device": dev.name, "app": app, "would_run": cmd,
                "note": "MCP never launches apps. Use CLI launch --confirm on the paired device."}
    if name == "device_open_website":
        dev = devices.get_device(args.get("device", ""))
        if not dev:
            return {"error": "unknown device"}
        cmd, err = openwebsite.command_for(dev, args.get("url", ""))
        if not cmd:
            return {"error": err}
        return {"dry_run": True, "device": dev.name, "url": args.get("url", ""), "would_run": cmd,
                "note": "MCP never opens a browser. Use CLI open-website --confirm on the paired device."}
    if name == "device_ui":
        dev = devices.get_device(args.get("device", ""))
        if not dev or dev.transport != "adb":
            return {"error": "unknown Android device"}
        action = args.get("action", "current")
        if action == "current":
            ok, res = ui.current_app(dev.address)
            return {"ok": ok, "result": res}
        if action == "dump":
            ok, res = ui.dump_ui(dev.address)
            return {"ok": ok, "result": res}
        if action == "tap":
            return {"dry_run": True, "text": args.get("text", ""),
                    "would_run": f"dump UI -> find '{args.get('text','')}' -> input tap <center>",
                    "note": "MCP never taps. Use CLI ui tap --confirm on the paired device."}
        return {"error": f"unknown ui action: {action}"}
    if name == "device_search_app":
        dev = devices.get_device(args.get("device", ""))
        if not dev or dev.transport != "adb":
            return {"error": "unknown Android device"}
        ok, pkgs = android.list_apps(dev.address)
        if not ok:
            return {"ok": False, "result": pkgs}
        return appsearch.search(args.get("query", ""), pkgs)
    if name == "device_screenshot":
        dev = devices.get_device(args.get("device", ""))
        if not dev or dev.transport != "adb":
            return {"error": "unknown Android device"}
        ok, res = adb.screenshot(dev.address, args.get("out", "/tmp/device-control-screenshot.png"))
        return {"ok": ok, "result": res}
    if name == "audit_verify":
        ok, count = security.AuditChain().verify()
        return {"audit_ok": ok, "entries": count}
    return {"error": f"unknown tool: {name}"}


def handle(req):
    method = req.get("method", "")
    rid = req.get("id")
    if method == "initialize":
        return {"jsonrpc": "2.0", "id": rid, "result": {
            "protocolVersion": "2024-11-05", "capabilities": {"tools": {}},
            "serverInfo": {"name": "device-control", "version": "0.1.0"}}}
    if method == "ping":
        return {"jsonrpc": "2.0", "id": rid, "result": {}}
    if method.startswith("notifications/"):
        return None
    if method == "tools/list":
        return {"jsonrpc": "2.0", "id": rid, "result": {"tools": [
            {"name": t["name"], "description": t["description"],
             "inputSchema": {"type": "object", "properties": {}}} for t in TOOLS]}}
    if method == "tools/call":
        params = req.get("params", {})
        result = call_tool(params.get("name", ""), params.get("arguments", {}))
        return {"jsonrpc": "2.0", "id": rid, "result": {
            "content": [{"type": "text", "text": json.dumps(result, ensure_ascii=False)}]}}
    return {"jsonrpc": "2.0", "id": rid, "error": {"code": -32601, "message": f"unknown method: {method}"}}


def main():
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            req = json.loads(line)
        except Exception:
            print(json.dumps({"jsonrpc": "2.0", "id": None, "error": {"code": -32700, "message": "parse error"}}), flush=True)
            continue
        resp = handle(req)
        if resp is not None:
            print(json.dumps(resp, ensure_ascii=False), flush=True)


if __name__ == "__main__":
    main()
