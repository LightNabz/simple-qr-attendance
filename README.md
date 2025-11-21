# Absensi QR (Simple QR Attendance)

Project sederhana untuk mencatat absensi menggunakan QR code dan kamera. Aplikasi ini berbasis command-line dengan beberapa fitur untuk:

- Memindai QR Code (sekali atau mode live) menggunakan kamera.
- Menyimpan log absensi ke `logs/absensi.csv` dan menyimpan sesi ke `logs/absensi-YYYYMMDD_HHMMSS.csv`.
- Mengelola daftar siswa (`siswa.json`) dan menghasilkan QR per siswa yang tersimpan di `qrcode_generated/{kelas}/`.
- Login admin sederhana menggunakan kredensial `user_db.json`.

## Fitur

- Scan absensi manual (mengambil satu frame dari kamera)
- Live scan absensi (menangani beberapa pemindaian dengan overlay kotak)
- CRUD siswa (tambah/hapus/import) dan generate QR
- Menyimpan sesi absensi terpisah

## Persyaratan

- Python 3.8+
- Kamera yang dapat diakses oleh OpenCV
- Sistem Linux/Windows/Mac dengan dukungan tampilan (untuk `cv2.imshow`)
- Alat `aplay` (opsional) untuk memainkan suara notifikasi pada Linux
- Library Python:
  - `opencv-python`
  - `pyzbar`
  - `qrcode`
  - `Pillow`

Instal dependensi Python (contoh):

```bash
pip install opencv-python pyzbar qrcode pillow
```

Catatan sistem (Linux):

- Untuk `pyzbar` pastikan `zbar` terpasang. Contoh (Debian/Ubuntu):

```bash
sudo apt-get install libzbar0
```

- Untuk suara notifikasi, `aplay` disediakan oleh `alsa-utils`:

```bash
sudo apt-get install alsa-utils
```

## Menjalankan Aplikasi

Dari direktori proyek, jalankan:

```bash
python main.py
```

atau,
```bash
QT_QPA_PLATFORM=xcb python main.py
```

Jika Anda mengalami masalah dengan tampilan/Qt (mis. `cv2.imshow`) di lingkungan tertentu (mis. Wayland/X11), Anda dapat menambahkan variabel lingkungan seperti contoh berikut:

```bash
QT_QPA_PLATFORM=xcb python main.py
```

Setelah program dijalankan, lakukan login admin menggunakan akun di `user_db.json` lalu pilih menu:

1. Scan Absensi (manual)
2. Live Scan Absensi
3. Lihat Laporan Absensi
4. Atur Absensi Siswa (tambah/hapus/generate/import)
5. Atur Sesi Absensi (simpan/lihat sesi tersimpan)

Untuk keluar pilih `0`.

## Struktur File Penting

- `main.py` - Entry point, menampilkan menu dan menghubungkan modul
- `absensi.py` - Logika pemindaian QR, penandaan absensi, dan laporan
- `siswa.py` - Manajemen data siswa dan pembuatan QR
- `sessions.py` - Menyimpan dan melihat sesi absensi
- `siswa.json` - Data siswa (format: { nis: {"nama":..., "kelas":...} } atau legacy: nis->nama)
- `user_db.json` - File username/password untuk login admin (format: { "user": "password" })
- `logs/` - Menyimpan `absensi.csv` dan `absensi-YYYYMMDD_HHMMSS.csv`
- `qrcode_generated/` - Folder hasil generate QR per kelas
- `sounds/beep.wav` - Suara notifikasi (opsional)

## Contoh Format File Minimal

`user_db.json`:

```json
{
  "admin": "password123"
}
```

`siswa.json` (baru, format yang disarankan):

```json
{
  "12345": {"nama": "Budi", "kelas": "kelas_a"},
  "67890": {"nama": "Siti", "kelas": "kelas_b"}
}
```

Legacy (nama saja) juga didukung:

```json
{
  "12345": "Budi",
  "67890": "Siti"
}
```

## Manajemen Siswa dan QR

- Tambah siswa lewat menu `Atur Absensi Siswa` -> `Tambah Siswa`. QR image akan otomatis dibuat di `qrcode_generated/{kelas}/{nis}.png`.
- Untuk membuat QR untuk semua siswa yang ada di `siswa.json`, pilih `Generate QR per Kelas`.
- Untuk mengimpor file JSON eksternal, gunakan `Import siswa dari file JSON` pada menu yang sama.

## Sesi dan Log

- Selama runtime, absensi sementara juga disimpan di `logs/absensi.csv`.
- Anda bisa menyimpan sesi ke file timestamped (CSV) lewat menu `Atur Sesi Absensi` -> `Simpan Sesi Absensi`.
- Laporan lengkap dapat dilihat lewat `Lihat Laporan Absensi` atau `Lihat Sesi Tersimpan`.

## Troubleshooting

- Kamera tidak terbuka: Pastikan kamera tidak digunakan aplikasi lain dan device index `0` benar. Uji dengan skrip OpenCV sederhana.
- `pyzbar` tidak menemukan QR: Pastikan `libzbar` terpasang di sistem.
- suara tidak terdengar: Pastikan `sounds/beep.wav` ada dan `aplay` tersedia di PATH.

## Kontribusi

Perbaikan kecil atau fitur baru dipersilakan melalui PR. Jaga backward compatibility untuk `siswa.json` (legacy format masih didukung).

## Lisensi

Gunakan sesuai kebutuhan (tidak ada lisensi resmi pada repository ini).
