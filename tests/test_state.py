import random
import sys
import unittest
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from core.entity import Package, Truck
from core.state import State
from util.fileHelper import INPUT_DIR, FileHelper


def make_packages(count: int, seed: int) -> list[Package]:
    rng = random.Random(seed)
    return [
        Package(
            f"P{i + 1}",
            (rng.randint(1, 5), rng.randint(1, 5), rng.randint(1, 4)),
            ("x", "y", "z"),
            rng.randint(20, 150),
            rng.randint(2, 15),
            rng.random() < 0.3,
            1,
        )
        for i in range(count)
    ]


class TestRandomInitialState(unittest.TestCase):
    def test_random_initial_state_is_always_valid(self):
        # Regresi: paket fragile yang ditempatkan belakangan pernah bisa
        # masuk ke bawah paket lain sehingga menjadi support.
        truck = Truck((10, 10, 6), 80)
        packages = make_packages(40, seed=1)

        for seed in range(50):
            random.seed(seed)
            state = State(packages, truck)
            self.assertTrue(state.isValid(), f"initial state invalid untuk seed {seed}")

    def test_fragile_package_never_supports_another(self):
        truck = Truck((10, 10, 6), 80)
        packages = make_packages(40, seed=2)

        for seed in range(50):
            random.seed(seed)
            state = State(packages, truck)
            for lower in packages:
                if not lower.isFragile:
                    continue
                for upper in packages:
                    if upper.id != lower.id:
                        self.assertFalse(
                            state.isSupport(lower, upper),
                            f"{lower.id} fragile menopang {upper.id} (seed {seed})",
                        )


class TestFileHelper(unittest.TestCase):
    def test_input_dir_points_to_project_input_folder(self):
        self.assertEqual(INPUT_DIR, ROOT_DIR / "input")

    def test_read_input_does_not_depend_on_working_directory(self):
        lines = FileHelper.readAllLines("input.txt")

        self.assertGreater(len(lines), 0)


if __name__ == "__main__":
    unittest.main()