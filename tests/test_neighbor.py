import sys
import unittest
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT_DIR / "src"

if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from core.entity import Package, Truck
from core.neighbor import Neighbor
from core.state import State


def make_state(packages, truck, positions):
    """
    Membuat State deterministik untuk unit test tanpa menjalankan
    State.__init__(), karena constructor State saat ini langsung
    melakukan random_position().
    """
    state = State.__new__(State)
    state.packages = packages
    state.truck = truck
    state.positions = dict(positions)
    return state


class TestNeighbor(unittest.TestCase):

    def test_swap_valid_and_does_not_modify_original_state(self):
        p1 = Package("A", (1, 1, 1), ("x", "y", "z"), 10, 1, False, 1)
        p2 = Package("B", (1, 1, 1), ("x", "y", "z"), 20, 1, False, 1)
        truck = Truck((4, 2, 1), 10)

        state = make_state(
            [p1, p2],
            truck,
            {
                "A": (0, 0, 0),
                "B": (2, 0, 0),
            },
        )

        neighbor = Neighbor.swap(state, "A", "B")

        self.assertIsNotNone(neighbor)
        self.assertTrue(neighbor.isValid())

        self.assertEqual(neighbor.positions["A"], (2, 0, 0))
        self.assertEqual(neighbor.positions["B"], (0, 0, 0))

        # Current state tidak boleh ikut berubah.
        self.assertEqual(state.positions["A"], (0, 0, 0))
        self.assertEqual(state.positions["B"], (2, 0, 0))

    def test_swap_same_package_returns_none(self):
        p1 = Package("A", (1, 1, 1), ("x", "y", "z"), 10, 1, False, 1)
        truck = Truck((2, 2, 1), 10)

        state = make_state(
            [p1],
            truck,
            {"A": (0, 0, 0)},
        )

        self.assertIsNone(Neighbor.swap(state, "A", "A"))

    def test_move_valid_and_does_not_modify_original_state(self):
        p1 = Package("A", (1, 1, 1), ("x", "y", "z"), 10, 1, False, 1)
        p2 = Package("B", (1, 1, 1), ("x", "y", "z"), 20, 1, False, 1)
        truck = Truck((4, 2, 1), 10)

        state = make_state(
            [p1, p2],
            truck,
            {
                "A": (0, 0, 0),
                "B": (2, 0, 0),
            },
        )

        neighbor = Neighbor.move(state, "A", (1, 0, 0))

        self.assertIsNotNone(neighbor)
        self.assertTrue(neighbor.isValid())
        self.assertEqual(neighbor.positions["A"], (1, 0, 0))

        # Current state harus tetap.
        self.assertEqual(state.positions["A"], (0, 0, 0))

    def test_move_to_same_position_returns_none(self):
        p1 = Package("A", (1, 1, 1), ("x", "y", "z"), 10, 1, False, 1)
        truck = Truck((2, 2, 1), 10)

        state = make_state(
            [p1],
            truck,
            {"A": (0, 0, 0)},
        )

        self.assertIsNone(Neighbor.move(state, "A", (0, 0, 0)))

    def test_move_that_causes_overlap_is_rejected(self):
        p1 = Package("A", (1, 1, 1), ("x", "y", "z"), 10, 1, False, 1)
        p2 = Package("B", (1, 1, 1), ("x", "y", "z"), 20, 1, False, 1)
        truck = Truck((4, 2, 1), 10)

        state = make_state(
            [p1, p2],
            truck,
            {
                "A": (0, 0, 0),
                "B": (2, 0, 0),
            },
        )

        # A dipindahkan tepat ke posisi B -> overlap.
        neighbor = Neighbor.move(state, "A", (2, 0, 0))

        self.assertIsNone(neighbor)

        # State asal tetap tidak berubah.
        self.assertEqual(state.positions["A"], (0, 0, 0))
        self.assertEqual(state.positions["B"], (2, 0, 0))

    def test_move_requires_integer_3d_coordinate(self):
        p1 = Package("A", (1, 1, 1), ("x", "y", "z"), 10, 1, False, 1)
        truck = Truck((2, 2, 1), 10)

        state = make_state(
            [p1],
            truck,
            {"A": (0, 0, 0)},
        )

        with self.assertRaises(ValueError):
            Neighbor.move(state, "A", (1, 0))

        with self.assertRaises(ValueError):
            Neighbor.move(state, "A", (1.5, 0, 0))

    def test_rotate_z_changes_orientation_and_dimensions(self):
        p1 = Package("A", (2, 1, 1), ("x", "y", "z"), 10, 1, False, 1)
        truck = Truck((3, 3, 1), 10)

        state = make_state(
            [p1],
            truck,
            {"A": (0, 0, 0)},
        )

        neighbor = Neighbor.rotate(state, "A", "z")

        self.assertIsNotNone(neighbor)
        self.assertTrue(neighbor.isValid())

        rotated_package = neighbor.packages[0]

        self.assertEqual(rotated_package.orientation, ("y", "x", "z"))
        self.assertEqual(neighbor.getDimOri(rotated_package), (1, 2, 1))

        # Orientasi package pada current state tidak boleh ikut berubah.
        self.assertEqual(state.packages[0].orientation, ("x", "y", "z"))
        self.assertEqual(state.getDimOri(state.packages[0]), (2, 1, 1))

    def test_rotate_invalid_axis_raises_value_error(self):
        p1 = Package("A", (2, 1, 1), ("x", "y", "z"), 10, 1, False, 1)
        truck = Truck((3, 3, 1), 10)

        state = make_state(
            [p1],
            truck,
            {"A": (0, 0, 0)},
        )

        with self.assertRaises(ValueError):
            Neighbor.rotate(state, "A", "q")

    def test_rotate_that_hits_truck_wall_is_rejected(self):
        p1 = Package("A", (2, 1, 1), ("x", "y", "z"), 10, 1, False, 1)
        truck = Truck((3, 1, 1), 10)

        state = make_state(
            [p1],
            truck,
            {"A": (0, 0, 0)},
        )

        # Awalnya dimensi efektif (2,1,1), masih muat.
        self.assertTrue(state.isValid())

        # Rotate Z -> dimensi efektif menjadi (1,2,1),
        # sehingga memotong batas Y peti.
        neighbor = Neighbor.rotate(state, "A", "z")

        self.assertIsNone(neighbor)

    def test_generate_swap_neighbors_returns_only_valid_states(self):
        p1 = Package("A", (1, 1, 1), ("x", "y", "z"), 10, 1, False, 1)
        p2 = Package("B", (1, 1, 1), ("x", "y", "z"), 20, 1, False, 1)
        truck = Truck((4, 2, 1), 10)

        state = make_state(
            [p1, p2],
            truck,
            {
                "A": (0, 0, 0),
                "B": (2, 0, 0),
            },
        )

        neighbors = Neighbor.generate_swap_neighbors(state)

        self.assertEqual(len(neighbors), 1)
        self.assertTrue(all(neighbor.isValid() for neighbor in neighbors))

    def test_generate_rotation_neighbors_returns_only_valid_states(self):
        p1 = Package("A", (2, 1, 1), ("x", "y", "z"), 10, 1, False, 1)
        truck = Truck((3, 3, 2), 10)

        state = make_state(
            [p1],
            truck,
            {"A": (0, 0, 0)},
        )

        neighbors = Neighbor.generate_rotation_neighbors(state)

        self.assertGreater(len(neighbors), 0)
        self.assertTrue(all(neighbor.isValid() for neighbor in neighbors))

        # Generator tidak boleh mengubah current state.
        self.assertEqual(state.packages[0].orientation, ("x", "y", "z"))

    def test_generate_move_neighbors_returns_valid_states(self):
        # Ukuran sangat kecil supaya exhaustive move tetap cepat.
        p1 = Package("A", (1, 1, 1), ("x", "y", "z"), 10, 1, False, 1)
        truck = Truck((1, 1, 1), 10)

        state = make_state(
            [p1],
            truck,
            {"A": (0, 0, 0)},
        )

        neighbors = Neighbor.generate_move_neighbors(state)

        self.assertGreater(len(neighbors), 0)
        self.assertTrue(all(neighbor.isValid() for neighbor in neighbors))

        # Current state tidak berubah.
        self.assertEqual(state.positions["A"], (0, 0, 0))
    def test_move_support_that_leaves_upper_package_floating_is_rejected(self):
        # Cek lokal hanya melihat package yang dipindah; cek penuh tetap harus
        # menolak state ketika package di atasnya jadi melayang.
        lower = Package("A", (2, 2, 1), ("x", "y", "z"), 10, 1, False, 1)
        upper = Package("B", (2, 2, 1), ("x", "y", "z"), 10, 1, False, 1)
        truck = Truck((5, 5, 3), 10)

        state = make_state(
            [lower, upper],
            truck,
            {"A": (0, 0, 0), "B": (0, 0, 1)},
        )
        self.assertTrue(state.isValid())

        self.assertIsNone(Neighbor.move(state, "A", (3, 3, 0)))

    def test_chained_rotations_do_not_affect_earlier_states(self):
        p1 = Package("A", (3, 2, 1), ("x", "y", "z"), 10, 1, False, 1)
        truck = Truck((5, 5, 5), 10)

        state = make_state([p1], truck, {"A": (0, 0, 0)})
        first = Neighbor.rotate(state, "A", "z")
        second = Neighbor.rotate(first, "A", "x")

        self.assertEqual(state.packages[0].orientation, ("x", "y", "z"))
        self.assertEqual(first.packages[0].orientation, ("y", "x", "z"))
        self.assertEqual(second.packages[0].orientation, ("z", "x", "y"))


if __name__ == "__main__":
    unittest.main()