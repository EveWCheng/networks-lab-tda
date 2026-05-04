import os
import json
import gudhi


class Rips:
    def __init__(self, distance_mat, max_dimension, log_path=None):
        self.D = distance_mat
        self.max_dimension = max_dimension
        self.log = {}
        self.log_path = log_path or os.path.join(os.getcwd(), "rips_log.json")

    def save_log(self):
        with open(self.log_path, "w") as f:
            json.dump(self.log, f, indent=2)

    def rips_filtration(self, threshold=float('inf'), log=False):
        rips = gudhi.RipsComplex(distance_matrix=self.D, max_edge_length=threshold)
        st = rips.create_simplex_tree(max_dimension=self.max_dimension)
        filtration = sorted(st.get_filtration(), key=lambda x: x[1])
        simplices = [list(s) for s, _ in filtration]
        births = [b for _, b in filtration]
        if log:
            self.log["simplices"] = simplices
            self.log["appears_at"] = births
        return simplices, births
