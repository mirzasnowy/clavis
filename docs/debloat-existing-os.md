# Debloat OS yang Sudah Ada — Tanpa Ganti OS

KOREKSI: NixOS BUKAN syarat debloat. NixOS hanya opsi kalau mau
ganti OS total. Debloat di bawah ini memakai OS yang sudah ada,
dengan perintah native OS itu sendiri. OS tetap Windows / Ubuntu /
Fedora / dsb, hanya dibersihkan dan di-custom.

## Cara kerja harness agent (semua OS, pola sama)

1. **Probe (read-only):** daftar app terinstall, service yang jalan,
   app startup, scheduled task / timer.
2. **Klasifikasi:** aman / tanya dulu / jangan sentuh. User centang
   app yang dipakai, sisanya baru masuk daftar.
3. **Backup:** daftar app + service + setting, restore point
   (Windows) / snapshot daftar paket (Linux). Tanpa backup, jangan
   ubah apa pun.
4. **Eksekusi bertahap, native:** disable dulu kalau bisa, uninstall
   hanya untuk app user yang jelas tidak dipakai. Jangan borongan
   buta dari daftar orang lain.
5. **Verifikasi:** reboot test, cek service penting masih jalan,
   cek boot time / RAM, screenshot / `systemctl status`.
6. **Rollback:** 1 perintah dari backup. Windows: restore point +
   reinstall dari Store. Linux: install ulang paket + enable service.

Agen harness di sini = controller kirim rencana → agen lokal di
device jalankan perintah native dalam allowlist → hasil + audit
balik ke controller. Bukan shell bebas, bukan script remote
yang di-pipe mentah tanpa dibaca.

## Windows (native, PowerShell admin)

List:
```powershell
Get-AppxPackage | Select Name, PackageFullName | Sort Name
Get-Service | Where-Object {$_.Status -eq 'Running'}
Get-ScheduledTask | Where-Object {$_.State -eq 'Ready'}
winget list
```

Hapus app per user (bukan hapus komponen sistem):
```powershell
Get-AppxPackage *XboxGamingOverlay* | Remove-AppxPackage
Get-AppxPackage *MicrosoftTeams* | Remove-AppxPackage
Get-AppxPackage *Solitaire* | Remove-AppxPackage
```

Service / startup (contoh pola, riset dulu per service):
```powershell
Set-Service -Name "DiagTrack" -StartupType Disabled
Stop-Service -Name "DiagTrack"
# Startup app: Settings > Apps > Startup, atau schtasks /Disable
```

Custom native Windows:
- Taskbar / Start: Settings, layout Start, pin/unpin, widget off.
- Explorer: tampilkan ekstensi, folder options, context menu.
- Power plan, visual effect (Performance Options), notifikasi,
  telemetri via Settings/Group Policy (bukan hapus file sistem).
- Registry hanya untuk setting yang memang registry key-nya
  (dan dicatat di backup, bisa di-undo).

Tool existing yang bisa dipakai agen sebagai modul (baca dulu,
jangan pipe `iex` buta):
- **WinUtil (Chris Titus Tech, open source):** debloat + tweak +
  install via winget + update control, ada tombol Undo Selected Tweaks
  + restore point otomatis.
- **Win11Debloat (open source):** fokus app saja, ada mode yang
  hanya hapus software tanpa ubah service — pilihan konservatif.
- **Sophia Script (open source, PowerShell):** 150+ tweak repeatable
  untuk Win10/11, bagus kalau mau profil yang bisa diulang.
- **O&O AppBuster (portable):** hanya list + hapus AppX, termasuk
  yang disembunyikan Settings, terintegrasi System Restore.

JANGAN sentuh tanpa riset: Windows Update service permanen off,
Store / .NET / Visual C++ runtime, driver OEM, Defender (kecuali
pengganti jelas), app yang dipakai kerja.

Catatan: update fitur Windows bisa menginstall ulang sebagian app
yang dihapus. Itu normal — jalankan ulang daftar yang sama, bukan
tanda debloat gagal.

## Linux — Ubuntu/Debian (native, apt + systemd)

List:
```bash
dpkg -l | grep ^ii
snap list; flatpak list
systemctl list-units --type=service --state=running
ls ~/.config/autostart/ /etc/xdg/autostart/
```

Stop + disable service (reversible):
```bash
sudo systemctl stop cups.service
sudo systemctl disable cups.service
systemctl is-enabled cups.service  # harus: disabled
```
`disable` = tidak auto-start, masih bisa start manual.
`mask` = diblok total, hanya untuk yang memang tidak dipakai.

Hapus paket:
```bash
sudo apt remove --purge <paket>
sudo apt autoremove
```

Custom native Linux:
- GNOME: `gsettings` (tema, dock, animasi, shortcut, wallpaper).
- KDE: `kwriteconfig`, System Settings, tema/plasma.
- Autostart: hapus / tambah file `.desktop` di `~/.config/autostart/`.
- Dotfiles di git: `.bashrc`, `.config/*`, terminal, editor.
- Fedora: `dnf remove` (bukan apt). Arch: `pacman -R`.
  Perintah paket beda, pola probe → backup → disable → hapus sama.

JANGAN sentuh: dbus, systemd-logind, NetworkManager (kalau pakai
WiFi), display manager (gdm/sddm), kernel, driver GPU.

## Linux server / VPS
Pola sama, tanpa desktop: `systemctl disable --now` service yang
tidak dipakai (misal `apport`, `postfix` kalau tidak kirim mail,
`qemu-guest-agent` kalau bukan VM), `apt remove` paket tak perlu,
firewall `ufw` hanya buka port yang dipakai. Backup daftar paket
+ service sebelum ubah, reboot test.

## Android TV / HP (sudah dibahas, pola sama)
ADB: probe → backup → `pm disable-user` → launcher → restore.
Lihat README + docs/debloat-and-appearance.md.

## Ringkas
- Debloat ≠ ganti OS. Debloat = bersihkan OS yang ada.
- NixOS = ganti OS total, opsional, bukan langkah debloat.
- Harness agent = orkestrasi perintah native + allowlist +
  backup + verifikasi + rollback, bukan satu script ajaib.
