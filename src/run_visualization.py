"""
Demo visualisasi initial & final state hasil Hill-Climbing.
"""

from __future__ import annotations
import argparse
import random
from pathlib import Path
from algorithm.hill_climbing import (
    RandomRestartHillClimbing,
    SidewaysMoveHillClimbing,
    SteepestAscentHillClimbing,
    StochasticHillClimbing,
)
from core.state import State
from util.parser import Parser
from visualization import visualize_result

OUTPUT_DIR = Path(__file__).resolve().parents[1] / "output" / "visualization"

# Tambahkan algoritma baru (mis. simulated annealing) cukup di registry ini.
ALGORITHMS = {
    "steepest": lambda args: SteepestAscentHillClimbing(seed=args.seed),
    "sideways": lambda args: SidewaysMoveHillClimbing(max_sideways=args.max_sideways, seed=args.seed),
    "stochastic": lambda args: StochasticHillClimbing(max_iterations=args.max_iterations, seed=args.seed),
    "random_restart": lambda args: RandomRestartHillClimbing(max_restarts=args.max_restarts, seed=args.seed),
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Visualisasi initial & final state hasil Hill-Climbing")
    parser.add_argument("--algorithm", choices=ALGORITHMS, default="steepest", help="Algoritma yang dijalankan")
    parser.add_argument("--input", default="input.txt", help="Nama file di folder input/")
    parser.add_argument("--seed", type=int, default=0, help="Random seed")

    parser.add_argument("--max-sideways", type=int, default=10, help="[sideways] batas sideways move")
    parser.add_argument("--max-iterations", type=int, default=1000, help="[stochastic] batas iterasi")
    parser.add_argument("--max-restarts", type=int, default=3, help="[random_restart] batas restart")

    parser.add_argument("--save", default=None, help="Path PNG/PDF (default: output/visualization/)")
    parser.add_argument("--no-save", action="store_true", help="Jangan simpan gambar")
    parser.add_argument("--no-show", action="store_true", help="Jangan membuka window visualisasi")
    parser.add_argument("--hide-outside", action="store_true", help="Sembunyikan package di luar truck")
    return parser.parse_args()

def resolve_save_path(args: argparse.Namespace) -> Path | None:
    if args.no_save:
        return None
    if args.save:
        return Path(args.save)
    return OUTPUT_DIR / f"{args.algorithm}_seed{args.seed}.png"

def main() -> None:
    args = parse_args()

    # State.random_position() memakai module random global, jadi seed perlu
    # dipasang sebelum State dibuat agar demo dapat direproduksi.
    random.seed(args.seed)

    packages, truck = Parser.parse(args.input)
    initial_state = State(packages, truck)

    result = ALGORITHMS[args.algorithm](args).run(initial_state)
    save_path = resolve_save_path(args)

    print("=== VISUALIZATION ===")
    print(f"Algorithm     : {result.algorithm}")
    print(f"Initial value : {result.initial_value}")
    print(f"Final value   : {result.final_value}")
    print(f"Iterations    : {result.iterations}")
    print(f"Stop reason   : {result.stop_reason}")
    if save_path:
        print(f"Saved to      : {save_path}")

    visualize_result(
        result,
        show_outside=not args.hide_outside,
        show=not args.no_show,
        save_path=save_path,
    )

if __name__ == "__main__":
    main()