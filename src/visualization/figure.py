from __future__ import annotations
from pathlib import Path
from typing import TYPE_CHECKING
import matplotlib.pyplot as plt
from matplotlib.axes import Axes
from matplotlib.figure import Figure
from matplotlib.gridspec import SubplotSpec
from matplotlib.lines import Line2D
from matplotlib.patches import Patch
from core.state import State
from . import style
from .draw_3d import draw_state_3d
from .draw_top_view import draw_state_top_view
from .geometry import Bounds3D, combined_bounds, state_bounds
from .package_table import draw_package_table, draw_truck_table

if TYPE_CHECKING:
    from algorithm.hill_climbing.result import HillClimbingResult

TABLE_ROW_HEIGHT = 0.32
TABLE_PADDING = 0.4

# visualize_state: landscape -> [3D | tampak atas] di atas, tabel di bawah.
STATE_WIDTH = 15.0
STATE_PANEL_HEIGHT = 6.5
STATE_WIDTH_RATIOS = (3, 2)

# visualize_result: satu kolom per state -> 3D, tampak atas, tabel.
RESULT_COLUMN_WIDTH = 9.0
RESULT_HEIGHT_3D = 6.5
RESULT_HEIGHT_TOP_VIEW = 4.5

# Jarak antar panel (inci untuk pad, fraksi untuk space).
LAYOUT_SPACING = {"w_pad": 0.15, "h_pad": 0.2, "wspace": 0.06, "hspace": 0.1}

def _table_height(n_packages: int) -> float:
    return TABLE_ROW_HEIGHT * (n_packages + 1) + TABLE_PADDING

def _truck_table_height(state: State) -> float:
    # Tabel ringkasan per truck hanya muncul untuk armada > 1 truck
    return _table_height(len(state.trucks)) if len(state.trucks) > 1 else 0.0

def _new_figure(width: float, height: float) -> Figure:
    fig = plt.figure(figsize=(width, height), layout="constrained")
    fig.get_layout_engine().set(**LAYOUT_SPACING)
    return fig

def _draw_state_panels(
    fig: Figure,
    state: State,
    *,
    spec_3d: SubplotSpec,
    spec_top: SubplotSpec,
    spec_table: SubplotSpec,
    spec_trucks: SubplotSpec | None = None,
    title: str,
    bounds: Bounds3D,
    colors: dict,
    show_outside: bool,
) -> Axes:
    ax_3d = fig.add_subplot(spec_3d, projection="3d")
    ax_top = fig.add_subplot(spec_top)
    ax_table = fig.add_subplot(spec_table)

    draw_state_3d(
        ax_3d, state,
        title=title, bounds=bounds, colors=colors, show_outside=show_outside,
    )
    draw_state_top_view(
        ax_top, state,
        bounds=bounds, colors=colors, show_outside=show_outside,
    )
    draw_package_table(ax_table, state, colors=colors)

    if spec_trucks is not None:
        draw_truck_table(fig.add_subplot(spec_trucks), state)

    return ax_3d

def _add_legend(fig: Figure) -> None:
    handles = [
        Line2D([0], [0], linewidth=style.TRUCK_EDGE_WIDTH, color=style.TRUCK_EDGE_COLOR, label="Truck boundary"),
        Patch(facecolor=style.TRUCK_FLOOR_COLOR, alpha=style.FLOOR_ALPHA, label="Truck floor"),
        Patch(facecolor=style.OUTSIDE_FLOOR_COLOR, alpha=style.FLOOR_ALPHA, label="Outside floor"),
        Patch(facecolor="gray", edgecolor=style.EDGE_COLOR, alpha=style.INSIDE_ALPHA, label="Inside truck"),
        Patch(facecolor="gray", edgecolor=style.EDGE_COLOR, alpha=style.OUTSIDE_ALPHA, label=f"Outside truck {style.OUTSIDE_TAG}"),
        Patch(
            facecolor="white",
            edgecolor=style.FRAGILE_EDGE_COLOR,
            linewidth=style.FRAGILE_EDGE_WIDTH,
            label=f"Fragile {style.FRAGILE_TAG}",
        ),
    ]
    fig.legend(handles=handles, loc="outside lower center", ncol=len(handles), frameon=False)

