import random


class StateHelper:
    @staticmethod
    def isOverlap1D(start1, end1, start2, end2) -> bool:
        return start1 < end2 and start2 < end1
    
    @staticmethod
    def randomize(dimPaket, dimPeti):
            w, d, h = dimPaket
            wp, dp, hp = dimPeti
    
            return(
                random.randint(0, wp + w),
                random.randint(0, dp + d),
                random.randint(0, hp + h)
        )