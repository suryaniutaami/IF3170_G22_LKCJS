import copy
import random
from collections.abc import Iterator
from core.state import State

class Neighbor:
    """
    Operasi neighbor untuk local search.
    Setiap operasi membuat deep copy dari state asal, menerapkan tepat satu
    perubahan, lalu memvalidasi hasil dengan State.isValid(). State asal tidak
    pernah dimodifikasi.
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
        #Menukar posisi dua package dan mengembalikan state valid baru.
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
        Rotasi 90 derajat berdasarkan representasi orientation saat ini.
        Karena orientation hanya menyimpan sumbu yang sejajar dengan tiap sisi
        package (tanpa arah positif/negatif), rotasi direpresentasikan sebagai:
        - sumbu x: y <-> z
        - sumbu y: x <-> z
        - sumbu z: x <-> y
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
    def iter_swap_neighbors(state: State) -> Iterator[State]:
        for i in range(len(state.packages)):
            for j in range(i + 1, len(state.packages)):
                candidate = Neighbor.swap(
                    state,
                    state.packages[i].id,
                    state.packages[j].id,
                )
                if candidate is not None:
                    yield candidate

    @staticmethod
    def iter_rotation_neighbors(state: State) -> Iterator[State]:
        for package in state.packages:
            for axis in ("x", "y", "z"):
                candidate = Neighbor.rotate(state, package.id, axis)
                if candidate is not None:
                    yield candidate

    @staticmethod
    def iter_move_neighbors(state: State) -> Iterator[State]:
        """
        Menghasilkan seluruh valid neighbor dari operasi pindah koordinat.
        Batas koordinat mengikuti StateHelper.randomize() saat ini:
        x = 0 .. truck_width  + package_width
        y = 0 .. truck_depth  + package_depth
        z = 0 .. truck_height + package_height
        """
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
                            yield candidate

    @staticmethod
    def iter_all(state: State) -> Iterator[State]:
        yield from Neighbor.iter_swap_neighbors(state)
        yield from Neighbor.iter_move_neighbors(state)
        yield from Neighbor.iter_rotation_neighbors(state)

    # Random successor for Stochastic Hill-Climbing

    @staticmethod
    def random_neighbor(
        state: State,
        rng: random.Random | None = None,
        max_attempts: int = 100,
    ):
        """
        Menghasilkan SATU successor valid secara random tanpa membangkitkan
        seluruh successor terlebih dahulu.

        Ini ditujukan untuk Stochastic Hill-Climbing sesuai materi kuliah:
        successor dibangkitkan secara acak, bukan memilih dari seluruh daftar.
        """
        if max_attempts <= 0:
            raise ValueError("max_attempts harus lebih dari 0.")
        if not state.packages:
            return None

        rng = rng or random.Random()
        operations = ["move", "rotate"]
        if len(state.packages) >= 2:
            operations.append("swap")

        truck_w, truck_d, truck_h = state.truck.dimPeti

        for _ in range(max_attempts):
            operation = rng.choice(operations)

            if operation == "swap":
                p1, p2 = rng.sample(state.packages, 2)
                candidate = Neighbor.swap(state, p1.id, p2.id)

            elif operation == "rotate":
                package = rng.choice(state.packages)
                axis = rng.choice(("x", "y", "z"))
                candidate = Neighbor.rotate(state, package.id, axis)

            else:
                package = rng.choice(state.packages)
                package_w, package_d, package_h = state.getDimOri(package)
                new_position = (
                    rng.randint(0, truck_w + package_w),
                    rng.randint(0, truck_d + package_d),
                    rng.randint(0, truck_h + package_h),
                )
                candidate = Neighbor.move(state, package.id, new_position)

            if candidate is not None:
                return candidate

        return None

    # Backward-compatible list generators

    @staticmethod
    def generate_swap_neighbors(state: State) -> list[State]:
        return list(Neighbor.iter_swap_neighbors(state))

    @staticmethod
    def generate_rotation_neighbors(state: State) -> list[State]:
        return list(Neighbor.iter_rotation_neighbors(state))

    @staticmethod
    def generate_move_neighbors(state: State) -> list[State]:
        return list(Neighbor.iter_move_neighbors(state))

    @staticmethod
    def generate_all(state: State) -> list[State]:
        return list(Neighbor.iter_all(state))