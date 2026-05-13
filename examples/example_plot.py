import os
import random
import string
import numpy as np
from network_lab_tda.tda_analysis import harmonic_cycle
from network_lab_tda.tda_visualisation.tda_visual import tda_visual_from_jason

HERE = os.path.dirname(os.path.abspath(__file__))

def main():
    #--- set up the distance matrix, replace for you project ---
    # two circles connected by a short bridge → two 1D holes
    n_per_circle = 30
    radius = 1.0
    rng = np.random.default_rng(0)
    theta = np.linspace(0.0, 2.0 * np.pi, n_per_circle, endpoint=False)

    # left circle centered at (-1.1, 0), right circle centered at (1.1, 0)
    # circles touch at the origin
    left = np.column_stack([radius * np.cos(theta) - 1.1, radius * np.sin(theta)])
    right = np.column_stack([radius * np.cos(theta) + 1.1, radius * np.sin(theta)])

    pts = np.vstack([left, right])
    pts = pts + rng.normal(scale=0.05, size=pts.shape)

    n = pts.shape[0]
    D = np.array([[np.linalg.norm(pts[i] - pts[j]) for j in range(n)] for i in range(n)])

#    pts = [(1, 0), (2, 0), (1, 1), (2, 1)]
#    D = np.array([[np.sqrt((x1-x2)**2 + (y1-y2)**2) for x2, y2 in pts] for x1, y1 in pts])

 
    # -- getting harmonic cycles --
    hc = harmonic_cycle(D.tolist(), cycle_dim=1, sim_log=True)
    simplices, appears_at = hc.rips_filtration() 
    hc.compute_harmonics(simplices, appears_at)
    hc.run_harmonics()
    hc.save_log()

    # -- getting the interactive graph  (output -> examples/rips_complex.html)
    index_to_name = {i: "".join(random.choices(string.ascii_letters, k=5)) for i in range(n)}
    plotter = tda_visual_from_jason(
        jason_path=hc.log_path,
        neighbour_layers=False,
        index_to_name=index_to_name
    )
    plotter.cycle_plot()

main()
