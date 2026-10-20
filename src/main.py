from __future__ import annotations

import argparse
import json
import math
import random
import os
from pathlib import Path

from algorithm.genetic_algorithm.genetic_algorithm import GeneticAlgorithm
from algorithm.hill_climbing import (
    RandomRestartHillClimbing,
    SidewaysMoveHillClimbing,
    SteepestAscentHillClimbing,
    StochasticHillClimbing,
)
from algorithm.simulated_annealing import SimulatedAnnealing
from core.neighbor import Neighbor
from core.state import State
from util.parser import Parser

ROOT_DIR = Path(__file__).resolve().parents[1]
SRC_DIR = Path(__file__).resolve().parent
INPUT_DIR = ROOT_DIR / "input"
OUTPUT_DIR = ROOT_DIR / "output"

ALGORITHMS = {
    "hill_climbing": "Hill Climbing",
    "simulated_annealing": "Simulated Annealing",
    "genetic_algorithm": "Genetic Algorithm",
}
HC_VARIANTS = {
    "steepest": "Steepest Ascent",
    "sideways": "Sideways Move",
    "stochastic": "Stochastic",
    "random_restart": "Random Restart",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Jalankan algoritma optimasi pemuatan paket. Argumen yang tidak diberikan akan ditanyakan interaktif."
    )
    parser.add_argument("--algorithm", choices=ALGORITHMS, help="hill_climbing, simulated_annealing, atau genetic_algorithm")
    parser.add_argument("--hc-variant", choices=HC_VARIANTS, help="Varian Hill Climbing")
    parser.add_argument("--input", help="Nama file di folder input/")
    parser.add_argument("--trucks", type=int, help="Gandakan truk tunggal pada file menjadi N truk")
    parser.add_argument("--output", help="Nama file JSON hasil (disimpan di folder output/)")
    parser.add_argument("--seed", type=int, help="Seed random")
    parser.add_argument("--max-sideways", type=int, help="Batas Sideways Move")
    parser.add_argument("--max-iterations", type=int, help="Batas iterasi Stochastic HC / Simulated Annealing")
    parser.add_argument("--max-neighbor-attempts", type=int, help="Batas percobaan mencari neighbor valid")
    parser.add_argument("--max-restarts", type=int, help="Jumlah restart untuk Random Restart HC")
    parser.add_argument("--target-value", type=int, help="Nilai target untuk menghentikan Random Restart HC")
    parser.add_argument("--initial-temperature", type=float, help="Override suhu awal SA; default dihitung otomatis")
    parser.add_argument("--cooling-rate", type=float, help="Faktor pendinginan Simulated Annealing (0 < nilai < 1)")
    parser.add_argument("--min-temperature", type=float, help="Temperatur minimum Simulated Annealing")
    parser.add_argument("--stuck-threshold", type=int, help="Batas langkah tanpa perubahan pada Simulated Annealing")
    parser.add_argument("--target-acceptance", type=float, help="Target penerimaan langkah menurun saat kalibrasi suhu SA")
    parser.add_argument("--temperature-samples", type=int, help="Jumlah neighbor untuk kalibrasi suhu SA")
    parser.add_argument("--population", type=int, help="Ukuran populasi Genetic Algorithm")
    parser.add_argument("--generations", type=int, help="Jumlah generasi Genetic Algorithm")
    visualization = parser.add_mutually_exclusive_group()
    visualization.add_argument("--visualize", dest="visualize", action="store_true", help="Tampilkan dan simpan visualisasi hasil")
    visualization.add_argument("--no-visualize", dest="visualize", action="store_false", help="Lewati visualisasi")
    parser.set_defaults(visualize=None)
    return parser.parse_args()


def ask(prompt: str, default: str | None = None) -> str:
    suffix = f" [{default}]" if default is not None else ""
    answer = input(f"{prompt}{suffix}: ").strip()
    return answer or (default if default is not None else "")


def choose(prompt: str, options: dict[str, str], default: str | None = None) -> str:
    keys = list(options)
    print(prompt)
    for index, key in enumerate(keys, start=1):
        marker = " (default)" if key == default else ""
        print(f"  {index}. {options[key]}{marker}")
    while True:
        answer = ask("Pilihan", str(keys.index(default) + 1) if default else None)
        if answer in keys:
            return answer
        if answer.isdigit() and 1 <= int(answer) <= len(keys):
            return keys[int(answer) - 1]
        print("Pilihan tidak valid; masukkan nomor atau nama pilihan.")


def ask_int(prompt: str, default: int) -> int:
    while True:
        answer = ask(prompt, str(default))
        try:
            return int(answer)
        except ValueError:
            print("Masukkan bilangan bulat.")


