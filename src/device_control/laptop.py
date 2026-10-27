"""Laptop dispatcher: Windows if PowerShell present, else Linux.

A laptop is not an OS. This dispatcher detects the host OS at
runtime instead of assuming it, so the same 'laptop' device works
whether it is Windows or Linux. On a non-matching host, callers get
the exact script/commands for the other OS in dry-run mode.
"""
import platform

from device_control import linux, windows


def detect():
    if platform.system() == "Windows" or windows.available():
        return "windows"
    return "linux"


def appearance_commands(profile="dark", wallpaper=""):
    if detect() == "windows":
        return windows.appearance_commands(profile, wallpaper)
    return linux.appearance_commands(profile)


def list_commands():
    if detect() == "windows":
        return windows.list_commands()
    return {"packages": "dpkg -l / dnf list installed / pacman -Q",
            "services": "systemctl list-units --type=service --state=running",
            "autostart": "~/.config/autostart/*.desktop"}
