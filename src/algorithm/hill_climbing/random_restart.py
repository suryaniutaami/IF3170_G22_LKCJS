from __future__ import annotations
from time import perf_counter
from core.state import State
from .base import HillClimbingBase
from .result import HillClimbingResult
from .steepest_ascent import SteepestAscentHillClimbing

class RandomRestartHillClimbing(HillClimbingBase):
    """
    Random-Restart Hill-Climbing.
    Satu pencarian Steepest-Ascent dijalankan dari initial state yang diberikan.
    Setelah itu algoritma membuat initial state random baru dan mengulang
    Steepest-Ascent sampai `max_restarts` tercapai. Hasil terbaik dari seluruh restart dikembalikan.
    `max_restarts` berarti banyak RESTART setelah run pertama, sehingga total
    run maksimum adalah `max_restarts + 1`.
    """

    def __init__(
        self,
        max_restarts: int = 10,
        target_value: int | None = None,
        seed: int | None = None,
    ):
        super().__init__(seed=seed)

        if max_restarts < 0:
            raise ValueError("max_restarts tidak boleh negatif.")

        self.max_restarts = max_restarts
        self.target_value = target_value

    def _run_steepest(self, state: State) -> HillClimbingResult:
        #Seed berbeda per run tetapi tetap reproducible dari seed utama.
        child_seed = self.rng.randrange(0, 2**32)
        return SteepestAscentHillClimbing(seed=child_seed).run(state)

    def run(self, initial_state: State) -> HillClimbingResult:
        start_time = perf_counter()

        first_initial = self._clone(initial_state)
        run_results: list[HillClimbingResult] = []
        restart_histories: list[list[int]] = []
        iterations_per_restart: list[int] = []

        current_initial = self._clone(initial_state)
        actual_restarts = 0
        stop_reason = "max_restarts_reached"

        for run_index in range(self.max_restarts + 1):
            run_result = self._run_steepest(current_initial)
            run_results.append(run_result)
            restart_histories.append(run_result.value_history)
            iterations_per_restart.append(run_result.iterations)

            if (
                self.target_value is not None
                and run_result.final_value >= self.target_value
            ):
                stop_reason = "target_value_reached"
                break

            if run_index == self.max_restarts:
                break

            current_initial = self._random_initial_state(initial_state)
            actual_restarts += 1

        best_index = max(
            range(len(run_results)),
            key=lambda index: run_results[index].final_value,
        )
        best = run_results[best_index]
        """
        Untuk plot keseluruhan proses, setiap restart ditambahkan berurutan.
        Titik awal dari setiap restart tetap disertakan agar reset terlihat.
        """
        combined_history: list[int] = []
        for history in restart_histories:
            combined_history.extend(history)

        total_iterations = sum(iterations_per_restart)
        total_accepted_moves = sum(
            result.accepted_moves for result in run_results
        )

        return HillClimbingResult(
            algorithm="random_restart",
            initial_state=first_initial,
            final_state=self._clone(best.final_state),
            iterations=total_iterations,
            accepted_moves=total_accepted_moves,
            value_history=combined_history,
            duration_seconds=perf_counter() - start_time,
            stop_reason=stop_reason,
            parameters={
                "max_restarts": self.max_restarts,
                "target_value": self.target_value,
                "seed": self.seed,
            },
            metadata={
                "restarts": actual_restarts,
                "runs": len(run_results),
                "best_restart_index": best_index,
                "iterations_per_restart": iterations_per_restart,
                "restart_histories": restart_histories,
                "final_values_per_restart": [
                    result.final_value for result in run_results
                ],
            },
        )