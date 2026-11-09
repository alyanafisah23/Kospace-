"""Koneksi, skema, dan inisialisasi database SQLite KOSPACE."""

from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

from .config import DB_PATH, ROOM_TYPES

SCHEMA = """
CREATE TABLE IF NOT EXISTS kamar (
    id_kamar       TEXT PRIMARY KEY,
    nomor_kamar    TEXT NOT NULL UNIQUE,
    tipe           TEXT NOT NULL,
    harga_bulanan  INTEGER NOT NULL CHECK (harga_bulanan > 0),
    fasilitas      TEXT NOT NULL,
    status         TEXT NOT NULL DEFAULT 'Tersedia'
                   CHECK (status IN ('Tersedia', 'Ditempati'))
);

CREATE TABLE IF NOT EXISTS penghuni (
    id_penghuni   TEXT PRIMARY KEY,
    nama          TEXT NOT NULL,
    telepon       TEXT NOT NULL,
    telepon_ortu  TEXT NOT NULL,
    alamat        TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS sewa (
    id_sewa        TEXT PRIMARY KEY,
    id_penghuni    TEXT NOT NULL,
    id_kamar       TEXT NOT NULL,
    tanggal_mulai  TEXT NOT NULL,
    tanggal_selesai TEXT NOT NULL,
    durasi         INTEGER NOT NULL CHECK (durasi > 0),
    harga_bulanan  INTEGER NOT NULL CHECK (harga_bulanan > 0),
    status_sewa    TEXT NOT NULL DEFAULT 'Aktif'
                   CHECK (status_sewa IN ('Aktif', 'Selesai')),
    CHECK (tanggal_selesai > tanggal_mulai),
    FOREIGN KEY (id_penghuni) REFERENCES penghuni (id_penghuni)
        ON UPDATE CASCADE ON DELETE RESTRICT,
    FOREIGN KEY (id_kamar) REFERENCES kamar (id_kamar)
        ON UPDATE CASCADE ON DELETE RESTRICT
);

CREATE TABLE IF NOT EXISTS pembayaran (
    id_pembayaran     TEXT PRIMARY KEY,
    id_sewa           TEXT NOT NULL,
    periode_bulan     INTEGER NOT NULL CHECK (periode_bulan BETWEEN 1 AND 12),
    periode_tahun     INTEGER NOT NULL CHECK (periode_tahun BETWEEN 2000 AND 2100),
    tanggal_bayar     TEXT NOT NULL,
    nominal           INTEGER NOT NULL CHECK (nominal > 0),
    status_pembayaran TEXT NOT NULL DEFAULT 'Lunas'
                      CHECK (status_pembayaran IN ('Lunas', 'Belum Dibayar', 'Terlambat')),
    FOREIGN KEY (id_sewa) REFERENCES sewa (id_sewa)
        ON UPDATE CASCADE ON DELETE RESTRICT,
    UNIQUE (id_sewa, periode_bulan, periode_tahun)
);

CREATE INDEX IF NOT EXISTS idx_sewa_kamar ON sewa (id_kamar);
CREATE INDEX IF NOT EXISTS idx_sewa_penghuni ON sewa (id_penghuni);
CREATE INDEX IF NOT EXISTS idx_bayar_sewa ON pembayaran (id_sewa);
"""


def get_connection(path: Path | str = DB_PATH) -> sqlite3.Connection:
    """Buka koneksi SQLite dengan foreign key aktif dan row factory."""
    if str(path) != ":memory:":
        Path(path).parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(path))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


@contextmanager
def db() -> Iterator[sqlite3.Connection]:
    """Konteks transaksi: commit bila sukses, rollback bila gagal."""
    conn = get_connection()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def create_schema(conn: sqlite3.Connection) -> None:
    conn.executescript(SCHEMA)


def seed_rooms(conn: sqlite3.Connection) -> int:
    """Isi 25 kamar awal bila tabel kamar masih kosong."""
    total = conn.execute("SELECT COUNT(*) FROM kamar").fetchone()[0]
    if total:
        return 0

    urutan = 0
    for tipe, meta in ROOM_TYPES.items():
        for nomor_urut in range(1, int(meta["jumlah"]) + 1):
            urutan += 1
            conn.execute(
                """
                INSERT INTO kamar
                    (id_kamar, nomor_kamar, tipe, harga_bulanan, fasilitas, status)
                VALUES (?, ?, ?, ?, ?, 'Tersedia')
                """,
                (
                    f"K{urutan:03d}",
                    f"{tipe}{nomor_urut:02d}",
                    tipe,
                    int(meta["harga"]),
                    str(meta["fasilitas"]),
                ),
            )
    return urutan


def init_db(path: Path | str = DB_PATH) -> None:
    """Buat skema dan data kamar awal. Aman dipanggil berulang."""
    conn = get_connection(path)
    try:
        create_schema(conn)
        seed_rooms(conn)
        conn.commit()
    finally:
        conn.close()
