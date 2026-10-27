"""Linux laptop/server driver — apt/dnf/pacman + systemd + gsettings.

Read-only probes run on any Linux host. Destructive commands are
returned as a script in dry-run mode, and only executed with
--confirm on a host where the package manager exists.
"""
import shutil
import subprocess


def run(cmd, timeout=60):
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    except Exception as e:
        return False, f"failed: {e}"
    if r.returncode != 0:
        return False, (r.stderr or r.stdout or "error").strip()
    return True, r.stdout.strip()


def pkg_manager():
    for m in ("apt", "dnf", "pacman"):
        if shutil.which(m):
            return m
    return None


def list_packages():
    m = pkg_manager()
    if m == "apt":
        ok, out = run(["dpkg", "-l"])
        if not ok:
            return ok, out
        pkgs = []
        for line in out.splitlines():
            if line.startswith("ii "):
                parts = line.split()
                if len(parts) >= 2:
                    pkgs.append(parts[1])
        return True, pkgs
    if m == "dnf":
        return run(["dnf", "list", "installed", "-q"])
    if m == "pacman":
        return run(["pacman", "-Q"])
    return False, "no supported package manager found"


def list_services():
    return run(["systemctl", "list-units", "--type=service", "--state=running", "--no-pager", "--no-legend"])


def list_autostart():
    import glob
    import os
    files = []
    for pat in (os.path.expanduser("~/.config/autostart/*.desktop"),
                "/etc/xdg/autostart/*.desktop"):
        files += glob.glob(pat)
    return True, files


def appearance_commands(profile="dark"):
    if profile == "dark":
        return ["gsettings set org.gnome.desktop.interface gtk-theme 'Yaru-dark'",
                "gsettings set org.gnome.desktop.interface color-scheme 'prefer-dark'"]
    if profile == "light":
        return ["gsettings set org.gnome.desktop.interface gtk-theme 'Yaru'",
                "gsettings set org.gnome.desktop.interface color-scheme 'prefer-light'"]
    if profile == "minimal":
        return ["gsettings set org.gnome.desktop.interface gtk-theme 'Yaru-dark'",
                "gsettings set org.gnome.desktop.interface enable-animations false"]
    return []


def launch_command(app, url=""):
    """Native Linux open/run. GUI app runs detached; URL/file via xdg-open."""
    if url:
        return f"xdg-open '{url}'"
    return f"nohup {app} >/dev/null 2>&1 &"


def debloat_commands(packages):
    m = pkg_manager()
    if m == "apt":
        return [f"sudo apt remove --purge -y {p}" for p in packages] + ["sudo apt autoremove -y"]
    if m == "dnf":
        return [f"sudo dnf remove -y {p}" for p in packages]
    if m == "pacman":
        return [f"sudo pacman -R --noconfirm {p}" for p in packages]
    return []
