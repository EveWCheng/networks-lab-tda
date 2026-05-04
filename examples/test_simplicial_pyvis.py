import json
import os
import numpy as np
from network_lab_tda.tda_analysis import harmonic_cycle
from network_lab_tda.tda_visualisation.simplicial_pyvis import simplicial_pyvis, read_cycles_from_jason

HERE = os.path.dirname(os.path.abspath(__file__))

def main():
    rng = np.random.default_rng(42)
    n = 16
    angles = np.linspace(0, 2 * np.pi, n, endpoint=False)
    pts = np.column_stack([np.cos(angles), np.sin(angles)])
    pts += rng.normal(0, 0.08, pts.shape)

    D = np.array([[np.linalg.norm(pts[i] - pts[j]) for j in range(n)] for i in range(n)])

    log_path = os.path.join(HERE, "test_log.json")
    hc = harmonic_cycle(D.tolist(), cycle_dim=1, sim_log=True, log_path=log_path)
    hc.run_harmonics()
    hc.save_log()

    with open(log_path) as f:
        data = json.load(f)

    if not data["harmonic_cycles"]:
        print("No cycles found.")
        return

    first_birth = min(c["birth"] for c in data["harmonic_cycles"])
    print(f"First cycle birth: {first_birth:.4f}")

    cycles = read_cycles_from_jason(log_path, threshold=first_birth)
    print(f"Cycles at threshold: {len(cycles)}")

    D_vis = D.copy()
    D_vis[D_vis > first_birth+1] = 0.0

    html_path = os.path.join(HERE, "test_network.html")
    vis = simplicial_pyvis(
        max_dim=1,
        distance_mat=D_vis,
        cycles=cycles,
        cycle_dim=1,
        only_neighbourhood=False,
        log_path=html_path,
    )
    vis.add_graph_to_net()
    vis.make_net()
    print(f"Saved to {html_path}")

main()
