import os
import numpy as np
import gudhi
import json
import matilda
import matilda.prototyping
import matilda.harmonic

class harmonic_cycle:
    def __init__(self, distance_mat, cycle_dim=1, sim_log=False, log_path=None):
        self.D = distance_mat
        self.cycle_dim = cycle_dim
        self.sim_log = sim_log
        self.log_path = log_path or os.path.join(os.getcwd(), "harmonic_log.json")
        self.log = {}

    def save_log(self):
        with open(self.log_path, "w") as f:
            json.dump(self.log, f, indent=2)

    def rips_filtration(self, threshold=float('inf')):
        rips = gudhi.RipsComplex(distance_matrix=self.D, max_edge_length=threshold)
        st = rips.create_simplex_tree(max_dimension=self.cycle_dim + 1)
        filtration = sorted(st.get_filtration(), key=lambda x: x[1])
        simplices = [list(s) for s, _ in filtration]
        births = [b for _, b in filtration]
        if self.sim_log:
            self.log["simplices"] = simplices
            self.log["appears_at"] = births
        return simplices, births
    
   
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
        for i, id in enumerate(harmonic_computer.harmonic_cycles[self.cycle_dim].keys()):
            edges = []
            for key, sign in harmonic_computer.harmonic_cycles[self.cycle_dim][id].items():
                edges.append({"simplex": simplices[key], "weight": float(sign)})
            cycles_log.append({"cycle_index": i, "edges": edges})
        self.log["harmonic_cycles"] = cycles_log

        return harmonic_computer
    
    

