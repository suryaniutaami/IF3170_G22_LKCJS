import json
import random
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT_DIR = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from algorithm.genetic_algorithm.genetic_algorithm import GeneticAlgorithm
from algorithm.hill_climbing import (
    RandomRestartHillClimbing,
    SidewaysMoveHillClimbing,
    SteepestAscentHillClimbing,
    StochasticHillClimbing,
)
from algorithm.simulated_annealing import SimulatedAnnealing
from core.entity import Package, Truck
from core.fleet import Fleet, INVALID, OUTSIDE, TRUCK_GAP
from core.neighbor import Neighbor
from core.state import State
from util.parser import Parser
from visualization import visualize_state
from visualization.package_table import package_rows, truck_rows
from visualization.summary import format_summary, summarize_state


def pkg(pid, dim=(1, 1, 1), value=10, weight=1, fragile=False, orientation=("x", "y", "z")):
    return Package(pid, dim, orientation, value, weight, fragile, 1)


def make_state(packages, trucks, positions):
    # State deterministik tanpa random_position().
    state = State.__new__(State)
    state.packages = packages
    state.trucks = trucks
    state.positions = dict(positions)
    return state


def reference_is_valid(state):
    # Logika validitas versi helper (isFloating / isSupport / isOverlapping),
    # dipakai sebagai pembanding terhadap State.isValid() yang dioptimasi.
    for p1 in state.packages:
        if state.isFloating(p1): return False
        if state.locate(p1) == INVALID: return False
        for p2 in state.packages:
            if p1.id == p2.id: continue
            if state.isSupport(p1, p2) and p1.isFragile: return False
            if state.isOverlapping(p1, p2): return False
    return not state.isTruckCapacityOverload()


class TestFleet(unittest.TestCase):
    def setUp(self):
        self.fleet = Fleet([Truck((10, 10, 6), 30), Truck((8, 8, 5), 20)])

    def test_trucks_are_laid_side_by_side_with_gap(self):
        self.assertEqual(self.fleet.origins, [(0, 0, 0), (10 + TRUCK_GAP, 0, 0)])
        self.assertEqual(self.fleet.extent, (10 + TRUCK_GAP + 8, 10, 6))

    def test_single_truck_matches_truck_dimensions(self):
        fleet = Fleet([Truck((4, 5, 6), 1)])
        self.assertEqual(fleet.origins, [(0, 0, 0)])
        self.assertEqual(fleet.extent, (4, 5, 6))

    def test_locate_inside_each_truck(self):
        self.assertEqual(self.fleet.locate((0, 0, 0), (3, 3, 3)), 0)
        self.assertEqual(self.fleet.locate((7, 7, 3), (3, 3, 3)), 0)
        self.assertEqual(self.fleet.locate((12, 0, 0), (8, 8, 5)), 1)

    def test_locate_outside_and_gap(self):
        self.assertEqual(self.fleet.locate((10, 0, 0), (2, 2, 1)), OUTSIDE)    # tepat di celah
        self.assertEqual(self.fleet.locate((0, 10, 0), (3, 3, 1)), OUTSIDE)    # di depan dinding y
        self.assertEqual(self.fleet.locate((0, 0, 6), (3, 3, 1)), OUTSIDE)     # di atas atap
        self.assertEqual(self.fleet.locate((20, 0, 0), (1, 1, 1)), OUTSIDE)    # setelah truk terakhir

    def test_locate_invalid_when_crossing_walls_or_negative(self):
        self.assertEqual(self.fleet.locate((9, 0, 0), (3, 3, 1)), INVALID)     # menembus dinding T1
        self.assertEqual(self.fleet.locate((10, 0, 0), (4, 2, 1)), INVALID)    # celah -> menembus T2
        self.assertEqual(self.fleet.locate((8, 0, 0), (6, 2, 1)), INVALID)     # menjembatani T1 & T2
        self.assertEqual(self.fleet.locate((0, 0, 4), (2, 2, 3)), INVALID)     # menembus atap
        self.assertEqual(self.fleet.locate((-3, 0, 0), (1, 1, 1)), INVALID)

    def test_requires_at_least_one_truck(self):
        with self.assertRaises(ValueError):
            Fleet([])


