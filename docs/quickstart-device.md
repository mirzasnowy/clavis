# Quickstart Device Nyata (setelah skeleton)

1. Mesh dulu: install Tailscale di laptop + server (+ HP kalau mau).
   Pastikan `tailscale status` menunjukkan semua device, tanpa port
   forwarding di router.
2. TV/HP Android:
   - Settings → About → tap Build number 7x → Developer Options nyala.
   - Developer Options → USB debugging ON.
   - Hubungkan USB dulu (paling aman pertama kali) atau ADB WiFi di
     jaringan rumah yang sama, BUKAN WiFi publik.
   - Di layar device, approve komputer kamu (fingerprint RSA/ADB).
   - `adb devices` harus muncul `device`, bukan `unauthorized`.
3. Di laptop:
   - `python3 -m device_control.cli probe --device tv-kamu`
   - Cek output: model, paket, launcher default.
   - Backup otomatis dibuat sebelum debloat apa pun.
4. Debloat:
   - Buat daftar dari probe + filter app yang dipakai.
   - `debloat --dry-run` → baca daftarnya → baru `--confirm`.
   - Install launcher pengganti dulu, cek screenshot, baru disable
     launcher lama.
5. Kalau ada yang salah:
   - `restore --device tv-kamu` (dari backup terakhir).
   - Atau di TV: Settings → Apps → enable paket yang tadi di-disable.
6. Server:
   - SSH hanya lewat IP Tailscale, user non-root, kunci Ed25519,
     bukan password. Allowlist service di `devices.json`.
