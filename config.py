"""Konstanta dan konfigurasi global KOSPACE."""

from __future__ import annotations

from pathlib import Path

# ---------------------------------------------------------------------------
# Lokasi berkas
# ---------------------------------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
DB_PATH = DATA_DIR / "kospace.db"

# ---------------------------------------------------------------------------
# Identitas aplikasi
# ---------------------------------------------------------------------------
APP_NAME = "KOSPACE"
APP_TAGLINE = "Sistem Administrasi Pengelolaan Kos"
APP_VERSION = "1.0.0"
OWNER_NAME = "Pemilik Kos"

# ---------------------------------------------------------------------------
# Aturan operasional
# ---------------------------------------------------------------------------
PAYMENT_DUE_DAY = 10  # Tanggal jatuh tempo pembayaran bulanan

# ---------------------------------------------------------------------------
# Tipe kamar (mengikuti dokumen rancangan)
# ---------------------------------------------------------------------------
ROOM_TYPES: dict[str, dict[str, object]] = {
    "A": {
        "label": "Tipe A",
        "fasilitas": "AC, Wi-Fi, kamar mandi dalam",
        "harga": 1_300_000,
        "jumlah": 5,
        "warna": "#B65C82",
    },
    "B": {
        "label": "Tipe B",
        "fasilitas": "AC, Wi-Fi, kamar mandi luar",
        "harga": 950_000,
        "jumlah": 10,
        "warna": "#7B3F61",
    },
    "C": {
        "label": "Tipe C",
        "fasilitas": "Kipas angin, Wi-Fi, kamar mandi luar",
        "harga": 700_000,
        "jumlah": 10,
        "warna": "#C99A6B",
    },
}

STATUS_KAMAR = ("Tersedia", "Ditempati")
STATUS_SEWA = ("Aktif", "Selesai")
STATUS_BAYAR = ("Lunas", "Belum Dibayar", "Terlambat")

MONTHS_ID = (
    "Januari",
    "Februari",
    "Maret",
    "April",
    "Mei",
    "Juni",
    "Juli",
    "Agustus",
    "September",
    "Oktober",
    "November",
    "Desember",
)

# Navigasi sidebar: (kunci halaman, label, ikon)
NAV_ITEMS = (
    ("dashboard", "Dashboard", "▦"),
    ("kamar", "Kamar", "▤"),
    ("penghuni", "Penghuni", "☺"),
    ("sewa", "Sewa", "⇄"),
    ("pembayaran", "Pembayaran", "Rp"),
    ("riwayat", "Riwayat", "◷"),
)
