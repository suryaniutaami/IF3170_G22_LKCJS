from core.entity import Package, Truck
from util.stateHelper import StateHelper

class State:
    def __init__(self, packages: list[Package], truck: Truck):
        self.packages = packages
        self.truck = truck
        # --- POSISI PETI DAN PAKET ---
        # Asumsi posisi peti kemas = (0,0,0) <- titik pojok kiri-bawah-belakang peti
        
        # Posisi paket random, mapping package.id -> position (x,y,z) <- titik pojok kiri-bawah-belakang paket
        self.positions = {}
        self.random_position()   
    
    # Initial position paket random
    def random_position(self):
        for p in self.packages:
            while True:
                position = StateHelper.randomize(self.getDimOri(p), self.truck.dimPeti)
                # Simpan sementara
                self.positions[p.id] = position
        
                # Cek validitas rando position p terhadap other paket yang udh ditempatkan
                valid = True
                if self.isFloating(p): valid = False
                if not self.isInsidePeti(p) and not self.isOutsidePeti(p): valid = False

                for other in self.packages:
                    if other.id == p.id: continue
                    if other.id not in self.positions: continue
                    if self.isSupport(other, p) and other.isFragile: valid = False
                    # p fragile tidak boleh tepat di bawah paket yang sudah ditempatkan
                    if self.isSupport(p, other) and p.isFragile: valid = False
                    if self.isOverlapping(p, other): valid = False

                if valid and self.isTruckCapacityOverload(): valid = False

                if not(valid):
                    del self.positions[p.id]
                else:
                    break

    # Getter
    def getPosition(self, p: Package):
        return self.positions[p.id]
    def getDimOri(self, p: Package):
        """Mengembalikan (width_x, length_y, height_z)"""
        j = 0
        for i in p.orientation:
            val = p.dim[j]
            if (i=="x"):
                x = val
            elif (i=="y"):
                y = val
            elif (i=="z"):
                z = val

            j+=1
        
        return (x, y, z)

    # Validitas State
    def isValid(self):
        for p1 in self.packages:
            if self.isFloating(p1): return False                          #paket gak napak
            if not(self.isInsidePeti(p1)) and not(self.isOutsidePeti(p1)): return False   #nabrak dinding peti 
            for p2 in self.packages:
                if p1.id == p2.id: continue
                if self.isSupport(p1, p2) and p1.isFragile: return False  #paket fragile jadi support
                if self.isOverlapping(p1, p2): return False               #antar paket nabrak

        if (self.isTruckCapacityOverload()): return False
        
        return True

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

        # Support dari lantai truk
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
    def isInsidePeti(self, p: Package):
        if p.id not in self.positions: return False
        x, y, z = self.positions[p.id]
        w, d, h = self.getDimOri(p)

        wp, dp, hp = self.truck.dimPeti

        return(
            x >= 0 and
            y >= 0 and
            z >= 0 and
            x + w <= wp and
            y + d <= dp and
            z + h <= hp
        )

    def isOutsidePeti(self, p: Package):
        if p.id not in self.positions: return False
        x, y, z = self.getPosition(p)

        wp, dp, hp = self.truck.dimPeti

        return(
            x >= wp or
            y >= dp or
            z >= hp
        )

    def isTruckCapacityOverload(self):
        totalCapacity = 0
        for p in self.packages:
            if not(self.isInsidePeti(p)): continue
            totalCapacity += p.weight
            if (totalCapacity > self.truck.maxCapacity): return True

        return False

    def getValue(self):
        totalValue = 0

        for p in self.packages:
            if self.isInsidePeti(p):
                totalValue += p.value

        return totalValue