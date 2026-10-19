from __future__ import annotations
from core.entity import Package
from core.state import State

Bounds3D = tuple[tuple[float, float], tuple[float, float], tuple[float, float]]
Box = tuple[tuple[int, int, int], tuple[int, int, int]]

def package_box(state: State, package: Package) -> Box:
    # Mengembalikan ((x, y, z), (width, depth, height)) setelah orientasi.
    return state.getPosition(package), state.getDimOri(package)

def placed_packages(state: State, *, show_outside: bool = True) -> list[Package]:
    # Package yang punya posisi, opsional tanpa package di luar truck.
    return [
        package
        for package in state.packages
        if package.id in state.positions
        and (show_outside or state.isInsidePeti(package))
    ]

def state_bounds(state: State) -> Bounds3D:
    # Batas visual agar truck dan package di luar truck tetap terlihat
    truck_w, truck_d, truck_h = state.extent   # bounding box seluruh armada

    min_x = min_y = min_z = 0.0
    max_x, max_y, max_z = float(truck_w), float(truck_d), float(truck_h)

    for package in placed_packages(state):
        (x, y, z), (w, d, h) = package_box(state, package)
        min_x, min_y, min_z = min(min_x, x), min(min_y, y), min(min_z, z)
        max_x, max_y, max_z = max(max_x, x + w), max(max_y, y + d), max(max_z, z + h)

    ranges = (
        max(max_x - min_x, 1.0),
        max(max_y - min_y, 1.0),
        max(max_z - min_z, 1.0),
    )
    pad_x, pad_y, pad_z = (max(0.5, axis_range * 0.05) for axis_range in ranges)

    return (
        (min_x - pad_x, max_x + pad_x),
        (min_y - pad_y, max_y + pad_y),
        (min_z, max_z + pad_z),
    )

def combined_bounds(*states: State) -> Bounds3D:
    # Axis limits yang sama untuk beberapa state agar perbandingan adil.
    bounds = [state_bounds(state) for state in states]

    return tuple(
        (
            min(bound[axis][0] for bound in bounds),
            max(bound[axis][1] for bound in bounds),
        )
        for axis in range(3)
    )