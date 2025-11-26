# Absensi QR (Simple QR Attendance)

Simple command-line QR attendance system for small classrooms or events. The app uses a webcam and QR codes containing a student's NIS (identifier) to record attendance entries, write logs, and optionally save sessions to timestamped files.

This README provides a developer-friendly overview of the code structure, runtime flow, function explanations, file formats, and usage notes so you can run, debug, or extend the project.

---

Table of Contents
- Overview
- Quick Start
- File Structure & Modules
- How the Code Works (Detailed flow)
- Function Reference (per module)
- Data Formats
- How to Test / Simulate Scans
- Troubleshooting & Common Issues
- Extending the Project
- Contributing

---

Overview
========

- The app scans QR codes (which encode the NIS/ID) using `pyzbar` + OpenCV.
- On a successful scan, the app writes to `logs/absensi.csv` and stores entries in an in-memory session list.
- A session can be saved as `logs/absensi-YYYYMMDD_HHMMSS.csv` which preserves history.
- `siswa.json` stores student metadata (NIS -> name & class) which maps NIS to a human-readable name and class. The legacy format (NIS -> name) is supported.

Quick Start
===========

1. Install dependencies:

```bash
pip install -r requirements.txt
```

2. Optional system packages (Linux):

```bash
sudo apt-get install libzbar0  # for pyzbar
sudo apt-get install alsa-utils # provides aplay for sound notifications
```

3. Run the application:

```bash
python main.py
```

If OpenCV windows do not show (e.g. Wayland or headless), you can try:

```bash
QT_QPA_PLATFORM=xcb python main.py
```

File Structure & Modules
========================

- `main.py` - Entry point, admin login, menu loop, wrappers for actions.
- `absensi.py` - Scanning and attendance logic, report rendering.
- `siswa.py` - Student management: add/delete/import/generate QR images.
- `sessions.py` - In-memory session and saving logic.
- `siswa.json` - Student metadata file.
- `user_db.json` - Admin credentials (username -> password plain-text).
- `qrcode_generated/` - QR images generated per class.
- `logs/` - Real-time `absensi.csv` and archived session CSVs.

How the Code Works (Detailed flow)
=================================

High-level flow (short):

1. Program starts: `main.py` -> `login()` -> `menu()`.
2. User chooses an action: scan manual, live scan, view reports, manage students, manage sessions.
3. Scanning logic calls `tanda_absen(nis, session_container)` which performs cooldown checks, student lookup, log writing, and in-memory session updates.

Detailed sequence (manual scan):

1. `main.scan_absensi()` calls `absensi.scan_absensi(play_sound, session_container)`.
2. `absensi.scan_absensi()` opens `cv2.VideoCapture(0)`, reads frames once, decodes with `pyzbar.decode(frame)`.
3. On decode:
   - Extract `data.decode('utf-8')` — this is expected to be the student's NIS.
   - Call `tanda_absen(nis, session_container)`.
4. `tanda_absen`:
   - Reads `logs/absensi.csv` in reverse to find the last entry for that NIS (for cooldown).
   - If within cooldown, prints a message and returns `False`.
   - If OK, resolves `kelas` from `siswa.json` (fallback `umum`) and appends a CSV row `nis,timestamp,kelas`.
   - Appends to `session_container.session_absensi` (list of tuples `(nis, waktu, kelas)` or `(nis, waktu)`).
   - Returns `True` on success.
5. Back in scan, if `tanda_absen` returned `True`, `play_sound()` is called (uses `aplay` on Linux), and the UI prints a message.

Detailed sequence (live scan):

1. `main.live_scan_absensi()` calls `absensi.live_scan_absensi(play_sound, session_container)`.
2. The function opens the camera in a loop. Each frame is decoded with `pyzbar.decode(frame)`.
3. For each decoded barcode in the frame:
   - Draw a green rectangle around `obj.rect` on the current frame using `cv2.rectangle` to visually indicate detection.
   - Use a small per-frame local cooldown map `last_scanned[data]` (seconds) to prevent processing the same QR multiple times at frame rate.
   - Call `tanda_absen()` same as above. If success, `play_sound` and print name/kls.
4. When the user presses `q`, the loop exits and the camera is released.

Function Reference (by module)
=============================

