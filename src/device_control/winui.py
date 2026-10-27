"""Windows UI Automation driver — Python wrapper around scripts/winui.ps1.

Official pattern (Microsoft Learn, System.Windows.Automation):
RootElement -> FindFirst/FindAll(TreeScope, PropertyCondition)
-> InvokePattern.Invoke() for buttons, ValuePattern.SetValue() for text.
No external download: UIAutomationClient/Types ship with Windows .NET.
FlaUI is the modern .NET wrapper around the same UIA2/UIA3 APIs — if
you prefer FlaUI, its pattern is identical: FindFirstDescendant(ByName)
-> AsButton().Click() / AsTextBox().Text = value. This driver uses
the built-in API so there is nothing extra to install.

On a non-Windows host, command() returns the exact PowerShell command
to run on the Windows host (dry-run). On Windows, run() executes it.
STATUS: written from official docs, NOT tested on a real Windows
desktop by this agent. Test on your Windows laptop first.
"""
import json
import os
import subprocess

SCRIPT = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
                      "scripts", "winui.ps1")
# When imported from src/, the scripts folder is at repo root:
# src/device_control/winui.py -> ../../scripts/winui.ps1
SCRIPT = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", "..", "scripts", "winui.ps1"))


def command(action, window="", name="", text=""):
    args = ["powershell", "-ExecutionPolicy", "Bypass", "-File", SCRIPT,
            "-Action", action]
    if window:
        args += ["-Window", window]
    if name:
        args += ["-Name", name]
    if text:
        args += ["-Text", text]
    return args


def run(action, window="", name="", text=""):
    from device_control import windows
    if not windows.available():
        return False, "PowerShell not found on this host — run the winui.ps1 command on a Windows host"
    cmd = command(action, window, name, text)
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
    except Exception as e:
        return False, f"winui failed: {e}"
    out = (r.stdout or "").strip()
    try:
        return r.returncode == 0, json.loads(out) if out else {}
    except Exception:
        return r.returncode == 0, out