class TestMultiTruckState(unittest.TestCase):
    def test_single_truck_api_is_preserved(self):
        truck = Truck((5, 5, 5), 10)
        state = make_state([pkg("A")], truck, {"A": (0, 0, 0)})

        self.assertIs(state.truck, truck)
        self.assertEqual(state.trucks, [truck])
        self.assertEqual(truck.id, "T1")
        self.assertEqual(state.extent, (5, 5, 5))

    def test_truck_ids_default_to_sequence(self):
        trucks = [Truck((3, 3, 3), 5), Truck((3, 3, 3), 5, "Big"), Truck((3, 3, 3), 5)]
        state = make_state([pkg("A")], trucks, {"A": (0, 0, 0)})
        self.assertEqual([t.id for t in state.trucks], ["T1", "Big", "T3"])

    def test_objective_sums_value_over_all_trucks(self):
        trucks = [Truck((4, 4, 2), 10), Truck((4, 4, 2), 10)]
        packages = [pkg("A", value=60), pkg("B", value=40), pkg("C", value=25)]
        state = make_state(packages, trucks, {"A": (0, 0, 0), "B": (6, 0, 0), "C": (0, 9, 0)})

        self.assertTrue(state.isValid())
        self.assertEqual(state.getValue(), 100)               # C di luar
        self.assertEqual(state.getTruckIndex(packages[0]), 0)
        self.assertEqual(state.getTruckIndex(packages[1]), 1)
        self.assertIsNone(state.getTruckIndex(packages[2]))
        self.assertEqual([state.getTruckValue(0), state.getTruckValue(1)], [60, 40])

    def test_local_position_is_relative_to_truck_origin(self):
        trucks = [Truck((4, 4, 2), 10), Truck((4, 4, 2), 10)]
        packages = [pkg("A"), pkg("B")]
        state = make_state(packages, trucks, {"A": (1, 2, 0), "B": (7, 3, 0)})   # T2 origin x=6

        self.assertEqual(state.localPosition(packages[0]), (1, 2, 0))
        self.assertEqual(state.localPosition(packages[1]), (1, 3, 0))

    def test_capacity_is_enforced_per_truck(self):
        trucks = [Truck((6, 4, 2), 10), Truck((6, 4, 2), 10)]
        a, b = pkg("A", (2, 2, 2), weight=8), pkg("B", (2, 2, 2), weight=8)

        separate = make_state([a, b], trucks, {"A": (0, 0, 0), "B": (8, 0, 0)})
        same = make_state([a, b], trucks, {"A": (0, 0, 0), "B": (3, 0, 0)})

        self.assertTrue(separate.isValid())     # 8/10 + 8/10
        self.assertFalse(same.isValid())        # 16/10 pada satu truk

    def test_heterogeneous_trucks_use_their_own_capacity(self):
        trucks = [Truck((4, 4, 2), 5), Truck((4, 4, 2), 50)]
        heavy = pkg("H", (2, 2, 2), weight=20)

        in_small = make_state([heavy], trucks, {"H": (0, 0, 0)})
        in_large = make_state([heavy], trucks, {"H": (6, 0, 0)})

        self.assertFalse(in_small.isValid())
        self.assertTrue(in_large.isValid())

    def test_package_crossing_truck_wall_is_invalid(self):
        trucks = [Truck((4, 4, 2), 10), Truck((4, 4, 2), 10)]
        state = make_state([pkg("A", (3, 2, 1))], trucks, {"A": (3, 0, 0)})   # x=3..6 menembus T1
        self.assertFalse(state.isValid())

    def test_package_in_gap_is_valid_and_outside(self):
        trucks = [Truck((4, 4, 2), 10), Truck((4, 4, 2), 10)]
        a = pkg("A", (2, 2, 1))
        state = make_state([a], trucks, {"A": (4, 0, 0)})

        self.assertTrue(state.isValid())
        self.assertTrue(state.isOutsidePeti(a))
        self.assertEqual(state.getValue(), 0)

    def test_stacking_works_inside_second_truck(self):
        trucks = [Truck((4, 4, 4), 50), Truck((4, 4, 4), 50)]
        base, top = pkg("B", (3, 3, 2)), pkg("T", (2, 2, 2))
        state = make_state([base, top], trucks, {"B": (6, 0, 0), "T": (6, 0, 2)})

        self.assertTrue(state.isValid())
        self.assertEqual(state.getTruckPackages(1), [base, top])

    def test_floating_in_second_truck_is_invalid(self):
        trucks = [Truck((4, 4, 4), 50), Truck((4, 4, 4), 50)]
        state = make_state([pkg("A", (2, 2, 1))], trucks, {"A": (6, 0, 2)})
        self.assertFalse(state.isValid())

    def test_state_is_not_shared_after_deepcopy(self):
        import copy
        trucks = [Truck((4, 4, 2), 10), Truck((4, 4, 2), 10)]
        a = pkg("A", (2, 1, 1))
        state = make_state([a], trucks, {"A": (0, 0, 0)})

        clone = copy.deepcopy(state)
        clone.positions["A"] = (6, 0, 0)
        clone.packages[0].orientation = ("y", "x", "z")

        self.assertEqual(state.positions["A"], (0, 0, 0))
        self.assertEqual(state.packages[0].orientation, ("x", "y", "z"))
        self.assertEqual(clone.fleet.origins, state.fleet.origins)

    def test_random_initial_state_is_valid_for_many_trucks(self):
        packages = [pkg(f"P{i}", (2, 2, 2), value=10 + i, weight=3) for i in range(8)]
        trucks = [Truck((6, 6, 4), 12), Truck((5, 5, 4), 9), Truck((4, 8, 4), 12)]

        for seed in range(15):
            state = State(packages, trucks, random.Random(seed))
            self.assertTrue(state.isValid(), f"seed {seed}")

    def test_is_valid_placement_rejects_fragile_package_under_existing_package(self):
        # R menopang Q, tetapi Q menjorok ke x=2..4. p (fragile) di x=2..4 akan
        # menopang Q -> tidak boleh, walaupun Q sudah dipasang lebih dulu.
        trucks = [Truck((8, 8, 6), 100)]
        r, q = pkg("R", (2, 2, 2)), pkg("Q", (4, 2, 1))
        p = pkg("P", (2, 2, 2), fragile=True)
        positions = {"R": (0, 0, 0), "Q": (0, 0, 2)}

        ok = State.isValidPlacement(p, (2, 0, 0), positions, [r, q, p], trucks, random.Random(0))

        self.assertFalse(ok)
        self.assertNotIn("P", positions)


