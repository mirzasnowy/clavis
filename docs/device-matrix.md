# Matriks Device

## Android TV / Google TV
Bisa: probe (model, Android version, daftar paket), backup, disable-user,
enable/restore, install APK/launcher, screenshot (via adb screencap),
remote key (input keyevent).
Tidak bisa: bypass lock, ubah firmware, uninstall permanen paket sistem
tanpa root, kontrol TV non-Android (LG webOS/Samsung Tizen pakai
protokol lain — lihat smartest-tv).
Risiko: disable launcher default tanpa launcher pengganti = layar hitam
sementara. Selalu install + set launcher pengganti dulu, baru disable
launcher lama, dan simpan restore.

## HP Android
Bisa: probe, debloat user, install, scrcpy mirror/kontrol, screenshot.
Tidak bisa: kontrol penuh tanpa ADB approval, bypass lock, semua brand
sama daftar bloat-nya (beda brand beda paket).
Risiko: disable app sistem yang dipakai (telepon, SMS, keyboard) bisa
bikin HP tidak nyaman. Checklist app yang dipakai dulu.

## iPhone / iPad
Tidak bisa kontrol penuh. Hanya Shortcuts, Focus, dan API Apple.
Jangan janji kontrol iPhone seperti Android di tool ini.

## Laptop (Windows/macOS/Linux)
Bisa: info sistem, file (allowlist), install paket (via package manager
yang diizinkan), service (Linux systemd / macOS launchd, allowlist).
Tidak bisa: satu perintah sama untuk semua OS. Windows/macOS/Linux
beda izin, path, dan package manager.
Risiko: shell bebas = risiko tertinggi. Di tool ini shell hanya
allowlist, bukan shell bebas.

## VPS / Server Linux
Bisa: SSH, Docker (ps/restart, allowlist), systemd, Ansible/Nix deploy.
Tidak bisa: tanpa mesh privat, jangan buka SSH ke internet.
Risiko: restart service prod tanpa konfirmasi = downtime. Wajib
dry-run + konfirmasi + snapshot/rollback.
