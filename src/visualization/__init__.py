"""
Visualisasi untuk state dan hasil algoritma pencarian IF3170.
Struktur modul:
- style.py         : warna, transparansi, sudut kamera, penanda fragile
- geometry.py      : kotak package dan batas sumbu
- summary.py       : ringkasan value, jumlah paket, berat/kapasitas
- draw_3d.py       : lantai, wireframe truck, dan package dalam 3D
- draw_top_view.py : tampak atas (X-Y)
- package_table.py : tabel status seluruh package
- figure.py        : penyusunan panel dan API publik di bawah ini
- history.py       : plot riwayat objective value (HC, SA, GA) dan e^(ΔE/T) (SA)
"""

from .figure import visualize_result, visualize_state
from .history import plot_history

__all__ = ["visualize_state", "visualize_result", "plot_history"]