import numpy as np
import os

class Data_Prep:
    def __init__(self,filepath=None,matrix=None,G=None,log_path=None):
        if (filepath is None and matrix is None and G is None):
            print("You need to pass either a distance matrix or a filepath or a networkx object")
        elif filepath is not None:
            self.matrix = np.loadtxt(filepath)
        elif matrix is not None:
            self.matrix = matrix
        else:
            self.G = G

        self.log_path = log_path or os.path.join(os.getcwd(), "outputs")
        os.makedirs(os.path.dirname(self.log_path), exist_ok=True)




