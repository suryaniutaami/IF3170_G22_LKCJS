"""
Struktur folder output yang seragam untuk seluruh algoritma:

output/
├── hill_climbing/
│   ├── steepest_ascent/
│   ├── sideways_move/
│   ├── stochastic/
│   └── random_restart/
├── simulated_annealing/
├── genetic_algorithm/
└── visualization/
    ├── hill_climbing/
    │   ├── steepest_ascent/
    │   ├── sideways_move/
    │   ├── stochastic/
    │   └── random_restart/
    ├── simulated_annealing/
    ├── genetic_algorithm/
    └── scenarios/

JSON hasil run disimpan di output/<algoritma>/, gambar di output/visualization/<algoritma>/.
"""

from __future__ import annotations
from pathlib import Path

OUTPUT_DIR = Path(__file__).resolve().parents[2] / "output"
VISUALIZATION_DIR = OUTPUT_DIR / "visualization"

# Nilai result.algorithm untuk tiap varian Hill-Climbing.
HILL_CLIMBING_VARIANTS = ("steepest_ascent", "sideways_move", "stochastic", "random_restart")

class OutputHelper:

    @staticmethod
    def algorithmSubdir(algorithm: str) -> Path:
        # Varian Hill-Climbing dikelompokkan di bawah hill_climbing/, algoritma lain langsung per nama.
        if algorithm in HILL_CLIMBING_VARIANTS:
            return Path("hill_climbing") / algorithm
        return Path(algorithm)

    @staticmethod
    def resultDir(algorithm: str) -> Path:
        return OUTPUT_DIR / OutputHelper.algorithmSubdir(algorithm)

    @staticmethod
    def visualizationDir(algorithm: str) -> Path:
        return VISUALIZATION_DIR / OutputHelper.algorithmSubdir(algorithm)
