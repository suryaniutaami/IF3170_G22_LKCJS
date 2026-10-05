import sys
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT_DIR = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT_DIR / "src"

if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from algorithm.hill_climbing import (
    RandomRestartHillClimbing,
    SidewaysMoveHillClimbing,
    SteepestAscentHillClimbing,
    StochasticHillClimbing,
)
from core.entity import Package, Truck
from core.neighbor import Neighbor
from core.state import State


def make_state(packages, truck, positions):
    state = State.__new__(State)
    state.packages = packages
    state.truck = truck
    state.positions = dict(positions)
    return state


class TestHillClimbing(unittest.TestCase):
    def make_outside_single_package_state(self):
        package = Package(
            "A",
            (1, 1, 1),
            ("x", "y", "z"),
            10,
            1,
            False,
            1,
        )
        truck = Truck((1, 1, 1), 10)
        return make_state([package], truck, {"A": (1, 0, 0)})

    def make_inside_single_package_state(self):
        package = Package(
            "A",
            (1, 1, 1),
            ("x", "y", "z"),
            10,
            1,
            False,
            1,
        )
        truck = Truck((2, 2, 1), 10)
        return make_state([package], truck, {"A": (0, 0, 0)})

    def test_steepest_ascent_moves_to_better_neighbor(self):
        state = self.make_outside_single_package_state()
        algorithm = SteepestAscentHillClimbing(seed=7)

        result = algorithm.run(state)

        self.assertEqual(result.algorithm, "steepest_ascent")
        self.assertEqual(result.initial_value, 0)
        self.assertEqual(result.final_value, 10)
        self.assertGreaterEqual(result.accepted_moves, 1)
        self.assertTrue(result.final_state.isValid())

        self.assertEqual(state.positions["A"], (1, 0, 0))
        self.assertEqual(state.getValue(), 0)

    def test_steepest_ascent_history_matches_iterations(self):
        state = self.make_outside_single_package_state()
        result = SteepestAscentHillClimbing(seed=1).run(state)

        self.assertEqual(len(result.value_history), result.iterations + 1)
        self.assertEqual(result.value_history[0], result.initial_value)
        self.assertEqual(result.value_history[-1], result.final_value)

    def test_sideways_move_respects_max_sideways(self):
        state = self.make_inside_single_package_state()
        algorithm = SidewaysMoveHillClimbing(max_sideways=2, seed=3)

        result = algorithm.run(state)

        self.assertEqual(result.final_value, state.getValue())
        self.assertEqual(result.metadata["sideways_moves"], 2)
        self.assertEqual(result.stop_reason, "max_sideways_reached")
        self.assertEqual(result.accepted_moves, 2)
        self.assertEqual(result.iterations, 3)

    def test_sideways_rejects_negative_limit(self):
        with self.assertRaises(ValueError):
            SidewaysMoveHillClimbing(max_sideways=-1)

    def test_stochastic_accepts_only_better_successor(self):
        state = self.make_outside_single_package_state()
        better = Neighbor.move(state, "A", (0, 0, 0))
        self.assertIsNotNone(better)
        equal = Neighbor.move(better, "A", (0, 0, 0))
        self.assertIsNone(equal)

        with patch.object(
            Neighbor,
            "random_neighbor",
            side_effect=[better, better, better],
        ):
            result = StochasticHillClimbing(
                max_iterations=3,
                seed=11,
            ).run(state)

        self.assertEqual(result.final_value, 10)
        self.assertEqual(result.accepted_moves, 1)
        self.assertEqual(result.metadata["rejected_moves"], 2)
        self.assertEqual(result.iterations, 3)
        self.assertEqual(len(result.value_history), 4)

    def test_stochastic_random_neighbor_returns_valid_state(self):
        state = self.make_inside_single_package_state()
        candidate = Neighbor.random_neighbor(
            state,
            rng=__import__("random").Random(10),
            max_attempts=100,
        )

        self.assertIsNotNone(candidate)
        self.assertTrue(candidate.isValid())

    def test_random_restart_runs_expected_number_of_restarts(self):
        state = self.make_outside_single_package_state()
        algorithm = RandomRestartHillClimbing(
            max_restarts=2,
            seed=5,
        )

        result = algorithm.run(state)

        self.assertEqual(result.algorithm, "random_restart")
        self.assertEqual(result.metadata["restarts"], 2)
        self.assertEqual(result.metadata["runs"], 3)
        self.assertEqual(len(result.metadata["iterations_per_restart"]), 3)
        self.assertEqual(len(result.metadata["restart_histories"]), 3)
        self.assertEqual(result.final_value, 10)
        self.assertTrue(result.final_state.isValid())

    def test_random_restart_can_stop_at_target_value(self):
        state = self.make_outside_single_package_state()
        algorithm = RandomRestartHillClimbing(
            max_restarts=10,
            target_value=10,
            seed=9,
        )

        result = algorithm.run(state)

        self.assertEqual(result.stop_reason, "target_value_reached")
        self.assertEqual(result.metadata["restarts"], 0)
        self.assertEqual(result.metadata["runs"], 1)
        self.assertEqual(result.final_value, 10)

    def test_result_to_dict_is_json_ready(self):
        state = self.make_outside_single_package_state()
        result = SteepestAscentHillClimbing(seed=2).run(state)
        data = result.to_dict()

        self.assertEqual(data["algorithm"], "steepest_ascent")
        self.assertEqual(data["final_value"], 10)
        self.assertIn("initial_state", data)
        self.assertIn("final_state", data)
        self.assertIsInstance(data["value_history"], list)


if __name__ == "__main__":
    unittest.main()