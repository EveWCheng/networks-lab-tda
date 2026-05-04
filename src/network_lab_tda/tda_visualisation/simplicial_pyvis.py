#TODO add appears at for all cycles
#separate the simplicies and appears_at to a different function

#edit pyvis setup here
def pyvis_setup():
    net = Network(height="650px", width="100%", bgcolor="#1a1a2e", font_color="white",notebook=False, directed=False)

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
        "size": 10,
        "color": { "background": "#e0e0ff", "border": "#ffffff", "highlight": { "background": "#ffffff", "border": "#ffcc00" } },
        "font": { "size": 13, "color": "#ffffff" }
      },
      "edges": {
        "color": { "color": "#7070cc", "highlight": "#ffcc00" },
        "width": 1.5,
        "smooth": false
      },
      "interaction": {
        "hover": true,
        "tooltipDelay": 100
      }
    }
                        """)
    return net

def read_cycles_from_jason(cycles_path):
    return None

#Distance matrix: designed for Rips. but also accepts simplicies
class simplicial_pyvis:
    def __init__(self, max_dim, distance_mat=None, simplicies=None, cycles=None, cycle_dim=None, index_to_name=None, only_neiborhood=False):
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
        self.only_neiborhood = only_neiborhood
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
            nodes = range(self.D.shape[1])
            rows, cols = np.where(np.triu(self.D) > 0)
            edge_pos = zip(rows.tolist(), cols.tolist())
            for node in nodes:
                self.net.add_node(node,label=self.index_to_name[node])
            for ind in edge_pos:
                self.net.add_edge(ind[0],ind[1],value=1/(max(D[ind[0],ind[1]],1e-5)))
        elif self.simplicies is not None:
            nodes = self.simplicies["0"]
            edges = self.simplicies["1"]
            self.net.add_nodes(nodes)
            self.net.add_edges(edges)








 






 








