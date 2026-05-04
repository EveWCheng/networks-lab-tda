import json
import os
import numpy as np
from pyvis.network import Network


#edit pyvis setup here
def pyvis_setup():
    net = Network(notebook=True,cdn_resources='remote')

    net.set_edge_smooth("continuous")
 
#    net = Network(height="650px", width="100%", bgcolor="#1a1a2e", font_color="white",notebook=False, directed=False)

    net.set_options("""
    {
      "physics": {
        "enabled": true,
        "forceAtlas2Based": {
          "gravitationalConstant": -80,
          "centralGravity": 0.01,
          "springLength": 100,
          "springConstant": 0.08,
          "damping": 0.4,
          "avoidOverlap": 0.5
        },
        "solver": "forceAtlas2Based",
        "stabilization": { "iterations": 200 }
      },
      "nodes": {
        "shape": "dot",
        "size": 5,
        "color": { "background": "#e0e0ff", "border": "#ffffff", "highlight": { "background": "#ffffff", "border": "#ffcc00" } },
        "font": { "size": 15, "color": "#ffffff" }
      },
      "edges": {
        "color": { "color": "#7070cc", "highlight": "#ffcc00" },
        "width": 1
      },
      "interaction": {
        "hover": true,
        "tooltipDelay": 100
      }
    }
                        """)
    return net

def read_cycles_from_jason(cycles_path, threshold):
    with open(cycles_path, "r") as f:
        data = json.load(f)
    cycles = []
    for cycle in data["harmonic_cycles"]:
        if cycle["birth"] <= threshold:
            cycles.append([edge["simplex"] for edge in cycle["edges"]])
    return cycles

def filter_D_threshold(D,threshold):
        D_ = D.deepcopy()
        D_[D_ > threshold] = 0.0
        return D_

#Distance matrix: designed for Rips. but also accepts simplicies
class simplicial_pyvis:
    def __init__(self, max_dim, distance_mat=None, simplicies=None, cycles=None, cycle_dim=None, index_to_name=None, only_neighbourhood=False, neighbour_layers=1, log_path=None):
        if distance_mat is None and simplicies is None:
            raise ValueError("Provide either distance_mat or simplicies.")
        if distance_mat is not None and simplicies is not None:
            raise ValueError("Provide only one of distance_mat or simplicies, not both.")

        self.D = distance_mat
        #dictionary: "0": 0-simplcies, "1": 1-simplicies
        self.simplicies = simplicies
        self.max_dim = max_dim
        # --- cycle-related ---
        #in the form of list of list of simplicies, e.g: [[[1,4],[3,4]],...]
        self.cycles = cycles
        self.cycle_dim = cycle_dim
        self.only_neighbourhood = only_neighbourhood
        self.neighbour_layers = neighbour_layers
        if log_path is None:
            self.log_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "network.html")
        else:
            self.log_path = log_path
        # ---------------------
        if index_to_name is not None:
            self.index_to_name = index_to_name
        elif distance_mat is not None:
            n = distance_mat.shape[0]
            self.index_to_name = dict(zip(range(n), range(n)))
        else:
            n = len(simplicies["0"])
            self.index_to_name = dict(zip(range(n), range(n)))
        self.net = pyvis_setup()
    
   #this needs to be added first, because the package does not overwrite
    def add_cycles(self):
        if self.cycles == None: 
            pass

        if self.cycle_dim == 1:
            for cycle in self.cycles:
                for edge in cycle:
                    source, target = edge
                    self.net.add_edge(source, target, color="red") 
        else:
            print("Warning: add cycles is not well-defined for higher dimensional cycles")

    def add_graph_to_net(self):
        if self.D is not None:
            if self.only_neighbourhood:
                D_new = self.neighbourhood_D()
            else:
                D_new = self.D
            active_nodes = np.where(np.any(D_new > 0, axis=0))[0]
            for node in active_nodes.tolist():
                self.net.add_node(node, label=self.index_to_name[node])

            self.add_cycles()
            rows, cols = np.where(np.triu(D_new) > 0)
            valid = np.isin(rows, active_nodes) & np.isin(cols, active_nodes)
            for r, c in zip(rows[valid].tolist(), cols[valid].tolist()):
                self.net.add_edge(r, c)
        elif self.simplicies is not None:
            nodes = self.simplicies["0"]
            edges = self.simplicies["1"]
            self.net.add_nodes(nodes)
            self.add_cycles()
            self.net.add_edges(edges)

    def make_net(self):
        self.net.show(self.log_path)

    def neighbourhood_D(self):
        D, cycles, num_layer = self.D, self.cycles, self.neighbour_layers

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
        all_verts = find_all_verts(D,cycles,num_layer)
        D_new = np.zeros_like(D)
        verts = list(all_verts)
        ix = np.ix_(verts, verts)
        D_new[ix] = D[ix]
        return D_new
    
    
    





 






 








