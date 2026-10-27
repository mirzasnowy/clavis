# Melihat Layar & Klik Tombol — UI Automation

## Android (lengkap, dites parsing + dry-run)
- `ui current/dump/tap/key`, `screenshot`, `search-app` — lihat
  docs sebelumnya. uiautomator dump -> node -> tap centre.

## Windows (ditulis dari dokumentasi resmi, BELUM dites di desktop nyata)
File: `scripts/winui.ps1` + `src/device_control/winui.py`.
Teknologi resmi: Microsoft UI Automation, `System.Windows.Automation`
(UIAutomationClient / UIAutomationTypes, bawaan .NET Windows, tanpa
download tambahan). FlaUI adalah wrapper .NET di atas UIA2/UIA3 yang
sama — pola yang dipakai di sini identik, hanya tanpa dependensi FlaUI.

Pola resmi yang dipakai:
```
RootElement
  -> FindFirst(TreeScope.Children, PropertyCondition(Name, "Calculator"))
  -> FindAll/FindFirst(TreeScope.Descendants, PropertyCondition(Name, "7"))
  -> GetCurrentPattern(InvokePattern.Pattern).Invoke()   # klik tombol
  -> GetCurrentPattern(ValuePattern.Pattern).SetValue("teks")  # isi kolom
```
Fail-closed: Click/Type menolak kalau 0 match atau >1 match (tidak
pernah klik match pertama kalau ambigu). Dump/ListWindows read-only.

Cara tes di laptop Windows kamu (desktop session, bukan SSH headless):
```powershell
# 1. Buka Calculator, lalu:
powershell -ExecutionPolicy Bypass -File scripts\winui.ps1 -Action ListWindows
powershell -ExecutionPolicy Bypass -File scripts\winui.ps1 -Action Dump -Window "Calculator"
# 2. Klik tombol 7, lalu = :
powershell -ExecutionPolicy Bypass -File scripts\winui.ps1 -Action Click -Window "Calculator" -Name "Seven"
#    (nama tombol di Calculator bisa "Seven", bukan "7" — cek hasil Dump dulu)
# 3. Via tool:
device-control ui --device pc-windows tap --window "Calculator" --text "Seven" --dry-run
device-control ui --device pc-windows tap --window "Calculator" --text "Seven" --confirm
```
Catatan: nama elemen di tiap app beda-beda — selalu Dump dulu,
jangan tebak nama tombol. App yang tidak mengekspos accessibility
tree (game, canvas custom, remote desktop) tidak akan terlihat —
itu batas UIA, bukan bug tool ini. Untuk app seperti itu, fallback
adalah screenshot + klik koordinat (rapuh, tergantung resolusi).

## Linux (ditulis dari dokumentasi AT-SPI, BELUM dites di desktop nyata)
File: `scripts/linuxui.py` + `src/device_control/linuxui.py`.
Teknologi resmi: AT-SPI2 (GNOME), via pyatspi.
Pola: `Registry.getDesktop(0)` -> app -> walk childCount/getChildAt
-> cari by name -> `queryAction().doAction("click"/"press")`,
isi teks via `queryEditableText().setText()`.

Install + tes di laptop Linux kamu (di dalam session desktop):
```bash
sudo apt install python3-pyatspi2 at-spi2-core
python3 scripts/linuxui.py dump --app Firefox
python3 scripts/linuxui.py click --app Firefox --name "Settings"
device-control ui --device laptop dump --window Firefox --dry-run
```
Catatan: AT-SPI hanya jalan di session desktop yang sama dengan
app-nya (DISPLAY/Wayland yang sama). Di SSH headless tanpa session,
dump akan kosong — itu expected, bukan bug.

## Kenapa saya bilang "secara intuisi bekerja"
Karena ketiga jalur (Android uiautomator, Windows UIA, Linux AT-SPI)
memakai pola yang SAMA dan sudah terbukti di ekosistemnya:
dump pohon -> cari by name -> aksi pada node itu, fail-closed kalau
ambigu. Yang berbeda hanya nama API per OS. Kode walker + fail-closed
di `linuxui.py` dites dengan node palsu di test suite, dan script
PowerShell-nya dites keberadaan pola resminya (RootElement,
FindFirst, InvokePattern, ValuePattern). Yang belum dites adalah
eksekusi di desktop nyata — itu langkah tes di atas, yang harus
kamu jalankan di device kamu dan laporkan hasilnya.
