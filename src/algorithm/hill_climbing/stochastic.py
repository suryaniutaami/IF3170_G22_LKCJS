from __future__ import annotations
from time import perf_counter
from core.neighbor import Neighbor
from core.state import State
from .base import HillClimbingBase
from .result import HillClimbingResult

class StochasticHillClimbing(HillClimbingBase):
    """
    Stochastic Hill-Climbing sesuai materi kuliah.
    Setiap iterasi hanya membangkitkan SATU random successor. Algoritma pindah
    jika successor tersebut lebih baik; successor dengan nilai sama atau lebih
    buruk dilewati. Pencarian berhenti saat `max_iterations` tercapai.
    """

    def __init__(
        self,
        max_iterations: int = 1000,
        max_neighbor_attempts: int = 100,
        seed: int | None = None,
    ):
        super().__init__(seed=seed)

        if max_iterations <= 0:
            raise ValueError("max_iterations harus lebih dari 0.")
        if max_neighbor_attempts <= 0:
            raise ValueError("max_neighbor_attempts harus lebih dari 0.")

        self.max_iterations = max_iterations
        self.max_neighbor_attempts = max_neighbor_attempts

    def run(self, initial_state: State) -> HillClimbingResult:
        start_time = perf_counter()

        initial = self._clone(initial_state)
        current = self._clone(initial_state)

        iterations = 0
        accepted_moves = 0
        rejected_moves = 0
        value_history = [current.getValue()]
        stop_reason = "max_iterations_reached"

        for _ in range(self.max_iterations):
            iterations += 1

            candidate = Neighbor.random_neighbor(
                current,
                rng=self.rng,
                max_attempts=self.max_neighbor_attempts,
            )

            if candidate is None:
                stop_reason = "no_valid_neighbor"
                value_history.append(current.getValue())
                break

            if candidate.getValue() > current.getValue():
                current = candidate
                accepted_moves += 1
            else:
                rejected_moves += 1

            value_history.append(current.getValue())

        return HillClimbingResult(
            algorithm="stochastic",
            initial_state=initial,
            final_state=self._clone(current),
            iterations=iterations,
            accepted_moves=accepted_moves,
            value_history=value_history,
            duration_seconds=perf_counter() - start_time,
            stop_reason=stop_reason,
            parameters={
                "max_iterations": self.max_iterations,
                "max_neighbor_attempts": self.max_neighbor_attempts,
                "seed": self.seed,
            },
            metadata={
                "rejected_moves": rejected_moves,
            },
        )