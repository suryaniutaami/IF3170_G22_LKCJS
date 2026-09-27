class Package:
    def __init__(self, id:str, dim: tuple[int, int, int], orientation:  tuple[str, str, str], value: int, weight:float, isFragile: bool, eta: int):
        self.id = id
        self.dim = dim  #(w, d, h) = (3, 4, 1}
        self.orientation = orientation  #(w, d, h) = ("x", "y", "z"}
        self.value = value
        self.weight = weight
        self.isFragile = isFragile
        self.eta = eta

class Truck:
    def __init__(self, dim: tuple[int, int, int], maxCapacity: float):
        self.dimPeti = dim  #(w, d, h) = (3, 4, 1}
        self.maxCapacity = maxCapacity

    