import numpy as np
import pandas as pd
import networkx as nx
import os



class Data_Prep:
    def __init__(self,filepath=None,matrix=None,G=None,log_path=None,headers=False,header_fn="header.txt"):
        self.log_path = log_path or os.path.join(os.getcwd(), "outputs")
        os.makedirs(self.log_path, exist_ok=True)
 
        if (filepath is None and matrix is None and G is None):
            print("You need to pass either a distance matrix or a filepath or a networkx object")
        elif filepath is not None:
            if headers:
                df = pd.read_csv(filepath, sep=None, engine="python", header=0, index_col=0)
                self.df = df
                self.matrix = df.to_numpy(dtype=float)
                headers_list = df.columns.tolist()
                with open(os.path.join(self.log_path, header_fn), "w") as f:
                    f.write("\n".join(headers_list))
 
            else:
                self.matrix = np.loadtxt(filepath)
        elif matrix is not None:
            self.matrix = matrix
        else:
            self.G = G
        self.headers = headers
        if G is None:
            n = self.matrix.shape[0]
            self.G = nx.Graph()
            self.G.add_nodes_from(range(n))
            for i in range(n):
                for j in range(i + 1, n):
                    if self.matrix[i,j]>0:
                        self.G.add_edge(i, j, length=self.matrix[i, j])




