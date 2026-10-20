from __future__ import annotations
import copy
import math
import random
from time import perf_counter

from core.neighbor import Neighbor
from core.state import State
from .result import SimulatedAnnealingResult


class SimulatedAnnealing:
    def __init__(
        self,
        initial_temperature: float = 100.0,
        cooling_rate: float = 0.999,
        min_temperature: float = 1e-3,
        max_iterations: int = 5000,
        max_neighbor_attempts: int = 100,
        stuck_threshold: int = 20,
        seed: int | None = None,
    ):
        if initial_temperature <= 0:
            raise ValueError("initial_temperature harus lebih dari 0.")
        if not 0 < cooling_rate < 1:
            raise ValueError("cooling_rate harus berada di antara 0 dan 1 (eksklusif).")
        if min_temperature <= 0 or min_temperature >= initial_temperature:
            raise ValueError("min_temperature harus > 0 dan < initial_temperature.")
        if max_iterations <= 0:
            raise ValueError("max_iterations harus lebih dari 0.")
        if max_neighbor_attempts <= 0:
            raise ValueError("max_neighbor_attempts harus lebih dari 0.")
        if stuck_threshold <= 0:
            raise ValueError("stuck_threshold harus lebih dari 0.")

        self.initial_temperature = initial_temperature
        self.cooling_rate = cooling_rate
        self.min_temperature = min_temperature
        self.max_iterations = max_iterations
        self.max_neighbor_attempts = max_neighbor_attempts
        self.stuck_threshold = stuck_threshold
        self.seed = seed
        self.rng = random.Random(seed)

    @staticmethod
    def _clone(state: State) -> State:
        return copy.deepcopy(state)

    @staticmethod
    def _acceptance_probability(delta: int, temperature: float) -> float:
        """e^(ΔE/T), di-cap ke 1.0 (ΔE > 0 selalu diterima)."""
        if delta >= 0:
            return 1.0
        return math.exp(delta / temperature)

    def run(self, initial_state: State) -> SimulatedAnnealingResult:
        start_time = perf_counter()

        initial = self._clone(initial_state)
        current = self._clone(initial_state)
        current_value = current.getValue()
        best_value = current_value

        temperature = self.initial_temperature
        iterations = 0
        accepted_moves = 0
        improving_moves = 0
        worse_moves_accepted = 0   # "escape" dari local optima
        rejected_moves = 0
        unchanged_streak = 0
        stuck_count = 0
        stop_reason = "max_iterations_reached"

        value_history = [current_value]
        probability_history: list[float] = []
        temperature_history: list[float] = []

        while iterations < self.max_iterations:
            if temperature <= self.min_temperature:
                stop_reason = "min_temperature_reached"
                break

            iterations += 1

            candidate = Neighbor.random_neighbor(
                current,
                rng=self.rng,
                max_attempts=self.max_neighbor_attempts,
            )

            if candidate is None:
                stop_reason = "no_valid_neighbor"
                iterations -= 1
                break

            candidate_value = candidate.getValue()
            delta = candidate_value - current_value
            probability = self._acceptance_probability(delta, temperature)

            probability_history.append(probability)
            temperature_history.append(temperature)

            if delta > 0 or self.rng.random() < probability:
                current = candidate
                current_value = candidate_value
                accepted_moves += 1
                if delta != 0:
                    unchanged_streak = 0
                else:
                    unchanged_streak += 1
                    if unchanged_streak == self.stuck_threshold:
                        stuck_count += 1
                if delta > 0:
                    improving_moves += 1
                elif delta < 0:
                    worse_moves_accepted += 1
                best_value = max(best_value, current_value)
            else:
                rejected_moves += 1
                unchanged_streak += 1
                if unchanged_streak == self.stuck_threshold:
                    stuck_count += 1

            value_history.append(current_value)
            temperature *= self.cooling_rate

        return SimulatedAnnealingResult(
            algorithm="simulated_annealing",
            initial_state=initial,
            final_state=self._clone(current),
            iterations=iterations,
            accepted_moves=accepted_moves,
            value_history=value_history,
            duration_seconds=perf_counter() - start_time,
            stop_reason=stop_reason,
            parameters={
                "initial_temperature": self.initial_temperature,
                "cooling_rate": self.cooling_rate,
                "min_temperature": self.min_temperature,
                "max_iterations": self.max_iterations,
                "max_neighbor_attempts": self.max_neighbor_attempts,
                "stuck_threshold": self.stuck_threshold,
                "seed": self.seed,
            },
            metadata={
                "improving_moves": improving_moves,
                "worse_moves_accepted": worse_moves_accepted,
                "rejected_moves": rejected_moves,
                "best_value_seen": best_value,
                "final_temperature": temperature,
            },
            probability_history=probability_history,
            temperature_history=temperature_history,
            stuck_count=stuck_count,
        )