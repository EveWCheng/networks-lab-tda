import os
import numpy as np
from network_lab_tda.tda_analysis import harmonic_cycle
from network_lab_tda.tda_visualisation.tda_plot import tda_plot_from_jason

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

    html_path = os.path.join(HERE, "test_network.html")
    plotter = tda_plot_from_jason(
        jason_path=log_path,
        threshold=None,
        distance_mat=D,
        neighbour_layers=0,
        log_path=html_path,
    )
    plotter.tda_plot()

main()
