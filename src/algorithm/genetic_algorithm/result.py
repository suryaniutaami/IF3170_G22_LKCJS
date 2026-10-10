from dataclasses import dataclass, field
from typing import Any
from algorithm.hill_climbing.result import HillClimbingResult

@dataclass
class GeneticAlgorithmResult(HillClimbingResult):
    average_value_history: list[float] = field(default_factory=list)

    def to_dict(self, include_states: bool = True) -> dict[str, Any]:
        data = super().to_dict(include_states=include_states)
        
        data["average_value_history"] = self.average_value_history
        return data