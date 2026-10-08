from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any

from algorithm.hill_climbing.result import HillClimbingResult


@dataclass
class SimulatedAnnealingResult(HillClimbingResult):
    probability_history: list[float] = field(default_factory=list)
    temperature_history: list[float] = field(default_factory=list)
    stuck_count: int = 0

    def to_dict(self, include_states: bool = True) -> dict[str, Any]:
        data = super().to_dict(include_states=include_states)
        data["probability_history"] = self.probability_history
        data["temperature_history"] = self.temperature_history
        data["stuck_count"] = self.stuck_count
        return data