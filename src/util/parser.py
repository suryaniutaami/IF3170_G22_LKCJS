# Format:
# jumlah_paket 
# (id width depth height [x y z] value weight isFragile eta)
# ...
# widthPeti depthPeti heightPeti maxCapacity

from core.entity import Package, Truck
from util.fileHelper import FileHelper

class Parser:

    @staticmethod
    def parse(path: str) -> tuple[list[Package], Truck]:
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

        # Truck
        parts = lines[idx].split()

        dimPeti = (int(parts[0]), int(parts[1]), int(parts[2]))
        maxCapacity = float(parts[3])

        truck = Truck(dimPeti, maxCapacity)

        return packages, truck