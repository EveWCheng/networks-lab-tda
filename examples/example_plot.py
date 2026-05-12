import os
import numpy as np
from network_lab_tda.tda_analysis import harmonic_cycle
from network_lab_tda.tda_visualisation.tda_visual import tda_visual_from_jason

HERE = os.path.dirname(os.path.abspath(__file__))

def main():
    #--- set up the distance matrix, replace for you project ---
    # three squares chained corner-to-corner: sides 1, 2, and 3
    # — gives three 1D holes of increasing size
    small_square = np.array([
        [0.0, 0.0],
        [1.0, 0.0],
        [1.0, 1.0],
        [0.0, 1.0],
    ])
    # shares (1, 1) with small_square
    medium_square = np.array([
        [3.0, 1.0],
        [3.0, 3.0],
        [1.0, 3.0],
    ])
    # shares (3, 3) with medium_square
    big_square = np.array([
        [6.0, 3.0],
        [6.0, 6.0],
        [3.0, 6.0],
    ])
    pts = np.vstack([small_square, medium_square, big_square])
    n = pts.shape[0]

    D = np.array([[np.linalg.norm(pts[i] - pts[j]) for j in range(n)] for i in range(n)])

#    pts = [(1, 0), (2, 0), (1, 1), (2, 1)]
#    D = np.array([[np.sqrt((x1-x2)**2 + (y1-y2)**2) for x2, y2 in pts] for x1, y1 in pts])

 
    # -- getting harmonic cycles --
    hc = harmonic_cycle(D.tolist(), cycle_dim=1, sim_log=True)
    hc.run_harmonics()
    hc.save_log()

    # -- getting the interactive graph  (output -> examples/rips_complex.html)
    plotter = tda_visual_from_jason(
        jason_path=hc.log_path,
        neighbour_layers=False
    )
    plotter.cycle_plot()

main()
