from pathlib import Path
from .simplicial_pyvis import simplicial_pyvis
import json
import numpy as np

class tda_plot_from_jason:
    def __init__(self,jason_path,threshold,which_cycle="harmonic_cycles",distance_mat=None,neighbour_layers=0,log_path=None):
        self.jason_path = jason_path
        self.threshold = threshold
        self.D = distance_mat
        self.neighbour_layers = neighbour_layers
        self.which_cycle = which_cycle
        self.log_path = log_path

        with open(self.jason_path) as f:
            data = json.load(f)
        self.data = data

        if self.threshold is None and data["harmonic_cycles"]:
            self.threshold = min(c["birth"] for c in data["harmonic_cycles"])

        if self.log_path is None:
            self.log_path = Path.cwd()

    
    def tda_plot(self):
        cycles = self.read_cycles_from_jason()
        D_neighbour = self.neighbourhood_D(cycles)
        D_neighbour[D_neighbour > self.threshold] = 0.0
        simplicies = self.filter_simplicies_threshold_from_jason()
        vis = simplicial_pyvis(
                distance_mat = D_neighbour,
                simplicies = simplicies,
                max_dim = 1,
                cycles = cycles,
                cycle_dim = 1,
                log_path = self.log_path,
                )
        vis.add_graph_to_net()
        vis.make_net()
        print(f"HTML saved to {self.log_path}")


    def read_cycles_from_jason(self):
        cycles = []
        for cycle in self.data[self.which_cycle]:
            if cycle["birth"] <= self.threshold:
                cycles.append([edge["simplex"] for edge in cycle["edges"]])
        return cycles
    
    def filter_D_threshold(self):
            D_ = self.D.deepcopy()
            D_[D_ > self.threshold] = 0.0
            return D_
    
    def filter_simplicies_threshold_from_jason(self):
        with open(self.jason_path, "r") as f:
            data = json.load(f)
        simplicies = {}
        for simplex, birth in zip(data["simplicies"], data["appears_at"]):
            if birth <= self.threshold:
                dim = str(len(simplex) - 1)
                simplicies.setdefault(dim, []).append([simplex, birth])
        return simplicies
    
    def neighbourhood_D(self,cycles):
        def find_all_verts(D,cycles,num_layer):
            cycle_verts = set()
            for cycle in cycles:
                for edge in cycle:
                    cycle_verts.update(edge)
    
            if num_layer == 0:
                return cycle_verts
    
            #expand n layers outward using D adjacency (D[i,j] > 0 = edge)
            all_verts = cycle_verts.copy()
            frontier = cycle_verts.copy()
            for _ in range(num_layer):
                next_frontier = set()
                for v in frontier:
                    neighbours = set(np.where(D[v] > 0)[0].tolist())
                    next_frontier.update(neighbours - all_verts)
                all_verts.update(next_frontier)
                frontier = next_frontier
            return all_verts
        #zero out every row/col not in the expanded vertex set
        all_verts = find_all_verts(self.D,cycles,self.neighbour_layers)
        D_new = np.zeros_like(self.D)
        verts = list(all_verts)
        ix = np.ix_(verts, verts)
        D_new[ix] = self.D[ix]
        return D_new
     
