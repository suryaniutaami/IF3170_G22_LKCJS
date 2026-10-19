from __future__ import annotations
from collections.abc import Sequence
from core.entity import Truck

TRUCK_GAP = 2

OUTSIDE = -1   # paket di luar truk
INVALID = -2   # paket menembus dinding truk / berada di koordinat negatif


class Fleet:
    def __init__(self, trucks: Sequence[Truck], gap: int = TRUCK_GAP):
        if len(trucks) == 0:
            raise ValueError("Minimal harus ada satu truk.")
        if gap < 0:
            raise ValueError("gap tidak boleh negatif.")

        self.gap = gap
        self.origins: list[tuple[int, int, int]] = []
        self.boxes: list[tuple[int, int, int, int, int, int]] = []

        cursor_x = 0
        for truck in trucks:
            w, d, h = truck.dimPeti
            self.origins.append((cursor_x, 0, 0))
            self.boxes.append((cursor_x, 0, 0, cursor_x + w, d, h))
            cursor_x += w + gap

        self.extent: tuple[int, int, int] = (
            max(box[3] for box in self.boxes),
            max(box[4] for box in self.boxes),
            max(box[5] for box in self.boxes),
        )

    def __len__(self) -> int:
        return len(self.boxes)

    def locate(
        self,
        position: tuple[int, int, int],
        dims: tuple[int, int, int],
    ) -> int:
        """
        Klasifikasi balok paket terhadap armada:
        - k >= 0 : seluruh paket di dalam truk k
        - OUTSIDE: tidak beririsan dengan truk mana pun
        - INVALID: menembus dinding truk, atau memakai koordinat negatif
        """
        x, y, z = position
        w, d, h = dims

        if x < 0 or y < 0 or z < 0:
            return INVALID

        x1, y1, z1 = x + w, y + d, z + h

        for index, (bx0, by0, bz0, bx1, by1, bz1) in enumerate(self.boxes):
            disjoint = (
                x1 <= bx0 or x >= bx1
                or y1 <= by0 or y >= by1
                or z1 <= bz0 or z >= bz1
            )
            if disjoint:
                continue

            if x1 <= bx1 and y1 <= by1 and z1 <= bz1 and x >= bx0 and y >= by0 and z >= bz0:
                return index

            return INVALID

        return OUTSIDE