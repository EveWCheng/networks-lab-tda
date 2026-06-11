import numpy as np
import networkx as nx
from pyvis.network import Network
from math import floor
import copy
import os

from .Data_Prep import Data_Prep

class Populate_Edge(Data_Prep):
    def __init__(self,filepath=None,matrix=None,log_path=None,epsilon=None):
        super().__init__(filepath=filepath,matrix=matrix,log_path=log_path)
        if epsilon == None:
            self.epsilon = np.min(self.matrix[self.matrix>0])
        else:
            print(f"Epsilon is set to a custom value {epsilon}")
            self.epsilon = epsilon
        self.G = nx.from_numpy_array(self.matrix,edge_attr='length')
        self.max_index = self.matrix.shape[0]
        self.original_node_count = self.matrix.shape[0]
 

    def visualise(self):
        net = Network(notebook=False)
        net.from_nx(self.G)
        for node in net.nodes:
            node["label"] = str(node["id"])
            node["color"] = "#000000" if node["id"] < self.original_node_count else "#ff0000"
        for edge in net.edges:
            edge["label"] = str(round(edge['length'], 3))
        net.write_html(os.path.join(self.log_path,"populated_network.html"))

    def add_nodes_to_one_edge(self,u,v,length):
        number_nodes = floor(length/self.epsilon)-(1 if length % self.epsilon == 0 else 0)
        if number_nodes > 1:
            last_edge_weight = length - number_nodes * self.epsilon
            max_index = self.max_index
            self.G.remove_edge(u,v)
            extra_nodes = []
            for number in range(number_nodes):
                node_name = max_index+number+1
                self.G.add_node(node_name)
                extra_nodes.append(node_name)

            self.G.add_edge(u,extra_nodes[0],length=self.epsilon)
            for i in range(1,number_nodes):
                self.G.add_edge(extra_nodes[i-1],extra_nodes[i],length=self.epsilon)
            self.G.add_edge(extra_nodes[-1],v,length=last_edge_weight)
            self.max_index = max_index + number_nodes

    def populate_edges(self):
        edges = copy.deepcopy(self.G.edges)
        for e in edges:
            u,v = e
            length = self.G.edges[e]['length']
            self.add_nodes_to_one_edge(u,v,length)
        dist_matrix = nx.floyd_warshall_numpy(self.G, weight='length')
        np.savetxt(os.path.join(self.log_path,"populated_distance_matrix.txt"), dist_matrix)
        self.visualise()
        return dist_matrix