class TestValidityEquivalence(unittest.TestCase):
    """isValid()/canPlace() yang dioptimasi harus setara dengan definisi berbasis helper."""

    def random_world(self, rng):
        n_trucks = rng.randint(1, 3)
        trucks = [Truck((rng.randint(3, 6), rng.randint(3, 6), rng.randint(2, 4)), rng.randint(4, 12)) for _ in range(n_trucks)]
        packages = [
            pkg(
                f"P{i}",
                (rng.randint(1, 3), rng.randint(1, 3), rng.randint(1, 3)),
                value=rng.randint(1, 50),
                weight=rng.randint(1, 5),
                fragile=rng.random() < 0.3,
                orientation=tuple(rng.sample("xyz", 3)),
            )
            for i in range(rng.randint(2, 6))
        ]
        return packages, trucks

    def test_is_valid_matches_reference_on_random_states(self):
        rng = random.Random(2026)
        seen = {True: 0, False: 0}

        for _ in range(800):
            packages, trucks = self.random_world(rng)
            extent = Fleet(trucks).extent

            if rng.random() < 0.5:
                # Posisi sepenuhnya acak (hampir selalu tidak valid).
                positions = {
                    p.id: (rng.randint(0, extent[0]), rng.randint(0, extent[1]), rng.choice((0, 0, 0, 1, 2, 3)))
                    for p in packages
                }
            else:
                # State valid, lalu (separuh waktu) satu-dua paket diacak posisinya.
                positions = dict(State(packages, trucks, random.Random(rng.randrange(10**6))).positions)
                if rng.random() < 0.5:
                    for p in rng.sample(packages, rng.randint(1, min(2, len(packages)))):
                        positions[p.id] = (rng.randint(0, extent[0]), rng.randint(0, extent[1]), rng.choice((0, 1, 2)))

            state = make_state(packages, trucks, positions)

            expected = reference_is_valid(state)
            seen[expected] += 1
            self.assertEqual(state.isValid(), expected, positions)

        # Pastikan kedua cabang benar-benar teruji.
        self.assertGreater(seen[True], 100)
        self.assertGreater(seen[False], 100)

    def test_move_neighbor_matches_brute_force(self):
        rng = random.Random(7)
        checked = 0

        for _ in range(60):
            packages, trucks = self.random_world(rng)
            state = State(packages, trucks, random.Random(rng.randrange(10**6)))
            extent = state.extent

            for _ in range(40):
                package = rng.choice(state.packages)
                new_position = (rng.randint(0, extent[0] + 2), rng.randint(0, extent[1] + 2), rng.choice((0, 0, 1, 2, 3)))
                if new_position == state.positions[package.id]:
                    continue

                brute = Neighbor.clone(state)
                brute.positions[package.id] = new_position
                expected = brute.isValid()

                got = Neighbor.move(state, package.id, new_position)
                self.assertEqual(got is not None, expected, (package.id, new_position))
                checked += 1

        self.assertGreater(checked, 500)

    def test_iter_move_neighbors_equals_unfiltered_enumeration(self):
        # Pembangkit neighbor dengan pre-filter harus menghasilkan himpunan yang sama
        # dengan enumerasi penuh x,y,z dengan validasi isValid().
        rng = random.Random(11)
        for _ in range(8):
            packages, trucks = self.random_world(rng)
            state = State(packages, trucks, random.Random(rng.randrange(10**6)))
            extent = state.extent

            expected = []
            for package in state.packages:
                w, d, h = state.getDimOri(package)
                for x in range(extent[0] + w + 1):
                    for y in range(extent[1] + d + 1):
                        for z in range(extent[2] + h + 1):
                            if (x, y, z) == state.positions[package.id]:
                                continue
                            candidate = Neighbor.clone(state)
                            candidate.positions[package.id] = (x, y, z)
                            if candidate.isValid():
                                expected.append(sorted(candidate.positions.items()))

            actual = [sorted(n.positions.items()) for n in Neighbor.iter_move_neighbors(state)]
            self.assertEqual(actual, expected)


