# Format:
# jumlah_paket 
# (id width depth height [x y z] value weight isFragile eta)
# ...
# [id] widthPeti depthPeti heightPeti maxCapacity     <- satu baris per truk, minimal satu
#
# Multi-truk: tulis satu baris truk per truk (id opsional, default T1, T2, ...).
# Setiap truk punya dimensi dan kapasitas sendiri.

import copy
from core.entity import Package, Truck
from util.fileHelper import FileHelper

class Parser:

    @staticmethod
    def parse(path: str, n_trucks: int | None = None) -> tuple[list[Package], list[Truck]]:
        lines = FileHelper.readAllLines(path)
        idx = 0

        n_paket = int(lines[idx])
        idx += 1

        # Terima input setiap package
        packages = []
        for i in range(n_paket):
            parts = lines[idx].split()
            if len(parts) == 11:
                id = parts[0]
                dim = (int(parts[1]), int(parts[2]), int(parts[3]))
                orientation = (parts[4], parts[5], parts[6])
                value = int(parts[7])
                weight = float(parts[8])
                isFragile = bool(int(parts[9]))
                eta = int(parts[10])

            elif len(parts) == 8:
                id = parts[0]
                dim = (int(parts[1]), int(parts[2]), int(parts[3]))
                orientation = ("x", "y", "z")
                value = int(parts[4])
                weight = float(parts[5])
                isFragile = bool(int(parts[6]))
                eta = int(parts[7])

            else:
                raise ValueError(
                    f"Format package tidak valid: {lines[idx]}"
                )
            
            package = Package(
                id,
                dim,
                orientation,
                value,
                weight,
                isFragile,
                eta
            )

            packages.append(package)
            idx += 1

        # Truck: setiap sisa baris adalah satu truk
        trucks = []
        for line in lines[idx:]:
            parts = line.split()

            if len(parts) == 4:
                truck_id = f"T{len(trucks) + 1}"
            elif len(parts) == 5:
                truck_id, parts = parts[0], parts[1:]
            else:
                raise ValueError(f"Format truck tidak valid: {line}")

            dimPeti = (int(parts[0]), int(parts[1]), int(parts[2]))
            maxCapacity = float(parts[3])
            trucks.append(Truck(dimPeti, maxCapacity, truck_id))

        if not trucks:
            raise ValueError("Input harus memuat minimal satu truk.")

        trucks = Parser._apply_truck_count(trucks, n_trucks)

        return packages, trucks

    @staticmethod
    def _apply_truck_count(trucks: list[Truck], n_trucks: int | None) -> list[Truck]:
        if n_trucks is None or n_trucks == len(trucks):
            return trucks
        if n_trucks < 1:
            raise ValueError("Jumlah truk minimal 1.")
        if len(trucks) != 1:
            raise ValueError(
                f"File mendefinisikan {len(trucks)} truk, tetapi diminta {n_trucks}. "
                "Gandakan truk hanya jika file memuat tepat satu truk."
            )

        template = trucks[0]
        return [
            Truck(template.dimPeti, template.maxCapacity, f"T{i + 1}")
            for i in range(n_trucks)
        ]