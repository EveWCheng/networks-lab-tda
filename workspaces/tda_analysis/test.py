import numpy as np
import gudhi
import json
import matilda
import matilda.prototyping
import matilda.harmonic

# ---------- Rips filtration (from before) ----------

def rips_filtration(D, threshold=float('inf')):
    rips = gudhi.RipsComplex(distance_matrix=D, max_edge_length=threshold)
    st = rips.create_simplex_tree(max_dimension=2)

    filtration = sorted(st.get_filtration(), key=lambda x: x[1])
    simplices = [list(s) for s, _ in filtration]
    births    = [b       for _, b in filtration]
    return simplices, births

def write_filtration_json(simplices, births, path):
    with open(path, "w") as f:
        json.dump({"simplices": simplices, "appears_at": births}, f)

# ---------- Harmonic cycles ----------

def compute_harmonics(simplices, appears_at, dim=1):
    simplices_np = [np.array(s) for s in simplices]

    K = matilda.prototyping.FilteredSimplicialComplex(
        dimension=2,
        simplices=simplices_np,
        simplices_indices=list(range(len(simplices_np))),
        appears_at=appears_at,
    )

    homology_computer = matilda.PersistentHomologyComputer()
    homology_computer.compute_persistent_homology(K, with_representatives=True, modulus=0)

    harmonic_computer = matilda.harmonic.HarmonicRepresentativesComputer(K, homology_computer)
    harmonic_computer.compute_harmonic_cycles(dim=dim, verbose=3)

    print("\n--- Harmonic Cycles ---")
    print(harmonic_computer.harmonic_cycles)

    for i, id in enumerate(harmonic_computer.harmonic_cycles[dim].keys()):
        print(f"\nCycle {i}, id={id}")
        for key, sign in harmonic_computer.harmonic_cycles[dim][id].items():
            print(f"  simplex={key}, weight={sign}")

    return harmonic_computer

# ---------- Main ----------

def main():
    pts = [(1, 0), (2, 0), (1, 1), (2, 1), (1.5,1.2)]
    D = [[np.sqrt((x1-x2)**2 + (y1-y2)**2) for x2, y2 in pts] for x1, y1 in pts]

    simplices, births = rips_filtration(D, threshold=1.5)

    print("Simplex filtration (0-indexed vertices):")
    for s, b in zip(simplices, births):
        print(f"  {s} -> {round(b, 6)}")

    write_filtration_json(simplices, births, "filtration.json")

    compute_harmonics(simplices, births, dim=1)

main()
