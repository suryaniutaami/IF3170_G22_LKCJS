from __future__ import annotations
import matplotlib.pyplot as plt
from core.state import State

RGBA = tuple[float, float, float, float]

# Kamera 3D
VIEW_ELEVATION = 24
VIEW_AZIMUTH = -58
VIEW_ZOOM = 1.2
PANE_COLOR = (1.0, 1.0, 1.0, 1.0)

# Package
INSIDE_ALPHA = 0.85
OUTSIDE_ALPHA = 0.35
EDGE_COLOR = "black"
EDGE_WIDTH = 0.8
FRAGILE_EDGE_COLOR = "red"
FRAGILE_EDGE_WIDTH = 2.2
FRAGILE_TAG = "[F]"
OUTSIDE_TAG = "(OUT)"

# Truck & lantai
TRUCK_EDGE_COLOR = "dimgray"
TRUCK_EDGE_WIDTH = 1.5
TRUCK_FLOOR_COLOR = "lightsteelblue"
OUTSIDE_FLOOR_COLOR = "darkgray"
FLOOR_ALPHA = 0.4

# Label
LABEL_FONT_SIZE = 8
LABEL_OFFSET_Z = 0.3
LABEL_BOX = {
    "boxstyle": "round,pad=0.15",
    "facecolor": "white",
    "edgecolor": "none",
    "alpha": 0.8,
}

def package_colors(*states: State) -> dict[str, RGBA]:
    """
    Warna konsisten per package ID di seluruh state yang diberikan.
    tab10 dipakai agar warna antar package kontras (tab20 memasangkan warna
    tua-muda yang mirip). Untuk lebih dari 10 package, warna diambil merata
    dari colormap turbo.
    """
    package_ids = sorted({package.id for state in states for package in state.packages})
    count = len(package_ids)

    if count <= 10:
        cmap = plt.get_cmap("tab10")
        return {package_id: cmap(index) for index, package_id in enumerate(package_ids)}

    cmap = plt.get_cmap("turbo")
    return {
        package_id: cmap(index / (count - 1))
        for index, package_id in enumerate(package_ids)
    }