main.py
-------
- login(): Read `user_db.json` (dictionary username->password), prompt for username and password (plaintext), validate credentials.
- play_sound(): Runs `os.system('aplay sounds/beep.wav')` on Linux; wrapped in try/except to avoid crashing on missing player or file.
- menu(): Main interactive loop listing options.

absensi.py
----------
- ABSEN_COOLDOWN_SECONDS = 300: Global cooldown in seconds.
- _get_last_absen_time(nis) -> datetime | None: Read `logs/absensi.csv` in reverse lines, parse a 'waktu' column, and returns the last datetime.
- _get_nama_from_siswa(siswa_map, nis): Utility to return a human-readable name from a loaded `siswa` dict (normalizes new/legacy formats).
- tanda_absen(nis, session_container) -> bool: Core attendance recording logic. Returns True if recording happened, False otherwise.
- scan_absensi(play_sound, session_container): Manual one-shot scanning, stops after the first QR.
- live_scan_absensi(play_sound, session_container): Live scanning loop. Uses `last_scanned` local map; marks `cv2.rectangle`.
- print_laporan_live(): Clear screen and print `logs/absensi.csv` in human-readable format using `siswa.json` lookups.
- lihat_laporan(): Similar to `print_laporan_live` but for non-live usage; prints `logs/absensi.csv` on the terminal.

siswa.py
--------
- _load_siswa() -> dict: Returns a normalised mapping `nis -> {nama, kelas}` reading `siswa.json`.
- _save_siswa(data): Writes normalized `siswa.json`.
- tambah_siswa(): CLI prompt to add a new student; generates QR into `qrcode_generated/{kelas}/{nis}.png`.
- hapus_siswa(): Prompt for NIS and remove student from `siswa.json`, remove QR file if present.
- generate_qr_per_kelas(): Read all students and write a QR for each student under the appropriate class folder.
- import_siswa_from_file(): Merge another JSON file into the current `siswa.json` and regenerate QR.

sessions.py
-----------
- session_absensi: A module-level list (in-memory) used to capture session events for the current run: entries are `(nis, waktu)` or `(nis, waktu, kelas)`.
- save_session_absensi(): Writes the current `session_absensi` list to a timestamped file under `logs/` then removes the `logs/absensi.csv` to reset runtime logs.
- lihat_saved_sessions(): List saved sessions and print the formatted entries of a chosen session.

Data Formats
============

- user_db.json: `{ "username": "password" }` (plaintext, insecure; replace with hashed in production).
- siswa.json (recommended format):

```json
{
  "1001": {"nama": "Aldi Saputra", "kelas": "kelas_a"},
  "1002": {"nama": "Siti Nurhayati", "kelas": "kelas_a"}
}
```

- siswa.json (legacy):

```json
{
  "1001": "Aldi Saputra",
  "1002": "Siti Nurhayati"
}
```

- logs/absensi.csv (runtime): CSV rows with `nis,waktu,kelas` where `waktu` is `YYYY-MM-DD HH:MM:SS` and `kelas` can be omitted for older entries.

- logs/absensi-YYYYMMDD_HHMMSS.csv: Session files with the same CSV structure as above.

How to Test / Simulate Scans
============================

1. Generate a QR PNG for a sample NIS using the project's Python dependencies:

```bash
python -c "import qrcode; qrcode.make('1001').save('1001.png')"
```

2. Open `1001.png` on another device or screen and run the application. Point the webcam to the QR to simulate a scan.

3. To unit-test `tanda_absen` without camera access, you can call it from Python REPL — e.g.:

```bash
python -c "from absensi import tanda_absen; import sessions; print(tanda_absen('1001', sessions))"
```

4. To test cooldown logic, call `tanda_absen` twice quickly and confirm the second returns False.

Troubleshooting & Common Issues
==============================

- Camera unavailable: If `cv2.VideoCapture(0)` fails, try different device indices (0, 1, 2) and ensure the camera is not used elsewhere.
- No QR detected: Ensure `libzbar` is installed on your system (for `pyzbar`) and the QR image is clear with good lighting.
- `cv2.imshow` not showing: Use `QT_QPA_PLATFORM=xcb` for Qt/X11 fallback or run in an environment with X11.
- Beep not playing: `aplay` not installed — install `alsa-utils` on Linux or replace `play_sound()` to use a cross-platform library.
- No logs appearing: Check `logs/` write permissions, and make sure `tanda_absen()` is actually being called (print debug messages on the console).

