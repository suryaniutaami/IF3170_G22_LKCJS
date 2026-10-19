from __future__ import annotations
import math
from matplotlib.axes import Axes
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
from core.entity import Package
from core.state import State
from . import style
from .geometry import Bounds3D, package_box, placed_packages
from .summary import format_summary, summarize_state

"""
Urutan gambar diatur manual (computed_zorder=False) dengan painter's algorithm:
objek yang jauh dari kamera digambar lebih dulu. Urutan otomatis matplotlib
membuat bidang lantai yang besar bisa menutupi package.
"""
Z_OUTSIDE_FLOOR = 0.0
Z_TRUCK_FLOOR = 0.1
Z_BACK_EDGES = 0.2
Z_PACKAGES = 1.0
Z_FRONT_EDGES = 50.0
Z_LABELS = 60.0

TRUCK_CORNERS = {
    "000": (0, 0, 0), "100": (1, 0, 0), "010": (0, 1, 0), "110": (1, 1, 0),
    "001": (0, 0, 1), "101": (1, 0, 1), "011": (0, 1, 1), "111": (1, 1, 1),
}
TRUCK_EDGES = (
    ("000", "100"), ("000", "010"), ("100", "110"), ("010", "110"),
    ("001", "101"), ("001", "011"), ("101", "111"), ("011", "111"),
    ("000", "001"), ("100", "101"), ("010", "011"), ("110", "111"),
)

def _camera_direction() -> tuple[float, float, float]:
    # Vektor satuan dari pusat scene ke kamera.
    elev = math.radians(style.VIEW_ELEVATION)
    azim = math.radians(style.VIEW_AZIMUTH)
    return (
        math.cos(elev) * math.cos(azim),
        math.cos(elev) * math.sin(azim),
        math.sin(elev),
    )

def _depth(point: tuple[float, float, float]) -> float:
    # Semakin besar nilainya, semakin dekat titik ke kamera.
    camera = _camera_direction()
    return sum(p * c for p, c in zip(point, camera))

def _floor_polygon(x0: float, x1: float, y0: float, y1: float, color: str, zorder: float):
    polygon = Poly3DCollection(
        [[(x0, y0, 0), (x1, y0, 0), (x1, y1, 0), (x0, y1, 0)]],
        facecolor=color,
        edgecolor="none",
        alpha=style.FLOOR_ALPHA,
    )
    polygon.set_zorder(zorder)
    return polygon

def draw_floor(ax: Axes, state: State, bounds: Bounds3D) -> None:
    """
    Lantai area luar (abu-abu) dan lantai tiap truck (biru muda) di z=0.
    Lantai ini membuat package di belakang truck tidak terlihat seolah
    melayang di dalam truck.
    """
    (x0, x1), (y0, y1), _ = bounds

    ax.add_collection3d(_floor_polygon(x0, x1, y0, y1, style.OUTSIDE_FLOOR_COLOR, Z_OUTSIDE_FLOOR))
    for bx0, by0, _, bx1, by1, _ in state.truckBoundsList():
        ax.add_collection3d(_floor_polygon(bx0, bx1, by0, by1, style.TRUCK_FLOOR_COLOR, Z_TRUCK_FLOOR))

def draw_truck_wireframe(ax: Axes, state: State) -> None:
    # Rusuk belakang digambar di bawah package, rusuk depan di atasnya.
    for bx0, by0, bz0, bx1, by1, bz1 in state.truckBoundsList():
        truck_dims = (bx1 - bx0, by1 - by0, bz1 - bz0)
        origin = (bx0, by0, bz0)
        corners = {
            key: tuple(o + unit * size for o, unit, size in zip(origin, unit_corner, truck_dims))
            for key, unit_corner in TRUCK_CORNERS.items()
        }
        center = tuple(o + size / 2 for o, size in zip(origin, truck_dims))
        center_depth = _depth(center)

        for start_key, end_key in TRUCK_EDGES:
            start, end = corners[start_key], corners[end_key]
            midpoint = tuple((s + e) / 2 for s, e in zip(start, end))
            is_front = _depth(midpoint) > center_depth

            ax.plot(
                [start[0], end[0]],
                [start[1], end[1]],
                [start[2], end[2]],
                linewidth=style.TRUCK_EDGE_WIDTH,
                color=style.TRUCK_EDGE_COLOR,
                alpha=0.8,
                zorder=Z_FRONT_EDGES if is_front else Z_BACK_EDGES,
            )

