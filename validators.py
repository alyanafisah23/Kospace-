"""Validasi input dan aturan bisnis KOSPACE (B01, B06, B08, B10, B14)."""

from __future__ import annotations

import re
import sqlite3
from datetime import date

from .config import ROOM_TYPES
from .utils import fmt_date, month_label, month_span, parse_date, rupiah

PHONE_RE = re.compile(r"^\+?[0-9][0-9\-\s()]{7,19}$")
ROOM_NUMBER_RE = re.compile(r"^[A-Z]{1,2}[0-9]{2,3}$")


class ValidationError(Exception):
    """Kesalahan input yang pesannya aman ditampilkan ke pengguna."""


# ---------------------------------------------------------------------------
# Kamar
# ---------------------------------------------------------------------------
def validate_kamar(
    conn: sqlite3.Connection,
    nomor: str,
    tipe: str,
    harga: int | float,
    exclude_id: str | None = None,
) -> tuple[str, int]:
    nomor = str(nomor or "").strip().upper()
    tipe = str(tipe or "").strip().upper()

    if tipe not in ROOM_TYPES:
        raise ValidationError("Tipe kamar harus A, B, atau C.")
    if not nomor:
        raise ValidationError("Nomor kamar wajib diisi.")
    if not ROOM_NUMBER_RE.match(nomor):
        raise ValidationError(
            "Format nomor kamar tidak valid. Contoh yang benar: A01, B10, C05."
        )
    if not nomor.startswith(tipe):
        raise ValidationError(
            f"Nomor kamar tipe {tipe} harus diawali huruf {tipe} (contoh: {tipe}01)."
        )

    harga = int(harga or 0)
    if harga <= 0:
        raise ValidationError("Harga bulanan harus lebih dari 0.")

    # B01 — nomor kamar tidak boleh kembar
    row = conn.execute(
        "SELECT id_kamar FROM kamar WHERE nomor_kamar = ? AND id_kamar <> ?",
        (nomor, exclude_id or ""),
    ).fetchone()
    if row:
        raise ValidationError(
            f"Nomor kamar {nomor} sudah dipakai kamar lain. "
            "Gunakan nomor yang berbeda (aturan B01)."
        )
    return nomor, harga


def validate_penghuni(
    nama: str, telepon: str, telepon_ortu: str, alamat: str
) -> tuple[str, str, str, str]:
    nama = str(nama or "").strip()
    telepon = str(telepon or "").strip()
    telepon_ortu = str(telepon_ortu or "").strip()
    alamat = str(alamat or "").strip()

    if len(nama) < 2:
        raise ValidationError("Nama penghuni wajib diisi (minimal 2 karakter).")
    if not PHONE_RE.match(telepon):
        raise ValidationError(
            "Nomor telepon tidak valid. Gunakan angka, spasi, tanda hubung, "
            "atau awalan + (8–20 karakter)."
        )
    if not PHONE_RE.match(telepon_ortu):
        raise ValidationError("Nomor telepon orang tua tidak valid.")
    if len(alamat) < 5:
        raise ValidationError("Alamat wajib diisi (minimal 5 karakter).")
    return nama, telepon, telepon_ortu, alamat


# ---------------------------------------------------------------------------
# Sewa
# ---------------------------------------------------------------------------
def validate_sewa_dates(tanggal_mulai: date, tanggal_selesai: date) -> None:
    # B06 — tanggal selesai harus setelah tanggal mulai
    if parse_date(tanggal_selesai) <= parse_date(tanggal_mulai):
        raise ValidationError(
            "Tanggal selesai harus setelah tanggal mulai. "
            f"Contoh: 01-01-2027 s.d. 31-03-2027, bukan "
            f"{fmt_date(tanggal_mulai)} s.d. {fmt_date(tanggal_selesai)} (aturan B06)."
        )


