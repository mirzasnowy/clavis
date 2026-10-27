# Capri-desktop — apa yang bisa dipakai untuk Clavis

Referensi: repo publik lachydotmcg/capri-desktop, branch main, versi 0.6.2
saat dibaca. Ringkasan ini ditulis ulang dengan kata-kata sendiri,
bukan salinan README atau kode repo tersebut.

## Gambaran repo itu
- Aplikasi desktop pendamping, fokus utama Windows 10/11 64-bit.
  Mac/Linux hanya pratinjau awal, dengan fitur lebih sedikit.
- Ditulis dengan C#, .NET 10 untuk versi lintas platform, memakai
  kerangka antarmuka Avalonia.
- Punya karakter overlay yang bisa diletakkan di jendela, ikon,
  atau bawah layar, bisa diajak chat teks maupun suara, dan bisa
  diminta melakukan tugas desktop sederhana.
- Lisensi: PolyForm Noncommercial 1.0.0. Artinya bebas untuk
  pemakaian non-komersial saja. Jangan salin kodenya mentah-mentah
  ke produk berbayar. Ambil polanya, tulis ulang dengan kode sendiri.

## Arsitektur yang diamati
- Lapisan karakter/overlay terpisah dari lapisan otak dan lapisan
  eksekusi. Overlay hanya menampilkan dan menerima input.
- Otak: klien model bahasa dengan gaya pemanggilan alat (tool calls).
  Mendukung dua mode: model lokal di PC sendiri, atau model lewat
  kunci API. Parameternya dijaga pendek dan hemat konteks.
- Mesin agen: loop langkah-demi-langkah. Setiap langkah adalah satu
  aksi kecil, lalu hasil aksi itu dibaca lagi sebelum langkah
  berikutnya. Loop berhenti pada aksi selesai atau aksi bertanya.
- Kontrol desktop Windows: memakai API aksesibilitas bawaan Windows
  (UI Automation). Jendela depan dijabarkan menjadi daftar target
  bernomor, lengkap dengan peran, nama, kotak posisi, dan nilai.
  Model memilih nomor target, bukan menebak koordinat atau nama.
- Penggerak mouse/keyboard terpisah sebagai modul tangan.
- Input suara dan output suara terpisah sebagai modul telinga/suara.
- Pengaturan otak dan suara terpusat di satu panel pengaturan.
- Versi lintas platform memakai kembali file sumber otak, mesin agen,
  tangan, dan suara yang sama, dengan fitur yang dipangkas.
- Situs statis dan layanan worker kecil hanya untuk halaman unduhan
  dan penghitung, bukan bagian inti kontrol desktop.

## Yang bisa dipakai untuk Clavis

### 1. Target bernomor, bukan cari nama saja
Ini pelajaran paling berharga. Clavis saat ini mencari elemen lewat
nama, dan menolak kalau ambigu. Capri memakai pendekatan yang lebih
kuat: jabarkan jendela menjadi daftar bernomor, tampilkan daftar itu
ke model, dan biarkan model memilih nomornya. Nomor itu stabil dalam
satu langkah, tidak bergantung pada teks yang berubah-ubah.
Terapkan di Clavis: `winui.ps1 Dump` mengembalikan daftar bernomor,
`Click` menerima nomor, bukan hanya nama. Simpan daftar itu di STATE
per langkah, dan buang setelah langkah selesai.

### 2. Alat buka aplikasi terpisah dari alat klik
Jangan suruh model membuka aplikasi dengan cara mengklik ikon di
desktop atau menu. Sediakan alat khusus untuk membuka aplikasi dan
membuka situs, dan alat klik hanya untuk elemen di dalam aplikasi
yang sudah terbuka. Ini mengurangi langkah, mengurangi kesalahan
klik, dan membuat audit lebih jelas: buka aplikasi tercatat sebagai
aksi buka, bukan sebagai klik acak.
Clavis sudah punya `launch`; tambahkan `open_website` sebagai alat
terpisah, dan tulis aturan ini di SKILL.md.