def _finish(fig: Figure, save_path: str | Path | None, show: bool) -> None:
    _add_legend(fig)

    if save_path is not None:
        path = Path(save_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(path, dpi=150)

    if show:
        plt.show()

def visualize_state(
    state: State,
    title: str = "State",
    *,
    show_outside: bool = True,
    show: bool = True,
    save_path: str | Path | None = None,
) -> tuple[Figure, Axes]:
    # Menampilkan satu state: 3D, tampak atas, dan tabel package.
    table_height = _table_height(len(state.packages))
    truck_height = _truck_table_height(state)
    has_truck_table = truck_height > 0
    fig = _new_figure(STATE_WIDTH, STATE_PANEL_HEIGHT + truck_height + table_height)

    # Baris: [3D | top view], (tabel truck bila multi-truck), tabel package
    height_ratios = [STATE_PANEL_HEIGHT]
    if has_truck_table:
        height_ratios.append(truck_height)
    height_ratios.append(table_height)
    grid = fig.add_gridspec(
        len(height_ratios), 2,
        width_ratios=STATE_WIDTH_RATIOS,
        height_ratios=height_ratios,
    )

    ax_3d = _draw_state_panels(
        fig, state,
        spec_3d=grid[0, 0], spec_top=grid[0, 1], spec_table=grid[len(height_ratios) - 1, :],
        spec_trucks=grid[1, :] if has_truck_table else None,
        title=title,
        bounds=state_bounds(state),
        colors=style.package_colors(state),
        show_outside=show_outside,
    )

    _finish(fig, save_path, show)
    return fig, ax_3d

def visualize_result(
    result: HillClimbingResult,
    *,
    show_outside: bool = True,
    show: bool = True,
    save_path: str | Path | None = None,
) -> tuple[Figure, tuple[Axes, Axes]]:
    """
    Membandingkan initial state dan final state secara berdampingan.
    Kedua kolom memakai axis limits dan warna package yang sama.
    """
    initial, final = result.initial_state, result.final_state
    table_height = _table_height(max(len(initial.packages), len(final.packages)))
    truck_height = max(_truck_table_height(initial), _truck_table_height(final))
    has_truck_table = truck_height > 0
    fig = _new_figure(
        RESULT_COLUMN_WIDTH * 2,
        RESULT_HEIGHT_3D + RESULT_HEIGHT_TOP_VIEW + truck_height + table_height,
    )

    # Baris: 3D, top view, (tabel truck bila multi-truck), tabel package
    height_ratios = [RESULT_HEIGHT_3D, RESULT_HEIGHT_TOP_VIEW]
    if has_truck_table:
        height_ratios.append(truck_height)
    height_ratios.append(table_height)
    grid = fig.add_gridspec(len(height_ratios), 2, height_ratios=height_ratios)
    table_row = len(height_ratios) - 1

    bounds = combined_bounds(initial, final)
    colors = style.package_colors(initial, final)
    algorithm_name = result.algorithm.replace("_", " ").title()

    ax_initial = _draw_state_panels(
        fig, initial,
        spec_3d=grid[0, 0], spec_top=grid[1, 0], spec_table=grid[table_row, 0],
        spec_trucks=grid[2, 0] if has_truck_table else None,
        title=f"{algorithm_name} — Initial State",
        bounds=bounds, colors=colors, show_outside=show_outside,
    )
    ax_final = _draw_state_panels(
        fig, final,
        spec_3d=grid[0, 1], spec_top=grid[1, 1], spec_table=grid[table_row, 1],
        spec_trucks=grid[2, 1] if has_truck_table else None,
        title=f"{algorithm_name} — Final State",
        bounds=bounds, colors=colors, show_outside=show_outside,
    )

    fig.suptitle(
        f"{algorithm_name}: {result.initial_value} → {result.final_value} "
        f"| Iterations: {result.iterations} "
        f"| Duration: {result.duration_seconds:.4f}s "
        f"| Stop: {result.stop_reason}",
        fontsize=14,
        fontweight="bold",
    )

    _finish(fig, save_path, show)
    return fig, (ax_initial, ax_final)