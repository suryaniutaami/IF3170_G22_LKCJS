import argparse
import json
import random
from pathlib import Path

from algorithm.simulated_annealing import SimulatedAnnealing
from core.state import State
from main import calibrate_initial_temperature
from util.outputHelper import OutputHelper
from util.parser import Parser

# JSON di output/simulated_annealing/, plot di output/visualization/simulated_annealing/.
OUTPUT_DIR = OutputHelper.resultDir("simulated_annealing")
PLOT_DIR = OutputHelper.visualizationDir("simulated_annealing")
N_RUNS = 3


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Eksperimen Simulated Annealing (3 run)")
    parser.add_argument("--input", default="input2.txt", help="Nama file di folder input/ (mis. input_multi.txt)")
    parser.add_argument("--trucks", type=int, default=None, help="Gandakan truk tunggal pada file menjadi N truk")
    parser.add_argument("--seed", type=int, default=42, help="Seed awal; tiap run memakai seed berurutan (default: 42)")
    return parser.parse_args()


def print_result(run_no, result):
    print(f"\n=== SIMULATED ANNEALING - RUN {run_no} ===")
    print(f"Initial value        : {result.initial_value}")
    print(f"Final value          : {result.final_value}")
    print(f"Best value seen      : {result.metadata['best_value_seen']}")
    print(f"Iterations           : {result.iterations}")
    print(f"Accepted moves       : {result.accepted_moves}")
    print(f"  - improving        : {result.metadata['improving_moves']}")
    print(f"  - worse (escape)   : {result.metadata['worse_moves_accepted']}")
    print(f"Rejected moves       : {result.metadata['rejected_moves']}")
    print(f"Stuck in local optima: {result.stuck_count} kali")
    print(f"Stop reason          : {result.stop_reason}")
    print(f"Duration             : {result.duration_seconds:.6f} s")


def save_plots(run_no, result, suffix=""):
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError:
        print("matplotlib tidak terpasang, plot dilewati (pip install matplotlib).")
        return

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 7), sharex=True)

    ax1.plot(range(len(result.value_history)), result.value_history)
    ax1.set_ylabel("Objective value")
    ax1.set_title(f"Simulated Annealing - Run {run_no}: objective value")
    ax1.grid(alpha=0.3)

    ax2.plot(range(1, len(result.probability_history) + 1), result.probability_history, lw=0.8)
    ax2.set_xlabel("Iterasi")
    ax2.set_ylabel("e^(ΔE/T)")
    ax2.set_title("Probabilitas penerimaan (ΔE > 0 dicatat sebagai 1.0)")
    ax2.set_ylim(-0.05, 1.05)
    ax2.grid(alpha=0.3)

    fig.tight_layout()
    PLOT_DIR.mkdir(parents=True, exist_ok=True)
    path = PLOT_DIR / f"sa_run{run_no}{suffix}.png"
    fig.savefig(path, dpi=150)
    plt.close(fig)
    print(f"Plot disimpan: {path}")


def main():
    args = parse_args()
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    packages, trucks = Parser.parse(args.input, args.trucks)
    input_stem = Path(args.input).stem
    truck_suffix = f"_{len(trucks)}trucks" if len(trucks) > 1 else ""
    suffix = f"_{input_stem}{truck_suffix}_seed{args.seed}"
    print(f"Jumlah truk: {len(trucks)}")

    summaries = []
    for run_no in range(1, N_RUNS + 1):
        run_seed = args.seed + run_no - 1
        initial_state = State(packages, trucks, random.Random(run_seed))
        initial_temperature, calibration = calibrate_initial_temperature(
            initial_state,
            target_acceptance=0.9,
            sample_size=100,
            max_neighbor_attempts=100,
            min_temperature=1e-3,
            seed=run_seed,
        )
        print(f"Seed run {run_no}: {run_seed}; suhu awal terkalibrasi: {initial_temperature:.6g}")
        algorithm = SimulatedAnnealing(
            initial_temperature=initial_temperature,
            cooling_rate=SimulatedAnnealing.DEFAULT_COOLING_RATE,
            min_temperature=SimulatedAnnealing.DEFAULT_MIN_TEMPERATURE,
            max_iterations=SimulatedAnnealing.DEFAULT_MAX_ITERATIONS,
            stuck_threshold=20,
            max_neighbor_attempts=100,
            seed=run_seed,
        )
        result = algorithm.run(initial_state)

        print_result(run_no, result)
        save_plots(run_no, result, suffix)

        result_data = result.to_dict()
        result_data["parameters"]["temperature_calibration"] = calibration
        with open(OUTPUT_DIR / f"sa_run{run_no}{suffix}.json", "w", encoding="utf-8") as f:
            json.dump(result_data, f, indent=2)

        summaries.append(
            {
                "run": run_no,
                "initial_value": result.initial_value,
                "final_value": result.final_value,
                "iterations": result.iterations,
                "stuck_count": result.stuck_count,
                "duration_seconds": result.duration_seconds,
            }
        )

    print("\n=== RINGKASAN ===")
    for s in summaries:
        print(s)


if __name__ == "__main__":
    main()