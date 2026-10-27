# Install

## Syarat
- Python 3.10+ (host ini: 3.12, teruji).
- Per device:
  - Windows: PowerShell + winget (bawaan Win10/11).
  - Linux: apt/dnf/pacman + systemd + gsettings (GNOME, opsional).
  - Android: Android platform-tools (`adb`) di controller, USB
    debugging / ADB WiFi di device, approve di layar device.
  - Server: OpenSSH client di controller, SSH key Ed25519.
- Opsional: `pip install cryptography` (Ed25519 via library, lebih
  cepat dari openssl CLI). Tanpa itu, tool memakai openssl CLI
  yang ada di Linux/macOS/Windows-OpenSSH.
- Mesh (untuk remote, bukan untuk test lokal): Tailscale atau
  Headscale. Tanpa mesh, jangan buka SSH/ADB ke internet.

## Install tool
```bash
cd device-control
# Cara 1 (tanpa install, paling cepat):
export PYTHONPATH=src
python3 -m device_control.cli devices list

# Cara 2 (install editable):
pip install -e .
device-control devices list

# Cara 3 (dengan Ed25519 library):
pip install -e ".[crypto]"
```

## Pasang di harness
Lihat `configs/harness/` + `docs/harness-compatibility.md`.
Intinya: command `python3 -m device_control.mcp_server`, transport
stdio, dari folder device-control (atau PYTHONPATH=src).
Skill: copy `skills/device-control/SKILL.md` ke folder skill harness
kamu (`.claude/skills/device-control/`, `.cursor/skills/`, dll).

## Verifikasi install
```bash
PYTHONPATH=src python3 -m unittest discover -s tests -v
# Harus: Ran 21 tests — OK
PYTHONPATH=src python3 -m device_control.cli devices list
# Harus: 4 device (pc-windows, laptop, hp-android, tv-android)
```
