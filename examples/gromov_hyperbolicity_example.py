import networkx as nx
from scipy.sparse import csr_matrix

from network_lab_tda.non_treeness.gromov_hyperbolicity import sample_hyperbolicity


def adj(G):
    return csr_matrix(nx.to_scipy_sparse_array(G))


def main():
    # A tree: no loops at all. Trees are exactly 0-hyperbolic, so we expect
    tree = nx.balanced_tree(r=2, h=4)  # 31 nodes, no cycles

    # A graph dominated by big loops: two long cycles glued at one vertex.
    loopy = nx.cycle_graph(20)
    second_cycle = nx.cycle_graph(range(19, 39))  # shares node 19 with the first
    loopy.add_edges_from(second_cycle.edges())

    graphs = {
        "tree (balanced_tree 2,4)": tree,
        "loopy (two 20-cycles glued)": loopy,
    }

    print(f"{'graph':<32} {'delta_max':>10} {'delta_mean':>12}")
    print("-" * 56)
    for name, G in graphs.items():
        #This is the line you need to run your matrix, if you have matrix M, you replace adj(G) with M
        delta_max, delta_mean = sample_hyperbolicity(adj(G), num_samples=20000)
        print(f"{name:<32} {delta_max:>10.3f} {delta_mean:>12.4f}")


main()
