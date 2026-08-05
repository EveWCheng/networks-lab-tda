import json
import os
import re
import networkx as nx
from pathlib import Path
from pyvis.network import Network
import copy


def load_one_tree(json_path):
    with open(json_path) as json_data:
        data = json.load(json_data)
    return {int(k): tuple(v) for k, v in data.items()}


def networkx_to_tree_groups(G: nx.DiGraph, numeric_labels: bool = False) -> dict:
    leaves = set(n for n in G.nodes() if G.nodes[n].get("is_leaf"))

    for n in G.nodes():
        if n not in leaves:
            G.nodes[n].pop("label", None)

    for leaf in leaves:
        label = G.nodes[leaf]["label"]
        if numeric_labels:
            match = re.search(r'\d+', str(label))
            label = int(match.group()) if match else label
        G.nodes[leaf]["label"] = [label]

    def label_predecessors(frontier):
        if not frontier:
            return
        candidates = set()
        for node in frontier:
            candidates.update(G.predecessors(node))

        newly_labeled = []
        for node in candidates:
            if "label" in G.nodes[node]:
                continue
            children = list(G.successors(node))
            if all("label" in G.nodes[child] for child in children):
                label_set = set()
                for child in children:
                    label_set.update(G.nodes[child]["label"])
                G.nodes[node]["label"] = sorted(label_set)
                newly_labeled.append(node)
        label_predecessors(newly_labeled)

    label_predecessors(leaves)

    tree_groups = {}
    for node in G.nodes():
        label = G.nodes[node]["label"]
        tree_groups.setdefault(len(label), []).append(label)

    return {str(level): tree_groups[level] for level in sorted(tree_groups)}


def networkx_to_tree_json(G: nx.DiGraph, output_path: str, numeric_labels: bool = False) -> dict:
    tree_groups = networkx_to_tree_groups(G, numeric_labels=numeric_labels)
    with open(output_path, "w") as f:
        json.dump(tree_groups, f, indent=4)
    return tree_groups


class TreeBuilder:
    def __init__(self, tree_groups=None):
        self.G = nx.Graph()
        self.n_graph = 0

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

    def add_G_nodes(self, names, flag):
        for name in names:
            node_id = tuple(name)
            if node_id not in self.G:
                self.G.add_node(node_id)
            self.G.nodes[node_id].setdefault("sources", set()).add(flag)

    def add_G_edge(self, u, v):
        if u not in self.G or v not in self.G:
            raise ValueError(f"Node {u} or {v} does not exist in G")
        if self.G.has_edge(u, v):
            self.G.edges[u, v]["n_graph"] += 1
            if self.G.edges[u, v]["n_graph"] == self.n_graph:
                self.G.edges[u, v]["label"] = "true_edge"
        else:
            self.G.add_edge(u, v, n_graph=1)

    def add_tree_nodes(self, flag):
        self.dim += 1
        nodes = self.tree_groups.get(self.dim, [])
        self.add_G_nodes(nodes, flag)
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

    def add_tree(self, flag):
        #add leaves
        self.add_tree_nodes(flag)
        #add the rest:
        while self.dim <= self.max_dim:
            self.add_tree_nodes(flag)
            self.add_tree_edges(n=1,nodes=list(copy.deepcopy(self.nodes)))
        

def build_tree(input_dir: str = None, graphs: list = None, numeric_labels: bool = False):
    builder = TreeBuilder()
    if graphs is not None:
        builder.n_graph = len(graphs)
        for i, G in enumerate(graphs):
            flag = G.graph.get("name", i)
            tree_groups = networkx_to_tree_groups(G, numeric_labels=numeric_labels)
            builder.load_tree(tree_groups)
            builder.add_tree(flag)
    else:
        json_files = list(Path(input_dir).glob("*tree*.json"))
        builder.n_graph = len(json_files)
        for json_file in json_files:
            flag = json_file.stem
            tree_groups = load_one_tree(json_file)
            builder.load_tree(tree_groups)
            builder.add_tree(flag)
    return builder



def visualize(G: nx.Graph, output: str = "tree.html") -> None:
    net = Network()
    def _node_id(node):
        return "_".join(str(x) for x in node) if isinstance(node, tuple) else str(node)
    for node, attrs in G.nodes(data=True):
        label = attrs["label"] if "label" in attrs else node
        net.add_node(_node_id(node), label=_node_id(label))
    for u, v in G.edges():
        net.add_edge(_node_id(u), _node_id(v))
    net.write_html(output)


def merge_trees(input_dir=".", output_dir=".", vis=False, graphs=None, save_json=True, numeric_labels: bool = False):
    builder = build_tree(input_dir=input_dir, graphs=graphs, numeric_labels=numeric_labels)
    if save_json:
        os.makedirs(output_dir, exist_ok=True)
        data = {"1": list(builder.G.nodes()), "2": list(builder.G.edges())}
        with open(os.path.join(output_dir, "merged_tree.json"), "w") as f:
            json.dump(data, f, indent=4, default=list)
    if vis:
        os.makedirs(output_dir, exist_ok=True)
        visualize(builder.G, output=os.path.join(output_dir, "tree.html"))
    return nx.convert_node_labels_to_integers(builder.G, label_attribute="label")


