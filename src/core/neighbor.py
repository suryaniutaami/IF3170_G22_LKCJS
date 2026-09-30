import copy
from core.state import State

class Neighbor:
    """
    Operasi neighbor untuk local search.
    Setiap operasi membuat deep copy state asal, menerapkan satu move,
    lalu memvalidasi hasil dengan State.isValid().
    """

    @staticmethod
    def clone(state: State) -> State:
        return copy.deepcopy(state)

    @staticmethod
    def _get_package(state: State, package_id: str):
        for package in state.packages:
            if package.id == package_id:
                return package
        raise ValueError(f"Package dengan id '{package_id}' tidak ditemukan.")

    @staticmethod
    def swap(state: State, package1_id: str, package2_id: str):
        #Menukar posisi dua package.
        if package1_id == package2_id:
            return None

        if package1_id not in state.positions:
            raise ValueError(f"Posisi package '{package1_id}' tidak ditemukan.")
        if package2_id not in state.positions:
            raise ValueError(f"Posisi package '{package2_id}' tidak ditemukan.")

        neighbor = Neighbor.clone(state)

        pos1 = neighbor.positions[package1_id]
        pos2 = neighbor.positions[package2_id]

        neighbor.positions[package1_id] = pos2
        neighbor.positions[package2_id] = pos1

        return neighbor if neighbor.isValid() else None

    @staticmethod
    def move(
        state: State,
        package_id: str,
        new_position: tuple[int, int, int]
    ):
        #Memindahkan satu package ke koordinat integer yang berbeda.
        if package_id not in state.positions:
            raise ValueError(f"Posisi package '{package_id}' tidak ditemukan.")

        if (
            not isinstance(new_position, tuple)
            or len(new_position) != 3
            or not all(isinstance(value, int) for value in new_position)
        ):
            raise ValueError("new_position harus berupa tuple[int, int, int].")

        if state.positions[package_id] == new_position:
            return None

        neighbor = Neighbor.clone(state)
        neighbor.positions[package_id] = new_position

        return neighbor if neighbor.isValid() else None

    @staticmethod
    def _rotate_orientation(
        orientation: tuple[str, str, str],
        axis: str
    ) -> tuple[str, str, str]:
        """
        Rotasi 90 derajat:
        x -> y <-> z
        y -> x <-> z
        z -> x <-> y
        Representasi orientation tidak menyimpan arah positif/negatif,
        jadi rotasi cukup direpresentasikan sebagai pertukaran sumbu.
        """
        axis = axis.lower()

        axis_mapping = {
            "x": {"x": "x", "y": "z", "z": "y"},
            "y": {"x": "z", "y": "y", "z": "x"},
            "z": {"x": "y", "y": "x", "z": "z"},
        }

        if axis not in axis_mapping:
            raise ValueError("Axis rotasi harus 'x', 'y', atau 'z'.")

        mapping = axis_mapping[axis]

        try:
            return tuple(mapping[current_axis] for current_axis in orientation)
        except KeyError as exc:
            raise ValueError(f"Orientation tidak valid: {orientation}") from exc

    @staticmethod
    def rotate(state: State, package_id: str, axis: str):
        # Merotasi package 90 derajat terhadap sumbu x/y/z. Posisi package dipertahankan.
        neighbor = Neighbor.clone(state)
        package = Neighbor._get_package(neighbor, package_id)

        package.orientation = Neighbor._rotate_orientation(
            package.orientation,
            axis
        )

        return neighbor if neighbor.isValid() else None

    @staticmethod
    def generate_swap_neighbors(state: State) -> list[State]:
        neighbors = []

        for i in range(len(state.packages)):
            for j in range(i + 1, len(state.packages)):
                p1 = state.packages[i]
                p2 = state.packages[j]

                candidate = Neighbor.swap(state, p1.id, p2.id)
                if candidate is not None:
                    neighbors.append(candidate)

        return neighbors

    @staticmethod
    def generate_rotation_neighbors(state: State) -> list[State]:
        neighbors = []

        for package in state.packages:
            for axis in ("x", "y", "z"):
                candidate = Neighbor.rotate(state, package.id, axis)
                if candidate is not None:
                    neighbors.append(candidate)

        return neighbors

    @staticmethod
    def generate_move_neighbors(state: State) -> list[State]:
        """
        Menghasilkan seluruh valid neighbor dari operasi pindah koordinat.
        Batas koordinat mengikuti StateHelper.randomize() saat ini:
        x = 0 .. truck_width  + package_width
        y = 0 .. truck_depth  + package_depth
        z = 0 .. truck_height + package_height
        Catatan: fungsi ini bisa menghasilkan kandidat sangat banyak.
        """
        neighbors = []

        truck_w, truck_d, truck_h = state.truck.dimPeti

        for package in state.packages:
            package_w, package_d, package_h = state.getDimOri(package)
            current_position = state.getPosition(package)

            max_x = truck_w + package_w
            max_y = truck_d + package_d
            max_z = truck_h + package_h

            for x in range(max_x + 1):
                for y in range(max_y + 1):
                    for z in range(max_z + 1):
                        new_position = (x, y, z)

                        if new_position == current_position:
                            continue

                        candidate = Neighbor.move(
                            state,
                            package.id,
                            new_position
                        )

                        if candidate is not None:
                            neighbors.append(candidate)

        return neighbors

    @staticmethod
    def generate_all(state: State) -> list[State]:
        #Gabungan valid neighbor dari swap, move, dan rotate.
        neighbors = []
        neighbors.extend(Neighbor.generate_swap_neighbors(state))
        neighbors.extend(Neighbor.generate_move_neighbors(state))
        neighbors.extend(Neighbor.generate_rotation_neighbors(state))
        return neighbors