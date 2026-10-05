from __future__ import annotations
from time import perf_counter
from core.state import State
from .base import HillClimbingBase
from .result import HillClimbingResult

class SteepestAscentHillClimbing(HillClimbingBase):
    """
    Steepest-Ascent Hill-Climbing.
    Pada setiap iterasi, seluruh valid successor dibandingkan dan algoritma
    berpindah ke successor dengan objective value tertinggi. Pencarian berhenti
    ketika tidak terdapat neighbor yang lebih baik dari current state.
    """

    def run(self, initial_state: State) -> HillClimbingResult:
        start_time = perf_counter()

        initial = self._clone(initial_state)
        current = self._clone(initial_state)

        iterations = 0
        accepted_moves = 0
        value_history = [current.getValue()]
        stop_reason = "local_optimum"

        while True:
            iterations += 1
            current_value = current.getValue()
            best = self._best_neighbor(current)

            if best is None:
                stop_reason = "no_valid_neighbor"
                value_history.append(current_value)
                break

            best_value = best.getValue()

            if best_value <= current_value:
                stop_reason = (
                    "flat_local_optimum"
                    if best_value == current_value
                    else "local_optimum"
                )
                value_history.append(current_value)
                break

            current = best
            accepted_moves += 1
            value_history.append(current.getValue())

        return HillClimbingResult(
            algorithm="steepest_ascent",
            initial_state=initial,
            final_state=self._clone(current),
            iterations=iterations,
            accepted_moves=accepted_moves,
            value_history=value_history,
            duration_seconds=perf_counter() - start_time,
            stop_reason=stop_reason,
            parameters={"seed": self.seed},
        )