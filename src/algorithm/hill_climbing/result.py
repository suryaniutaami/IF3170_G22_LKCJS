from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any
from core.state import State

def snapshot_state(state: State) -> dict[str, Any]:
    #Mengubah State menjadi struktur sederhana yang siap diserialisasi.
    packages = []
    for package in state.packages:
        packages.append(
            {
                "id": package.id,
                "position": list(state.positions[package.id]),
                "orientation": list(package.orientation),
                "oriented_dimensions": list(state.getDimOri(package)),
                "value": package.value,
                "weight": package.weight,
                "is_fragile": package.isFragile,
                "eta": package.eta,
                "inside_truck": state.isInsidePeti(package),
            }
        )

    return {
        "value": state.getValue(),
        "valid": state.isValid(),
        "truck": {
            "dimensions": list(state.truck.dimPeti),
            "max_capacity": state.truck.maxCapacity,
        },
        "packages": packages,
    }


@dataclass
class HillClimbingResult:
    #Format hasil yang seragam untuk seluruh varian Hill-Climbing.

    algorithm: str
    initial_state: State
    final_state: State
    iterations: int
    accepted_moves: int
    value_history: list[int]
    duration_seconds: float
    stop_reason: str
    parameters: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def initial_value(self) -> int:
        return self.initial_state.getValue()

    @property
    def final_value(self) -> int:
        return self.final_state.getValue()

    def to_dict(self, include_states: bool = True) -> dict[str, Any]:
        #Representasi dictionary untuk log/JSON eksperimen berikutnya.
        data: dict[str, Any] = {
            "algorithm": self.algorithm,
            "initial_value": self.initial_value,
            "final_value": self.final_value,
            "iterations": self.iterations,
            "accepted_moves": self.accepted_moves,
            "value_history": self.value_history,
            "duration_seconds": self.duration_seconds,
            "stop_reason": self.stop_reason,
            "parameters": self.parameters,
            "metadata": self.metadata,
        }

        if include_states:
            data["initial_state"] = snapshot_state(self.initial_state)
            data["final_state"] = snapshot_state(self.final_state)

        return data