def validate_jadwal_kamar(
    conn: sqlite3.Connection,
    id_kamar: str,
    tanggal_mulai: date,
    tanggal_selesai: date,
    exclude_id: str | None = None,
) -> None:
    """Tolak sewa yang jadwalnya bertabrakan di kamar yang sama."""
    kamar = conn.execute(
        "SELECT nomor_kamar FROM kamar WHERE id_kamar = ?", (id_kamar,)
    ).fetchone()
    if not kamar:
        raise ValidationError("Kamar tidak ditemukan.")

    # Bentrok jika mulai_baru <= selesai_lama DAN selesai_baru >= mulai_lama
    row = conn.execute(
        """
        SELECT s.id_sewa, s.tanggal_mulai, s.tanggal_selesai, p.nama
        FROM sewa s
        JOIN penghuni p ON p.id_penghuni = s.id_penghuni
        WHERE s.id_kamar = ?
          AND s.status_sewa = 'Aktif'
          AND s.id_sewa <> ?
          AND ? <= s.tanggal_selesai
          AND ? >= s.tanggal_mulai
        ORDER BY s.tanggal_mulai
        LIMIT 1
        """,
        (
            id_kamar,
            exclude_id or "",
            parse_date(tanggal_mulai).isoformat(),
            parse_date(tanggal_selesai).isoformat(),
        ),
    ).fetchone()

    if row:
        raise ValidationError(
            f"Jadwal bertabrakan dengan sewa {row['id_sewa']} "
            f"({row['nama']}, {fmt_date(row['tanggal_mulai'])} s.d. "
            f"{fmt_date(row['tanggal_selesai'])}) di kamar "
            f"{kamar['nomor_kamar']}. Pilih tanggal lain atau kamar lain."
        )


# ---------------------------------------------------------------------------
# Pembayaran
# ---------------------------------------------------------------------------
def validate_pembayaran(
    conn: sqlite3.Connection,
    id_sewa: str,
    periode_bulan: int,
    periode_tahun: int,
    nominal: int | float,
) -> None:
    sewa = conn.execute(
        "SELECT * FROM sewa WHERE id_sewa = ?", (id_sewa,)
    ).fetchone()
    if not sewa:
        raise ValidationError("Data sewa tidak ditemukan.")

    periode_bulan = int(periode_bulan)
    periode_tahun = int(periode_tahun)
    nominal = int(nominal or 0)

    if not 1 <= periode_bulan <= 12:
        raise ValidationError("Bulan periode harus antara 1 dan 12.")
    if periode_tahun < 2000:
        raise ValidationError("Tahun periode tidak valid.")

    # B08 — nominal harus lebih dari 0 dan sama dengan harga sewa
    if nominal <= 0:
        raise ValidationError("Nominal pembayaran harus lebih dari 0 (aturan B08).")
    if nominal != int(sewa["harga_bulanan"]):
        raise ValidationError(
            f"Nominal pembayaran harus sama dengan harga sewa "
            f"{rupiah(sewa['harga_bulanan'])} (aturan B08)."
        )

    # Periode harus berada di dalam rentang sewa
    if (periode_tahun, periode_bulan) not in month_span(
        sewa["tanggal_mulai"], sewa["tanggal_selesai"]
    ):
        raise ValidationError(
            f"Periode {month_label(periode_bulan, periode_tahun)} berada di luar "
            f"masa sewa {fmt_date(sewa['tanggal_mulai'])} s.d. "
            f"{fmt_date(sewa['tanggal_selesai'])}."
        )

    # B14 — satu periode hanya boleh dibayar sekali
    row = conn.execute(
        """
        SELECT id_pembayaran FROM pembayaran
        WHERE id_sewa = ? AND periode_bulan = ? AND periode_tahun = ?
        """,
        (id_sewa, periode_bulan, periode_tahun),
    ).fetchone()
    if row:
        raise ValidationError(
            f"Pembayaran untuk periode "
            f"{month_label(periode_bulan, periode_tahun)} sudah tercatat "
            f"({row['id_pembayaran']}). Satu periode hanya boleh dibayar sekali "
            "(aturan B14)."
        )
