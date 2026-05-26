import random
from itertools import combinations

import networkx as nx
import numpy as np

def sample_hyperbolicity(adjacency_matrix, num_samples=50000):
    G = nx.from_scipy_sparse_array(adjacency_matrix)
    assert nx.is_connected(G), "Graph must be connected."

    dist = dict(nx.all_pairs_shortest_path_length(G))

    all_quads = list(combinations(G.nodes(), 4))
    k = min(num_samples, len(all_quads))
    quads = all_quads if k >= len(all_quads) else random.sample(all_quads, k)

    hyps = []
    for u, v, w, x in quads:
        s = sorted([
            dist[u][v] + dist[w][x],
            dist[u][w] + dist[v][x],
            dist[u][x] + dist[v][w],
        ], reverse=True)
        hyps.append((s[0] - s[1]) / 2)

    return np.max(hyps), np.mean(hyps)
