"""KOSPACE — entry point aplikasi Streamlit."""

from __future__ import annotations

import traceback

import streamlit as st

from kospace.database import init_db
from kospace.services.dashboard import sync_statuses
from kospace.ui import dashboard, kamar, pembayaran, penghuni, riwayat, sewa
from kospace.ui.components import inject_css, render_flash, sidebar

st.set_page_config(
    page_title="KOSPACE — Administrasi Kos",
    page_icon="🏠",
    layout="wide",
    initial_sidebar_state="expanded",
)

inject_css()

# Siapkan database (idempoten) dan segarkan status kamar/sewa.
try:
    init_db()
    sync_statuses()
except Exception as exc:  # pragma: no cover - jalur darurat
    st.error(f"Gagal menyiapkan database: {exc}")
    st.stop()

PAGES = {
    "dashboard": dashboard.render,
    "kamar": kamar.render,
    "penghuni": penghuni.render,
    "sewa": sewa.render,
    "pembayaran": pembayaran.render,
    "riwayat": riwayat.render,
}

halaman = sidebar()
render_flash()

try:
    PAGES.get(halaman, dashboard.render)()
except Exception as exc:  # pragma: no cover - jalur darurat
    st.error(f"Terjadi kesalahan saat membuka halaman: {exc}")
    with st.expander("Detail teknis"):
        st.code(traceback.format_exc(), language="text")
