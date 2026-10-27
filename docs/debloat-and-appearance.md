# Debloat & Tampilan — Prinsip dan Profil

## Prinsip (tidak bisa ditawar)
1. Backup dulu: daftar paket + status + launcher default + wallpaper.
2. Disable-user saja, jangan uninstall paket sistem.
3. Tanya dulu app yang dipakai: streaming, Live TV, input switcher,
   remote, keyboard, accessibility.
4. Dry-run dulu, tampilkan daftar yang akan di-disable, baru confirm.
5. Restore 1 perintah, dan Settings → Apps di device bisa mengaktifkan
   ulang tanpa tool ini.

## Kategori aman untuk dipertimbangkan (filter per device!)
- Telemetri / analytics pabrikan (bukan app yang dipakai).
- Iklan / sponsored rows / content recommendation yang bukan app.
- App preload yang tidak pernah dibuka dan bukan dependensi sistem.
- Demo / sample / game preload pabrikan.

## Kategori JANGAN disentuh tanpa riset model spesifik
- Launcher default SEBELUM launcher pengganti terinstall + ter-set.
- Settings, System UI, Input / keyboard, Accessibility.
- Play Store / Play Services (kalau masih mau install app dari Play).
- Live TV / input switcher / HDMI-CEC kalau dipakai.
- Remote / Bluetooth / WiFi system app.
- App yang dipakai user, walau namanya mirip bloat.

## Profil tampilan
- **Minimal (FLauncher):** grid/kategori, tanpa iklan, tanpa carousel,
  wallpaper custom, tampilkan app sideloaded.
- **Apple TV-style (CleanYourTV pattern):** dock, top shelf, tema,
  clock screensaver, launcher ringan ~300 KB.
- **Fire TV minimal (dumbtv pattern):** launcher 41 KB, tanpa internet
  permission, khusus Fire TV, hati-hati dengan daftar paketnya.
- **Dock kustom:** pilih 5-8 app yang benar-benar dibuka tiap hari,
  sisanya di kategori, bukan di home.

## Contoh alur TV (aman)
1. `probe` → model + daftar paket.
2. Backup otomatis ke `backups/<device>/<tanggal>/`.
3. Dry-run debloat dari daftar yang sudah difilter.
4. Install launcher pengganti, set sebagai default, cek screenshot.
5. Baru disable launcher lama + kategori bloat yang disetujui.
6. Reboot, cek screenshot lagi, simpan restore script.

File contoh di `examples/debloat/generic-safe.txt` HANYA berisi
kategori + placeholder, bukan daftar paket brand mentah. Ganti dengan
daftar per model dari CleanYourTV / tv-home setelah probe, dan filter
app yang dipakai.
