"""Android driver (HP + TV) — ADB native, no root."""
from device_control import adb


def appearance_commands(profile="minimal"):
    if profile == "minimal":
        return [
            "# 1. Install FLauncher (or Projectivy) APK first",
            "# 2. adb shell cmd package set-home-activity <launcher-package>",
            "# 3. Verify: adb exec-out screencap -p > check.png",
            "# 4. Only then, with backup, disable the old launcher",
        ]
    return [
        "adb shell settings put global window_animation_scale 0.5",
        "adb shell settings put global transition_animation_scale 0.5",
        "adb shell settings put global animator_duration_scale 0.5",
    ]


def launch_command(package, activity="", url=""):
    """Native Android open/run. package = e.g. com.netflix.ninja (TV) / com.whatsapp (HP)."""
    if url:
        return f"adb shell am start -a android.intent.action.VIEW -d '{url}'"
    if activity:
        return f"adb shell am start -n {package}/{activity}"
    return f"adb shell monkey -p {package} -c android.intent.category.LAUNCHER 1"


def launch(device_address="", package="", activity="", url=""):
    cmd = launch_command(package, activity, url)
    # Strip leading 'adb shell ' for run_adb
    inner = cmd.replace("adb shell ", "", 1)
    return adb.run_adb(["shell"] + inner.split(), device_address)


def list_apps(device_address=""):
    return adb.list_packages(device_address)


def probe(device_address=""):
    return adb.probe(device_address)
