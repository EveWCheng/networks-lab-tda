#TODO: make example into a function here to plot pyvis
#TODO: add polygons
#TODO: investigate why the nodes are not labelled
#TODO: death time for cycles


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


#Distance matrix: designed for Rips. but also accepts simplicies
class simplicial_pyvis:
    def __init__(self, max_dim, simplicies, distance_mat=None, cycles=None, cycle_dim=None, index_to_name=None, log_path=None):
        self.D = distance_mat
        #dictionary: "0": [[simplex1,birth],[simplex2,birth]], "1": 1-simplicies
        self.simplicies = simplicies
        self.max_dim = max_dim
        # --- cycle-related ---
        #in the form of list of list of simplicies, e.g: [[[1,4],[3,4]],...]
        self.cycles = cycles
        self.cycle_dim = cycle_dim
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
            return None

        if self.cycle_dim == 1:
            for cycle in self.cycles:
                for edge in cycle:
                    source, target = edge
                    self.net.add_edge(source, target, color="red") 
        else:
            print("Warning: add cycles is not well-defined for higher dimensional cycles")

    def add_graph_to_net(self):
        if self.D is not None:
            active_nodes = np.where(np.any(self.D > 0, axis=0))[0]
            for node in active_nodes.tolist():
                self.net.add_node(node, label=self.index_to_name[node])

            self.add_cycles()
            rows, cols = np.where(np.triu(self.D) > 0)
            valid = np.isin(rows, active_nodes) & np.isin(cols, active_nodes)
            for r, c in zip(rows[valid].tolist(), cols[valid].tolist()):
                self.net.add_edge(r, c)
        else:
            nodes = self.simplicies["0"]
            edges = self.simplicies["1"]
            self.net.add_nodes(nodes)
            self.add_cycles()
            self.net.add_edges(edges)

    def add_polygon_to_net(self):
        return None


    def make_net(self):
        self.net.show(self.log_path)

   
    
    





 






 








