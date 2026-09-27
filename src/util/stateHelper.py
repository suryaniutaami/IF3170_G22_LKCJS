import random
from core.entity import Package

class StateHelper:
    def isOverlap1D(start1, end1, start2, end2) -> bool:
        return start1 < end2 and start2 < end1
    
    def randomize(self, p: Package):
            w, d, h = self.getDimOri(p)
            wp, dp, hp = self.truck.dimPeti
    
            return(
                random.randint(0, wp + w),
                random.randint(0, dp + d),
                random.randint(0, hp + h)
        )