import json
import os
import networkx as nx
from pathlib import Path
from pyvis.network import Network
import copy


def load_one_tree(json_path):
    with open(json_path) as json_data:
        return {int(k): tuple(v) for k, v in json.load(json_data).items()}


class TreeBuilder:
    def __init__(self, tree_groups=None):
        self.G = nx.Graph()

    def load_tree(self, tree_groups):
        self.tree_groups = tree_groups
        self.max_dim = max(self.tree_groups.keys())
        self.dim = 0
        self.nodes = []

    def previous_nodes(self, n=1):
        return self.tree_groups.get(self.dim - n, [])

    def next_nodes(self, n=1):
        if self.dim + n > self.max_dim:
            return []
        return self.tree_groups.get(self.dim + n, [])

    def add_G_nodes(self, names):
        for name in names:
            node_id = tuple(name)
            self.G.add_node(node_id)

    def add_G_edge(self, u, v):
        if u not in self.G or v not in self.G:
            raise ValueError(f"Node {u} or {v} does not exist in G")
        self.G.add_edge(u, v)

    def add_tree_nodes(self):
        self.dim += 1
        nodes = self.tree_groups.get(self.dim, [])
        self.add_G_nodes(nodes)
        self.nodes = nodes

    def add_tree_edges(self,n,nodes):
        if self.dim - n < 1:
            return
        if all(node == [] for node in nodes):
            return

        for i in range(len(self.nodes)):
            for prev_node in self.previous_nodes(n):
                if set(prev_node).issubset(set(nodes[i])):
                    self.add_G_edge(tuple(prev_node), tuple(self.nodes[i]))
                    for x in prev_node:
                        nodes[i].remove(x)
        self.add_tree_edges(n+1,nodes)

    def add_tree(self):
        #add leaves
        self.add_tree_nodes()
        #add the rest:
        while self.dim <= self.max_dim:
            self.add_tree_nodes() 
            self.add_tree_edges(n=1,nodes=list(copy.deepcopy(self.nodes)))
        

def build_tree(input_dir: str):
    builder = TreeBuilder()
    for json_file in Path(input_dir).glob("*tree*.json"):
        tree_groups = load_one_tree(json_file)
        builder.load_tree(tree_groups)
        builder.add_tree()
    return builder



def visualize(G: nx.Graph, output: str = "tree.html") -> None:
    net = Network()
    def _node_id(node):
        return "_".join(str(x) for x in node) if isinstance(node, tuple) else str(node)
    for node in G.nodes():
        net.add_node(_node_id(node), label=_node_id(node))
    for u, v in G.edges():
        net.add_edge(_node_id(u), _node_id(v))
    net.write_html(output)


def merge_trees(input_dir=".", output_dir=".", vis=False):
    os.makedirs(output_dir, exist_ok=True)
    builder = build_tree(input_dir=input_dir)
    data = {"nodes": list(builder.G.nodes()), "edges": list(builder.G.edges())}
    with open(os.path.join(output_dir, "merged_tree.json"), "w") as f:
        json.dump(data, f, indent=4, default=list)
    if vis:
        visualize(builder.G, output=os.path.join(output_dir, "tree.html"))


