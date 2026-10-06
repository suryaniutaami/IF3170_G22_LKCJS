from __future__ import annotations
from dataclasses import dataclass
from core.state import State

@dataclass(frozen=True)
class StateSummary:
    value: int
    inside: int
    outside: int
    weight: float
    capacity: float

def summarize_state(state: State) -> StateSummary:
    inside_packages = [p for p in state.packages if state.isInsidePeti(p)]

    return StateSummary(
        value=state.getValue(),
        inside=len(inside_packages),
        outside=len(state.packages) - len(inside_packages),
        weight=sum(p.weight for p in inside_packages),
        capacity=state.truck.maxCapacity,
    )

def format_summary(summary: StateSummary) -> str:
    return (
        f"Objective Value: {summary.value} | "
        f"Inside: {summary.inside} | Outside: {summary.outside} | "
        f"Weight: {summary.weight:g}/{summary.capacity:g}"
    )