from __future__ import annotations
from dataclasses import dataclass
from core.state import State

@dataclass(frozen=True)
class TruckSummary:
    id: str
    value: int
    count: int
    weight: float
    capacity: float
    origin_x: int
    dimensions: tuple[int, int, int]

@dataclass(frozen=True)
class StateSummary:
    value: int
    inside: int
    outside: int
    weight: float
    capacity: float
    trucks: tuple[TruckSummary, ...] = ()

def summarize_state(state: State) -> StateSummary:
    inside_packages = [p for p in state.packages if state.isInsidePeti(p)]

    trucks = []
    for index, truck in enumerate(state.trucks):
        packages = state.getTruckPackages(index)
        trucks.append(
            TruckSummary(
                id=truck.id,
                value=sum(p.value for p in packages),
                count=len(packages),
                weight=sum(p.weight for p in packages),
                capacity=truck.maxCapacity,
                origin_x=state.truckOrigin(index)[0],
                dimensions=truck.dimPeti,
            )
        )

    return StateSummary(
        value=state.getValue(),
        inside=len(inside_packages),
        outside=len(state.packages) - len(inside_packages),
        weight=sum(p.weight for p in inside_packages),
        # Kapasitas total armada (untuk satu truk = MaxCapacity truk itu).
        capacity=sum(t.maxCapacity for t in state.trucks),
        trucks=tuple(trucks),
    )

def format_summary(summary: StateSummary) -> str:
    if len(summary.trucks) > 1:
        used = sum(1 for truck in summary.trucks if truck.count > 0)
        return (
            f"Objective Value: {summary.value} | "
            f"Inside: {summary.inside} | Outside: {summary.outside} | "
            f"Trucks used: {used}/{len(summary.trucks)}"
        )

    return (
        f"Objective Value: {summary.value} | "
        f"Inside: {summary.inside} | Outside: {summary.outside} | "
        f"Weight: {summary.weight:g}/{summary.capacity:g}"
    )