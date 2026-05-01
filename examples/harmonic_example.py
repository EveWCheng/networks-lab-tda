import numpy as np
from tda_analysis import harmonic_cycle


def main():
    pts = [(1, 0), (2, 0), (1, 1), (2, 1), (2.2, 0.5)]
    D = [[np.sqrt((x1-x2)**2 + (y1-y2)**2) for x2, y2 in pts] for x1, y1 in pts]

    hc = harmonic_cycle(D, cycle_dim=1, sim_log=True)
    simplices, births = hc.rips_filtration(threshold=1.5)
    hc.compute_harmonics(simplices, births)
    hc.save_log()


main()