def ask_optional_int(prompt: str) -> int | None:
    answer = ask(prompt, "kosong")
    if not answer or answer.lower() in {"kosong", "none", "tidak"}:
        return None
    try:
        return int(answer)
    except ValueError as error:
        raise ValueError(f"{prompt} harus berupa bilangan bulat atau dikosongkan.") from error


def get_input_name(value: str | None) -> str:
    available = sorted(path.name for path in INPUT_DIR.iterdir() if path.is_file())
    if value is None:
        print(f"File input tersedia: {', '.join(available) or '(belum ada)'}")
        value = ask("Nama file input", "input.txt")
    filename = Path(value).name
    if filename != value or not (INPUT_DIR / filename).is_file():
        raise FileNotFoundError(f"File input '{value}' tidak ditemukan di folder input/.")
    return filename


def load_input(filename: str, n_trucks: int | None):
    previous_cwd = Path.cwd()
    try:
        os.chdir(SRC_DIR)
        return Parser.parse(filename, n_trucks)
    finally:
        os.chdir(previous_cwd)

def calibrate_initial_temperature(
    state: State,
    *,
    target_acceptance: float,
    sample_size: int,
    max_neighbor_attempts: int,
    min_temperature: float,
    seed: int,
) -> tuple[float, dict]:
    """Estimate SA's initial temperature from sampled downhill neighbors.

    Solves mean(exp(-loss / temperature)) ~= target_acceptance by bisection.
    """
    if not 0 < target_acceptance < 1:
        raise ValueError("Target acceptance harus di antara 0 dan 1.")
    if sample_size <= 0:
        raise ValueError("Jumlah sampel suhu harus lebih dari 0.")

    rng = random.Random(seed + 1)
    current_value = state.getValue()
    losses = []
    sampled_neighbors = 0
    for _ in range(sample_size):
        candidate = Neighbor.random_neighbor(
            state,
            rng=rng,
            max_attempts=max_neighbor_attempts,
        )
        if candidate is None:
            continue
        sampled_neighbors += 1
        loss = current_value - candidate.getValue()
        if loss > 0:
            losses.append(loss)

    if not losses:
        # Jika tidak ada downhill move, estimasi loss dengan nilai paket
        typical_loss = sum(abs(package.value) for package in state.packages) / max(1, len(state.packages))
        fallback = typical_loss / -math.log(target_acceptance) if typical_loss else 1.0
        fallback = max(fallback, min_temperature * 1.01)
        return fallback, {
            "mode": "fallback_package_value_scale",
            "target_acceptance": target_acceptance,
            "sample_size": sample_size,
            "valid_neighbors": sampled_neighbors,
            "downhill_samples": 0,
            "typical_package_value": typical_loss,
        }

    def mean_acceptance(temperature: float) -> float:
        return sum(math.exp(-loss / temperature) for loss in losses) / len(losses)

    low = 0.0
    high = max(max(losses), min_temperature)
    while mean_acceptance(high) < target_acceptance:
        high *= 2
    for _ in range(80):
        middle = (low + high) / 2
        if mean_acceptance(middle) < target_acceptance:
            low = middle
        else:
            high = middle

    temperature = max(high, min_temperature * 1.01)
    return temperature, {
        "mode": "sampled_downhill_neighbors",
        "target_acceptance": target_acceptance,
        "sample_size": sample_size,
        "valid_neighbors": sampled_neighbors,
        "downhill_samples": len(losses),
    }


