"""Isi database dengan data contoh untuk demonstrasi dashboard.

Jalankan dari root proyek:
    python -m kospace.seed_demo
"""

from __future__ import annotations

from datetime import date, timedelta

from .database import db, init_db
from .repositories import pembayaran as repo_bayar
from .repositories import penghuni as repo_penghuni
from .repositories import sewa as repo_sewa
from .services.dashboard import sync_statuses
from .utils import month_span


def main() -> None:
    init_db()

    with db() as conn:
        sudah_ada = conn.execute(
            "SELECT COUNT(*) FROM penghuni"
        ).fetchone()[0]
        if sudah_ada:
            print(
                "Data contoh tidak ditambahkan: tabel penghuni sudah berisi "
                f"{sudah_ada} data."
            )
            return

        hari_ini = date.today()

        alya = repo_penghuni.create_penghuni(
            conn,
            "Alya Nafisah",
            "0812-3456-7890",
            "0813-1111-2222",
            "Bandung, Jawa Barat",
        )
        marensya = repo_penghuni.create_penghuni(
            conn,
            "Marensya Aurellya",
            "0857-8899-1122",
            "0812-3333-4444",
            "Surabaya, Jawa Timur",
        )
        shintia = repo_penghuni.create_penghuni(
            conn,
            "Shintia Nova P. A.",
            "0878-2233-4455",
            "0856-7777-8888",
            "Yogyakarta, DI Yogyakarta",
        )

        kamar = {
            r["nomor_kamar"]: r
            for r in conn.execute("SELECT * FROM kamar").fetchall()
        }

        sewa_1 = repo_sewa.create_sewa(
            conn,
            alya,
            kamar["A01"]["id_kamar"],
            hari_ini - timedelta(days=70),
            hari_ini + timedelta(days=295),
        )
        sewa_2 = repo_sewa.create_sewa(
            conn,
            marensya,
            kamar["B03"]["id_kamar"],
            hari_ini - timedelta(days=40),
            hari_ini + timedelta(days=140),
        )
        sewa_3 = repo_sewa.create_sewa(
            conn,
            shintia,
            kamar["C05"]["id_kamar"],
            hari_ini - timedelta(days=10),
            hari_ini + timedelta(days=80),
        )

        def catat(id_sewa: str, jumlah_periode: int) -> None:
            sewa = repo_sewa.get_sewa(conn, id_sewa)
            periode = month_span(sewa["tanggal_mulai"], sewa["tanggal_selesai"])
            for tahun, bulan in periode[:jumlah_periode]:
                repo_bayar.create_pembayaran(
                    conn,
                    id_sewa,
                    bulan,
                    tahun,
                    hari_ini,
                    int(sewa["harga_bulanan"]),
                )

        catat(sewa_1, 2)
        catat(sewa_2, 1)
        # Sewa 3 sengaja belum dibayar agar muncul sebagai tunggakan.

    sync_statuses()
    print("Data contoh berhasil ditambahkan:")
    print("  - 3 penghuni (Alya, Marensya, Shintia)")
    print("  - 3 sewa: A01, B03, C05")
    print("  - 3 pembayaran contoh, 1 tunggakan aktif")
    print("Jalankan: streamlit run app.py")


if __name__ == "__main__":
    main()