def draw_truck_labels(ax: Axes, state: State) -> None:
    # Penanda "T1", "T2", ... di atas tiap truck (hanya bila armada > 1 truck)
    if len(state.trucks) < 2:
        return

    for index, truck in enumerate(state.trucks):
        bx0, by0, bz0, bx1, by1, bz1 = state.truckBounds(index)
        ax.text(
            (bx0 + bx1) / 2, by0, bz1 + style.LABEL_OFFSET_Z * 2,
            truck.id,
            ha="center",
            va="bottom",
            fontsize=style.LABEL_FONT_SIZE + 2,
            fontweight="bold",
            color=style.TRUCK_EDGE_COLOR,
            zorder=Z_LABELS,
        )

def package_label(state: State, package: Package) -> str:
    label = package.id
    if package.isFragile:
        label += f" {style.FRAGILE_TAG}"
    if not state.isInsidePeti(package):
        label += f" {style.OUTSIDE_TAG}"
    return label

def _supports_other(state: State, package: Package) -> bool:
    return any(
        other.id != package.id
        and other.id in state.positions
        and state.isSupport(package, other)
        for other in state.packages
    )

def _label_anchor(state: State, package: Package) -> tuple[float, float, float]:
    """
    Label diletakkan di atas balok agar tidak tertutup sisi yang solid.
    Jika ada package lain di atasnya, label dipindah ke sisi depan (y minimum,
    menghadap kamera) supaya tidak tampak menempel di package atas.
    """
    (x, y, z), (w, d, h) = package_box(state, package)
    if _supports_other(state, package):
        return (x + w / 2, y, z + h / 2)
    return (x + w / 2, y + d / 2, z + h + style.LABEL_OFFSET_Z)

def draw_package(ax: Axes, state: State, package: Package, color, zorder: float) -> None:
    # Satu package sebagai balok, dengan label di atasnya.
    (x, y, z), (w, d, h) = package_box(state, package)
    inside = state.isInsidePeti(package)

    box = ax.bar3d(
        x, y, z, w, d, h,
        color=color,
        alpha=style.INSIDE_ALPHA if inside else style.OUTSIDE_ALPHA,
        edgecolor=style.FRAGILE_EDGE_COLOR if package.isFragile else style.EDGE_COLOR,
        linewidth=style.FRAGILE_EDGE_WIDTH if package.isFragile else style.EDGE_WIDTH,
        shade=True,
    )
    box.set_zorder(zorder)

    ax.text(
        *_label_anchor(state, package),
        package_label(state, package),
        ha="center",
        va="center",
        fontsize=style.LABEL_FONT_SIZE,
        fontweight="bold",
        bbox=style.LABEL_BOX,
        zorder=Z_LABELS,
    )

def _package_center(state: State, package: Package) -> tuple[float, float, float]:
    (x, y, z), (w, d, h) = package_box(state, package)
    return (x + w / 2, y + d / 2, z + h / 2)

def draw_state_3d(
    ax: Axes,
    state: State,
    *,
    title: str,
    bounds: Bounds3D,
    colors: dict,
    show_outside: bool,
) -> None:
    # Menggambar satu State lengkap pada Axes 3D.
    ax.computed_zorder = False

    draw_floor(ax, state, bounds)
    draw_truck_wireframe(ax, state)
    draw_truck_labels(ax, state)

    packages = placed_packages(state, show_outside=show_outside)
    packages.sort(key=lambda package: _depth(_package_center(state, package)))
    for order, package in enumerate(packages):
        draw_package(ax, state, package, colors[package.id], Z_PACKAGES + order)

    ax.set_title(f"{title}\n{format_summary(summarize_state(state))}")
    ax.set_xlabel("X / Width")
    ax.set_ylabel("Y / Depth")
    ax.set_zlabel("Z / Height")

    ax.set_xlim(*bounds[0])
    ax.set_ylim(*bounds[1])
    ax.set_zlim(*bounds[2])
    ax.set_box_aspect(tuple(high - low for low, high in bounds), zoom=style.VIEW_ZOOM)
    ax.view_init(elev=style.VIEW_ELEVATION, azim=style.VIEW_AZIMUTH)
    ax.grid(True, alpha=0.25)
    # Dinding plot putih agar lantai abu-abu di z=0 terlihat kontras.
    for axis in (ax.xaxis, ax.yaxis, ax.zaxis):
        axis.set_pane_color(style.PANE_COLOR)