def build_algorithm(args: argparse.Namespace, name: str, seed: int, initial_state: State):
    if name == "hill_climbing":
        variant = args.hc_variant or choose("Pilih varian Hill Climbing:", HC_VARIANTS, "steepest")
        if variant == "steepest":
            return SteepestAscentHillClimbing(seed=seed)
        if variant == "sideways":
            limit = args.max_sideways if args.max_sideways is not None else ask_int("Batas sideways move", 10)
            return SidewaysMoveHillClimbing(max_sideways=limit, seed=seed)
        if variant == "stochastic":
            # Selaras dengan run_hill_climbing.py dan run_visualization.py
            # memakai default terpisah sebesar 1000.
            limit = args.max_iterations if args.max_iterations is not None else ask_int("Batas iterasi", 100)
            attempts = args.max_neighbor_attempts if args.max_neighbor_attempts is not None else ask_int("Percobaan maksimum mencari neighbor valid", 100)
            return StochasticHillClimbing(max_iterations=limit, max_neighbor_attempts=attempts, seed=seed)
        limit = args.max_restarts if args.max_restarts is not None else ask_int("Jumlah restart (di luar run pertama)", 3)
        target = args.target_value if args.target_value is not None else ask_optional_int("Nilai target (kosongkan untuk tanpa target)")
        return RandomRestartHillClimbing(max_restarts=limit, target_value=target, seed=seed)

    if name == "simulated_annealing":
        min_temperature = args.min_temperature if args.min_temperature is not None else 0.001
        cooling_rate = args.cooling_rate if args.cooling_rate is not None else 0.99
        max_iterations = args.max_iterations if args.max_iterations is not None else ask_int("Batas iterasi", 5000)
        attempts = args.max_neighbor_attempts if args.max_neighbor_attempts is not None else 100
        stuck = args.stuck_threshold if args.stuck_threshold is not None else 20
        target_acceptance = args.target_acceptance if args.target_acceptance is not None else 0.9
        sample_size = args.temperature_samples if args.temperature_samples is not None else 100
        initial_temperature = args.initial_temperature
        calibration = {"mode": "manual", "initial_temperature": initial_temperature}
        if initial_temperature is None:
            initial_temperature, calibration = calibrate_initial_temperature(
                initial_state,
                target_acceptance=target_acceptance,
                sample_size=sample_size,
                max_neighbor_attempts=attempts,
                min_temperature=min_temperature,
                seed=seed,
            )
            if calibration["mode"] == "sampled_downhill_neighbors":
                print(
                    f"Suhu awal SA hasil kalibrasi: {initial_temperature:.6g} "
                    f"({calibration['downhill_samples']} sampel menurun)"
                )
            else:
                print(
                    "Sampel tidak menemukan langkah menurun; suhu awal SA "
                    f"diestimasi dari nilai paket: {initial_temperature:.6g}."
                )
        args.temperature_calibration = calibration
        return SimulatedAnnealing(
            initial_temperature=initial_temperature,
            cooling_rate=cooling_rate,
            min_temperature=min_temperature,
            max_iterations=max_iterations,
            max_neighbor_attempts=attempts,
            stuck_threshold=stuck,
            seed=seed,
        )

    population = args.population if args.population is not None else ask_int("Ukuran populasi", 20)
    generations = args.generations if args.generations is not None else ask_int("Jumlah generasi", 50)
    if population < 2:
        raise ValueError("Ukuran populasi Genetic Algorithm minimal 2.")
    if generations < 0:
        raise ValueError("Jumlah generasi tidak boleh negatif.")
    return GeneticAlgorithm(nPopulation=population, nGeneration=generations, seed=seed)


def output_path(name: str | None, algorithm: str, trucks: int) -> Path:
    suffix = f"_{trucks}trucks" if trucks > 1 else ""
    default_name = f"{algorithm}{suffix}.json"
    filename = ask("Nama file output JSON", default_name) if name is None else name
    filename = Path(filename).name
    if not filename.endswith(".json"):
        filename += ".json"
    return OUTPUT_DIR / filename


def main() -> None:
    args = parse_args()
    algorithm_name = args.algorithm or choose("Pilih algoritma:", ALGORITHMS, "hill_climbing")
    seed = args.seed if args.seed is not None else ask_int("Seed random", 42)
    input_name = get_input_name(args.input)
    packages, trucks = load_input(input_name, args.trucks)
    initial_state = State(packages, trucks, random.Random(seed))
    algorithm = build_algorithm(args, algorithm_name, seed, initial_state)
    path = output_path(args.output, algorithm_name, len(trucks))
    result = algorithm.run(initial_state)

    path.parent.mkdir(parents=True, exist_ok=True)
    result_data = result.to_dict()
    if algorithm_name == "simulated_annealing":
        result_data["parameters"]["temperature_calibration"] = args.temperature_calibration
    path.write_text(json.dumps(result_data, indent=2), encoding="utf-8")

    print("\n=== HASIL ===")
    print(f"Algoritma     : {result.algorithm}")
    print(f"Input         : input/{input_name}")
    print(f"Jumlah truk   : {len(trucks)}")
    print(f"Nilai awal    : {result.initial_value}")
    print(f"Nilai akhir   : {result.final_value}")
    print(f"Iterasi       : {result.iterations}")
    print(f"Durasi pencarian: {result.duration_seconds:.6f} detik")
    print(f"Alasan berhenti: {result.stop_reason}")
    print(f"Output        : {path}")

    show_visualization = args.visualize
    if show_visualization is None:
        answer = ask("Ingin melihat visualisasi hasil? (y/n)", "n").lower()
        show_visualization = answer in {"y", "yes", "ya"}

    if show_visualization:
        from visualization import plot_history, visualize_result

        image_path = OUTPUT_DIR / "visualization" / f"{path.stem}.png"
        visualize_result(result, show=True, save_path=image_path)
        print(f"Visualisasi disimpan: {image_path}")

        history_path = OUTPUT_DIR / "visualization" / f"{path.stem}_history.png"
        plot_history(result, show=True, save_path=history_path)
        print(f"Plot riwayat nilai disimpan: {history_path}")


if __name__ == "__main__":
    main()
