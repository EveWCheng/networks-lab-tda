#TODO: death time for cycles
#TODO: harmonic weight apply


import os
import colorsys
import random
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
     "interaction": {
        "hover": true,
        "tooltipDelay": 100
      }
    }
                        """)
    return net


#Distance matrix: designed for Rips. but also accepts simplicies
class simplicial_pyvis:
    def __init__(self, max_dim, simplicies, cycles=None, cycle_dim=1, index_to_name=None, log_path=None):
        #dictionary: "0": {simplex1:birth},{simplex2:birth}, "1": ...
        self.simplicies = simplicies
        self.max_dim = max_dim
        # --- cycle-related ---
        #in the form of list of list of simplicies, e.g: [[[1,4],[3,4]],...]
        self.cycles = cycles
        self.cycle_dim = cycle_dim

        self.log_path = log_path or os.path.join(os.getcwd(), "outputs","network.html")
        os.makedirs(os.path.dirname(self.log_path), exist_ok=True)

        # ---------------------
        if index_to_name is not None:
            self.index_to_name = index_to_name
        else:
            n = len(simplicies["0"])
            self.index_to_name = dict(zip(range(n), range(n)))
        self.net = pyvis_setup()

    def edge_to_length(self, edge):
        return self.simplicies['1'][tuple(sorted(edge))]

    #this needs to be added first, because the package does not overwrite
    def add_cycles(self):
        if self.cycles == None: 
            return None

        if self.cycle_dim == 1:
            n = len(self.cycles)
            hues = [(i + random.random()) / n for i in range(n)]
            random.shuffle(hues)
            colors = [
                "#{:02x}{:02x}{:02x}".format(
                    *(int(255 * c) for c in colorsys.hsv_to_rgb(h, 0.7, 0.95))
                )
                for h in hues
            ]
            for cycle, color in zip(self.cycles, colors):
                edges = []
                for edge in cycle:
                    source, target = edge
                    edges.append(edge)
                    self.net.add_edge(source, target, length = self.edge_to_length(edge),color=color)
        else:
            print("Warning: add cycles is not well-defined for higher dimensional cycles")


    def add_graph_to_net(self):
        nodes = [k[0] for k in self.simplicies["0"].keys()]
        for node in nodes:
            self.net.add_node(node, label=str(self.index_to_name[node]))

        self.add_cycles()

        for source, target in self.simplicies["1"].keys():
            self.net.add_edge(source, target, color="black")

    def make_net(self):
        self.net.show(self.log_path)

   
    
    





 






 