Extending the Project
=====================

- Replace `user_db.json` plaintext with hashed passwords (bcrypt) stored in a new JSON or a small DB.
- Add a web-based or GUI frontend for scan monitoring and user management.
- Add an API to ingest QR codes from a remote scanner or an external app.
- Add unit tests for each module (`tanda_absen`, `_get_last_absen_time`, `session save/load` etc.).
- Add environment variable configuration for camera index, cooldown, and log path.

Contributing
============

PRs welcome — please:

- Provide a clear change description.
- Keep backward compatibility where possible (especially with `siswa.json` format).
- Add tests for new logic.

License
=======
No license is currently set. Add a LICENSE file to declare one if desired.

---

If this README still needs extra details in certain areas (e.g., sequence diagrams with ASCII art, function call graphs, or example debug sessions), tell me which area you want expanded and I’ll add it in the next update.
# Absensi QR (Simple QR Attendance)

Simple command-line application to record attendance using QR codes and a webcam. This repository contains a small, easy-to-run QR attendance system with support for manual and live scanning, student management, and session logs.

---

## Overview

- Input: QR code that encodes a student's NIS (number/identifier).
- Output: Logs of attendance written to `logs/absensi.csv` during runtime and persisted sessions under `logs/absensi-YYYYMMDD_HHMMSS.csv`.
- Student data is maintained in `siswa.json` (supports both a legacy simple mapping and a newer `{nis: {nama, kelas}}` format).
- Admin login is required to access the menu using credentials stored in `user_db.json`.

---

## Quick Start

1. Install project dependencies:

```bash
pip install -r requirements.txt
```

2. Run the app:

```bash
python main.py
```

If you have Qt/Wayland issues (OpenCV window not showing), try:

```bash
QT_QPA_PLATFORM=xcb python main.py
```

3. Login with credentials from `user_db.json` (sample `admin` / `12345`).

---

## Key Concepts and Flow

1. Entry point (`main.py`) displays login and the main menu.
2. User authenticates with `user_db.json` and chooses functionality from the main menu.
3. Scan options:
   - Manual scan (`absensi.scan_absensi()`): opens camera, captures one frame, decodes, and then calls `tanda_absen()` to write log.
   - Live scan (`absensi.live_scan_absensi()`): continuously opens camera, decodes repeatedly with a short per-frame cooldown, and calls `tanda_absen()` for each detected QR.
4. Attendance processing (`absensi.tanda_absen`) checks global cooldown (default 5 minutes), writes to `logs/absensi.csv`, and appends the entry to `sessions.session_absensi`.
5. Save session (`sessions.save_session_absensi`) writes the in-memory session list to a timestamped CSV and removes the working `logs/absensi.csv`.
6. Student management (`siswa.py`) handles adding, deleting, importing, and generating QR images per class.

---

## Important Files and Modules

- `main.py`: Menu and entry point.
- `absensi.py`: Camera capture, QR decode, `tanda_absen` logic, live-mode report.
- `siswa.py`: Student data normalization, CRUD operations, QR generation.
- `sessions.py`: In-memory session storage and session file persisting.
- `siswa.json`: Student data; recommended format: `{ "nis": {"nama":"...","kelas":"..."}}`.
- `user_db.json`: Admin credentials mapping `username -> password`.
- `qrcode_generated/`: Generated QR images per class.
- `logs/`: Contains `absensi.csv` in runtime, and `absensi-YYYYMMDD_HHMMSS.csv` for archived sessions.

---

## How `tanda_absen` Works (Detailed)

- `ABSEN_COOLDOWN_SECONDS` (in `absensi.py`) is by default 300 seconds = 5 minutes: blocks repeated entries for a single NIS.
- Sequence:
  1. Determine last recorded time for the NIS by scanning `logs/absensi.csv` (read lines in reverse for quick check).
  2. If last recorded time is within cooldown -> report remaining time and return False.
  3. Determine the student's `kelas` using `siswa.json` (fallback `umum`).
  4. Append `nis,waktu,kelas` to `logs/absensi.csv` and to `sessions.session_absensi` list.
  5. Return True to indicate successful attendance.

