"""Windows driver — PowerShell native. Dry-run = return script, not execute.

On a real Windows host, run_powershell executes the script.
On any other host, available() is False and callers must show the
script to the user instead of pretending it ran.
"""
import shutil
import subprocess

POWERSHELL = shutil.which("pwsh") or shutil.which("powershell")


def available():
    return POWERSHELL is not None


def run_powershell(script):
    if not available():
        return False, "PowerShell not found on this host (not a Windows host)"
    try:
        r = subprocess.run([POWERSHELL, "-NoProfile", "-Command", script],
                           capture_output=True, text=True, timeout=90)
    except Exception as e:
        return False, f"powershell failed: {e}"
    if r.returncode != 0:
        return False, (r.stderr or r.stdout or "powershell error").strip()
    return True, r.stdout.strip()


def list_commands():
    return {
        "apps": "Get-AppxPackage | Select-Object Name, PackageFullName | Sort-Object Name",
        "services_running": "Get-Service | Where-Object {$_.Status -eq 'Running'} | Select-Object Name, DisplayName",
        "startup": "Get-ScheduledTask | Where-Object {$_.State -eq 'Ready'} | Select-Object TaskName",
        "winget": "winget list",
    }


def appearance_script(profile="dark", wallpaper=""):
    cmds = []
    if wallpaper:
        cmds.append(f"Set-ItemProperty -Path 'HKCU:\\Control Panel\\Desktop' -Name Wallpaper -Value '{wallpaper}'")
        cmds.append("RUNDLL32.EXE user32.dll,UpdatePerUserSystemParameters")
    if profile == "dark":
        cmds += [
            "Set-ItemProperty -Path 'HKCU:\\Software\\Microsoft\\Windows\\CurrentVersion\\Themes\\Personalize' -Name AppsUseLightTheme -Value 0",
            "Set-ItemProperty -Path 'HKCU:\\Software\\Microsoft\\Windows\\CurrentVersion\\Themes\\Personalize' -Name SystemUsesLightTheme -Value 0",
        ]
    elif profile == "light":
        cmds += [
            "Set-ItemProperty -Path 'HKCU:\\Software\\Microsoft\\Windows\\CurrentVersion\\Themes\\Personalize' -Name AppsUseLightTheme -Value 1",
            "Set-ItemProperty -Path 'HKCU:\\Software\\Microsoft\\Windows\\CurrentVersion\\Themes\\Personalize' -Name SystemUsesLightTheme -Value 1",
        ]
    elif profile == "minimal":
        cmds += [
            "Set-ItemProperty -Path 'HKCU:\\Software\\Microsoft\\Windows\\CurrentVersion\\Themes\\Personalize' -Name AppsUseLightTheme -Value 0",
            "# Minimal: also hide widgets/taskbar search via Settings > Personalization > Taskbar (manual, recorded in manifest)",
        ]
    return cmds


def appearance_commands(profile="dark", wallpaper=""):
    return appearance_script(profile, wallpaper)


def debloat_commands(packages):
    return [f"Get-AppxPackage *{p}* | Remove-AppxPackage" for p in packages]


def service_disable_commands(services):
    cmds = []
    for s in services:
        cmds.append(f"Set-Service -Name '{s}' -StartupType Disabled")
        cmds.append(f"Stop-Service -Name '{s}' -ErrorAction SilentlyContinue")
    return cmds


def launch_command(app, url=""):
    """Native Windows open/run. app = exe name, path, or Store app name."""
    if url:
        return f"Start-Process '{url}'"
    return f"Start-Process '{app}'"


def backup_script():
    return "\n".join([
        "Get-AppxPackage | Select-Object Name, PackageFullName | Export-Csv -Path \"$env:USERPROFILE\\device-control-appx.csv\" -NoTypeInformation",
        "Get-Service | Select-Object Name, DisplayName, Status, StartType | Export-Csv -Path \"$env:USERPROFILE\\device-control-services.csv\" -NoTypeInformation",
        "Checkpoint-Computer -Description 'device-control backup' -RestorePointType 'MODIFY_SETTINGS'  # requires admin, may be disabled on some editions",
    ])
