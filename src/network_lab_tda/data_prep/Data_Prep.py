import numpy as np
import os

class Data_Prep:
    def __init__(self,filepath=None,matrix=None,log_path=None):
        if filepath == None and matrix == None:
            raise ValueError("You need to pass either a distance matrix or a filepath")
        elif matrix == None:
            self.matrix = np.loadtxt(filepath)
        else:
            self.matrix = matrix

        self.log_path = log_path or os.path.join(os.getcwd(), "outputs")
        os.makedirs(os.path.dirname(self.log_path), exist_ok=True)