This function isolates the logic for checking repeated entries, writing logs, and updating session storage, making it easy to change cooldown rules or log format.

---

## Student (Siswa) Management

- `_load_siswa()` returns normalized mapping `{nis: {nama, kelas}}` and supports legacy `nis: name` format.
- `tambah_siswa()` stores a new student in `siswa.json` and writes a QR file under `qrcode_generated/{kelas}/{nis}.png`.
- `generate_qr_per_kelas()` regenerates QR images for all students grouped by `kelas`.
- `import_siswa_from_file()` merges another JSON file into `siswa.json` (supporting both formats) then regenerates QR images.

---

## Sessions and Logs

- `logs/absensi.csv` is a working file while the application runs (entries appended as `nis,timestamp,kelas`).
- After saving a session, `sessions.save_session_absensi()` writes a new file `logs/absensi-YYYYMMDD_HHMMSS.csv` and removes the working `logs/absensi.csv`.
- Sessions allow you to open saved CSV files to view a historical report without affecting runtime logs.

---

## Troubleshooting & Tips ⚠️

- Camera incorrect index: try different device numbers in `cv2.VideoCapture()`.
- `pyzbar` doesn't decode: install `libzbar` on Linux.
- `cv2.imshow` fails in headless environments or with Wayland: use `QT_QPA_PLATFORM=xcb` or run in an X11 session.
- No sound: ensure `sounds/beep.wav` exists and `aplay` is installed (Linux) or adapt to platform's audio player.
- Missing write permission: ensure `logs/`, `qrcode_generated/` and other directories are writable.

---

## Development & Extensions

- Suggested improvements:
  - Replace plaintext password in `user_db.json` with hashed passwords.
  - Add a minimal web server to show current live scan and reports.
  - Add a small GUI for easier day-to-day usage.
  - Add tests for `tanda_absen()` logic, formatting, and cooldown behavior.

---

## Contributing

Contributions are welcome: open a PR with your change, add tests when possible, and keep backward compatibility for `siswa.json` legacy format.

---

## License

No license is currently defined. Add a LICENSE file if you want to specify a license.

---

If you'd like sample sequences, visual flowchart images, or troubleshooting examples, tell me which you'd like and I can add them to the README.
# Absensi QR (Simple QR Attendance)

Project sederhana berbasis command-line untuk pencatatan kehadiran siswa menggunakan QR code dan kamera. Dirancang untuk mudah digunakan, mudah dikonfigurasi, dan mudah diperluas.

---

## Ringkasan Singkat ✅

- Input: QR code (berisi NIS siswa)
- Output: Log absensi (CSV), sesi berjudul timestamp, dan laporan singkat di terminal
- Manajemen siswa: `siswa.json` menyimpan data siswa (support legacy & new formats). QR disimpan di `qrcode_generated/` per kelas.
- Login admin sederhana melalui `user_db.json` untuk membuka menu manajemen.

---

## Fitur Utama

- Scan QR Manual (mengambil satu frame dari kamera)
- Live Scan (mode kamera terus menerus dengan deteksi ulang yang dikontrol cooldown)
- CRUD untuk `siswa.json` (Tambah / Hapus / Import) dan pembuatan QR per siswa/kelas
- Menyimpan sesi absensi saat runtime ke CSV dengan timestamped filename
- Menampilkan laporan saat runtime dan membuka sesi yang tersimpan

---

## Struktur File & Peran Modul 🔧

- `main.py` - Titik masuk aplikasi: login, menu, dan pemanggilan fungsi lain.
- `absensi.py` - Logika pemindaian QR, validasi cooldown, penulisan log, dan laporan live/terkini.
- `siswa.py` - Manajemen data siswa, normalisasi `siswa.json`, pembuatan QR, import data siswa.
- `sessions.py` - Menyimpan sesi absensi runtime ke file CSV timestamped, melihat/ membuka sesi yang tersimpan.
- `siswa.json` - Data siswa (format baru: object per `nis` atau legacy: `nis -> nama` string).
- `user_db.json` - Username/password untuk login admin (format: `{ "user": "password" }`).
- `qrcode_generated/` - Folder keluaran QR per kelas.
- `logs/` - Folder menyimpan `absensi.csv` (sementara) dan `absensi-YYYYMMDD_HHMMSS.csv` (sesi disimpan).
- `sounds/beep.wav` - Suara notifikasi ketika pembaca QR berhasil dibaca.