class TestMultiTruckNeighbors(unittest.TestCase):
    def test_swap_across_trucks(self):
        trucks = [Truck((3, 3, 1), 10), Truck((3, 3, 1), 10)]
        a, b = pkg("A", (2, 2, 1), value=10), pkg("B", (2, 2, 1), value=70)
        state = make_state([a, b], trucks, {"A": (0, 0, 0), "B": (5, 0, 0)})

        neighbor = Neighbor.swap(state, "A", "B")

        self.assertIsNotNone(neighbor)
        self.assertEqual(neighbor.getTruckIndex(neighbor.packages[0]), 1)
        self.assertEqual(neighbor.getTruckIndex(neighbor.packages[1]), 0)
        self.assertEqual(neighbor.getValue(), state.getValue())     # keduanya tetap di dalam

    def test_move_outside_package_into_second_truck_increases_value(self):
        trucks = [Truck((3, 3, 1), 10), Truck((3, 3, 1), 10)]
        a = pkg("A", (2, 2, 1), value=30)
        state = make_state([a], trucks, {"A": (0, 8, 0)})

        neighbor = Neighbor.move(state, "A", (5, 0, 0))     # T2 origin x=5

        self.assertIsNotNone(neighbor)
        self.assertEqual(neighbor.getTruckIndex(neighbor.packages[0]), 1)
        self.assertEqual(neighbor.getValue(), 30)

    def test_exhaustive_moves_reach_every_truck(self):
        trucks = [Truck((3, 3, 1), 10), Truck((3, 3, 1), 10), Truck((3, 3, 1), 10)]
        a = pkg("A", (2, 2, 1))
        state = make_state([a], trucks, {"A": (0, 0, 0)})

        reached = {n.getTruckIndex(n.packages[0]) for n in Neighbor.iter_move_neighbors(state)}

        self.assertEqual(reached, {0, 1, 2, None})

    def test_move_cannot_cross_wall_between_trucks(self):
        trucks = [Truck((3, 3, 1), 10), Truck((3, 3, 1), 10)]
        a = pkg("A", (2, 2, 1))
        state = make_state([a], trucks, {"A": (0, 0, 0)})

        self.assertIsNone(Neighbor.move(state, "A", (2, 0, 0)))     # x=2..4 menembus dinding T1


