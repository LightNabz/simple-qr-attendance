import json
import qrcode
from pyzbar.pyzbar import decode
from datetime import datetime
import os
import cv2
import time
import glob
import http.server
import socketserver
import threading

# ===================== LOGIN =====================

def login():
    with open("user_db.json", "r") as f:
        users = json.load(f)

    print("=== LOGIN ADMIN ===")
    username = input("Username: ")
    password = input("Password: ")

    if username in users and users[username] == password:
        print("Login berhasil!\n")
        return True
    else:
        print("Login gagal!\n")
        return False

# ===================== SOUND =====================

def play_sound():
    try:
        os.system("aplay sounds/beep.wav > /dev/null 2>&1")
    except:
        pass

import absensi
import siswa
import sessions

# session container to pass into absensi functions OwO
session_container = sessions

def scan_absensi():
    return absensi.scan_absensi(play_sound, session_container)


def live_scan_absensi():
    return absensi.live_scan_absensi(play_sound, session_container)


def lihat_laporan():
    return absensi.lihat_laporan()


def atur_siswa_menu():
    return siswa.atur_siswa_menu()


def atur_sesi_menu():
    return sessions.atur_sesi_menu()

# ===================== MENU =====================

def menu():
    while True:
        print("\n=== MENU UTAMA ===")
        print("1. Scan Absensi (manual)")
        print("2. Live Scan Absensi")
        print("3. Lihat Laporan Absensi")
        print("4. Atur Absensi Siswa")
        print("5. Atur Sesi Absensi")
        print("0. Exit")

        pilihan = input("Pilih menu: ")

        if pilihan == "1":
            scan_absensi()
        elif pilihan == "2":
            live_scan_absensi()
        elif pilihan == "3":
            lihat_laporan()
        elif pilihan == "4":
            atur_siswa_menu()
        elif pilihan == "5":
            atur_sesi_menu()
        elif pilihan == "0":
            print("Keluar...")
            if not os.path.exists("logs/absensi.csv"):
                pass
            else:
                os.remove("logs/absensi.csv")
            break
        else:
            print("Pilihan tidak valid.\n")

# ===================== MAIN =====================

if __name__ == "__main__":
    if login():
        menu()
