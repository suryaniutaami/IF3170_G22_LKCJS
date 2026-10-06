import sys
import unittest
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT_DIR = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from algorithm.hill_climbing.result import HillClimbingResult
from core.entity import Package, Truck
from core.state import State
from visualization import visualize_result, visualize_state
from visualization.draw_3d import package_label
from visualization.package_table import package_rows
from visualization.style import package_colors
from visualization.summary import summarize_state

def make_state(positions: dict[str, tuple[int, int, int]]) -> State:
    packages = [
        Package("P1", (2, 2, 2), ("x", "y", "z"), 100, 1, False, 1),
        Package("P2", (2, 2, 2), ("x", "y", "z"), 50, 1, True, 1),
    ]
    truck = Truck((5, 5, 5), 10)

    state = State.__new__(State)
    state.packages = packages
    state.truck = truck
    state.positions = positions.copy()
    return state

class TestVisualization(unittest.TestCase):
    def tearDown(self):
        plt.close("all")

    def test_visualize_state_returns_3d_axes(self):
        state = make_state({"P1": (0, 0, 0), "P2": (5, 0, 0)})

        fig, ax = visualize_state(state, show=False)

        self.assertIsNotNone(fig)
        self.assertEqual(ax.name, "3d")
        self.assertIn("Objective Value: 100", ax.get_title())
        self.assertIn("Inside: 1", ax.get_title())
        self.assertIn("Outside: 1", ax.get_title())

    def test_visualize_result_uses_same_axis_limits_for_comparison(self):
        initial = make_state({"P1": (5, 0, 0), "P2": (5, 3, 0)})
        final = make_state({"P1": (0, 0, 0), "P2": (2, 0, 0)})
        result = HillClimbingResult(
            algorithm="steepest_ascent",
            initial_state=initial,
            final_state=final,
            iterations=2,
            accepted_moves=2,
            value_history=[0, 100, 150],
            duration_seconds=0.1,
            stop_reason="local_optimum",
        )

        fig, (ax_initial, ax_final) = visualize_result(result, show=False)

        self.assertIsNotNone(fig)
        self.assertEqual(ax_initial.get_xlim(), ax_final.get_xlim())
        self.assertEqual(ax_initial.get_ylim(), ax_final.get_ylim())
        self.assertEqual(ax_initial.get_zlim(), ax_final.get_zlim())
        self.assertIn("Initial State", ax_initial.get_title())
        self.assertIn("Final State", ax_final.get_title())

    def test_visualize_state_has_3d_top_view_and_table_panels(self):
        state = make_state({"P1": (0, 0, 0), "P2": (5, 0, 0)})

        fig, _ = visualize_state(state, show=False)

        self.assertEqual(len(fig.axes), 3)
        self.assertEqual(fig.axes[1].get_title(), "Top View (X-Y)")

    def test_title_shows_weight_against_capacity(self):
        state = make_state({"P1": (0, 0, 0), "P2": (5, 0, 0)})

        _, ax = visualize_state(state, show=False)

        self.assertIn("Weight: 1/10", ax.get_title())

    def test_summary_counts_only_inside_weight(self):
        state = make_state({"P1": (0, 0, 0), "P2": (2, 0, 0)})

        summary = summarize_state(state)

        self.assertEqual((summary.inside, summary.outside), (2, 0))
        self.assertEqual(summary.weight, 2)

    def test_package_label_marks_fragile_and_outside(self):
        state = make_state({"P1": (0, 0, 0), "P2": (5, 0, 0)})
        p1, p2 = state.packages

        self.assertEqual(package_label(state, p1), "P1")
        self.assertEqual(package_label(state, p2), "P2 [F] (OUT)")

    def test_package_rows_list_inside_packages_first(self):
        state = make_state({"P1": (5, 0, 0), "P2": (0, 0, 0)})

        rows = package_rows(state)

        self.assertEqual([row[0] for row in rows], ["P2", "P1"])
        self.assertEqual(rows[0][1], "IN")
        self.assertEqual(rows[1][1], "OUT")
        self.assertEqual(rows[0][6], "Yes")

    def test_package_colors_are_distinct(self):
        state = make_state({"P1": (0, 0, 0), "P2": (5, 0, 0)})

        colors = package_colors(state)

        self.assertNotEqual(colors["P1"], colors["P2"])

if __name__ == "__main__":
    unittest.main()