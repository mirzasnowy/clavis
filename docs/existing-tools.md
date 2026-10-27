# Repo Existing yang Dipakai — Jangan dari Nol

## TV / HP Android
- **adb (platform-tools, Google)** — transport dasar. `adb devices`,
  `adb shell pm list packages`, `pm disable-user`, `pm enable`,
  `adb install`, `adb screencap`. Tanpa ini tidak ada kontrol Android.
- **scrcpy (Genymobile, Apache 2.0)** — mirror + kontrol layar Android
  tanpa root, tanpa app permanen, latensi 35-70 ms, USB/WiFi.
  Dipakai untuk: lihat TV/HP, klik, ketik, screenshot verifikasi.
- **CleanYourTV (Gathin23/cleanyourtv)** — pola debloat TV: backup →
  disable-user → launcher minimal → restore 1 perintah. Tidak root,
  tidak uninstall. Tested 100+ model / 30+ brand (Okt 2026).
- **tv-home pattern (mihirgupta0900/tv-home)** — skrip probe, daftar
  debloat per model di `examples/`, build launcher, restore.
  Pola prompt-nya: tanya dulu app yang dipakai, backup, cek pakai
  screenshot, baru ubah.
- **FLauncher (GitLab, Flutter, open source)** — launcher minimal:
  kategori, reorder, wallpaper, tanpa iklan, tanpa carousel,
  tampilkan app sideloaded. Alternatif: Projectivy (kustom penuh),
  dumbtv (41 KB, tanpa internet, Fire TV).
- **smartest-tv / stv (Hybirdss, pip)** — kontrol TV via bahasa alami
  + MCP 21 tool + Home Assistant: LG webOS, Samsung Tizen,
  Android TV/Fire TV, Roku. Pairing Android TV pakai PIN 6 digit di TV.
  Referensi driver TV, bukan otak.

## Laptop / Server / VPS
- **Ansible (Red Hat, GPL)** — konfigurasi via SSH, agentless,
  idempotent. Untuk VPS/laptop yang sudah jalan.
- **NixOS (MIT/Apache, Nix)** — sistem deklaratif penuh di
  `configuration.nix`, rollback per generasi. Untuk Linux yang mau
  custom OS total. Tidak berlaku untuk Windows/macOS.
- **Docker / systemd** — service di server, restart, log. Via SSH
  allowlist saja di tool ini, bukan shell bebas.

## Jaringan & Keamanan
- **Tailscale / Headscale (WireGuard)** — mesh privat, tanpa port publik.
  Headscale = self-host control plane Tailscale.
- **WireGuard protocol** — X25519, ChaCha20-Poly1305, BLAKE2s, Noise IK.
- **Ed25519 (produksi)** — identitas device, via library `cryptography`
  di Python atau `ssh-keygen -t ed25519`. Skeleton v0 memakai HMAC
  demo saja — lihat security.md.

## Harness / Otak
- **MCP (Model Context Protocol)** — protokol standar tool harness.
  Server di tool ini: stdio, JSON-RPC, 5 tool. Klien: Claude Code,
  Codex, OpenCode, Cursor, Gemini CLI, VS Code, dan semua MCP client.
- **OpenClaw (MIT)** — referensi arsitektur gateway + node + approval,
  bukan fork. Dipakai sebagai pembanding, bukan dependensi.
- **Home Assistant (Apache 2.0)** — kalau sudah ada HA, TV bisa jadi
  remote/dashboard via integrasi `androidtv` (ADB). Tool ini bisa
  dipanggil dari HA, tidak menggantikannya.

## Yang TIDAK dipakai / dihindari
- Situs reupload template berbayar (ShareAE/AVXGFX/dll) — lisensi
  abu-abu, tidak dipakai sebagai sumber debloat/appearance.
- Tool closed-source yang minta akun + upload video/data device ke cloud.
- Root HP/TV hanya demi debloat — tidak perlu, dan merusak keamanan.
- Daftar debloat brand mentah tanpa filter app yang dipakai user.
