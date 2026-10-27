"""NEVER lists — packages/services that must never be auto-disabled.

These are checked before ANY debloat, even with --confirm.
If a user explicitly wants one of these changed, they must do it
manually outside this tool, after reading the warning.
"""
NEVER_WINDOWS = {
    # substrings, lowercased
    "microsoft.windowsstore", "microsoft.desktopappinstaller",
    "microsoft.net", "microsoft.vclibs", "windows.terminal",
    "microsoftwindows.client.webexperience",
}
NEVER_LINUX_PACKAGES = {
    "systemd", "dbus", "network-manager", "networkmanager",
    "gdm3", "sddm", "lightdm", "linux-image", "linux-headers",
    "grub", "ubuntu-desktop", "gnome-shell",
}
NEVER_LINUX_SERVICES = {
    "dbus.service", "systemd-logind.service", "systemd-journald.service",
    "NetworkManager.service", "gdm.service", "sddm.service",
}
NEVER_ANDROID = {
    "com.android.settings", "com.android.systemui",
    "com.android.launcher", "com.google.android.inputmethod.latin",
    "com.android.phone", "com.android.contacts",
}


def is_never_windows(name):
    n = name.lower()
    return any(x in n for x in NEVER_WINDOWS)


def is_never_linux_package(name):
    return name.lower() in NEVER_LINUX_PACKAGES


def is_never_linux_service(name):
    return name in NEVER_LINUX_SERVICES


def is_never_android(pkg):
    return pkg in NEVER_ANDROID


def filter_never(items, kind):
    """Return (safe, blocked). kind in windows/linux-pkg/linux-svc/android."""
    safe, blocked = [], []
    for it in items:
        if kind == "windows" and is_never_windows(it):
            blocked.append(it)
        elif kind == "linux-pkg" and is_never_linux_package(it):
            blocked.append(it)
        elif kind == "linux-svc" and is_never_linux_service(it):
            blocked.append(it)
        elif kind == "android" and is_never_android(it):
            blocked.append(it)
        else:
            safe.append(it)
    return safe, blocked
