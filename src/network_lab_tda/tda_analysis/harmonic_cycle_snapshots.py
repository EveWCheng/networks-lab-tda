import bisect

import numpy as np
import scipy.sparse as sp
from scipy.linalg import null_space, orth

from .rips import Rips


class harmonic_cycle_snapshots(Rips):
    def __init__(self, distance_mat, thresholds, cycle_dim=1, sim_log=False, log_path=None):
        super().__init__(distance_mat, max_dimension=cycle_dim + 1, log_path=log_path)
        self.thresholds = sorted(thresholds)
        self.cycle_dim = cycle_dim
        self.sim_log = sim_log

    # Builds the filtration once, up to the largest requested threshold, then reuses it for every threshold below that (each is just a prefix, since appears_at is sorted ascending)
    def run_snapshots(self, save=True, atol=1e-8):
        simplices, appears_at = self.rips_filtration(threshold=self.thresholds[-1], log=self.sim_log)

        results = {}
        for threshold in self.thresholds:
            cutoff = bisect.bisect_right(appears_at, threshold)
            results[threshold] = self.compute_snapshot(simplices[:cutoff], threshold, atol=atol)

        self.log["harmonic_cycles"] = self._flatten_by_birth(results, atol)
        if save:
            self.save_log()
        return results

    # Each cycle above is tagged with the threshold it was computed at, not a true birth
    # time, so the same persistent cycle would otherwise be logged once per threshold
    # it's still alive at -- and with multiplicity > 1 its basis vector can rotate
    # between thresholds, so "same cycle" can't be checked by comparing vectors directly
    # (see harmonic subspace vs. basis vector matching in test_harmonic_cycle_snapshot.py).
    # Sweeping thresholds ascending and keeping only the directions not already spanned
    # by lower thresholds' cycles -- via the same subspace projection _orthogonal_complement
    # already uses for the boundary space -- gives each independent cycle a single entry,
    # at the lowest threshold it appears in, matching harmonic_cycle's birth/death log shape.
    def _flatten_by_birth(self, results, atol):
        all_edges = sorted({tuple(e["simplex"]) for cycles in results.values() for c in cycles for e in c["edges"]})
        edge_index = {edge: i for i, edge in enumerate(all_edges)}

        def to_matrix(cycles):
            matrix = np.zeros((len(edge_index), len(cycles)))
            for col, cycle in enumerate(cycles):
                for e in cycle["edges"]:
                    matrix[edge_index[tuple(e["simplex"])], col] = e["weight"]
            return matrix

        flat_cycles = []
        recorded_basis = np.zeros((len(edge_index), 0))
        for threshold in self.thresholds:
            cycles = results[threshold]
            if not cycles:
                continue

            new_directions = self._orthogonal_complement(to_matrix(cycles), recorded_basis, atol)
            for col in range(new_directions.shape[1]):
                vec = new_directions[:, col]
                edges = [
                    {"simplex": list(edge), "weight": float(vec[idx])}
                    for edge, idx in edge_index.items() if abs(vec[idx]) > atol
                ]
                flat_cycles.append({"cycle_index": len(flat_cycles), "birth": threshold, "death": None, "edges": edges})

            if new_directions.shape[1] > 0:
                recorded_basis = np.hstack([recorded_basis, new_directions])

        return flat_cycles

    def compute_snapshot(self, simplices, threshold, atol=1e-8):
        simplices_by_dim = self._group_by_dimension(simplices)
        cycle_dim = self.cycle_dim

        cycle_space = null_space(self._boundary_matrix(simplices_by_dim, cycle_dim))
        boundary_space = self._boundary_image(simplices_by_dim, cycle_dim + 1)
        harmonic_basis = self._orthogonal_complement(cycle_space, boundary_space, atol)

        simplex_list = simplices_by_dim.get(cycle_dim, [])
        return self._cycles_log(harmonic_basis, simplex_list, threshold, atol)

    @staticmethod
    def _group_by_dimension(simplices):
        simplices_by_dim = {}
        for simplex in simplices:
            dim = len(simplex) - 1
            simplices_by_dim.setdefault(dim, []).append(tuple(sorted(simplex)))
        return simplices_by_dim

    # Matrix of the boundary map C_dim -> C_{dim-1}, in the basis given by simplices_by_dim.
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

    # Orthonormal basis for the image of the boundary map C_dim -> C_{dim-1}.
    @classmethod
    def _boundary_image(cls, simplices_by_dim, dim):
        matrix = cls._boundary_matrix(simplices_by_dim, dim)
        if matrix.shape[1] == 0:
            return np.zeros((matrix.shape[0], 0))
        return orth(matrix)

    # Harmonic representatives = cycles, minus their projection onto the boundaries.
    # A plain rank/orth cutoff with the default relative tolerance isn't safe here:
    # once the projection is subtracted the residual is numerically zero (~1e-16)
    # rather than exactly zero, and a relative tolerance still reads that noise as
    # extra dimensions. So the rank of the harmonic space is taken with an explicit
    # absolute tolerance on the singular values instead.
    @staticmethod
    def _orthogonal_complement(cycle_space, boundary_space, atol):
        if cycle_space.shape[1] == 0:
            return cycle_space

        if boundary_space.shape[1] > 0:
            projection = boundary_space @ (boundary_space.T @ cycle_space)
            residual = cycle_space - projection
        else:
            residual = cycle_space

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
            cycles_log.append({"cycle_index": i, "threshold": threshold, "edges": edges})
        return cycles_log
