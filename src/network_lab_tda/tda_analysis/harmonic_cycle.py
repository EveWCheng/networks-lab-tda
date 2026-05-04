import numpy as np
import matilda
import matilda.prototyping
import matilda.harmonic

from .rips import Rips


class harmonic_cycle(Rips):
    def __init__(self, distance_mat, cycle_dim=1, sim_log=False, log_path=None):
        super().__init__(distance_mat, max_dimension=cycle_dim + 1, log_path=log_path)
        self.cycle_dim = cycle_dim
        self.sim_log = sim_log

    def run_harmonics(self, threshold=float('inf')):
        simplices, appears_at = self.rips_filtration(threshold=threshold, log=self.sim_log)
        return self.compute_harmonics(simplices, appears_at)

    def compute_harmonics(self, simplices, appears_at):
        simplices_np = [np.array(s) for s in simplices]

        K = matilda.prototyping.FilteredSimplicialComplex(
            dimension=self.cycle_dim+1,
            simplices=simplices_np,
            simplices_indices=list(range(len(simplices_np))),
            appears_at=appears_at,
        )

        homology_computer = matilda.PersistentHomologyComputer()
        homology_computer.compute_persistent_homology(K, with_representatives=True, modulus=0)

        harmonic_computer = matilda.harmonic.HarmonicRepresentativesComputer(K, homology_computer)
        harmonic_computer.compute_harmonic_cycles(dim=self.cycle_dim)

        cycles_log = []
        #check if id is the simplex index of cycle's creator
        for i, id_ in enumerate(harmonic_computer.harmonic_cycles[self.cycle_dim].keys()):
            edges = []
            for key, sign in harmonic_computer.harmonic_cycles[self.cycle_dim][id_].items():
                edges.append({"simplex": simplices[key], "weight": float(sign)})
            cycles_log.append({"cycle_index": i, "birth": appears_at[id_], "edges": edges})
        self.log["harmonic_cycles"] = cycles_log

        return harmonic_computer
