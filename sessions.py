import os
import glob
import json
from datetime import datetime

# In-memory list to track this run's absensi entries (nis, waktu)
session_absensi = []


def save_session_absensi():
    """Save the current session's absensi to a dated CSV in `logs/`.

    Filename format: logs/absensi-YYYYMMDD_HHMMSS.csv
    """
    global session_absensi
    if not session_absensi:
        print("Tidak ada data absensi di sesi ini untuk disimpan.\n")
        return

    t = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"logs/absensi-{t}.csv"

    os.makedirs(os.path.dirname(filename), exist_ok=True)
    with open(filename, 'w') as f:
        for entry in session_absensi:
            # entry may be (nis, waktu) or (nis, waktu, kelas)
            if isinstance(entry, (list, tuple)) and len(entry) >= 3:
                nis, waktu, kelas = entry[0], entry[1], entry[2]
                f.write(f"{nis},{waktu},{kelas}\n")
            elif isinstance(entry, (list, tuple)) and len(entry) >= 2:
                nis, waktu = entry[0], entry[1]
                f.write(f"{nis},{waktu}\n")
            else:
                # fallback: write as-is
                f.write(str(entry) + "\n")

    os.remove("logs/absensi.csv")
    print(f"Sesi absensi disimpan ke: {filename}\n")


def lihat_saved_sessions():
    """List saved session files and allow opening one like laporan."""
    files = sorted(glob.glob('logs/absensi-*.csv'))
    if not files:
        print("Belum ada sesi absensi yang disimpan.\n")
        return

    print("\n=== Sesi Absensi Tersimpan ===")
    for i, fpath in enumerate(files, start=1):
        print(f"{i}. {os.path.basename(fpath)}")

    print("0. Batal")
    choice = input("Pilih nomor untuk membuka: ")
    try:
        idx = int(choice)
    except ValueError:
        print("Pilihan tidak valid.\n")
        return

    if idx == 0:
        return

    if 1 <= idx <= len(files):
        fpath = files[idx-1]
        # Display like laporan
        print(f"\n=== LAPORAN: {os.path.basename(fpath)} ===")
        with open("siswa.json", "r") as f:
            siswa = json.load(f)

        with open(fpath, 'r') as f:
            for line in f:
                parts = line.strip().split(',')
                if len(parts) < 2:
                    continue
                nis = parts[0]
                waktu = parts[1]
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
    else:
        print("Pilihan diluar jangkauan.\n")


def atur_sesi_menu():
    while True:
        print("\n=== ATUR SESI ABSENSI ===")
        print("1. Simpan Sesi Absensi")
        print("2. Lihat Sesi Tersimpan")
        print("0. Kembali")
        pilihan = input("Pilih: ")
        if pilihan == "1":
            save_session_absensi()
        elif pilihan == "2":
            lihat_saved_sessions()
        elif pilihan == "0":
            break
        else:
            print("Pilihan tidak valid.\n")
