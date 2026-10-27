# Changelog — Clavis

## 0.1.0 — 2026-10-27 (rilis GitHub pertama)

Versi sengaja 0.x: tool sudah lengkap di atas kertas dan lulus tes
di host Linux, tapi belum teruji di device Windows/Android nyata.
Jangan anggap 1.0 sebelum pairing + eksekusi di device nyata lulus.

Isi rilis ini:
- CLI lengkap: devices, probe, apps, services, appearance, debloat,
  launch, open-website, ui, search-app, screenshot, backup, restore,
  pair, token, audit, revoke, mcp.
- MCP stdio 14 tool, dengan aturan dry-run only untuk aksi
  destruktif di MCP (debloat, appearance, launch, open-website, tap).
- Driver Windows (PowerShell + UI Automation), Linux (apt/dnf/pacman,
  systemd, gsettings, AT-SPI), Android (ADB: debloat disable-user,
  launch, UI dump/tap, screenshot, app search by name).
- Keamanan: pairing Ed25519 + SAS 6 digit, token perintah 60 detik,
  audit hash-chain, NEVER list, backup sebelum debloat Android.
- Aturan SKILL: buka aplikasi/situs hanya lewat alat khusus
  (device_launch / device_open_website), klik hanya di dalam
  aplikasi yang sudah terbuka.
- Dokumen: INSTALL, OPERATIONS, security, device-matrix,
  debloat-existing-os (debloat OS yang ada, bukan ganti OS),
  full-access-matrix, ui-automation, capri-takeaways.
- Tes: 42/42 lulus di host Linux (probe read-only 783 paket,
  dry-run semua jalur, MCP JSON-RPC, Ed25519 via openssl).

Yang belum ada / belum teruji:
- Eksekusi di Windows nyata, Android nyata, dan desktop Linux nyata.
- Web gateway untuk kontrol dari HP (masih desain, belum dibangun).
- Repo GitHub: remote dikonfigurasi ke `mirzasnowy/clavis`,
  push pertama menunggu login GitHub yang sah dari pemilik akun.
