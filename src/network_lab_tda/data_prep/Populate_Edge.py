import numpy as np
import networkx as nx
from pyvis.network import Network
import math
import os
import time
import warnings

from .Data_Prep import Data_Prep

class Populate_Edge(Data_Prep):
    def __init__(self,G,log_path=None,headers=False,header_fn="header.txt",populated_header_fn="populated_headers.txt",epsilon=None,vis=False,max_node_per_edge=5,verbose=False,weight_attr='length'):
        super().__init__(G=G,log_path=log_path,headers=headers,header_fn=header_fn,weight_attr=weight_attr)
        if G.is_directed():
            warnings.warn(
                "Populate_Edge received a directed graph; populate_edges() computes all-pairs distances with nx.floyd_warshall_numpy, which follows edge direction only -- most pairs (e.g. siblings, child->ancestor) will have no directed path and come out as inf. Pass G.to_undirected() if you want real pairwise distances.",
                UserWarning,
            )
        self.verbose = verbose
        if headers:
            headers_path = os.path.join(self.log_path, header_fn)
            with open(headers_path, "r") as f:
                headers_list = [line.strip() for line in f.readlines()]
            self.index_to_name = dict(enumerate(headers_list))
        elif all('label' in attrs for _, attrs in G.nodes(data=True)):
            self.index_to_name = {i: attrs['label'] for i, (_, attrs) in enumerate(G.nodes(data=True))}
        else:
            self.index_to_name = {i: -i for i in range(G.number_of_nodes())}
        if epsilon is None:
            self.epsilon = np.percentile([d for _, _, d in G.edges(data=self.weight_attr)], 40)
        else:
            if self.verbose:
                print(f"Epsilon is set to a custom value {epsilon}")
            self.epsilon = epsilon
        self.max_index = G.number_of_nodes()  # phantom nodes are named "added_node_<i>" (strings), so this is just a label offset, not a collision-avoidance mechanism anymore
        self.original_node_count = G.number_of_nodes()
        self.vis = vis
        self.num_added = 0
        self.populated_header_fn = populated_header_fn
        self.max_node_per_edge = max_node_per_edge
 

    def visualise(self,name):
        net = Network(notebook=False)
        net.from_nx(self.G)
        for node in net.nodes:
            node["label"] = str(node["id"])
            node["color"] = "#ff0000" if isinstance(node["id"], str) and node["id"].startswith("added_node_") else "#000000"
            node["font"] = {"size": 8}
        for edge in net.edges:
            edge["label"] = str(round(edge[self.weight_attr], 3))
            edge["font"] = {"size": 8}
        net.write_html(os.path.join(self.log_path,name))

    def add_nodes_to_one_edge(self,u,v,length):
        number_nodes = math.floor(length/self.epsilon)-(1 if math.isclose(length % self.epsilon, 0) else 0)
        if number_nodes > self.max_node_per_edge:
            number_nodes = self.max_node_per_edge
            edge_weight = length / (number_nodes + 1)
            last_edge_weight = edge_weight
        else:
            edge_weight = self.epsilon
            last_edge_weight = length - number_nodes * self.epsilon
        if number_nodes >= 1:
            max_index = self.max_index
            self.G.remove_edge(u,v)
            extra_nodes = []
            for number in range(number_nodes):
                node_name = f"added_node_{max_index+number}"
                self.G.add_node(node_name)
                self.index_to_name[max_index+number] = node_name
                extra_nodes.append(node_name)

            self.G.add_edge(u,extra_nodes[0],**{self.weight_attr:edge_weight})
            for i in range(1,number_nodes):
                self.G.add_edge(extra_nodes[i-1],extra_nodes[i],**{self.weight_attr:edge_weight})
            self.G.add_edge(extra_nodes[-1],v,**{self.weight_attr:last_edge_weight})
            self.max_index = max_index + number_nodes
            self.num_added += number_nodes

    def populate_edges(self):
        if self.num_added > 0:
            raise RuntimeError("populate_edges() has already been called; create a new Populate_Edge instance to re-populate.")
        if self.vis:
            self.visualise("unpopulated_network.html")
 
        edges = list(self.G.edges(data=False))
        for e in edges:
            u,v = e
            length = self.G.edges[e][self.weight_attr]
            self.add_nodes_to_one_edge(u,v,length)
        print(f"Populate_Edge: added {self.num_added} phantom nodes ({self.original_node_count} -> {self.original_node_count + self.num_added})")

        with open(os.path.join(self.log_path, self.populated_header_fn), "w") as f:
            f.write("\n".join(str(v) for v in self.index_to_name.values()))

        dist_matrix = nx.floyd_warshall_numpy(self.G, weight=self.weight_attr)
        self.matrix = dist_matrix
        np.savetxt(os.path.join(self.log_path,"populated_distance_matrix.txt"), dist_matrix)
        if self.vis:
            self.visualise("populated_network.html")
        return dist_matrix