class TestParserMultiTruck(unittest.TestCase):
    PACKAGES = ["2", "A 1 1 1 10 1 0 1", "B 2 2 2 x z y 20 2 1 3"]

    def parse(self, truck_lines, n_trucks=None):
        with patch("util.parser.FileHelper.readAllLines", return_value=self.PACKAGES + truck_lines):
            return Parser.parse("ignored.txt", n_trucks)

    def test_single_truck_line_still_works(self):
        packages, trucks = self.parse(["10 10 6 30"])
        self.assertEqual(len(packages), 2)
        self.assertEqual(len(trucks), 1)
        self.assertEqual((trucks[0].dimPeti, trucks[0].maxCapacity, trucks[0].id), ((10, 10, 6), 30.0, "T1"))

    def test_multiple_truck_lines(self):
        _, trucks = self.parse(["10 10 6 30", "8 8 5 20", "6 12 6 35"])
        self.assertEqual([t.dimPeti for t in trucks], [(10, 10, 6), (8, 8, 5), (6, 12, 6)])
        self.assertEqual([t.maxCapacity for t in trucks], [30.0, 20.0, 35.0])
        self.assertEqual([t.id for t in trucks], ["T1", "T2", "T3"])

    def test_truck_line_with_explicit_id(self):
        _, trucks = self.parse(["Alpha 10 10 6 30", "8 8 5 20"])
        self.assertEqual([t.id for t in trucks], ["Alpha", "T2"])

    def test_n_trucks_replicates_a_single_truck(self):
        _, trucks = self.parse(["10 10 6 30"], n_trucks=3)
        self.assertEqual(len(trucks), 3)
        self.assertEqual([t.id for t in trucks], ["T1", "T2", "T3"])
        self.assertTrue(all(t.dimPeti == (10, 10, 6) and t.maxCapacity == 30.0 for t in trucks))
        self.assertIsNot(trucks[0], trucks[1])

    def test_n_trucks_conflicting_with_file_raises(self):
        with self.assertRaises(ValueError):
            self.parse(["10 10 6 30", "8 8 5 20"], n_trucks=3)

    def test_n_trucks_equal_to_file_is_accepted(self):
        _, trucks = self.parse(["10 10 6 30", "8 8 5 20"], n_trucks=2)
        self.assertEqual(len(trucks), 2)

    def test_missing_truck_raises(self):
        with self.assertRaises(ValueError):
            self.parse([])

    def test_invalid_truck_line_raises(self):
        with self.assertRaises(ValueError):
            self.parse(["10 10 6"])

    def test_bundled_multi_truck_input_parses(self):
        path = ROOT_DIR / "input" / "input_multi.txt"
        lines = [line.strip() for line in path.read_text().splitlines() if line.strip()]
        with patch("util.parser.FileHelper.readAllLines", return_value=lines):
            packages, trucks = Parser.parse("input_multi.txt")
        self.assertEqual(len(packages), 14)
        self.assertEqual(len(trucks), 3)


