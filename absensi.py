import os
import cv2
import time
import json
from datetime import datetime

# Cooldown (seconds) before the same siswa can absen again
ABSEN_COOLDOWN_SECONDS = 300  # 5 minutes


def _get_last_absen_time(nis):
    """Return last absensi datetime for `nis` from logs, or None if not found."""
    if not os.path.exists("logs/absensi.csv"):
        return None
    try:
        with open("logs/absensi.csv", "r") as f:
            lines = f.readlines()
    except Exception:
        return None

    for line in reversed(lines):
        parts = line.strip().split(',')
        if len(parts) < 2:
            continue
        n, waktu = parts[0], parts[1]
        if n == nis:
            try:
                return datetime.strptime(waktu, "%Y-%m-%d %H:%M:%S")
            except Exception:
                return None
    return None


def _get_nama_from_siswa(siswa_map, nis):
    """Return a display name given loaded siswa mapping which may be legacy or new format."""
    v = siswa_map.get(nis)
    if isinstance(v, dict):
        return v.get('nama', nis)
    if isinstance(v, str):
        return v
    return nis


def tanda_absen(nis, session_container):
    """Attempt to record attendance for `nis`.

    Returns True if attendance was recorded, False if blocked by cooldown.
    `session_container` should be the module or object that exposes `session_absensi` list.
    """
    now_dt = datetime.now()

    last = _get_last_absen_time(nis)
    if last is not None:
        elapsed = (now_dt - last).total_seconds()
        if elapsed < ABSEN_COOLDOWN_SECONDS:
            remaining = int(ABSEN_COOLDOWN_SECONDS - elapsed)
            # Try to get name for friendlier message
            try:
                with open("siswa.json", "r") as f:
                    siswa = json.load(f)
                # support both legacy and new format
                if isinstance(siswa.get(nis), dict):
                    nama = siswa.get(nis, {}).get('nama', nis)
                else:
                    nama = siswa.get(nis, 'Unknown')
            except Exception:
                nama = nis
            print(f"{nama} ({nis}) sudah absen baru-baru ini. Tunggu {remaining} detik sebelum absen lagi.")
            return False

    waktu = now_dt.strftime("%Y-%m-%d %H:%M:%S")
    # Determine kelas (store into the CSV for easier later processing)
    try:
        with open("siswa.json", "r") as f:
            siswa = json.load(f)
        if isinstance(siswa.get(nis), dict):
            kelas = siswa.get(nis, {}).get('kelas', 'umum')
        else:
            kelas = 'umum'
    except Exception:
        kelas = 'umum'

    # Ensure logs directory exists
    os.makedirs(os.path.dirname("logs/absensi.csv"), exist_ok=True)
    with open("logs/absensi.csv", "a") as f:
        # New format: nis,waktu,kelas  (legacy readers expecting two columns are supported)
        f.write(f"{nis},{waktu},{kelas}\n")

    # Track in current session provided by caller
    if not hasattr(session_container, 'session_absensi') or session_container.session_absensi is None:
        session_container.session_absensi = []
    # Append kelas in-session too (some runs may still append 2-tuples elsewhere)
    session_container.session_absensi.append((nis, waktu, kelas))
    return True


def scan_absensi(play_sound, session_container):
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("Tidak dapat mengakses kamera.")
        return

    print("Tekan 'q' untuk keluar.")

    while True:
        ret, frame = cap.read()
        if not ret:
            print("Gagal membaca frame.")
            break

        from pyzbar.pyzbar import decode
        decoded_objects = decode(frame)
        for obj in decoded_objects:
            data = obj.data.decode('utf-8')
            print(f"QR Code terdeteksi: {data}")

            success = tanda_absen(data, session_container)
            if success:
                play_sound()
                print("Absensi berhasil!\n")
            # stop after processing first detected QR (whether success or cooldown)
            cap.release()
            cv2.destroyAllWindows()
            return

        cv2.imshow("Scan QR Code", frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()


def live_scan_absensi(play_sound, session_container):
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("Tidak dapat mengakses kamera.")
        return

    print("Tekan 'q' untuk keluar. Mode live scan aktif.")
    last_scanned = {}
    cooldown = 3  # detik

    from pyzbar.pyzbar import decode

    while True:
        ret, frame = cap.read()
        if not ret:
            print("Gagal membaca frame.")
            break

        decoded_objects = decode(frame)
        for obj in decoded_objects:
            # --- Kotak hijau ---
            (x, y, w, h) = obj.rect
            cv2.rectangle(frame, (x, y), (x + w, y + h), (0,255,0), 2)

            data = obj.data.decode("utf-8")
            now = time.time()

            # Cegah spam QR sama (frame-level cooldown to avoid extremely rapid repeats)
            if data in last_scanned and now - last_scanned[data] < cooldown:
                continue

            last_scanned[data] = now

            success = tanda_absen(data, session_container)
            if success:
                play_sound()
                try:
                    with open("siswa.json", "r") as f:
                        siswa = json.load(f)
                    if isinstance(siswa.get(data), dict):
                        nama = siswa.get(data, {}).get('nama', data)
                        kelas = siswa.get(data, {}).get('kelas', 'umum')
                    else:
                        nama = siswa.get(data, data)
                        kelas = 'umum'
                except Exception:
                    nama = data
                    kelas = 'umum'

                print(f"QR Code terdeteksi: {data} -> {nama} ({kelas})")
                print("Absensi berhasil!")
                print_laporan_live()

        cv2.imshow("Live Scan QR Code", frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()


def print_laporan_live():
    os.system('clear')
    print("\n=== LAPORAN ABSENSI LIVE ===")

    if not os.path.exists("logs/absensi.csv"):
        print("Belum ada data absensi.\n")
        return

    with open("siswa.json", "r") as f:
        siswa = json.load(f)

    with open("logs/absensi.csv", "r") as f:
        for line in f:
            parts = line.strip().split(',')
            if len(parts) < 2:
                continue
            nis = parts[0]
            waktu = parts[1]
            # If kelas was stored in the CSV, use it; otherwise fall back to siswa.json
            if len(parts) >= 3 and parts[2].strip():
                kelas = parts[2]
            else:
                if isinstance(siswa.get(nis), dict):
                    kelas = siswa.get(nis, {}).get('kelas', 'umum')
                else:
                    kelas = 'umum'

            if isinstance(siswa.get(nis), dict):
                nama = siswa.get(nis, {}).get('nama', nis)
            else:
                nama = siswa.get(nis, 'Unknown')

            print(f"{nis} - {nama} - {kelas} - {waktu}")

    print()


def lihat_laporan():
    print("\n=== LAPORAN ABSENSI ===")

    if not os.path.exists("logs/absensi.csv"):
        print("Belum ada data absensi.\n")
        return

    with open("siswa.json", "r") as f:
        siswa = json.load(f)

    with open("logs/absensi.csv", "r") as f:
        for line in f:
            parts = line.strip().split(',')
            if len(parts) < 2:
                continue
            nis = parts[0]
            waktu = parts[1]
            # If kelas was stored in the CSV, use it; otherwise fall back to siswa.json
            if len(parts) >= 3 and parts[2].strip():
                kelas = parts[2]
            else:
                if isinstance(siswa.get(nis), dict):
                    kelas = siswa.get(nis, {}).get('kelas', 'umum')
                else:
                    kelas = 'umum'

            if isinstance(siswa.get(nis), dict):
                nama = siswa.get(nis, {}).get('nama', nis)
            else:
                nama = siswa.get(nis, 'Unknown')

            print(f"{nis} - {nama} - {kelas} - {waktu}")

    print()
