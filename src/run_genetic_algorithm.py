from __future__ import annotations

import argparse
import json
import random
from pathlib import Path
from typing import Any

from algorithm.genetic_algorithm.genetic_algorithm import GeneticAlgorithm
from core.state import State
from util.parser import Parser

ROOT_DIR = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = ROOT_DIR / "output" / "genetic_algorithm_experiments.json"
RUNS_PER_CONFIGURATION = 3


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Eksperimen Genetic Algorithm untuk populasi dan jumlah generasi.")
    parser.add_argument("--input", default="input.txt", help="Nama file input di folder input/")
    parser.add_argument("--trucks", type=int, default=None, help="Gandakan truk tunggal pada file menjadi N truk")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT, help="Path file JSON hasil")
    parser.add_argument("--seed", type=int, default=0, help="Seed dasar eksperimen")
    parser.add_argument("--population-control", type=int, default=20, help="Populasi tetap saat menguji variasi jumlah generasi")
    parser.add_argument("--generation-variations", type=int, nargs=3, default=(25, 50, 100), metavar=("N1", "N2", "N3"), help="Tiga jumlah generasi yang diuji pada populasi tetap")
    parser.add_argument("--generation-control", type=int, default=50, help="Jumlah generasi tetap saat menguji variasi populasi")
    parser.add_argument("--population-variations", type=int, nargs=3, default=(10, 20, 40), metavar=("N1", "N2", "N3"), help="Tiga jumlah populasi yang diuji pada generasi tetap")
    return parser.parse_args()


def run_configuration(packages, trucks, *, population: int, generations: int, seed: int, experiment: str) -> dict[str, Any]:
    initial_state = State(packages, trucks, random.Random(seed))
    result = GeneticAlgorithm(nPopulation=population, nGeneration=generations, seed=seed).run(initial_state)

    return {
        "experiment": experiment,
        "population": population,
        "generations": generations,
        "run_seed": seed,
        "result": result.to_dict(),
    }


def print_result(run_no: int, run: dict[str, Any]) -> None:
    result = run["result"]
    print(f"\n=== GENETIC ALGORITHM - RUN {run_no} ===")
    print(f"Experiment            : {run['experiment']}")
    print(f"Population            : {run['population']}")
    print(f"Generations           : {run['generations']}")
    print(f"Seed                  : {run['run_seed']}")
    print(f"Initial value         : {result['initial_value']}")
    print(f"Final value           : {result['final_value']}")
    print(f"Best value seen       : {result['metadata']['best_value_seen']}")
    print(f"Iterations            : {result['iterations']}")
    print(f"Stop reason           : {result['stop_reason']}")
    print(f"Duration              : {result['duration_seconds']:.6f} s")
    print(f"Average value history : {result['average_value_history']}")


def main() -> None:
    args = parse_args()
    if args.population_control < 2 or args.generation_control < 0:
        raise ValueError("Populasi kontrol minimal 2 dan jumlah generasi tidak boleh negatif.")
    if any(population < 2 for population in args.population_variations):
        raise ValueError("Setiap variasi populasi harus minimal 2.")
    if any(generations < 0 for generations in args.generation_variations):
        raise ValueError("Jumlah generasi tidak boleh negatif.")

    packages, trucks = Parser.parse(args.input, args.trucks)
    if len(trucks) > 1 and args.output == DEFAULT_OUTPUT:
        # Hasil multi-truk diberi akhiran agar tidak menimpa hasil single-truck
        args.output = DEFAULT_OUTPUT.with_name(f"genetic_algorithm_experiments_{len(trucks)}trucks.json")
    print(f"Jumlah truk: {len(trucks)}")
    seed_rng = random.Random(args.seed)
    runs: list[dict[str, Any]] = []

    for generations in args.generation_variations:
        for _ in range(RUNS_PER_CONFIGURATION):
            run = run_configuration(packages, trucks, population=args.population_control, generations=generations, seed=seed_rng.randrange(2**32), experiment="fixed_population")
            runs.append(run)
            print_result(len(runs), run)

    for population in args.population_variations:
        for _ in range(RUNS_PER_CONFIGURATION):
            run = run_configuration(packages, trucks, population=population, generations=args.generation_control, seed=seed_rng.randrange(2**32), experiment="fixed_generations")
            runs.append(run)
            print_result(len(runs), run)

    output = {
        "runs_per_configuration": RUNS_PER_CONFIGURATION,
        "results": runs,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(output, indent=2), encoding="utf-8")

    print("\n=== RINGKASAN ===")
    for run_no, run in enumerate(runs, start=1):
        result = run["result"]
        print(f"Run {run_no}: {run['experiment']}, population={run['population']}, generations={run['generations']}, final_value={result['final_value']}, duration={result['duration_seconds']:.6f} s")
    print(f"Selesai: {len(runs)} run disimpan ke {args.output}")


if __name__ == "__main__":
    main()