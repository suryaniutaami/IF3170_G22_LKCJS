from __future__ import annotations
from time import perf_counter
from core.state import State
from .base import HillClimbingBase
from .result import HillClimbingResult

class SidewaysMoveHillClimbing(HillClimbingBase):
    """
    Hill-Climbing with Sideways Move.
    Neighbor dengan nilai sama diperbolehkan untuk melewati plateau/shoulder,
    tetapi hanya sampai `max_sideways` perpindahan sama-nilai berturut-turut.
    Ketika ditemukan perbaikan, counter sideways berturut-turut di-reset.
    """

    # Default batas sideways mengikuti contoh 8-queens pada salindia kuliah (limit 100).
    DEFAULT_MAX_SIDEWAYS = 100

    def __init__(self, max_sideways: int = DEFAULT_MAX_SIDEWAYS, seed: int | None = None):
        super().__init__(seed=seed)
        if max_sideways < 0:
            raise ValueError("max_sideways tidak boleh negatif.")
        self.max_sideways = max_sideways

    def run(self, initial_state: State) -> HillClimbingResult:
        start_time = perf_counter()

        initial = self._clone(initial_state)
        current = self._clone(initial_state)

        iterations = 0
        accepted_moves = 0
        total_sideways_moves = 0
        consecutive_sideways = 0
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

            if best_value < current_value:
                stop_reason = "local_optimum"
                value_history.append(current_value)
                break

            if best_value == current_value:
                if consecutive_sideways >= self.max_sideways:
                    stop_reason = "max_sideways_reached"
                    value_history.append(current_value)
                    break

                current = best
                consecutive_sideways += 1
                total_sideways_moves += 1
                accepted_moves += 1
                value_history.append(current.getValue())
                continue

            #best_value > current_value
            current = best
            consecutive_sideways = 0
            accepted_moves += 1
            value_history.append(current.getValue())

        return HillClimbingResult(
            algorithm="sideways_move",
            initial_state=initial,
            final_state=self._clone(current),
            iterations=iterations,
            accepted_moves=accepted_moves,
            value_history=value_history,
            duration_seconds=perf_counter() - start_time,
            stop_reason=stop_reason,
            parameters={
                "max_sideways": self.max_sideways,
                "seed": self.seed,
            },
            metadata={
                "sideways_moves": total_sideways_moves,
                "final_consecutive_sideways": consecutive_sideways,
            },
        )