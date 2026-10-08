import sys
import unittest
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT_DIR / "src"

if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from algorithm.simulated_annealing import SimulatedAnnealing
from core.entity import Package, Truck
from core.state import State


def make_state(packages, truck, positions):
    state = State.__new__(State)
    state.packages = packages
    state.truck = truck
    state.positions = dict(positions)
    return state


def outside_single_package_state():
    package = Package("A", (1, 1, 1), ("x", "y", "z"), 10, 1, False, 1)
    truck = Truck((1, 1, 1), 10)
    return make_state([package], truck, {"A": (1, 0, 0)})


class TestSimulatedAnnealing(unittest.TestCase):
    def test_invalid_parameters(self):
        with self.assertRaises(ValueError):
            SimulatedAnnealing(initial_temperature=0)
        with self.assertRaises(ValueError):
            SimulatedAnnealing(cooling_rate=1.0)
        with self.assertRaises(ValueError):
            SimulatedAnnealing(min_temperature=1000, initial_temperature=10)
        with self.assertRaises(ValueError):
            SimulatedAnnealing(max_iterations=0)

    def test_reproducible_with_seed(self):
        r1 = SimulatedAnnealing(max_iterations=50, seed=3).run(outside_single_package_state())
        r2 = SimulatedAnnealing(max_iterations=50, seed=3).run(outside_single_package_state())
        self.assertEqual(r1.value_history, r2.value_history)

    def test_does_not_mutate_initial_state(self):
        state = outside_single_package_state()
        before = dict(state.positions)
        SimulatedAnnealing(max_iterations=30, seed=1).run(state)
        self.assertEqual(state.positions, before)

    def test_result_is_consistent_and_valid(self):
        result = SimulatedAnnealing(max_iterations=200, seed=5).run(outside_single_package_state())
        self.assertTrue(result.final_state.isValid())
        self.assertEqual(len(result.value_history), result.iterations + 1)
        self.assertEqual(len(result.probability_history), result.iterations)
        self.assertEqual(len(result.temperature_history), result.iterations)
        self.assertTrue(all(0.0 <= p <= 1.0 for p in result.probability_history))

    def test_finds_improvement_on_trivial_problem(self):
        result = SimulatedAnnealing(
            initial_temperature=10, max_iterations=500, seed=7
        ).run(outside_single_package_state())
        # Paket bernilai 10 harus masuk ke peti (1x1x1) -> value 10.
        self.assertEqual(result.metadata["best_value_seen"], 10)

    def test_stops_at_min_temperature(self):
        result = SimulatedAnnealing(
            initial_temperature=1.0,
            cooling_rate=0.5,
            min_temperature=0.1,
            max_iterations=1000,
            seed=1,
        ).run(outside_single_package_state())
        self.assertEqual(result.stop_reason, "min_temperature_reached")
        self.assertLessEqual(result.iterations, 4)


if __name__ == "__main__":
    unittest.main()