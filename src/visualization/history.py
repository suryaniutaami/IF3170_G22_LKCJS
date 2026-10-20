"""
Plot riwayat hasil eksperimen:
- Hill-Climbing      : objective value terhadap iterasi (Random Restart diberi penanda tiap restart)
- Simulated Annealing: objective value dan e^(ΔE/T) terhadap iterasi
- Genetic Algorithm  : objective value maksimum dan rata-rata populasi terhadap generasi

Menerima objek result (HillClimbingResult dan turunannya) maupun dictionary
hasil to_dict() / JSON di folder output/.
"""

from __future__ import annotations
from pathlib import Path
from typing import Any
import matplotlib.pyplot as plt
from matplotlib.axes import Axes
from matplotlib.figure import Figure

FIGURE_WIDTH = 10.0
PANEL_HEIGHT = 3.6
LINE_COLOR = "tab:blue"
AVERAGE_COLOR = "tab:orange"
RESTART_COLOR = "gray"
PROBABILITY_COLOR = "tab:red"

def _get(result: Any, key: str, default: Any = None) -> Any:
    # Mendukung objek result maupun dictionary dari JSON.
    if isinstance(result, dict):
        return result.get(key, default)
    return getattr(result, key, default)

def _title(result: Any) -> str:
    algorithm = str(_get(result, "algorithm", "")).replace("_", " ").title()
    initial = _get(result, "initial_value")
    final = _get(result, "final_value")
    duration = _get(result, "duration_seconds", 0.0)
    return (
        f"{algorithm}: {initial} → {final} "
        f"| Iterations: {_get(result, 'iterations')} "
        f"| Duration: {duration:.4f}s "
        f"| Stop: {_get(result, 'stop_reason')}"
    )

def _draw_value_history(ax: Axes, result: Any) -> None:
    metadata = _get(result, "metadata", {}) or {}
    restart_histories = metadata.get("restart_histories")

    if restart_histories:
        # Random Restart: riwayat tiap restart digabung berurutan, awal restart diberi garis putus-putus.
        offset = 0
        for index, history in enumerate(restart_histories):
            xs = range(offset, offset + len(history))
            ax.plot(xs, history, color=LINE_COLOR, marker="o", markersize=3)
            if index > 0:
                ax.axvline(offset, color=RESTART_COLOR, linestyle="--", linewidth=0.8)
            offset += len(history)
        ax.plot([], [], color=RESTART_COLOR, linestyle="--", linewidth=0.8, label="Restart")
        ax.legend(loc="lower right")
    else:
        history = _get(result, "value_history", [])
        marker = "o" if len(history) <= 50 else None
        ax.plot(range(len(history)), history, color=LINE_COLOR, marker=marker, markersize=3)

    ax.set_xlabel("Iterasi")
    ax.set_ylabel("Objective value")
    ax.set_title("Objective value terhadap iterasi")
    ax.grid(alpha=0.3)

def _draw_acceptance_probability(ax: Axes, result: Any) -> None:
    # probability_history[i] adalah e^(ΔE/T) pada iterasi ke-(i+1); ΔE >= 0 dicatat sebagai 1.0.
    probabilities = _get(result, "probability_history", [])
    xs = range(1, len(probabilities) + 1)
    ax.scatter(xs, probabilities, s=4, color=PROBABILITY_COLOR, alpha=0.5)
    ax.set_xlabel("Iterasi")
    ax.set_ylabel("e^(ΔE/T)")
    ax.set_title("Probabilitas penerimaan e^(ΔE/T) terhadap iterasi (ΔE ≥ 0 dicatat sebagai 1.0)")
    ax.set_ylim(-0.05, 1.05)
    ax.grid(alpha=0.3)

def _draw_ga_history(ax: Axes, result: Any) -> None:
    maximum = _get(result, "value_history", [])
    average = _get(result, "average_value_history", [])
    marker = "o" if len(maximum) <= 50 else None
    ax.plot(range(len(maximum)), maximum, color=LINE_COLOR, marker=marker, markersize=3, label="Maksimum populasi")
    ax.plot(range(len(average)), average, color=AVERAGE_COLOR, marker=marker, markersize=3, label="Rata-rata populasi")
    ax.set_xlabel("Generasi")
    ax.set_ylabel("Objective value")
    ax.set_title("Objective value maksimum dan rata-rata populasi terhadap generasi")
    ax.grid(alpha=0.3)
    ax.legend(loc="best")

def plot_history(
    result: Any,
    *,
    show: bool = True,
    save_path: str | Path | None = None,
) -> Figure:
    """
    Memilih plot sesuai jenis hasil:
    GA jika ada average_value_history, SA jika ada probability_history, selain itu Hill-Climbing.
    """
    is_ga = bool(_get(result, "average_value_history"))
    is_sa = bool(_get(result, "probability_history"))

    if is_sa:
        fig, (ax_value, ax_probability) = plt.subplots(
            2, 1, figsize=(FIGURE_WIDTH, PANEL_HEIGHT * 2), layout="constrained"
        )
        _draw_value_history(ax_value, result)
        _draw_acceptance_probability(ax_probability, result)
    else:
        fig, ax = plt.subplots(figsize=(FIGURE_WIDTH, PANEL_HEIGHT + 0.6), layout="constrained")
        if is_ga:
            _draw_ga_history(ax, result)
        else:
            _draw_value_history(ax, result)

    fig.suptitle(_title(result), fontsize=11, fontweight="bold")

    if save_path is not None:
        path = Path(save_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(path, dpi=150)

    if show:
        plt.show()

    return fig