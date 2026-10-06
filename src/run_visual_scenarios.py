"""
Skenario visualisasi dengan hasil yang sudah diketahui.
Setiap skenario memakai posisi yang ditentukan manual (bukan random), sehingga
gambar bisa dicocokkan dengan kolom "expect" dan angka ringkasannya dicek
otomatis (value, jumlah paket di dalam, berat, validitas).
"""

from __future__ import annotations
import argparse
from dataclasses import dataclass
from pathlib import Path
import matplotlib.pyplot as plt
from core.entity import Package, Truck
from core.state import State
from visualization import visualize_state
from visualization.summary import summarize_state

OUTPUT_DIR = Path(__file__).resolve().parents[1] / "output" / "visualization" / "scenarios"
TRUCK_DIMS = (10, 10, 6)
TRUCK_CAPACITY = 30

@dataclass(frozen=True)
class Scenario:
    name: str
    expect: str
    packages: list[Package]
    positions: dict[str, tuple[int, int, int]]
    expected_value: int
    expected_inside: int
    expected_weight: float
    expected_valid: bool = True

def box(package_id, dim, value, weight, fragile=False, orientation=("x", "y", "z")) -> Package:
    return Package(package_id, dim, orientation, value, weight, fragile, 1)

def build_state(scenario: Scenario) -> State:
    """State dengan posisi manual; State() biasa selalu mengacak posisi."""
    state = State.__new__(State)
    state.packages = scenario.packages
    state.truck = Truck(TRUCK_DIMS, TRUCK_CAPACITY)
    state.positions = dict(scenario.positions)
    return state

SCENARIOS = [
    Scenario(
        name="corner",
        expect="P1 menempel di sudut (0,0,0) truck",
        packages=[box("P1", (3, 4, 1), 60, 5)],
        positions={"P1": (0, 0, 0)},
        expected_value=60, expected_inside=1, expected_weight=5,
    ),
    Scenario(
        name="touch_wall",
        expect="P1 IN, sisinya berimpit dinding x=10 dan y=10",
        packages=[box("P1", (3, 4, 1), 60, 5)],
        positions={"P1": (7, 6, 0)},
        expected_value=60, expected_inside=1, expected_weight=5,
    ),
    Scenario(
        name="just_outside",
        expect="P1 OUT, transparan, menempel di luar dinding x=10",
        packages=[box("P1", (3, 4, 1), 60, 5)],
        positions={"P1": (10, 0, 0)},
        expected_value=0, expected_inside=0, expected_weight=0,
    ),
    Scenario(
        name="stacked",
        expect="P2 duduk tepat di atas P1 (z=2), label top view P2 z=2",
        packages=[box("P1", (4, 4, 2), 80, 10), box("P2", (2, 2, 1), 40, 3)],
        positions={"P1": (0, 0, 0), "P2": (1, 1, 2)},
        expected_value=120, expected_inside=2, expected_weight=13,
    ),
    Scenario(
        name="fragile_on_top",
        expect="P2 fragile (tepi merah, [F]) di atas P1 biasa -> valid",
        packages=[box("P1", (4, 4, 2), 80, 10), box("P2", (2, 2, 1), 40, 3, fragile=True)],
        positions={"P1": (0, 0, 0), "P2": (1, 1, 2)},
        expected_value=120, expected_inside=2, expected_weight=13,
    ),
    Scenario(
        name="fragile_as_support",
        expect="P1 fragile menopang P2 -> INVALID",
        packages=[box("P1", (4, 4, 2), 80, 10, fragile=True), box("P2", (2, 2, 1), 40, 3)],
        positions={"P1": (0, 0, 0), "P2": (1, 1, 2)},
        expected_value=120, expected_inside=2, expected_weight=13, expected_valid=False,
    ),
    Scenario(
        name="floating",
        expect="P1 melayang di z=3 tanpa penopang -> INVALID",
        packages=[box("P1", (3, 4, 1), 60, 5)],
        positions={"P1": (2, 2, 3)},
        expected_value=60, expected_inside=1, expected_weight=5, expected_valid=False,
    ),
    Scenario(
        name="all_outside",
        expect="Semua OUT: Value 0, Inside 0, Weight 0/30",
        packages=[box("P1", (3, 4, 1), 60, 5), box("P2", (2, 2, 3), 100, 8), box("P3", (5, 2, 2), 80, 12)],
        positions={"P1": (11, 0, 0), "P2": (0, 11, 0), "P3": (11, 11, 0)},
        expected_value=0, expected_inside=0, expected_weight=0,
    ),
    Scenario(
        name="orientations",
        expect="Dim (4,2,1) -> P1 (4,2,1), P2 (2,4,1), P3 (1,2,4) berdiri",
        packages=[
            box("P1", (4, 2, 1), 10, 1, orientation=("x", "y", "z")),
            box("P2", (4, 2, 1), 10, 1, orientation=("y", "x", "z")),
            box("P3", (4, 2, 1), 10, 1, orientation=("z", "y", "x")),
        ],
        positions={"P1": (0, 0, 0), "P2": (5, 0, 0), "P3": (8, 6, 0)},
        expected_value=30, expected_inside=3, expected_weight=3,
    ),
    Scenario(
        name="full_capacity",
        expect="Berat tepat di batas: Weight 30/30, masih valid",
        packages=[box("P1", (3, 3, 2), 50, 15), box("P2", (3, 3, 2), 50, 15)],
        positions={"P1": (0, 0, 0), "P2": (4, 0, 0)},
        expected_value=100, expected_inside=2, expected_weight=30,
    ),
    Scenario(
        name="over_capacity",
        expect="Berat 31/30 -> INVALID",
        packages=[box("P1", (3, 3, 2), 50, 15), box("P2", (3, 3, 2), 50, 16)],
        positions={"P1": (0, 0, 0), "P2": (4, 0, 0)},
        expected_value=100, expected_inside=2, expected_weight=31, expected_valid=False,
    ),
]