---

## Instalasi & Prasyarat 🛠️

- Python 3.8+
- Kamera yang bisa diakses oleh OpenCV (device index default `0` digunakan)
- (Opsional) `aplay` (ALSA) di Linux untuk memainkan `sounds/beep.wav`
- Install dependencies:

```bash
pip install -r requirements.txt
```

Atau manual:

```bash
pip install opencv-python pyzbar qrcode pillow
```

Catatan: Untuk `pyzbar` pada Linux, pasang `libzbar`:

```bash
sudo apt-get install libzbar0
```

---

## Menjalankan Aplikasi 🏃

1. Jalankan:

```bash
python main.py
```

2. Jika mengalami masalah tampilan (Qt/Wayland), jalankan:

```bash
QT_QPA_PLATFORM=xcb python main.py
```

3. Login menggunakan kredensial pada `user_db.json` (contoh pada repo: `admin` / `12345`).

---

## Penjelasan Alur Program (Flow) 🔁

1. Program memulai dengan `main.login()`:
   - Membaca `user_db.json` dan memverifikasi username/password.

2. Setelah login, `main.menu()` menampilkan opsi operasional (scan manual, live scan, laporan, manajemen siswa, manajemen sesi).

3. Manual & Live Scan (di `absensi.py`):
   - `scan_absensi()` (manual): membuka kamera (`cv2.VideoCapture(0)`), ambil 1 frame, panggil `pyzbar.decode(frame)`, lalu `tanda_absen()` ketika QR terdeteksi.
   - `live_scan_absensi()` (live): membuka kamera terus menerus, menandai QR dengan kotak hijau (`cv2.rectangle()`), mencegah spam scan (local cooldown `3` detik dan global cooldown `ABSEN_COOLDOWN_SECONDS`), lalu memanggil `tanda_absen()`.

4. `tanda_absen(nis, session_container)` (`absensi.py`):
   - Mengecek cooldown global (`ABSEN_COOLDOWN_SECONDS`, default `300s`) untuk NIS.
   - Mengambil `nama` & `kelas` dari `siswa.json` (fallback ke `umum`).
   - Menulis entri ke `logs/absensi.csv` (format `nis,YYYY-MM-DD HH:MM:SS,kelas`).
   - Menambahkan entri ke `sessions.session_absensi` (list in-memory untuk sesi saat itu).

5. `sessions.py`
   - `session_absensi` adalah list in-memory berisi entri sesi.
   - `save_session_absensi()` menulis entri ke file `logs/absensi-YYYYMMDD_HHMMSS.csv` lalu menghapus `logs/absensi.csv` (file sementara) agar sesi baru dimulai bersih.

6. `siswa.py` - Manajemen data siswa & QR
   - `_load_siswa()` menormalisasi `siswa.json` menjadi bentuk `{ nis: {"nama":..., "kelas":...}}`.
   - `tambah_siswa()` menambahkan siswa, menyimpannya di `siswa.json`, dan membuat QR di folder per kelas.
   - `hapus_siswa()`, `generate_qr_per_kelas()`, `import_siswa_from_file()` tersedia untuk mengelola data siswa.

---

## Format & Contoh File 🔎

- `user_db.json`:

```json
{
  "admin": "password123"
}
```

- `siswa.json` (direkomendasikan):

```json
{
  "12345": {"nama": "Budi", "kelas": "kelas_a"},
  "67890": {"nama": "Siti", "kelas": "kelas_b"}
}
```

- `siswa.json` (legacy):

```json
{
  "12345": "Budi",
  "67890": "Siti"
}
```

- `logs/absensi.csv` (sementara):

```
nis,YYYY-MM-DD HH:MM:SS,kelas
12345,2023-01-11 08:25:12,kelas_a
```

---

## Konfigurasi Penting & Constants ⚙️

- `ABSEN_COOLDOWN_SECONDS` di `absensi.py` (default `300`) — membatasi interval absen berulang per NIS.
- Kamera index (`cv2.VideoCapture(0)`) bisa disesuaikan agar mendukung device lain.

