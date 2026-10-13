import numpy as np
import matilda
import matilda.prototyping
import matilda.harmonic

from .rips import Rips


class harmonic_cycle(Rips):
    def __init__(self, distance_mat, cycle_dim=1, sim_log=False, log_path=None, histories=False):
        super().__init__(distance_mat, max_dimension=cycle_dim + 1, log_path=log_path)
        self.cycle_dim = cycle_dim
        self.sim_log = sim_log
        self.histories = histories

    def run_harmonics(self, threshold=float('inf'), save=True):
        simplices, appears_at = self.rips_filtration(threshold=threshold, log=self.sim_log)
        result = self.compute_harmonics(simplices, appears_at)
#        births = {c["birth"] for c in self.log.get("harmonic_cycles", [])}
#        self.log["thresholds"] = sorted(set(self.log.get("thresholds", [])) | births)
        if save:
            self.save_log()
        return result

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

        cycles_log = []
        if homology_computer.persistent_cycles.get(self.cycle_dim):
            bars = homology_computer.bars[self.cycle_dim]
            harmonic_computer.compute_harmonic_cycles(dim=self.cycle_dim)
            #id used for bars and cycles (harmonic.py: line 192)
            before = harmonic_computer.harmonic_cycles_before_projection[self.cycle_dim]
            histories = harmonic_computer.compute_harmonic_histories(self.cycle_dim) if self.histories else None
            for i, id_ in enumerate(harmonic_computer.harmonic_cycles[self.cycle_dim].keys()):
                edges = []
                for key, sign in harmonic_computer.harmonic_cycles[self.cycle_dim][id_].items():
                    edges.append({
                        "simplex": simplices[key],
                        "weight": float(sign),
                        # weight before projecting off the other still-alive cycles, so edges shared with them aren't diluted
                        "weight_before_projection": float(before[id_].get(key, 0.0)),
                    })
                birth, death = bars[id_]
                death = float(death) if np.isfinite(death) else None
                cycle_log = {
                    "cycle_index": i,
                    "birth": float(birth),
                    "death": death,
                    "edges": edges,
                }
                if histories is not None:
                    cycle_log["weight_history"] = [
                        {"simplex": simplices[key], "history": [[t, w] for t, w in points]}
                        for key, points in histories[id_].items()
                    ]
                cycles_log.append(cycle_log)
        self.log["harmonic_cycles"] = cycles_log

        return harmonic_computer