### 3. Loop langkah dengan observasi ulang
Jangan jalankan rencana panjang sekaligus. Polanya:
rencana satu langkah -> eksekusi -> baca ulang layar/aplikasi ->
tentukan langkah berikutnya -> ulangi, sampai selesai atau bertanya.
Tambahkan aksi `wait` (tunggu aplikasi selesai memuat) dan aksi
`ask` (berhenti dan tanya pengguna kalau ambigu). Ini mencegah
klik beruntun ke layar yang belum berubah.

### 4. Inti bersama, driver tipis per platform
Satu inti untuk otak, mesin langkah, dan audit; driver per OS hanya
menerjemahkan aksi inti menjadi perintah native OS itu. Ini sudah
menjadi arah Clavis, dan Capri mengonfirmasi arah itu: file otak,
mesin, dan tangan dipakai bersama, hanya lapisan tampilan dan
perintah native yang berbeda. Pertahankan struktur ini, jangan
duplikasi logika langkah di tiap driver.

### 5. Dua mode otak
Tawarkan mode lokal dan mode kunci API sebagai pilihan konfigurasi,
bukan sebagai dua produk berbeda. Mode lokal untuk privasi dan
tanpa biaya per token; mode API untuk kualitas dan tanpa beban
perangkat. Di Clavis, ini berarti MCP/CLI tidak boleh mengunci
satu penyedia model.

### 6. Panel pengaturan dan pintasan, kalau mau (opsional)
Panel pengaturan terpusat untuk otak, suara, dan izin perangkat,
plus pintasan keyboard global untuk mulai/berhenti dan lepas dari
kursor, adalah pola UX yang bagus. Untuk Clavis, ini opsional dan
bukan prioritas: fokus dulu ke kontrol yang benar, baru ke overlay.

### 7. Suara sebagai lapisan opsional
Input suara dan output suara dipisah dari inti. Kalau Clavis mau
suara nanti, tambahkan sebagai modul opsional di atas mesin yang
sama, bukan sebagai mode terpisah. Jangan jadikan suara sebagai
syarat untuk kontrol desktop.

## Yang TIDAK perlu diambil
- Karakter overlay, sprite, animasi, dan persona pendamping. Itu
  identitas produk lain, bukan kebutuhan Clavis.
- Layanan penghitung unduhan dan situs pemasaran. Tidak relevan
  untuk alat kontrol perangkat.
- Ketergantungan pada satu penyedia suara atau satu penyedia model.
  Clavis harus tetap bisa ganti penyedia.
- Kode sumbernya secara mentah, karena lisensi non-komersial dan
  karena gaya kodenya terikat pada kerangka C# mereka. Tulis ulang
  polanya dalam Python/PowerShell Clavis sendiri.

## Batasan yang ditemukan saat membaca repo
- Resep build Windows tidak terlihat di repo: folder aplikasi hanya
  berisi file sumber dan manifest, tanpa file proyek Windows.
  Hanya file proyek lintas platform yang tersedia. Jadi repo ini
  tidak cukup untuk mereplikasi build Windows-nya secara persis.
- Fitur Mac/Linux masih pratinjau dan lebih sedikit. Jangan jadikan
  repo ini patokan untuk janji lintas platform penuh.
- Jumlah bintang saat dibaca masih kecil (puluhan, bukan ribuan),
  dan isu terbuka cukup banyak. Perlakukan repo ini sebagai
  referensi pola yang bagus, bukan sebagai standar industri.

## Rencana penerapan di Clavis (urutan)
1. Ubah Dump Windows menjadi daftar bernomor + Click by number.
2. Tambahkan alat open_website terpisah dan aturan SKILL: buka
   aplikasi/situs lewat alat khusus, bukan lewat klik.
   [SELESAI 2026-10-27: CLI `open-website`, MCP `device_open_website`
   (dry-run only), modul `src/device_control/openwebsite.py` dengan
   validasi http/https, aturan SKILL no. 7, tes 42/42 lulus.]
3. Tambahkan aksi wait dan ask ke loop mesin langkah.
4. Dokumentasikan mode otak lokal vs kunci API sebagai konfigurasi.
5. Baru setelah itu, pertimbangkan panel pengaturan dan suara
   sebagai modul opsional.
