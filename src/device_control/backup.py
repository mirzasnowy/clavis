"""Backup manifest + restore plan. Backup FIRST, change second.

A backup is a JSON manifest, not a disk image:
- Windows: AppX list, services list, startup list, theme/registry keys
- Linux: package list, service list, autostart list, gsettings dump
- Android: package list + launcher default + settings dump
Restore = re-enable / reinstall / re-apply from the manifest.
For Android, restore.sh is also written (pm enable per package).
"""
import datetime
import json
import os


def backup_dir_for(device_name, stamp=None):
    stamp = stamp or datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    path = os.path.expanduser(f"~/.device-control/backups/{device_name}/{stamp}")
    os.makedirs(path, exist_ok=True)
    return path


def write_manifest(device_name, data, backup_dir=None):
    backup_dir = backup_dir or backup_dir_for(device_name)
    path = os.path.join(backup_dir, "manifest.json")
    manifest = {"device": device_name, "created": backup_dir.split("/")[-1], **data}
    with open(path, "w") as f:
        json.dump(manifest, f, indent=2)
    return path


def latest_backup(device_name):
    base = os.path.expanduser(f"~/.device-control/backups/{device_name}")
    if not os.path.isdir(base):
        return None
    dirs = sorted(os.listdir(base))
    return os.path.join(base, dirs[-1]) if dirs else None


def restore_plan(device_name):
    latest = latest_backup(device_name)
    if not latest:
        return {"error": f"no backup found for {device_name}"}
    manifest_path = os.path.join(latest, "manifest.json")
    manifest = {}
    if os.path.exists(manifest_path):
        with open(manifest_path) as f:
            manifest = json.load(f)
    return {"device": device_name, "backup_dir": latest, "manifest": manifest,
            "steps": [
                "Android: run sh restore.sh in backup dir, or Settings > Apps > enable each package",
                "Windows: reinstall AppX from Microsoft Store, re-enable services from manifest",
                "Linux: apt install <packages from manifest>, systemctl enable <services from manifest>",
            ]}