---

## Troubleshooting & Tips ⚠️

- Kamera tak terbaca? Cek device index, pastikan kamera tidak dibuka aplikasi lain.
- `pyzbar` tak mendeteksi? Pastikan `libzbar` ter-install.
- `cv2.imshow` error (Qt/Wayland) => gunakan `QT_QPA_PLATFORM=xcb` atau jalankan di lingkungan yang mendukung X.
- Bunyi beep tidak keluar? Periksa `sounds/beep.wav` dan keberadaan `aplay` di PATH (Linux).
- Pastikan folder `logs/` writable.

---

## Contoh Alur Penggunaan (Step-by-step) 📋

1. Jalankan `python main.py`.
2. Login sebagai `admin`.
3. Pilih `Atur Absensi Siswa` -> `Generate QR per Kelas` untuk membuat QR.
4. Kembali ke menu utama, pilih `Live Scan Absensi` untuk memindai banyak QR.
5. Ketika selesai, pilih `Atur Sesi Absensi` -> `Simpan Sesi Absensi` agar sesi tersimpan sebagai file timestamped.

---

## Pengembangan & Catatan Tambahan 💡

- Normalisasi `siswa.json` memudahkan manajemen data dan kompatibilitas antara format lama dan baru.
- Menyimpan sesi akan menghapus `logs/absensi.csv` sehingga setiap sesi dianggap terpisah.
- Area peningkatan: enkripsi password, autentikasi lebih kuat, integrasi server/web UI, export ke Excel/CSV secara otomatis.

---

## Contribusi

Perbaikan kecil atau fitur baru diterima melalui PR. Sertakan deskripsi perubahan dan cek backward compatibility terhadap `siswa.json` legacy format.

---

## Lisensi

Repository belum memiliki lisensi formal — tambahkan LICENSE sesuai kebutuhan.

---

Jika Anda mau, saya bisa menambahkan diagram visual alur kerja (svg/png), contoh log, dan instruksi debug tambahan.
````markdown
# Absensi QR (Simple QR Attendance)

Project sederhana berbasis command-line untuk mencatat kehadiran siswa menggunakan QR code + kamera.
Dirancang agar mudah dipakai (scan QR manual atau live), mudah dikonfigurasi (JSON), dan sederhana untuk dikembangkan lebih lanjut.

---

## Ringkasan Singkat ✅

- Input: QR code (berisi NIS siswa)
- Output: Log absensi (CSV), sesi berjudul timestamp, dan laporan singkat di terminal
- Manajemen siswa: `siswa.json` menyimpan data (support legacy & new formats). QR disimpan di `qrcode_generated/` per kelas.
- Login admin sederhana melalui `user_db.json` untuk membuka menu manajemen

---

## Fitur Utama

- Scan QR Manual (mengambil satu frame dari kamera)
- Live Scan (mode kamera terus menerus dengan deteksi ulang yang dikontrol cooldown)
- CRUD untuk `siswa.json` (Tambah / Hapus / Import) dan pembuatan QR per siswa/kelas
- Menyimpan sesi absensi saat runtime ke CSV berpenamaan timestamp
- Menampilkan laporan saat runtime dan membuka sesi yang tersimpan

---

## Struktur File dan Peran Modul 🔧

- `main.py` - Titik masuk (entrypoint) aplikasi: login, menu, dan pemanggilan fungsi lain.
- `absensi.py` - Semua logika terkait pemindaian QR, validasi cooldown, penulisan log, dan fungsi untuk menampilkan laporan live/terkini.
- `siswa.py` - Manajemen data siswa, normalisasi `siswa.json`, pembuatan QR, import data siswa.
- `sessions.py` - Menyimpan sesi absensi runtime ke file CSV timestamped, melihat / membuka sesi yang tersimpan.
- `siswa.json` - Data siswa (format baru: object per `nis` atau legacy: `nis -> nama` string).
- `user_db.json` - Username/password untuk login admin (format: `{ "user": "password" }`).
- `qrcode_generated/` - Folder keluaran QR per kelas. Contoh `qrcode_generated/kelas_a/1001.png`.
- `logs/` - Folder menyimpan `absensi.csv` (sementara) dan `absensi-YYYYMMDD_HHMMSS.csv` (sesi disimpan).
- `sounds/beep.wav` - Suara notifikasi ketika pembaca QR berhasil dibaca.

