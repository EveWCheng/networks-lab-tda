import networkx as nx
import numpy as np
import scipy.sparse as sp
from scipy.linalg import null_space, orth

from .rips import Rips


class harmonic_cycle_snapshot(Rips):
    # "fundamental_cycle" is much faster (networkx.cycle_basis is a linear-time graph
    # traversal instead of a dense SVD over the full edge width) but only computes
    # ker(∂_1) -- there's no spanning-tree analogue for ker(∂_p) at p > 1 -- so it's
    # only valid for cycle_dim=1. "stacked_null_space" works for any cycle_dim.
    METHODS = ("fundamental_cycle", "stacked_null_space")

    def __init__(self, distance_mat, thresholds, cycle_dim=1, sim_log=False, log_path=None, method="fundamental_cycle"):
        super().__init__(distance_mat, max_dimension=cycle_dim + 1, log_path=log_path)
        if method == "fundamental_cycle" and cycle_dim != 1:
            raise ValueError("fundamental_cycle method only supports cycle_dim=1")
        self.threshold = thresholds[0]
        self.cycle_dim = cycle_dim
        self.sim_log = sim_log
        self.method = method

    def run_snapshot(self, save=True, atol=1e-8):
        simplices, _ = self.rips_filtration(threshold=self.threshold, log=self.sim_log)
        result = self.compute_snapshot(simplices, self.threshold, atol=atol)

        self.log["harmonic_cycles"] = result
        if save:
            self.save_log()
        return result

    def compute_snapshot(self, simplices, threshold, atol=1e-8):
        simplices_by_dim = self._group_by_dimension(simplices)
        if self.method == "fundamental_cycle":
            harmonic_basis = self._harmonic_basis_fundamental_cycle(simplices_by_dim, self.cycle_dim, atol)
        elif self.method == "stacked_null_space":
            harmonic_basis = self._harmonic_basis_stacked_null_space(simplices_by_dim, self.cycle_dim)
        simplex_list = simplices_by_dim.get(self.cycle_dim, [])
        return self._cycles_log(harmonic_basis, simplex_list, threshold, atol)

    @staticmethod
    def _group_by_dimension(simplices):
        simplices_by_dim = {}
        for simplex in simplices:
            dim = len(simplex) - 1
            simplices_by_dim.setdefault(dim, []).append(tuple(sorted(simplex)))
        return simplices_by_dim

    @staticmethod
    def _boundary_matrix(simplices_by_dim, dim):
        face_index = {face: i for i, face in enumerate(simplices_by_dim.get(dim - 1, []))}
        simplices = simplices_by_dim.get(dim, [])

        rows, cols, signs = [], [], []
        for col, simplex in enumerate(simplices):
            for i in range(len(simplex)):
                face = simplex[:i] + simplex[i + 1:]
                rows.append(face_index[face])
                cols.append(col)
                signs.append((-1) ** i)

        shape = (len(face_index), len(simplices))
        return sp.coo_matrix((signs, (rows, cols)), shape=shape).toarray()

    @classmethod
    def _harmonic_basis_stacked_null_space(cls, simplices_by_dim, dim):
        boundary_p = cls._boundary_matrix(simplices_by_dim, dim)
        boundary_p1 = cls._boundary_matrix(simplices_by_dim, dim + 1)
        return null_space(np.vstack([boundary_p, boundary_p1.T]))

    # ker(boundary_p) restricted to dim=1 is exactly a graph's cycle space, so a spanning
    # tree gives a basis for free (one fundamental cycle per non-tree edge) -- no dense
    # SVD over the full edge width needed, unlike the stacked_null_space method.
    #   CHECK
    @classmethod
    def _harmonic_basis_fundamental_cycle(cls, simplices_by_dim, dim, atol):
        edges = simplices_by_dim.get(dim, [])
        edge_index = {edge: i for i, edge in enumerate(edges)}

        G = nx.Graph()
        G.add_nodes_from(v[0] for v in simplices_by_dim.get(dim - 1, []))
        G.add_edges_from(edges)

        node_cycles = nx.cycle_basis(G)
        raw_cycles = np.zeros((len(edges), len(node_cycles)))
        for col, node_cycle in enumerate(node_cycles):
            k = len(node_cycle)
            for i in range(k):
                a, b = node_cycle[i], node_cycle[(i + 1) % k]
                edge = tuple(sorted((a, b)))
                raw_cycles[edge_index[edge], col] += 1.0 if a < b else -1.0

        boundary_p1 = cls._boundary_matrix(simplices_by_dim, dim + 1)
        boundary_space = orth(boundary_p1) if boundary_p1.shape[1] > 0 else np.zeros((len(edges), 0))

        if boundary_space.shape[1] > 0:
            residual = raw_cycles - boundary_space @ (boundary_space.T @ raw_cycles)
        else:
            residual = raw_cycles

        basis, singular_values, _ = np.linalg.svd(residual, full_matrices=False)
        return basis[:, singular_values > atol]

    @staticmethod
    def _cycles_log(harmonic_basis, simplex_list, threshold, atol):
        cycles_log = []
        for i in range(harmonic_basis.shape[1]):
            edges = [
                {"simplex": list(simplex), "weight": float(weight)}
                for simplex, weight in zip(simplex_list, harmonic_basis[:, i])
                if abs(weight) > atol
            ]
            cycles_log.append({"cycle_index": i, "birth": threshold, "death": None, "edges": edges})
        return cycles_log
