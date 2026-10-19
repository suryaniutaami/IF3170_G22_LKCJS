# Demo sederhana untuk menjalankan seluruh varian Hill-Climbing.

import argparse
import random
from algorithm.hill_climbing import (
    RandomRestartHillClimbing,
    SidewaysMoveHillClimbing,
    SteepestAscentHillClimbing,
    StochasticHillClimbing,
)
from core.state import State
from util.parser import Parser


def print_result(result):
    print(f"\n=== {result.algorithm.upper()} ===")
    print(f"Initial value : {result.initial_value}")
    print(f"Final value   : {result.final_value}")
    print(f"Iterations    : {result.iterations}")
    print(f"Accepted moves: {result.accepted_moves}")
    print(f"Stop reason   : {result.stop_reason}")
    print(f"Duration      : {result.duration_seconds:.6f} s")
    print(f"History       : {result.value_history}")

    if result.metadata:
        print(f"Metadata      : {result.metadata}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Demo seluruh varian Hill-Climbing")
    parser.add_argument("--input", default="input.txt", help="Nama file di folder input/ (mis. input_multi.txt)")
    parser.add_argument("--trucks", type=int, default=None, help="Gandakan truk tunggal pada file menjadi N truk")
    return parser.parse_args()


def main():
    args = parse_args()
    packages, trucks = Parser.parse(args.input, args.trucks)
    initial_state = State(packages, trucks, random.Random())
    print(f"Jumlah truk: {len(trucks)}")

    algorithms = [
        SteepestAscentHillClimbing(seed=42),
        SidewaysMoveHillClimbing(max_sideways=10, seed=42),
        StochasticHillClimbing(max_iterations=100, seed=42),
        RandomRestartHillClimbing(max_restarts=3, seed=42),
    ]

    print("Initial state valid:", initial_state.isValid())
    print("Initial objective value:", initial_state.getValue())

    for algorithm in algorithms:
        result = algorithm.run(initial_state)
        print_result(result)


if __name__ == "__main__":
    main()