---

## Instalasi & Prasyarat 🛠️

- Python 3.8+
- Kamera yang bisa diakses oleh OpenCV (indeks device default `0` digunakan)
- Optional: `aplay` (ALSA) di Linux untuk memainkan `sounds/beep.wav`
- Install Python packages:

```bash
pip install -r requirements.txt
```

Tuliskan alternatif jika Anda mau menginstall manual:

```bash
pip install opencv-python pyzbar qrcode pillow
```

Catatan: Untuk `pyzbar` pada Linux, Anda mungkin perlu menginstall `libzbar`:

```bash
sudo apt-get install libzbar0
```

---

## Cara Menjalankan 🏃

```
python main.py
```

Jika Anda mengalami masalah GUI/Qt (mis. Wayland/X11), coba:

```
QT_QPA_PLATFORM=xcb python main.py
```

Saat run, login menggunakan `user_db.json` (default: `admin` dengan password `12345` pada contoh repo ini).

---

## Penjelasan Alur Program (Flow) 🔁

1. User memanggil `python main.py`. Program menampilkan prompt login di `main.login()`:
   - Membaca `user_db.json` (JSON key-value username -> password).
   - Jika login berhasil, menampilkan `menu()` utama.

2. Pada `menu()` pengguna memilih satu dari opsi: `Scan Absensi (manual)`, `Live Scan Absensi`, `Lihat Laporan`, `Atur Absensi Siswa`, `Atur Sesi Absensi`, `Exit`.

3. Manual Scan & Live Scan (di `absensi.py`)
   - `absensi.scan_absensi()` (manual): membuka kamera (`cv2.VideoCapture(0)`), mengambil frame, decode QR menggunakan `pyzbar.decode(frame)`, memanggil `tanda_absen(nis, session_container)` jika QR ditemukan; kemudian menutup kamera.
   - `absensi.live_scan_absensi()` (live): membuka kamera terus menerus, menampilkan kotak hijau untuk QR yang terdeteksi, mencegah spam repeat scan di tingkat frame menggunakan cache `last_scanned` dan cooldown local (3 detik). Setiap scan memanggil `tanda_absen()` yang menulis ke `logs/absensi.csv` dan menambahkan ke `sessions.session_absensi`.
   - Jika `tanda_absen()` sukses, aplikasi memainkan `sounds/beep.wav` (menggunakan `aplay` pada Linux), lalu menampilkan nama & kelas siswa berdasarkan `siswa.json`.

4. `tanda_absen(nis, session_container)`
   - Path: `absensi.tanda_absen()`
   - Fungsi ini melakukan pengecekan cooldown global (default 5 menit, `ABSEN_COOLDOWN_SECONDS = 300`) untuk menghindari spam absensi berulang dari NIS yang sama.
   - Membaca `siswa.json` untuk mengetahui `nama` dan `kelas`; jika gagal diambil, fallback ke `umum`.
   - Menulis baris ke `logs/absensi.csv` berformat: `nis,YYYY-MM-DD HH:MM:SS,kelas`.
   - Menyimpan entri ini ke `sessions.session_absensi` (list in-memory untuk sesi saat itu).

5. Lihat Laporan (`absensi.lihat_laporan()` / `sessions.lihat_saved_sessions()`)
   - Membaca `logs/absensi.csv` (untuk laporan saat ini) atau file sesi `logs/absensi-YYYYMMDD_HHMMSS.csv` (untuk laporan tersimpan) dan merender daftar `nis - nama - kelas - waktu`.

6. Manajemen Siswa (`siswa.py`)
   - `_load_siswa()` normalizes `siswa.json` (mendukung legacy/baru). Output selalu menjadi shape `{ nis: {'nama':..., 'kelas':...}}`.
   - `tambah_siswa()` menambah siswa, menyimpan ke `siswa.json` dan membuat QR (`qrcode.make(nis)`) di `qrcode_generated/{kelas}/{nis}.png`.
   - `hapus_siswa()` menghapus siswa dan menghapus file QR bila ada.
   - `generate_qr_per_kelas()` membuat/memperbarui QR untuk seluruh `siswa.json`.
   - `import_siswa_from_file()` mengimpor file JSON eksternal dan mem-merge ke `siswa.json` lalu generate QR per kelas.

