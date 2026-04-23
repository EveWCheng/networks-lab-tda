import numpy as np
import gudhi

def points_gen():
    n = 100
    theta = np.linspace(0, 2 * np.pi, n)
    noise = 0.05
    points = np.column_stack([
    np.cos(theta) + np.random.randn(n) * noise,
    np.sin(theta) + np.random.randn(n) * noise
])
    return points

def persistence(points):
# --- Build Rips complex and compute persistent homology ---
    rips = gudhi.RipsComplex(points=points, max_edge_length=0.5)
    simplex_tree = rips.create_simplex_tree(max_dimension=2)
    simplex_tree.compute_persistence(homology_coeff_field=2)
    persistence_pairs = simplex_tree.persistence_pairs()
    h1_pairs = [(birth_simplex, death_simplex) for birth_simplex, death_simplex in persistence_pairs if len(birth_simplex) == 2 and len(death_simplex) == 3 ]
    for birth_simplex, death_simplex in h1_pairs:
        birth_val = simplex_tree.filtration(birth_simplex)
        death_val = simplex_tree.filtration(death_simplex)
        print(f"birth={birth_val:.3f}, death={death_val:.3f}, birth_simplex={birth_simplex}, death_simplex={death_simplex}")

def main():
    points = points_gen()
    persistence(points)

main()
