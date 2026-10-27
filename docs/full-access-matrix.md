# Full Access — Scope yang Disepakati 2026-10-27

Device dalam scope (tidak ada lagi NixOS sebagai syarat, tidak ada
iPhone, tidak ada ganti OS):
1. **PC Windows** (`pc-windows`)
2. **Laptop** (`laptop`) — driver auto-detect: Windows dulu, Linux
   (apt/systemd) kalau laptopnya Linux. Registry default di tool ini
   memakai profil Windows, ganti `kind` kalau laptop kamu Linux.
3. **HP Android** (`hp-android`)
4. **TV Android** (`tv-android`)

## Prinsip akses
Security key = autentikasi + otorisasi, bukan bypass OS.
Agen harus terinstall sebagai admin/service di device itu untuk
aksi admin. Tanpa itu, agen hanya sebatas user biasa.
Semua aksi destruktif: dry-run dulu, backup dulu, konfirmasi
eksplisit, scope terpisah per device, audit hash-chain.

## Windows (PC + laptop Windows) — bisa, native PowerShell
- Tampilan: wallpaper, tema dark/light, accent, taskbar alignment,
  Start pin/layout, font, animasi, power plan.
  Perintah native: PowerShell + registry + Settings.
  Contoh dry-run di tool ini (tidak dieksekusi tanpa --confirm):
  `Set-ItemProperty -Path 'HKCU:\Control Panel\Desktop' -Name Wallpaper -Value 'C:\Wallpapers\x.jpg'`
  `Set-ItemProperty -Path 'HKCU:\Software\Microsoft\Windows\CurrentVersion\Themes\Personalize' -Name AppsUseLightTheme -Value 0`
- Aplikasi: `Get-AppxPackage`, `Remove-AppxPackage` (per user),
  `winget list/install/uninstall`.
- Service/startup: `Get-Service`, `Set-Service -StartupType Disabled`,
  `Get-ScheduledTask`, Settings > Apps > Startup.
- Sistem: user baru, firewall rule (`New-NetFirewallRule`),
  power plan (`powercfg`), update control (hati-hati, jangan off permanen).
- TIDAK bisa: bypass BitLocker tanpa recovery key, ubah firmware/
  Secure Boot dari agen biasa, bypass MDM kantor, hapus komponen
  sistem yang ditandai non-removable.

## Laptop Linux (kalau laptopnya Linux, bukan Windows)
- Tampilan: `gsettings` (GNOME), KDE Settings, wallpaper, tema,
  dock, shortcut, autostart `.desktop`.
- Aplikasi: `apt remove` / `dnf remove` / `pacman -R`,
  `snap list/remove`, `flatpak list/uninstall`.
- Service: `systemctl disable --now`, `systemctl enable`,
  `systemctl status` verifikasi.
- TIDAK bisa: hapus dbus/systemd-logind/NetworkManager/display
  manager/kernel tanpa merusak boot.

## HP Android — bisa, ADB, tanpa root
- Tampilan: ganti launcher (misal FLauncher), wallpaper via
  `adb shell cmd wallpaper` / app launcher, animasi via
  `settings put global window_animation_scale` (dan sejenisnya).
- Aplikasi: `pm list packages`, `pm disable-user` / `pm enable`,
  `adb install`, `pm uninstall -k --user 0` hanya untuk app user
  (hati-hati, pola default tool ini adalah disable-user, bukan uninstall).
- Kontrol: `input keyevent/tap/swipe`, `screencap`, scrcpy mirror.
- TIDAK bisa: ubah partisi sistem, bypass lock screen, hapus paket
  sistem permanen, kontrol penuh seperti root, tanpa ADB approval
  di layar HP.

## TV Android — bisa, ADB, tanpa root
Sama seperti HP Android, plus:
- Launcher default diganti (install dulu, set default, cek
  screenshot, baru disable launcher lama).
- Debloat: backup → `pm disable-user` → restore.
- TIDAK bisa: ubah firmware TV, bypass lock/vendor, hapus paket
  sistem permanen.

## Yang TIDAK masuk scope v1
- iPhone/iPad, Chromebook terkunci, device MDM kantor.
- Ganti OS total (NixOS / install ulang) — itu proyek terpisah,
  bukan debloat/custom OS yang ada.
- Root HP/TV — tidak disarankan, tidak diperlukan untuk scope di atas.
