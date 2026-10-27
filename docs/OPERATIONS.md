# Operasi — Pairing, Backup, Rollback, Troubleshooting

## Pairing (sekali per device)
```bash
device-control pair --device hp-android
# Output: SAS 6 digit + fingerprint SHA-256 + backend (cryptography/openssl)
# 1. Cocokkan SAS di layar device dan controller.
# 2. Kalau cocok, approve di kedua sisi.
# 3. Kalau TIDAK cocok, STOP — kemungkinan MITM.
# 4. Fingerprint tersimpan di registry, private key tetap di keys/ (0600).
```

## Alur aman standar (jangan dilompat)
1. `probe` + `apps` (read-only).
2. Centang app yang dipakai, buat daftar debloat dari hasil probe.
3. `backup --device <nama>` — catat backup_dir-nya.
4. `debloat --dry-run` — baca would_disable + blocked_never.
5. `debloat --confirm` — hanya di device yang sudah terpairing.
6. Verifikasi: `probe` / `apps` / screenshot (Android) / service
   status (Windows/Linux). Reboot test untuk perubahan service.
7. `audit` — pastikan hash-chain OK.

## Rollback
- Android: `restore --device <nama>` (dari packages.txt backup
  terakhir), atau jalankan `restore.sh` di folder backup, atau
  Settings > Apps > enable paket.
- Windows: reinstall AppX dari Store, re-enable service dari
  manifest CSV, atau System Restore point yang dibuat sebelum ubah.
- Linux: `apt install <paket>`, `systemctl enable <service>`,
  dari manifest backup.

## Troubleshooting
- `adb not found` → install platform-tools, cek `adb devices`.
- `unauthorized` di adb → approve di layar device, cabut-colok USB
  sekali, cek fingerprint RSA yang muncul.
- `PowerShell not found` → kamu bukan di host Windows; jalankan
  script dry-run di PC Windows yang sudah terpairing, bukan di sini.
- `unknown device` → `devices list`, lalu `devices add` dengan
  nama/kind/transport/scope yang benar.
- `audit FAIL` → jangan lanjut ubah apa pun; audit file di
  `~/.device-control/audit.jsonl` sudah tidak utuh — investigasi
  dulu, restore dari backup terakhir yang terverifikasi.
- Update Windows menginstall ulang app yang dihapus → normal,
  jalankan ulang daftar debloat yang sama.
- TV layar hitam setelah ganti launcher → jangan panik: launcher
  baru belum ter-set. Sambungkan adb, `cmd package set-home-activity`
  ke launcher baru, atau restore launcher lama dari backup.
