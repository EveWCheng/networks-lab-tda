import numpy as np
import networkx as nx
from pyvis.network import Network
import math
import os
import time

from .Data_Prep import Data_Prep

class Populate_Edge(Data_Prep):
    def __init__(self,G,log_path=None,headers=False,header_fn="header.txt",populated_header_fn="populated_headers.txt",epsilon=None,vis=False,num_added = 0):
        super().__init__(G=G,log_path=log_path,headers=headers,header_fn=header_fn)
        if headers:
            headers_path = os.path.join(self.log_path, header_fn)
            with open(headers_path, "r") as f:
                self.headers_list = [line.strip() for line in f.readlines()]
            self.node_labels = dict(enumerate(self.headers_list))
        else:
            self.node_labels = {i: i for i in range(G.number_of_nodes())}
        if epsilon == None:
            self.epsilon = np.percentile([d for _, _, d in G.edges(data='length')], 25)
        else:
            print(f"Epsilon is set to a custom value {epsilon}")
            self.epsilon = epsilon
        self.max_index = G.number_of_nodes()
        self.original_node_count = G.number_of_nodes()
        self.vis = vis
        self.num_added = 0
        self.populated_header_fn = populated_header_fn
 

    def visualise(self,name):
        net = Network(notebook=False)
        net.from_nx(self.G)
        for node in net.nodes:
            node["label"] = str(node["id"])
            node["color"] = "#000000" if node["id"] < self.original_node_count else "#ff0000"
        for edge in net.edges:
            edge["label"] = str(round(edge['length'], 3))
        net.write_html(os.path.join(self.log_path,name))

    def add_nodes_to_one_edge(self,u,v,length):
        number_nodes = math.floor(length/self.epsilon)-(1 if math.isclose(length % self.epsilon, 0) else 0)
        if number_nodes > 1:
            last_edge_weight = length - number_nodes * self.epsilon
            max_index = self.max_index
            self.G.remove_edge(u,v)
            extra_nodes = []
            for number in range(number_nodes):
                node_name = max_index+number+1
                self.G.add_node(node_name)
                self.node_labels[node_name] = node_name
                extra_nodes.append(node_name)

            self.G.add_edge(u,extra_nodes[0],length=self.epsilon)
            for i in range(1,number_nodes):
                self.G.add_edge(extra_nodes[i-1],extra_nodes[i],length=self.epsilon)
            self.G.add_edge(extra_nodes[-1],v,length=last_edge_weight)
            self.max_index = max_index + number_nodes
            self.num_added += number_nodes

    def populate_edges(self):
        if self.vis:
            self.visualise("unpopulated_network.html")
 
        edges = list(self.G.edges(data=False))
        for e in edges:
            u,v = e
            length = self.G.edges[e]['length']
            self.add_nodes_to_one_edge(u,v,length)
        print(f"{self.num_added} nodes added")

        with open(os.path.join(self.log_path, self.populated_header_fn), "w") as f:
            f.write("\n".join(str(v) for v in self.node_labels.values()))

        dist_matrix = nx.floyd_warshall_numpy(self.G, weight='length')
        np.savetxt(os.path.join(self.log_path,"populated_distance_matrix.txt"), dist_matrix)
        print("populated distance matrix is saved")
        if self.vis:
            self.visualise("populated_network.html")
        return dist_matrix





