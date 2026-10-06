from __future__ import annotations
from matplotlib.axes import Axes
from matplotlib.patches import Rectangle
from core.state import State
from . import style
from .geometry import Bounds3D, package_box, placed_packages

def _top_z(state: State, package) -> int:
    (_, _, z), (_, _, h) = package_box(state, package)
    return z + h

def draw_state_top_view(
    ax: Axes,
    state: State,
    *,
    bounds: Bounds3D,
    colors: dict,
    show_outside: bool,
) -> None:
    """
    Package yang lebih tinggi digambar paling akhir sehingga tampak di atas.
    Label memuat koordinat z karena tumpukan tidak terlihat dari atas.
    """
    truck_w, truck_d, _ = state.truck.dimPeti
    ax.add_patch(
        Rectangle(
            (0, 0), truck_w, truck_d,
            facecolor=style.TRUCK_FLOOR_COLOR,
            edgecolor=style.TRUCK_EDGE_COLOR,
            linewidth=style.TRUCK_EDGE_WIDTH,
            alpha=style.FLOOR_ALPHA,
        )
    )

    packages = placed_packages(state, show_outside=show_outside)
    packages.sort(key=lambda package: _top_z(state, package))

    for package in packages:
        (x, y, z), (w, d, _) = package_box(state, package)
        inside = state.isInsidePeti(package)

        ax.add_patch(
            Rectangle(
                (x, y), w, d,
                facecolor=colors[package.id],
                alpha=style.INSIDE_ALPHA if inside else style.OUTSIDE_ALPHA,
                edgecolor=style.FRAGILE_EDGE_COLOR if package.isFragile else style.EDGE_COLOR,
                linewidth=style.FRAGILE_EDGE_WIDTH if package.isFragile else style.EDGE_WIDTH,
            )
        )
        ax.text(
            x + w / 2,
            y + d / 2,
            f"{package.id}\nz={z}",
            ha="center",
            va="center",
            fontsize=style.LABEL_FONT_SIZE,
            fontweight="bold",
            bbox=style.LABEL_BOX,
        )

    ax.set_xlim(*bounds[0])
    ax.set_ylim(*bounds[1])
    ax.set_aspect("equal")
    ax.set_xlabel("X / Width")
    ax.set_ylabel("Y / Depth")
    ax.set_title("Top View (X-Y)", fontsize=10, pad=8)
    ax.grid(True, alpha=0.25)