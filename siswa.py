import json
import qrcode
import os


def _load_siswa():
    """Load `siswa.json` and normalize entries to dict format:
    { nis: { 'nama': ..., 'kelas': ... }, ... }
    Supports legacy format where value is a plain name string.
    """
    try:
        with open("siswa.json", "r") as f:
            data = json.load(f)
    except Exception:
        return {}

    normalized = {}
    for nis, v in data.items():
        if isinstance(v, dict):
            nama = v.get('nama') or v.get('name') or ''
            kelas = v.get('kelas') or v.get('class') or 'umum'
        else:
            nama = str(v)
            kelas = 'umum'
        normalized[nis] = {'nama': nama, 'kelas': kelas}
    return normalized


def _save_siswa(data):
    """Save normalized siswa mapping to `siswa.json`.
    `data` expected as { nis: {'nama':..., 'kelas':...}, ... }
    """
    try:
        with open("siswa.json", "w") as f:
            json.dump(data, f, indent=2)
    except Exception:
        print("Gagal menyimpan siswa.json")


def tambah_siswa():
    nama = input("Nama siswa: ")
    nis = input("NIS: ")
    kelas = input("Kelas (contoh: kelas_a): ") or 'umum'

    data = _load_siswa()
    data[nis] = {'nama': nama, 'kelas': kelas}
    _save_siswa(data)

    # create QR under class folder
    outdir = os.path.join('qrcode_generated', kelas)
    os.makedirs(outdir, exist_ok=True)
    qr = qrcode.make(nis)
    qr.save(os.path.join(outdir, f"{nis}.png"))

    print(f"QR untuk {nama} ({nis}) di {kelas} berhasil dibuat!\n")


def hapus_siswa():
    """Hapus siswa berdasarkan NIS."""
    data = _load_siswa()
    if not data:
        print("Gagal membaca file siswa.json atau tidak ada data.\n")
        return

    if not data:
        print("Tidak ada siswa untuk dihapus.\n")
        return

    print("\n=== Hapus Siswa ===")
    for nis, info in data.items():
        print(f"{nis} - {info.get('nama')} - {info.get('kelas')}")

    nis_to_delete = input("Masukkan NIS siswa yang akan dihapus (atau 0 untuk batal): ")
    if nis_to_delete == "0":
        return
    if nis_to_delete not in data:
        print("NIS tidak ditemukan.\n")
        return

    info = data.pop(nis_to_delete)
    try:
        _save_siswa(data)
    except Exception:
        print("Gagal menyimpan perubahan ke siswa.json\n")
        return

    # remove QR file(s) if exists
    qr_path = os.path.join('qrcode_generated', info.get('kelas', 'umum'), f"{nis_to_delete}.png")
    try:
        if os.path.exists(qr_path):
            os.remove(qr_path)
    except Exception:
        pass

    print(f"Siswa {info.get('nama')} ({nis_to_delete}) berhasil dihapus.\n")


def atur_siswa_menu():
    while True:
        print("\n=== ATUR SISWA ===")
        print("1. Tambah Siswa")
        print("2. Hapus Siswa")
        print("3. Generate QR per Kelas (dari siswa.json)")
        print("4. Import siswa dari file JSON")
        print("0. Kembali")
        pilihan = input("Pilih: ")
        if pilihan == "1":
            tambah_siswa()
        elif pilihan == "2":
            hapus_siswa()
        elif pilihan == "3":
            generate_qr_per_kelas()
        elif pilihan == "4":
            import_siswa_from_file()
        elif pilihan == "0":
            break
        else:
            print("Pilihan tidak valid.\n")


def generate_qr_per_kelas():
    """Generate QR images for all students grouped into `qrcode_generated/{kelas}/`.
    This reads `siswa.json` and creates directories per `kelas`.
    """
    data = _load_siswa()
    if not data:
        print("Belum ada data siswa untuk dibuatkan QR.\n")
        return

    for nis, info in data.items():
        kelas = info.get('kelas', 'umum') or 'umum'
        outdir = os.path.join('qrcode_generated', kelas)
        os.makedirs(outdir, exist_ok=True)
        qr = qrcode.make(nis)
        try:
            qr.save(os.path.join(outdir, f"{nis}.png"))
        except Exception:
            print(f"Gagal menyimpan QR untuk {nis} di {outdir}")

    print("Semua QR siswa berhasil dibuat/diupdate per kelas.\n")


def import_siswa_from_file():
    """Import siswa data from another JSON file and merge into `siswa.json`.
    The imported file may use either legacy format (nis->name) or new format (nis->object).
    After merge, QR per kelas will be generated.
    """
    path = input("Path file JSON untuk diimport (contoh: import_siswa.json): ")
    if not os.path.exists(path):
        print("File tidak ditemukan.\n")
        return

    try:
        with open(path, 'r') as f:
            incoming = json.load(f)
    except Exception:
        print("Gagal membaca file import. Pastikan format JSON benar.\n")
        return

    current = _load_siswa()
    # normalize incoming same as _load_siswa logic
    for nis, v in incoming.items():
        if isinstance(v, dict):
            nama = v.get('nama') or v.get('name') or ''
            kelas = v.get('kelas') or v.get('class') or 'umum'
        else:
            nama = str(v)
            kelas = 'umum'
        current[nis] = {'nama': nama, 'kelas': kelas}

    _save_siswa(current)
    print("Import selesai. Membuat QR per kelas sekarang...")
    generate_qr_per_kelas()