def check(scenario: Scenario, state: State) -> list[str]:
    """Mengembalikan daftar ketidakcocokan antara hasil dan ekspektasi."""
    summary = summarize_state(state)
    actual = {
        "value": summary.value,
        "inside": summary.inside,
        "weight": summary.weight,
        "valid": state.isValid(),
    }
    expected = {
        "value": scenario.expected_value,
        "inside": scenario.expected_inside,
        "weight": scenario.expected_weight,
        "valid": scenario.expected_valid,
    }
    return [
        f"{key}: expected {expected[key]}, got {actual[key]}"
        for key in expected
        if expected[key] != actual[key]
    ]

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Render skenario visualisasi yang hasilnya sudah diketahui")
    parser.add_argument("--only", choices=[s.name for s in SCENARIOS], help="Jalankan satu skenario saja")
    parser.add_argument("--show", action="store_true", help="Buka window (bisa diputar dengan mouse)")
    return parser.parse_args()

def main() -> None:
    args = parse_args()
    scenarios = [s for s in SCENARIOS if args.only in (None, s.name)]
    failures = 0

    for scenario in scenarios:
        state = build_state(scenario)
        problems = check(scenario, state)
        valid_tag = "VALID" if state.isValid() else "INVALID"
        save_path = OUTPUT_DIR / f"{scenario.name}.png"

        visualize_state(
            state,
            title=f"[{scenario.name}] {valid_tag}\nExpect: {scenario.expect}",
            show=args.show,
            save_path=save_path,
        )
        plt.close("all")

        status = "PASS" if not problems else "FAIL"
        failures += bool(problems)
        print(f"{status}  {scenario.name:<20} {scenario.expect}")
        for problem in problems:
            print(f"      - {problem}")

    print(f"\n{len(scenarios) - failures}/{len(scenarios)} skenario cocok. Gambar: {OUTPUT_DIR}")

if __name__ == "__main__":
    main()