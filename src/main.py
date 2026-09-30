from util.parser import Parser
from core.state import State
from core.neighbor import Neighbor


packages, truck = Parser.parse("input.txt")
state = State(packages, truck)

print("=== INITIAL STATE ===")
print("Positions:", state.positions)
print("Value:", state.getValue())
print("Valid:", state.isValid())


# Coba move package pertama ke posisi valid lain
package = packages[0]

print("\nPackage yang dicoba dipindah:", package.id)
print("Posisi awal:", state.getPosition(package))

neighbor = None

# Cari satu posisi baru yang valid di dalam peti
truck_w, truck_d, truck_h = truck.dimPeti
package_w, package_d, package_h = state.getDimOri(package)

for x in range(truck_w - package_w + 1):
    for y in range(truck_d - package_d + 1):
        new_position = (x, y, 0)

        if new_position == state.getPosition(package):
            continue

        candidate = Neighbor.move(
            state,
            package.id,
            new_position
        )

        if candidate is not None:
            neighbor = candidate
            break

    if neighbor is not None:
        break


print("\n=== AFTER MOVE ===")

if neighbor is None:
    print("Tidak ditemukan move valid.")
else:
    print("Posisi original:", state.positions)
    print("Posisi neighbor:", neighbor.positions)

    print("Original tetap valid:", state.isValid())
    print("Neighbor valid:", neighbor.isValid())

    print("Original value:", state.getValue())
    print("Neighbor value:", neighbor.getValue())