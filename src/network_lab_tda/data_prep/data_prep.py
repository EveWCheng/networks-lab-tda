import numpy as np

class Data_Prep:
    def __init__(self,filepath=None,matrix=None):
        if filepath == None and matrix == None:
            raise ValueError("You need to pass either a distance matrix or a filepath")
        elif matrix == None:
            self.matrix = np.loadtxt(filepath)
        else:
            self.matrix = matrix



