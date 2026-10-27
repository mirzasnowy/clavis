"""ADB driver — Android HP + TV. No root, disable-user only."""
import os
import shutil
import subprocess


def adb_available():
    return shutil.which("adb") is not None


def run_adb(args, device_address=""):
    if not adb_available():
        return False, "adb not found: install Android platform-tools first (https://developer.android.com/tools/adb)"
    cmd = ["adb"]
    if device_address:
        cmd += ["-s", device_address]
    cmd += args
    try:
        out = subprocess.run(cmd, capture_output=True, text=True, timeout=90)
    except Exception as e:
        return False, f"adb failed: {e}"
    if out.returncode != 0:
        return False, (out.stderr or out.stdout or "adb error").strip()
    return True, out.stdout.strip()


def list_devices():
    ok, out = run_adb(["devices", "-l"])
    if not ok:
        return ok, out
    devs = []
    for line in out.splitlines()[1:]:
        if not line.strip():
            continue
        p = line.split()
        devs.append({"serial": p[0], "state": p[1] if len(p) > 1 else ""})
    return True, devs


def probe(device_address=""):
    results = {}
    for label, args in [
        ("model", ["shell", "getprop", "ro.product.model"]),
        ("brand", ["shell", "getprop", "ro.product.brand"]),
        ("android", ["shell", "getprop", "ro.build.version.release"]),
        ("launcher", ["shell", "cmd", "package", "resolve-activity", "--brief",
                      "-a", "android.intent.action.MAIN",
                      "-c", "android.intent.category.HOME"]),
    ]:
        ok, out = run_adb(args, device_address)
        results[label] = out if ok else f"error: {out}"
    ok, out = run_adb(["shell", "pm", "list", "packages"], device_address)
    results["package_count"] = len(out.splitlines()) if ok else f"error: {out}"
    return True, results


def list_packages(device_address=""):
    ok, out = run_adb(["shell", "pm", "list", "packages"], device_address)
    if not ok:
        return ok, out
    return True, [l.replace("package:", "").strip() for l in out.splitlines() if l.strip()]


def backup_packages(device_address="", backup_dir=""):
    ok, out = run_adb(["shell", "pm", "list", "packages"], device_address)
    if not ok:
        return False, out
    os.makedirs(backup_dir, exist_ok=True)
    with open(os.path.join(backup_dir, "packages.txt"), "w") as f:
        f.write(out + "\n")
    with open(os.path.join(backup_dir, "restore.sh"), "w") as f:
        f.write("#!/bin/sh\n# Restore Android: re-enable packages from packages.txt\n")
        for line in out.splitlines():
            pkg = line.replace("package:", "").strip()
            if pkg:
                f.write(f"adb shell pm enable {pkg}\n")
    return True, {"packages_file": os.path.join(backup_dir, "packages.txt"),
                  "restore_script": os.path.join(backup_dir, "restore.sh"),
                  "count": len(out.splitlines())}


def parse_debloat_list(path):
    pkgs = []
    with open(path) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#"):
                pkgs.append(line)
    return pkgs


def debloat(device_address="", packages=None, dry_run=True, backup_dir=""):
    packages = packages or []
    if dry_run:
        return True, {"dry_run": True, "would_disable": packages,
                      "note": "No change made. Re-run with --confirm to apply."}
    if not backup_dir:
        return False, "backup_dir required before any real debloat"
    results = {}
    for pkg in packages:
        ok, out = run_adb(["shell", "pm", "disable-user", "--user", "0", pkg], device_address)
        results[pkg] = "disabled" if ok else f"error: {out}"
    return True, results


def restore(device_address="", packages=None):
    results = {}
    for pkg in (packages or []):
        ok, out = run_adb(["shell", "pm", "enable", pkg], device_address)
        results[pkg] = "enabled" if ok else f"error: {out}"
    return True, results


def screenshot(device_address="", out_path="/tmp/device-control-screenshot.png"):
    ok, out = run_adb(["exec-out", "screencap", "-p"], device_address)
    # exec-out is binary; subprocess text mode above corrupts it, so redo binary
    if adb_available():
        cmd = ["adb"]
        if device_address:
            cmd += ["-s", device_address]
        cmd += ["exec-out", "screencap", "-p"]
        r = subprocess.run(cmd, capture_output=True, timeout=60)
        if r.returncode == 0 and r.stdout[:8] == b"\x89PNG\r\n\x1a\n":
            with open(out_path, "wb") as f:
                f.write(r.stdout)
            return True, {"screenshot": out_path, "bytes": len(r.stdout)}
        return False, (r.stderr.decode(errors="ignore") or "screencap failed")
    return False, out


def install_apk(device_address="", apk_path=""):
    return run_adb(["install", "-r", apk_path], device_address)


def set_launcher(device_address="", launcher_pkg=""):
    return run_adb(["shell", "cmd", "package", "set-home-activity", launcher_pkg], device_address)
