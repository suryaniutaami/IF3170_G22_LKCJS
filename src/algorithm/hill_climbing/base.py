from __future__ import annotations
import copy
import random
from typing import Iterable
from core.neighbor import Neighbor
from core.state import State

class HillClimbingBase:
    #Helper bersama untuk seluruh varian Hill-Climbing.

    def __init__(self, seed: int | None = None):
        self.seed = seed
        self.rng = random.Random(seed)

    @staticmethod
    def _clone(state: State) -> State:
        return copy.deepcopy(state)

    def _best_neighbor(self, state: State) -> State | None:
        """
        Mengambil successor dengan objective value tertinggi.
        Jika terdapat beberapa successor terbaik dengan nilai sama, salah satu
        dipilih secara random sesuai materi local search.
        """
        best_value: int | None = None
        best_states: list[State] = []

        for neighbor in Neighbor.iter_all(state):
            value = neighbor.getValue()

            if best_value is None or value > best_value:
                best_value = value
                best_states = [neighbor]
            elif value == best_value:
                best_states.append(neighbor)

        if not best_states:
            return None

        return self.rng.choice(best_states)

    def _random_initial_state(self, template: State) -> State:
        """
        Membuat initial state random baru untuk Random-Restart HC.
        Posisi state baru memakai RNG algoritma agar urutan hasil tetap seedable.
        """
        return State(
            copy.deepcopy(template.packages),
            copy.deepcopy(template.trucks),
            self.rng,
        )

    @staticmethod
    def _best_result(results: Iterable):
        return max(results, key=lambda result: result.final_value)