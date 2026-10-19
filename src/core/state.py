import copy
from collections.abc import Sequence
from core.entity import Package, Truck
from core.fleet import Fleet, INVALID, OUTSIDE
from util.stateHelper import StateHelper

_AXIS_INDEX = {"x": 0, "y": 1, "z": 2}


class State:

    def __init__(self, packages: list[Package], trucks: Truck | Sequence[Truck], rng, random: bool = True, positions = None):
        """Inisialisasi state dengan posisi paket acak atau posisi yang diberikan

        `trucks` boleh satu Truck (single-truck) atau daftar Truck (multi-truck).
        Jika random bernilai True, posisi paket dibuat secara acak
        menggunakan rng. Jika False, posisi diambil dari positions"""

        self.packages = packages
        self.trucks = trucks
        self.rng = rng
        self.random = random
        # --- POSISI TRUK, PETI, DAN PAKET ---
        # Seluruh truk berada di satu sistem koordinat global (lihat core/fleet.py):
        # truk ke-i berdampingan sepanjang sumbu x. Asumsi truk pertama berawal di (0,0,0)
        # <- titik pojok kiri-bawah-depan peti.

        # Posisi paket random, mapping package.id -> position (x,y,z) <- titik pojok kiri-bawah-depan paket
        self.positions = {} if positions is None else dict(positions)
        self.random_position()

    # Armada
    @property
    def trucks(self) -> list[Truck]:
        return self._trucks

    @trucks.setter
    def trucks(self, value: Truck | Sequence[Truck]):
        if isinstance(value, Truck):
            value = [value]
        value = list(value)
        for index, truck in enumerate(value):
            if truck.id is None:
                truck.id = f"T{index + 1}"
        self._trucks = value
        self.fleet = Fleet(value)

    @property
    def truck(self) -> Truck:
        """Truk pertama. Dipertahankan agar kode single-truck lama tetap berjalan."""
        return self._trucks[0]

    @truck.setter
    def truck(self, value: Truck):
        self.trucks = value

    @property
    def extent(self) -> tuple[int, int, int]:
        """Bounding box seluruh armada (dipakai untuk membangkitkan koordinat acak)."""
        return self.fleet.extent

    def truckOrigin(self, truck_index: int) -> tuple[int, int, int]:
        """Origin global truk; konsumen tidak perlu mengakses implementasi Fleet."""
        return self.fleet.origins[truck_index]

    def truckBounds(self, truck_index: int) -> tuple[int, int, int, int, int, int]:
        """Batas global truk sebagai (x0, y0, z0, x1, y1, z1)."""
        return self.fleet.boxes[truck_index]

    def truckBoundsList(self) -> list[tuple[int, int, int, int, int, int]]:
        """Batas seluruh truk, untuk rendering dan ringkasan."""
        return list(self.fleet.boxes)

    def __deepcopy__(self, memo):
        clone = self.__class__.__new__(self.__class__)
        clone.__dict__.update(self.__dict__)
        clone.packages = [copy.copy(p) for p in self.packages]
        clone.positions = dict(self.positions)
        memo[id(self)] = clone
        return clone

    # Initial position paket random
    def random_position(self):
        if self.random == True:
            for p in self.packages:
                while True:
                    position = StateHelper.randomize(self.getDimOri(p), self.extent, self.rng)
                    if self.isValidPlacement(p, position, self.positions, self.packages, self.trucks, self.rng):
                        break

    # Getter
    def getPosition(self, p: Package):
        return self.positions[p.id]
    def getDimOri(self, p: Package):
        """Mengembalikan (width_x, length_y, height_z)"""
        out = [0, 0, 0]
        for axis, size in zip(p.orientation, p.dim):
            out[_AXIS_INDEX[axis]] = size
        return (out[0], out[1], out[2])

    # Validitas State
    def isValid(self):
        # Setiap paket diperiksa terhadap: dinding truk, penyangga (floating / fragile), dan tabrakan dengan paket lain. Balok dihitung sekali agar cepat.
        items = []
        for p in self.packages:
            x, y, z = self.positions[p.id]
            w, d, h = self.getDimOri(p)
            items.append((p, x, y, z, w, d, h))

        for p, x, y, z, w, d, h in items:
            if self.fleet.locate((x, y, z), (w, d, h)) == INVALID: return False   #nabrak dinding peti

            supported = (z == 0)    #alas truk / lantai
            for q, qx, qy, qz, qw, qd, qh in items:
                if q is p: continue
                if not (x < qx + qw and qx < x + w and y < qy + qd and qy < y + d): continue

                if z < qz + qh and qz < z + h: return False       #antar paket nabrak
                if qz + qh == z:
                    if q.isFragile: return False                  #paket fragile jadi support
                    supported = True

            if not supported: return False                        #paket gak napak

        if (self.isTruckCapacityOverload()): return False

        return True

    def otherBoxes(self, p: Package) -> list:
        boxes = []
        for q in self.packages:
            if q.id == p.id: continue
            qpos = self.positions.get(q.id)
            if qpos is None: continue
            qw, qd, qh = self.getDimOri(q)
            boxes.append((q, qpos[0], qpos[1], qpos[2], qw, qd, qh))
        return boxes

    def canPlace(self, p: Package, position, others: list | None = None) -> bool:
        x, y, z = position
        w, d, h = self.getDimOri(p)

        if self.fleet.locate(position, (w, d, h)) == INVALID: return False
        if others is None: others = self.otherBoxes(p)

        supported = (z == 0)
        for q, qx, qy, qz, qw, qd, qh in others:
            if not (x < qx + qw and qx < x + w and y < qy + qd and qy < y + d): continue

            if z < qz + qh and qz < z + h: return False           #nabrak
            if qz + qh == z:
                if q.isFragile: return False                      #q fragile jadi support p
                supported = True
            elif z + h == qz and p.isFragile:
                return False                                      #p fragile jadi support q

        return supported

    @staticmethod
    def isValidPlacement(p: Package, position, positions, packages: list[Package], trucks: Truck | Sequence[Truck], rng) -> bool:
        # Simpan posisi kandidat sementara
        positions[p.id] = position

        # Buat state sementara
        state = State(packages, trucks, rng, False, positions)

        # Cek validitas rando position p terhadap other paket yang udh ditempatkan
        # (tidak ngambang, di dalam/di luar peti, tidak nabrak, fragile bukan support)
        valid = state.canPlace(p, position)

        # Kapasitas tiap truk
        if valid and state.isTruckCapacityOverload():
            valid = False

        if not valid:
            del positions[p.id]
        return valid

    def isSupport(self, p1: Package, p2: Package):
        """p1 berada di bawah p2"""
        w1, d1, h1 = self.getDimOri(p1)
        x1, y1, z1 = self.getPosition(p1)

        w2, d2, h2 = self.getDimOri(p2)
        x2, y2, z2 = self.getPosition(p2)

        if not(z1+h1 == z2): return False
        overlap_x = StateHelper.isOverlap1D(x1, x1+w1, x2, x2+w2)
        overlap_y = StateHelper.isOverlap1D(y1, y1+d1, y2, y2+d2)

        return (overlap_x and overlap_y)

    def isFloating(self, p: Package):
        """Paket ngambang"""
        x, y, z = self.getPosition(p)

        # Support dari lantai truck
        if z == 0: return False
        # Support dari paket lain
        for p2 in self.packages:
            if p2.id == p.id: continue
            if p2.id not in self.positions: continue
            if self.isSupport(p2, p):
                return False

        return True

    def isOverlapping(self, p1: Package, p2: Package):
        """Paket nabrak paket lain"""
        w1, d1, h1 = self.getDimOri(p1)
        x1, y1, z1 = self.getPosition(p1)

        w2, d2, h2 = self.getDimOri(p2)
        x2, y2, z2 = self.getPosition(p2)

        overlap_x = StateHelper.isOverlap1D(x1, x1+w1, x2, x2+w2)
        overlap_y = StateHelper.isOverlap1D(y1, y1+d1, y2, y2+d2)
        overlap_z = StateHelper.isOverlap1D(z1, z1+h1, z2, z2+h2)

        return (overlap_x and overlap_y and overlap_z)

    # Hubungan paket <-> peti
    def locate(self, p: Package) -> int:
        """Indeks truk yang memuat p, Fleet OUTSIDE (-1), atau INVALID (-2)."""
        if p.id not in self.positions: return INVALID
        return self.fleet.locate(self.positions[p.id], self.getDimOri(p))

    def getTruckIndex(self, p: Package):
        """Indeks truk yang memuat p secara utuh, atau None jika p tidak di dalam truk mana pun."""
        index = self.locate(p)
        return index if index >= 0 else None

    def isInsidePeti(self, p: Package):
        """Paket seluruhnya di dalam salah satu truk."""
        return self.locate(p) >= 0

    def isOutsidePeti(self, p: Package):
        """Seluruh bagian paket di luar semua truk."""
        return self.locate(p) == OUTSIDE

    def localPosition(self, p: Package):
        """Posisi p relatif terhadap origin truk yang memuatnya (None jika di luar)."""
        index = self.getTruckIndex(p)
        if index is None: return None
        ox, oy, oz = self.truckOrigin(index)
        x, y, z = self.getPosition(p)
        return (x - ox, y - oy, z - oz)

    def getTruckPackages(self, truck_index: int) -> list[Package]:
        return [p for p in self.packages if self.getTruckIndex(p) == truck_index]

    def getTruckWeight(self, truck_index: int):
        return sum(p.weight for p in self.getTruckPackages(truck_index))

    def getTruckValue(self, truck_index: int):
        return sum(p.value for p in self.getTruckPackages(truck_index))

    def isTruckCapacityOverload(self):
        """Kapasitas dicek per truk: tiap truk punya MaxCapacity sendiri."""
        loads = [0] * len(self.trucks)
        for p in self.packages:
            index = self.getTruckIndex(p)
            if index is None: continue
            loads[index] += p.weight
            if loads[index] > self.trucks[index].maxCapacity: return True

        return False

    def getValue(self):
        """F.O: Memaksimalkan total value paket dalam peti (seluruh truk di armada)"""
        totalValue = 0

        for p in self.packages:
            if self.isInsidePeti(p):
                totalValue += p.value

        return totalValue

    def getValueWithUrgency(self):
            """F.O: Memaksimalkan total value paket berbobot urgensi dalam peti 

            berdasarkan ETA, dengan skor urgensi 1 / (1 + ETA)"""
            totalValue = 0
    
            for p in self.packages:
                if self.isInsidePeti(p):
                    totalValue += p.value / (1 + p.eta)
    
            return totalValue