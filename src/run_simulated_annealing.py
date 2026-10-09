import json
import random
from pathlib import Path

from algorithm.simulated_annealing import SimulatedAnnealing
from core.state import State
from util.parser import Parser

OUTPUT_DIR = Path(__file__).resolve().parents[1] / "output"
N_RUNS = 3


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


def save_plots(run_no, result):
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
    path = OUTPUT_DIR / f"sa_run{run_no}.png"
    fig.savefig(path, dpi=150)
    plt.close(fig)
    print(f"Plot disimpan: {path}")


def main():
    OUTPUT_DIR.mkdir(exist_ok=True)
    packages, truck = Parser.parse("input.txt")
    rng = random.Random()

    summaries = []
    for run_no in range(1, N_RUNS + 1):
        initial_state = State(packages, truck, rng)  # initial state random baru tiap run
        algorithm = SimulatedAnnealing(
            initial_temperature=100.0,
            cooling_rate=0.99,
            min_temperature=1e-3,
            max_iterations=5000,
            stuck_threshold=20,
        )
        result = algorithm.run(initial_state)

        print_result(run_no, result)
        save_plots(run_no, result)

        with open(OUTPUT_DIR / f"sa_run{run_no}.json", "w", encoding="utf-8") as f:
            json.dump(result.to_dict(), f, indent=2)

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