7. Sesi (`sessions.py`)
   - `session_absensi` adalah list in-memory untuk sesi berjalan (format tuple `(nis, waktu)` atau `(nis, waktu, kelas)`).
   - `save_session_absensi()` menulis `session_absensi` ke file `logs/absensi-YYYYMMDD_HHMMSS.csv` lalu menghapus `logs/absensi.csv` (sementara) agar sesi baru mulai bersih.

---

## Format & Contoh File 🔎

- `user_db.json`
```json
{
  "admin": "password123"
}
```

- `siswa.json` (format baru yang direkomendasikan):
```json
{
  "12345": {"nama": "Budi", "kelas": "kelas_a"},
  "67890": {"nama": "Siti", "kelas": "kelas_b"}
}
```

- `siswa.json` (legacy/old format juga didukung):
```json
{
  "12345": "Budi",
  "67890": "Siti"
}
```

- `logs/absensi.csv` (sementara/real-time)
CSV: `nis,YYYY-MM-DD HH:MM:SS,kelas`
contoh: `12345,2023-01-11 08:25:12,kelas_a`

---

## Konfigurasi Penting & Constants ⚙️

- `ABSEN_COOLDOWN_SECONDS` (di `absensi.py`, default `300`) — waktu (detik) antara absensi yang diterima untuk NIS yang sama.
- Kamera index di `cv2.VideoCapture(0)` dapat diubah jika perangkat Anda memiliki indeks lain.

---

## Troubleshooting & Tips ⚠️

- Kamera tidak terbuka? Tutup aplikasi lain yang menggunakan kamera atau ubah index (0 -> 1, 2).
- `pyzbar` tidak mendeteksi QR? Pastikan `libzbar` terinstal di sistem.
- Jika gambar `cv2.imshow` tidak tampil (error Qt/Wayland), jalankan dengan `QT_QPA_PLATFORM=xcb` atau sesuaikan environment display.
- Bunyi tidak terdengar? Periksa `sounds/beep.wav` dan apakah `aplay` tersedia (Linux).
- Jika log tidak tercatat, pastikan folder `logs/` dapat ditulisi dan Anda belum lupa menginisialisasi `siswa.json`/`user_db.json`.

---

## Contoh Alur Penggunaan (Step-by-step) 📋

1. Jalankan: `python main.py`.
2. Login sebagai `admin`.
3. Pilih `Atur Absensi Siswa` -> `Generate QR per Kelas` untuk membuat QR untuk setiap siswa. Files di `qrcode_generated/*`.
4. Kembal ke menu utama, pilih `Live Scan Absensi`.
5. Arahkan kamera ke QR; ketika terdeteksi akan muncul kotak hijau dan log ditulis ke `logs/absensi.csv`. Jika `tanda_absen` sukses, akan dimainkan suara beep.
6. Setelah sesi selesai, pilih `Atur Sesi Absensi` -> `Simpan Sesi Absensi` untuk menyimpan entri runtime ke `logs/absensi-*.csv`.

---

## Pengembangan & Catatan Tambahan 💡

- Format `siswa.json` dinormalisasi untuk mempermudah manipulasi; fungsi `_load_siswa()` mengubah data legacy ke bentuk object `{ nis: {nama, kelas}}`.
- Perhatikan: `logs/absensi.csv` dihapus ketika menyimpan sesi karena file sementara dianggap reset setiap run.
- Menambahkan autentikasi lebih baik, enkripsi password, atau server kecil untuk remote scanning adalah fitur yang layak dikembangkan.

---

## Contribusi

Silakan buka PR untuk perbaikan bug, pembaruan dokumentasi, atau penambahan fitur (mis. integrasi server, export, UI sederhana).

---

## Lisensi

Repository ini tidak menyertakan lisensi formal—gunakan dengan bijak dan tambahkan LICENSE jika perlu.

---

Jika Anda ingin saya menambah diagram alur (grafis), contoh data, atau instruksi debug lebih mendetail (contoh log / contoh step-by-step troubleshooting), beri tahu dan saya akan menambahkannya.

````
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
