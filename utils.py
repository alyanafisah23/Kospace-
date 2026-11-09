"""Utilitas format tanggal, rupiah, periode, dan ID otomatis."""

from __future__ import annotations

import calendar
import sqlite3
from datetime import date, datetime, timedelta

from .config import MONTHS_ID

DATE_DB = "%Y-%m-%d"
DATE_ID = "%d-%m-%Y"


# ---------------------------------------------------------------------------
# Tanggal
# ---------------------------------------------------------------------------
def today() -> date:
    return date.today()


def today_str() -> str:
    return date.today().strftime(DATE_DB)


def parse_date(value: str | date | datetime) -> date:
    """Ubah nilai database (YYYY-MM-DD) atau objek tanggal menjadi date."""
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    return datetime.strptime(str(value), DATE_DB).date()


def fmt_date(value: str | date | datetime | None) -> str:
    """Tanggal untuk tampilan: DD-MM-YYYY."""
    if value is None or value == "":
        return "—"
    return parse_date(value).strftime(DATE_ID)


def fmt_date_short(value: str | date | datetime | None) -> str:
    """Tanggal ringkas untuk kartu: 09 Nov 2026."""
    if value is None or value == "":
        return "—"
    d = parse_date(value)
    return f"{d.day:02d} {MONTHS_ID[d.month - 1][:3]} {d.year}"


def days_between(start: str | date, end: str | date) -> int:
    return (parse_date(end) - parse_date(start)).days


# ---------------------------------------------------------------------------
# Uang & periode
# ---------------------------------------------------------------------------
def rupiah(value: int | float | None) -> str:
    if value is None:
        return "—"
    return f"Rp{int(round(value)):,}".replace(",", ".")


def month_label(month: int, year: int) -> str:
    return f"{MONTHS_ID[int(month) - 1]} {year}"


def add_months(year: int, month: int, delta: int) -> tuple[int, int]:
    index = (year * 12 + (month - 1)) + delta
    return index // 12, index % 12 + 1


def month_span(start: str | date, end: str | date) -> list[tuple[int, int]]:
    """Daftar (tahun, bulan) dari bulan mulai sampai bulan selesai."""
    a = parse_date(start)
    b = parse_date(end)
    periods: list[tuple[int, int]] = []
    year, month = a.year, a.month
    while (year, month) <= (b.year, b.month):
        periods.append((year, month))
        year, month = add_months(year, month, 1)
    return periods


def _add_months_clamped(value: date, months: int) -> date:
    tahun, bulan = add_months(value.year, value.month, months)
    hari = min(value.day, calendar.monthrange(tahun, bulan)[1])
    return date(tahun, bulan, hari)


def duration_months(start: str | date, end: str | date) -> int:
    """Durasi sewa dalam bulan, menghitung tanggal selesai secara inklusif.

    Contoh: 01-01-2027 s.d. 31-03-2027 = 3 bulan,
    31-08-2026 s.d. 31-08-2027 = 12 bulan.
    """
    a = parse_date(start)
    b = parse_date(end)
    months = (b.year - a.year) * 12 + (b.month - a.month)
    if b.day < a.day:
        months -= 1

    jangkar = _add_months_clamped(a, months)
    if b > jangkar:
        months += 1
    return max(1, months)


def add_days(value: str | date, days: int) -> date:
    return parse_date(value) + timedelta(days=days)


# ---------------------------------------------------------------------------
# ID otomatis: K001, P001, S001, BY001
# ---------------------------------------------------------------------------
def next_id(conn: sqlite3.Connection, table: str, column: str, prefix: str) -> str:
    """Buat ID berikutnya berdasarkan nomor terbesar yang sudah ada."""
    allowed = {
        ("kamar", "id_kamar"): "K",
        ("penghuni", "id_penghuni"): "P",
        ("sewa", "id_sewa"): "S",
        ("pembayaran", "id_pembayaran"): "BY",
    }
    if (table, column) not in allowed or allowed[(table, column)] != prefix:
        raise ValueError("Tabel/kolom ID tidak dikenal.")

    row = conn.execute(
        f"SELECT {column} FROM {table} WHERE {column} LIKE ? "
        f"ORDER BY {column} DESC LIMIT 1",
        (f"{prefix}%",),
    ).fetchone()
    if not row:
        return f"{prefix}001"
    try:
        nomor = int(str(row[0])[len(prefix) :]) + 1
    except ValueError:
        nomor = 1
    return f"{prefix}{nomor:03d}"


def initials(name: str) -> str:
    parts = [p for p in str(name).strip().split() if p]
    if not parts:
        return "?"
    if len(parts) == 1:
        return parts[0][:2].upper()
    return (parts[0][0] + parts[-1][0]).upper()