class TestAlgorithmsMultiTruck(unittest.TestCase):
    """Dua truk 4x4x2 hanya bisa memuat satu paket 4x4x2 masing-masing -> optimum = 2 paket."""

    def setUp(self):
        self.trucks = [Truck((4, 4, 2), 10), Truck((4, 4, 2), 10)]
        self.packages = [
            pkg("A", (4, 4, 2), value=10, weight=5),
            pkg("B", (4, 4, 2), value=30, weight=5),
            pkg("C", (4, 4, 2), value=20, weight=5),
            pkg("D", (4, 4, 2), value=25, weight=5),
        ]
        # Semua paket di luar -> value awal 0.
        self.state = make_state(
            self.packages,
            self.trucks,
            {"A": (0, 5, 0), "B": (5, 5, 0), "C": (10, 5, 0), "D": (15, 5, 0)},
        )

    def assert_valid_result(self, result):
        self.assertTrue(result.final_state.isValid())
        self.assertGreaterEqual(result.final_value, result.initial_value)
        self.assertEqual(result.initial_value, 0)

    def test_steepest_ascent_fills_both_trucks_with_best_packages(self):
        result = SteepestAscentHillClimbing(seed=1).run(self.state)

        self.assert_valid_result(result)
        self.assertEqual(result.final_value, 55)      # B(30) + D(25)

    def test_sideways_move(self):
        result = SidewaysMoveHillClimbing(max_sideways=3, seed=1).run(self.state)
        self.assert_valid_result(result)
        self.assertGreaterEqual(result.final_value, 50)

    def test_stochastic(self):
        # Instans longgar: paket kecil punya banyak koordinat valid di dalam truk.
        small = [pkg(f"S{i}", (1, 1, 1), value=10 * (i + 1), weight=1) for i in range(4)]
        state = make_state(
            small,
            self.trucks,
            {f"S{i}": (i * 2, 8, 0) for i in range(4)},
        )

        result = StochasticHillClimbing(max_iterations=400, seed=1).run(state)

        self.assertTrue(result.final_state.isValid())
        self.assertEqual(result.initial_value, 0)
        self.assertGreater(result.final_value, 0)

    def test_random_restart_keeps_all_trucks(self):
        result = RandomRestartHillClimbing(max_restarts=1, seed=1).run(self.state)
        self.assertTrue(result.final_state.isValid())
        self.assertEqual(len(result.final_state.trucks), 2)
        self.assertGreaterEqual(result.final_value, 30)

    def test_simulated_annealing(self):
        result = SimulatedAnnealing(max_iterations=800, seed=3).run(self.state)
        self.assertTrue(result.final_state.isValid())
        self.assertEqual(len(result.final_state.trucks), 2)

    def test_genetic_algorithm_keeps_valid_multi_truck_states(self):
        initial = State(self.packages, self.trucks, random.Random(0))
        result = GeneticAlgorithm(nPopulation=8, nGeneration=6, seed=0).run(initial)

        self.assertTrue(result.final_state.isValid())
        self.assertEqual(len(result.final_state.trucks), 2)
        self.assertEqual(len(result.value_history), len(result.average_value_history))

    def test_result_to_dict_is_json_ready_and_lists_every_truck(self):
        result = SteepestAscentHillClimbing(seed=1).run(self.state)
        data = json.loads(json.dumps(result.to_dict()))

        final = data["final_state"]
        self.assertEqual([t["id"] for t in final["trucks"]], ["T1", "T2"])
        self.assertEqual(sum(t["value"] for t in final["trucks"]), final["value"])
        self.assertEqual(sum(p["inside_truck"] for p in final["packages"]), 2)
        inside = [p for p in final["packages"] if p["inside_truck"]]
        self.assertTrue(all(p["truck"] in ("T1", "T2") and p["local_position"] is not None for p in inside))
        self.assertIn("truck", final)       # kompatibel dengan format single-truck


class TestMultiTruckVisualization(unittest.TestCase):
    def tearDown(self):
        plt.close("all")

    def make(self):
        trucks = [Truck((5, 5, 5), 10), Truck((5, 5, 5), 10)]
        packages = [pkg("P1", (2, 2, 2), 100, 3), pkg("P2", (2, 2, 2), 50, 4, True), pkg("P3", (2, 2, 2), 20, 1)]
        return make_state(packages, trucks, {"P1": (0, 0, 0), "P2": (8, 0, 0), "P3": (0, 8, 0)})

    def test_summary_has_per_truck_breakdown(self):
        summary = summarize_state(self.make())

        self.assertEqual((summary.value, summary.inside, summary.outside), (150, 2, 1))
        self.assertEqual([t.id for t in summary.trucks], ["T1", "T2"])
        self.assertEqual([t.value for t in summary.trucks], [100, 50])
        self.assertEqual([t.weight for t in summary.trucks], [3, 4])
        self.assertEqual(summary.trucks[1].origin_x, 5 + TRUCK_GAP)
        self.assertIn("Trucks used: 2/2", format_summary(summary))

    def test_package_rows_include_truck_column(self):
        rows = package_rows(self.make())
        by_id = {row[0]: row for row in rows}

        self.assertEqual(by_id["P1"][7], "T1")
        self.assertEqual(by_id["P2"][7], "T2")
        self.assertEqual(by_id["P3"][7], "-")
        self.assertEqual(by_id["P3"][1], "OUT")

    def test_truck_rows(self):
        rows = truck_rows(self.make())
        self.assertEqual([r[0] for r in rows], ["T1", "T2"])
        self.assertEqual(rows[0][4], "3 / 10")
        self.assertEqual(rows[1][5], "50")

    def test_visualize_state_adds_truck_table_panel(self):
        fig, ax = visualize_state(self.make(), show=False)

        self.assertEqual(ax.name, "3d")
        self.assertEqual(len(fig.axes), 4)      # 3D, top view, tabel truck, tabel package
        self.assertIn("Objective Value: 150", ax.get_title())

    def test_single_truck_figure_keeps_three_panels(self):
        state = make_state([pkg("P1")], Truck((5, 5, 5), 10), {"P1": (0, 0, 0)})
        fig, _ = visualize_state(state, show=False)
        self.assertEqual(len(fig.axes), 3)


if __name__ == "__main__":
    unittest.main()
