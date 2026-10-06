from __future__ import annotations
from matplotlib.axes import Axes
from core.state import State
from .geometry import package_box

COLUMNS = ("ID", "Status", "Pos (x,y,z)", "Dim (w,d,h)", "Value", "Weight", "Fragile")
ID_CELL_ALPHA = 0.55

def _format_tuple(values: tuple[int, int, int]) -> str:
    return "(" + ", ".join(str(value) for value in values) + ")"

def package_rows(state: State) -> list[list[str]]:
    # Satu baris per package: yang di dalam truck lebih dulu, lalu urut ID.
    packages = sorted(
        (package for package in state.packages if package.id in state.positions),
        key=lambda package: (not state.isInsidePeti(package), package.id),
    )

    rows = []
    for package in packages:
        position, dimensions = package_box(state, package)
        rows.append(
            [
                package.id,
                "IN" if state.isInsidePeti(package) else "OUT",
                _format_tuple(position),
                _format_tuple(dimensions),
                str(package.value),
                f"{package.weight:g}",
                "Yes" if package.isFragile else "No",
            ]
        )
    return rows

def draw_package_table(ax: Axes, state: State, *, colors: dict) -> None:
    ax.axis("off")
    rows = package_rows(state)
    if not rows:
        return

    table = ax.table(cellText=rows, colLabels=COLUMNS, loc="center", cellLoc="center")
    table.auto_set_font_size(False)
    table.set_fontsize(9)
    table.scale(1, 1.4)

    for column in range(len(COLUMNS)):
        table[0, column].set_text_props(fontweight="bold")

    for row_index, row in enumerate(rows, start=1):
        package_id, status = row[0], row[1]
        red, green, blue, _ = colors[package_id]
        table[row_index, 0].set_facecolor((red, green, blue, ID_CELL_ALPHA))

        if status == "OUT":
            for column in range(1, len(COLUMNS)):
                table[row_index, column].set_text_props(color="gray")
        if row[6] == "Yes":
            table[row_index, 6].set_text_props(color="red", fontweight="bold")